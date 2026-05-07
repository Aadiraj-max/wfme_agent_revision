import pandas as pd
import re
from typing import List, Dict, Any
from db_connection import get_hana_engine
from semantic_models import models
from sqlalchemy import text

# Use the vendored Ibis
try:
    from xorq.vendor import ibis as xibis
except ImportError:
    import ibis as xibis

_OPS = {
    "=": lambda col, val: col == val,
    "==": lambda col, val: col == val,
    "!=": lambda col, val: col != val,
    ">": lambda col, val: col > val,
    ">=": lambda col, val: col >= val,
    "<": lambda col, val: col < val,
    "<=": lambda col, val: col <= val,
    "in": lambda col, val: col.isin(val),
    "not in": lambda col, val: col.notin(val),
    "like": lambda col, val: col.like(val),
    "ilike": lambda col, val: col.ilike(val),
    "is null": lambda col, val: col.isnull(),
    "is not null": lambda col, val: col.notnull(),
}

def _build_callable_filters(model, filters_json: List[Dict[str, Any]]):
    callables = []
    dims = model.get_dimensions()
    for f in filters_json:
        field_name = f["field"]
        field_obj = dims.get(field_name)
        if field_obj is None and "." in field_name:
            field_obj = dims.get(field_name.split(".", 1)[1])
        if field_obj is None: continue
        op_fn = _OPS.get(f.get("operator", "="))
        if not op_fn: continue
        expr_fn = field_obj.expr if hasattr(field_obj, "expr") else field_obj
        def make_filter(ex, op, val):
            return lambda t: op(ex(t) if callable(ex) else ex.resolve(t), val)
        callables.append(make_filter(expr_fn, op_fn, f.get("value")))
    return callables

def finalize_hana_sql(sql: str) -> str:
    """
    Manually rewrites the SQL to satisfy HANA's strict GROUP BY requirements.
    It replaces 'GROUP BY 1, 2' with the actual column expressions.
    """
    # 1. Standardize names: replace dots in aliases with underscores
    sql = re.sub(r'AS \"([^\"]+)\.([^\"]+)\"', r'AS "\1_\2"', sql)
    sql = re.sub(r'\"([^\"]+)\"\.\"([^\"]+)\.([^\"]+)\"', r'"\1"."\2_\3"', sql)
    
    # 2. Fix the GROUP BY
    # We find the SELECT block just before the GROUP BY
    # We look for "table"."column" pairs
    group_match = re.search(r'SELECT\s+(.*?)\s+FROM.*?GROUP BY\s+([\d\s,]+)', sql, re.DOTALL | re.IGNORECASE)
    if group_match:
        select_content = group_match.group(1)
        # Extract the dimension columns (ignoring the COUNT(*) or metrics)
        # These are usually the ones that don't have aggregation functions
        select_cols = []
        for part in select_content.split(','):
            part = part.strip()
            if 'COUNT(' not in part.upper() and 'SUM(' not in part.upper():
                # Extract the expression (everything before the 'AS')
                expr = part.split('AS')[0].strip()
                select_cols.append(expr)
        
        if select_cols:
            group_by_replacement = "GROUP BY " + ", ".join(select_cols)
            sql = re.sub(r'GROUP BY\s+[\d\s,]+', group_by_replacement, sql)
            
    return sql

def execute_wfm_query(query_json: Dict[str, Any]):
    model_name = query_json.get("model", "shifts")
    model = models[model_name]
    
    bsl_query = model.query(
        measures=query_json.get("metrics", []),
        dimensions=query_json.get("dimensions", []),
        filters=_build_callable_filters(model, query_json.get("filters", [])),
        limit=query_json.get("limit")
    )
    
    # Use postgres dialect as it's the most compatible base
    raw_sql = xibis.to_sql(bsl_query.to_untagged(), dialect="postgres")
    
    # Apply the HANA Hammer
    hana_sql = finalize_hana_sql(raw_sql)
    
    print("\n[DEBUG] Hammered HANA SQL:")
    print(hana_sql)
    
    engine = get_hana_engine()
    with engine.connect() as conn:
        df = pd.read_sql_query(text(hana_sql), conn)
        return df

if __name__ == "__main__":
    test_intent = {
        "model": "shifts",
        "metrics": ["shifts.shift_count"],
        "dimensions": ["employees.dept_name", "shifts.shift_type"],
        "filters": [{"field": "shifts.status", "operator": "=", "value": "ACTIVE"}],
        "limit": 5
    }
    
    try:
        print("Executing test query...")
        results = execute_wfm_query(test_intent)
        print("\n--- QUERY RESULTS ---")
        print(results)
    except Exception as e:
        import traceback
        print(f"\nExecution Failed: {e}")
        traceback.print_exc()
