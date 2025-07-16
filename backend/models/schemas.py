"""
Defines Pydantic models (schemas) for request and response validation in the API. These models ensure that incoming and outgoing data is structured and validated consistently across endpoints.
"""
from pydantic import BaseModel
from typing import Optional, List

class Query(BaseModel):
    """Model for a query request containing a user question."""
    question: str

class ChartDataRequest(BaseModel):
    """Model for requesting chart data, including table and column info, and optional date filtering."""
    table_name: str
    x_column: str
    y_column: str
    date_range: Optional[List[str]] = None 