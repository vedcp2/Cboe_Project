"""
Defines the /chart-data endpoint for retrieving chart data from Snowflake, with optional date filtering. Used for data visualization features.
"""
from fastapi import APIRouter, HTTPException
import os
import re
import logging
from sqlalchemy import text
from backend.models.schemas import ChartDataRequest
from backend.services.snowflake_service import get_engine

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/chart-data")
def get_chart_data(request: ChartDataRequest):
    """
    Retrieve chart data from a Snowflake table, with optional date filtering.
    Args:
        request (ChartDataRequest): Request model containing table, columns, and date options.
    Returns:
        dict: Chart data, SQL query, and total points.
    Raises:
        HTTPException: If query fails or table name is invalid.
    """
    try:
        engine = get_engine()
        schema = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
        if not re.match(r'^[a-zA-Z0-9_]+$', request.table_name):
            raise HTTPException(status_code=400, detail="Invalid table name")
        qualified_table_name = f'"{schema}"."{request.table_name}"'
        
        sql_parts = []
        
        # Since dates are now stored as DATE type, we can select them directly
        x_column_expr = f'"{request.x_column}" AS x'
        y_column_expr = f'CAST("{request.y_column}" AS FLOAT) AS y'
        
        sql_parts.append(f"SELECT {x_column_expr}, {y_column_expr}")
        sql_parts.append(f"FROM {qualified_table_name}")
        
        # Add date range filtering if provided
        if request.date_range and len(request.date_range) == 2:
            start_date, end_date = request.date_range
            if start_date and end_date:
                # Since dates are stored as DATE type, we can compare directly
                sql_parts.append(f'WHERE "{request.x_column}" BETWEEN \'{start_date}\' AND \'{end_date}\'')
        
        sql_parts.append("ORDER BY x")
        sql_parts.append("LIMIT 1000")
        
        sql_query = " ".join(sql_parts)
        logger.info(f"Chart data SQL query: {sql_query}")
        
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            rows = []
            for row in result:
                rows.append({
                    "x": row[0],
                    "y": float(row[1]) if row[1] is not None else 0.0
                })
        
        return {
            "chart_data": rows,
            "sql_query": sql_query,
            "total_points": len(rows)
        }
    except Exception as e:
        logger.error(f"Error getting chart data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get chart data: {str(e)}") 