from typing import Any, Literal, Optional, List
from pydantic import BaseModel, Field

# --- Legacy Schemas for backward compatibility ---

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

class MultiQueryPlan(BaseModel):
    """
    Used to decompose complex user prompts into discrete, independently executable SQL queries.
    """
    queries: list[QueryPlan] = Field(
        default_factory=list,
        description="A list of distinct QueryPlan objects representing the decomposed intents."
    )

# --- New Dynamic Schema Reflection Models (Phase 4) ---

class CubeFilter(BaseModel):
    member: str = Field(
        ..., 
        description="The fully qualified dimension or measure to filter on (e.g., 'UserDetails.gender')."
    )
    operator: str = Field(
        ..., 
        description="The operator for filter comparison (e.g., 'equals', 'contains', 'gt', 'lt', 'inDateRange', etc.)."
    )
    values: List[str] = Field(
        ..., 
        description="List of string values to filter by."
    )

class CubeTimeDimension(BaseModel):
    dimension: str = Field(
        ..., 
        description="The fully qualified time dimension (e.g., 'EmpPlanning.workdate')."
    )
    dateRange: List[str] = Field(
        ..., 
        description="List containing start date and end date in YYYY-MM-DD format (e.g., ['2026-05-01', '2026-05-31'])."
    )

class CubeQuery(BaseModel):
    measures: List[str] = Field(
        default_factory=list, 
        description="List of fully qualified measures (e.g., ['RosterItem.totalHoursSum'])."
    )
    dimensions: List[str] = Field(
        default_factory=list, 
        description="List of fully qualified dimensions (e.g., ['Locations.locationdesc'])."
    )
    timeDimensions: List[CubeTimeDimension] = Field(
        default_factory=list, 
        description="List of time dimensions and their date ranges."
    )
    filters: List[CubeFilter] = Field(
        default_factory=list, 
        description="List of filter conditions to apply."
    )
    limit: Optional[int] = Field(
        100, 
        description="The maximum number of rows to return. Default is 100."
    )

class UnifiedCubeQueryPlan(BaseModel):
    query: CubeQuery = Field(
        ..., 
        description="The main Cube query payload matching Cube's /load API contract."
    )
