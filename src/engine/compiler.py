from typing import Any
from sqlalchemy import text, select, table, column, func
from sqlalchemy.dialects import postgresql # Using a generic dialect or HANA if available
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
        tables_involved = set()

        # Process Dimensions
        for dim_name in self.plan.dimensions:
            dim_info = self.bsl_mapping["dimensions"].get(dim_name)
            if dim_info:
                tbl_key = dim_info["table"]
                col_name = dim_info["column"]
                
                # Get physical table name
                physical_table = self.bsl_mapping["tables"][tbl_key]["physical_name"]
                tables_involved.add(physical_table)
                
                # Create SQLAlchemy column
                col = column(col_name).label(dim_name)
                select_columns.append(col)
                group_by_columns.append(col)

        # Process Metrics
        for metric_name in self.plan.metrics:
            metric_info = self.bsl_mapping["metrics"].get(metric_name)
            if metric_info:
                tbl_key = metric_info["table"]
                col_name = metric_info["column"]
                agg_func_name = metric_info["aggregation"]
                
                # Get physical table name
                physical_table = self.bsl_mapping["tables"][tbl_key]["physical_name"]
                tables_involved.add(physical_table)
                
                # Create SQLAlchemy aggregation
                agg_func = getattr(func, agg_func_name)
                col = agg_func(column(col_name)).label(metric_name)
                select_columns.append(col)

        # Build basic select statement
        stmt = select(*select_columns)

        # Simple FROM clause handling (comma-separated tables for now)
        if tables_involved:
            from_clause = ", ".join(tables_involved)
            stmt = stmt.select_from(text(from_clause))

        # Add GROUP BY if dimensions exist
        if group_by_columns:
            stmt = stmt.group_by(*group_by_columns)

        # Add LIMIT
        if self.plan.limit:
            stmt = stmt.limit(self.plan.limit)

        # Compile to string
        # Note: We use a generic dialect here as a placeholder; 
        # in production, we would use the actual HANA dialect.
        from sqlalchemy.dialects import oracle # Oracle is often similar to HANA in some respects, 
                                               # but let's use the default for simplicity.
        
        # To get the HANA dialect, we would ideally have sqlalchemy-hana installed and imported.
        # For now, we'll use a generic compilation that handles literal binds.
        compiled = stmt.compile(compile_kwargs={"literal_binds": True})
        
        return str(compiled)
