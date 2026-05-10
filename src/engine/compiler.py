from typing import Any
from sqlalchemy import select, table, column, func
from sqlalchemy_hana.dialect import HANAHDBCLIDialect
from src.core.schema import QueryPlan

class HanaQueryCompiler:
    def __init__(self, plan: QueryPlan, bsl_mapping: dict[str, Any]):
        self.plan = plan
        self.bsl_mapping = bsl_mapping

    def compile(self) -> str:
        """
        Compiles the QueryPlan into a raw SAP HANA SQL string.
        """
        select_columns = []
        group_by_columns = []
        base_physical_table = None

        # Step 1 — Process Dimensions
        for dim_name in self.plan.dimensions:
            dim_info = self.bsl_mapping["dimensions"].get(dim_name)
            if dim_info:
                tbl_key = dim_info["table"]
                col_name = dim_info["column"]
                
                physical_name = self.bsl_mapping["tables"][tbl_key]["physical_name"]
                if base_physical_table is None:
                    base_physical_table = physical_name
                
                col = column(col_name).label(dim_name)
                select_columns.append(col)
                group_by_columns.append(col)

        # Step 2 — Process Metrics
        for metric_name in self.plan.metrics:
            metric_info = self.bsl_mapping["metrics"].get(metric_name)
            if metric_info:
                tbl_key = metric_info["table"]
                col_name = metric_info["column"]
                agg_func_name = metric_info["aggregation"]
                
                physical_name = self.bsl_mapping["tables"][tbl_key]["physical_name"]
                if base_physical_table is None:
                    base_physical_table = physical_name
                
                agg_expr = getattr(func, agg_func_name)(column(col_name)).label(metric_name)
                select_columns.append(agg_expr)

        # Step 3 — Build SELECT and FROM
        stmt = select(*select_columns)
        if base_physical_table is not None:
            stmt = stmt.select_from(table(base_physical_table))

        # Step 4 — Apply Filters
        for filt in self.plan.filters:
            col = column(filt.field)
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
                # This column name 'RECORD_DATE' must be replaced per table in a future sprint.
                stmt = stmt.where(column('RECORD_DATE').between(start, end))

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
