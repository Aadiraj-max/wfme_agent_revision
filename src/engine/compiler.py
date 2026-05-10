from typing import Any
from sqlalchemy import select, table, column, func
from sqlalchemy_hana.dialect import HANADialect
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

        # Process Dimensions
        for dim_name in self.plan.dimensions:
            dim_info = self.bsl_mapping["dimensions"].get(dim_name)
            if dim_info:
                tbl_key = dim_info["table"]
                col_name = dim_info["column"]
                
                # Set base physical table if not already set
                physical_table_name = self.bsl_mapping["tables"][tbl_key]["physical_name"]
                if base_physical_table is None:
                    base_physical_table = physical_table_name
                
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
                
                # Set base physical table if not already set
                physical_table_name = self.bsl_mapping["tables"][tbl_key]["physical_name"]
                if base_physical_table is None:
                    base_physical_table = physical_table_name
                
                # Create SQLAlchemy aggregation
                agg_func = getattr(func, agg_func_name)
                col = agg_func(column(col_name)).label(metric_name)
                select_columns.append(col)

        # Build basic select statement
        stmt = select(*select_columns)

        # Use the table of the first metric or dimension as the FROM clause
        # This avoids Cartesian products before join logic is implemented.
        if base_physical_table:
            stmt = stmt.select_from(table(base_physical_table))

        # Add GROUP BY if dimensions exist
        if group_by_columns:
            stmt = stmt.group_by(*group_by_columns)

        # Add LIMIT
        if self.plan.limit:
            stmt = stmt.limit(self.plan.limit)

        # Compile using the specific HANA dialect to ensure valid SAP HANA SQL
        compiled = stmt.compile(
            dialect=HANADialect(), 
            compile_kwargs={"literal_binds": True}
        )
        
        return str(compiled)
