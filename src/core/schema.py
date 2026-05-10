from typing import Any, Literal, Optional
from pydantic import BaseModel, Field

class FilterCondition(BaseModel):
    """
    Represents a single filter condition applied to a business field.
    """
    field: str = Field(
        ..., 
        description="The name of the business field to filter on (e.g., 'country_code')."
    )
    operator: Literal["eq", "neq", "gt", "lt", "gte", "lte", "in"] = Field(
        ..., 
        description="The comparison operator for the filter."
    )
    value: Any = Field(
        ..., 
        description="The value to compare against. Can be a string, number, or list (for 'in' operator)."
    )

class TimeRange(BaseModel):
    """
    Defines a temporal boundary for the query.
    """
    start_date: Optional[str] = Field(
        None, 
        description="The starting date for the query range in ISO format (e.g., '2023-01-01')."
    )
    end_date: Optional[str] = Field(
        None, 
        description="The ending date for the query range in ISO format (e.g., '2023-12-31')."
    )

class QueryPlan(BaseModel):
    """
    The main execution contract consumed by the query engine to generate SQL for SAP HANA.
    """
    metrics: list[str] = Field(
        default_factory=list, 
        description="List of business metrics to aggregate (e.g., ['total_revenue', 'headcount'])."
    )
    dimensions: list[str] = Field(
        default_factory=list, 
        description="List of dimensions to group the metrics by (e.g., ['region', 'department'])."
    )
    filters: list[FilterCondition] = Field(
        default_factory=list, 
        description="List of filter conditions to apply to the dataset."
    )
    time_range: Optional[TimeRange] = Field(
        None, 
        description="Optional time range boundary for the query."
    )
    limit: int = Field(
        100, 
        description="The maximum number of rows to return. Default is 100."
    )
