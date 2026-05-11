from typing import Any
from sqlalchemy import select, table, column, func, text
from sqlalchemy_hana.dialect import HANAHDBCLIDialect
from src.core.schema import QueryPlan
from src.graph.schema_graph import SchemaGraph

class HanaQueryCompiler:
    def __init__(self, plan: QueryPlan, bsl_mapping: dict[str, Any]):
        self.plan = plan
        self.bsl_mapping = bsl_mapping
        self.schema_graph = SchemaGraph()

    def _parse_physical_name(self, physical_name: str) -> tuple[str, str]:
        """
        Splits physical_name on the first "." only.
        Returns (schema, table_name) tuple.
        """
        if "." in physical_name:
            schema, table_name = physical_name.split(".", 1)
            return schema, table_name
        return "", physical_name

    def resolve_join_chain(self, bsl_table_keys: list[str]) -> list[dict]:
        if not bsl_table_keys or len(bsl_table_keys) <= 1:
            return []
            
        physical_tables = [self.bsl_mapping["tables"][k]["physical_name"] for k in bsl_table_keys]
        base_table = physical_tables[0]
        
        join_steps = []
        seen_pairs = set()
        
        for target_table in physical_tables[1:]:
            path = self.schema_graph.get_join_path(base_table, target_table)
            if not path:
                raise ValueError(f"No join path exists between {base_table} and {target_table}")
                
            details = self.schema_graph.get_join_details(path)
            for step in details:
                pair1 = (step["from_table"], step["to_table"])
                pair2 = (step["to_table"], step["from_table"])
                if pair1 not in seen_pairs and pair2 not in seen_pairs:
                    join_steps.append(step)
                    seen_pairs.add(pair1)
                    seen_pairs.add(pair2)
                    
        return join_steps

    def compile(self) -> str:
        """
        Compiles the QueryPlan into a raw SAP HANA SQL string.
        """
        self._tables = {}
        def get_table(physical_name: str, col_name: str = None):
            schema_name, tbl_name = self._parse_physical_name(physical_name)
            key = physical_name
            if key not in self._tables:
                self._tables[key] = table(tbl_name, schema=schema_name)
            tbl = self._tables[key]
            if col_name is not None and col_name not in tbl.c:
                tbl.append_column(column(col_name))
            return tbl

        select_columns = []
        group_by_columns = []
        base_physical_table = None

        bsl_keys = []
        
        # Step 1 — Process Dimensions
        for dim_name in self.plan.dimensions:
            dim_info = self.bsl_mapping["dimensions"].get(dim_name)
            if dim_info:
                tbl_key = dim_info["table"]
                if tbl_key not in bsl_keys:
                    bsl_keys.append(tbl_key)
                col_name = dim_info["column"]
                
                physical_name = self.bsl_mapping["tables"][tbl_key]["physical_name"]
                
                col = get_table(physical_name, col_name).c[col_name]
                select_columns.append(col.label(dim_name))
                group_by_columns.append(col)

        # Step 2 — Process Metrics
        for metric_name in self.plan.metrics:
            metric_info = self.bsl_mapping["metrics"].get(metric_name)
            if metric_info:
                tbl_key = metric_info["table"]
                if tbl_key not in bsl_keys:
                    bsl_keys.append(tbl_key)
                col_name = metric_info["column"]
                agg_func_name = metric_info["aggregation"]
                
                physical_name = self.bsl_mapping["tables"][tbl_key]["physical_name"]
                
                agg_expr = getattr(func, agg_func_name)(get_table(physical_name, col_name).c[col_name]).label(metric_name)
                select_columns.append(agg_expr)

        if bsl_keys:
            base_physical_table = self.bsl_mapping["tables"][bsl_keys[0]]["physical_name"]

        # Step 3 — Build SELECT and FROM
        stmt = select(*select_columns)
        
        if len(bsl_keys) > 1:
            join_steps = self.resolve_join_chain(bsl_keys)
            
            from_obj = get_table(base_physical_table)
            joined_tables = {base_physical_table}
            
            for step in join_steps:
                left_t = step["from_table"]
                right_t = step["to_table"]
                left_col = step["from_column"]
                right_col = step["to_column"]
                
                if left_t in joined_tables and right_t not in joined_tables:
                    existing_t, existing_col = left_t, left_col
                    new_t, new_col = right_t, right_col
                elif right_t in joined_tables and left_t not in joined_tables:
                    existing_t, existing_col = right_t, right_col
                    new_t, new_col = left_t, left_col
                else:
                    existing_t, existing_col = left_t, left_col
                    new_t, new_col = right_t, right_col
                
                existing_schema, existing_tbl = self._parse_physical_name(existing_t)
                new_schema, new_tbl = self._parse_physical_name(new_t)
                
                new_table_obj = get_table(new_t)
                from_obj = from_obj.outerjoin(
                    new_table_obj,
                    text(f'"{existing_schema}"."{existing_tbl}"."{existing_col}" = "{new_schema}"."{new_tbl}"."{new_col}"')
                )
                joined_tables.add(new_t)
                joined_tables.add(existing_t)
                
            stmt = stmt.select_from(from_obj)
        elif base_physical_table is not None:
            stmt = stmt.select_from(get_table(base_physical_table))

        # Step 4 — Apply Filters
        for filt in self.plan.filters:
            found_table = base_physical_table
            if len(bsl_keys) > 1:
                for k in bsl_keys:
                    if filt.field in self.bsl_mapping["tables"][k]["columns"]:
                        found_table = self.bsl_mapping["tables"][k]["physical_name"]
                        break
            
            if found_table is None:
                continue
                
            col = get_table(found_table, filt.field).c[filt.field]
            
            if filt.operator == "eq":
                condition = (col == filt.value)
            elif filt.operator == "neq":
                condition = (col != filt.value)
            elif filt.operator == "gt":
                condition = (col > filt.value)
            elif filt.operator == "lt":
                condition = (col < filt.value)
            elif filt.operator == "gte":
                condition = (col >= filt.value)
            elif filt.operator == "lte":
                condition = (col <= filt.value)
            elif filt.operator == "in":
                condition = col.in_(filt.value)
            else:
                raise ValueError(f"Unrecognized operator: {filt.operator}")
            
            stmt = stmt.where(condition)

        # Step 5 — Apply Time Range
        if self.plan.time_range is not None:
            start = self.plan.time_range.start_date
            end = self.plan.time_range.end_date
            if start or end:
                if base_physical_table:
                    stmt = stmt.where(get_table(base_physical_table, 'RECORD_DATE').c['RECORD_DATE'].between(start, end))

        # Step 6 — Apply GROUP BY and LIMIT
        if group_by_columns:
            stmt = stmt.group_by(*group_by_columns)
        
        if self.plan.limit:
            stmt = stmt.limit(self.plan.limit)

        # Step 7 — Compile and Return
        compiled = stmt.compile(
            dialect=HANAHDBCLIDialect(), 
            compile_kwargs={'literal_binds': True}
        )
        return str(compiled)
