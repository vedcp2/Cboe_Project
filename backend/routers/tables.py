"""
Defines endpoints for listing tables, previewing table data, and deleting tables in Snowflake. Used for dataset management in the web app.
"""
from fastapi import APIRouter, HTTPException, Body
import os
import re
import logging
from backend.services.snowflake_service import get_engine, list_tables, get_table_row_count, drop_table
from sqlalchemy import text

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/list-tables")
def list_tables_route():
    """
    List all tables in the configured Snowflake schema, including row counts.
    Returns:
        dict: List of tables, schema name, and total table count.
    Raises:
        HTTPException: If listing fails.
    """
    try:
        engine = get_engine()
        schema = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
        tables = list_tables(engine, schema)
        for table in tables:
            try:
                table["row_count"] = get_table_row_count(engine, schema, table["name"])
            except Exception as e:
                logger.warning(f"Could not get row count for {table['name']}: {e}")
                table["row_count"] = 0
        return {
            "tables": tables,
            "schema": schema,
            "total_tables": len(tables)
        }
    except Exception as e:
        logger.error(f"Error listing tables: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list tables: {str(e)}")

@router.get("/table-preview")
def get_table_preview(table_name: str):
    """
    Get a preview (first 5 rows) and column names for a specific table in Snowflake.
    Args:
        table_name (str): Name of the table to preview.
    Returns:
        dict: Columns, rows, and table metadata.
    Raises:
        HTTPException: If preview fails or table name is invalid.
    """
    try:
        engine = get_engine()
        schema = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
        if not re.match(r'^[a-zA-Z0-9_]+$', table_name):
            raise HTTPException(status_code=400, detail="Invalid table name")
        qualified_table_name = f'"{schema}"."{table_name}"'
        with engine.connect() as conn:
            columns_result = conn.execute(text(f"DESCRIBE TABLE {qualified_table_name}"))
            columns = [row[0] for row in columns_result if row[2] == 'COLUMN']
            preview_result = conn.execute(text(f"SELECT * FROM {qualified_table_name} LIMIT 5"))
            rows = [list(row) for row in preview_result]
            return {
                "columns": columns,
                "rows": rows,
                "table_name": table_name,
                "qualified_table_name": qualified_table_name
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting table preview for {table_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get table preview: {str(e)}")

@router.get("/table-date-range")
def get_table_date_range(table_name: str, date_column: str):
    """
    Get the min and max dates from a specific date column in a table.
    Args:
        table_name (str): Name of the table.
        date_column (str): Name of the date column.
    Returns:
        dict: Min and max dates from the column.
    Raises:
        HTTPException: If query fails or table/column name is invalid.
    """
    try:
        engine = get_engine()
        schema = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
        if not re.match(r'^[a-zA-Z0-9_]+$', table_name):
            raise HTTPException(status_code=400, detail="Invalid table name")
        if not re.match(r'^[a-zA-Z0-9_]+$', date_column):
            raise HTTPException(status_code=400, detail="Invalid column name")
        
        qualified_table_name = f'"{schema}"."{table_name}"'
        qualified_column_name = f'"{date_column}"'
        
        with engine.connect() as conn:
            # Get min and max dates from the full table
            result = conn.execute(text(
                f"SELECT MIN({qualified_column_name}) as min_date, MAX({qualified_column_name}) as max_date "
                f"FROM {qualified_table_name} "
                f"WHERE {qualified_column_name} IS NOT NULL"
            ))
            row = result.fetchone()
            
            if row and row[0] and row[1]:
                return {
                    "min_date": str(row[0]),
                    "max_date": str(row[1]),
                    "table_name": table_name,
                    "date_column": date_column
                }
            else:
                return {
                    "min_date": "",
                    "max_date": "",
                    "table_name": table_name,
                    "date_column": date_column
                }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting date range for {table_name}.{date_column}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get date range: {str(e)}")

@router.delete("/delete-table")
def delete_table_route(table_name: str = Body(..., embed=True)):
    try:
        engine = get_engine()
        schema = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
        if not re.match(r'^[a-zA-Z0-9_]+$', table_name):
            raise HTTPException(status_code=400, detail="Invalid table name")
        drop_table(engine, schema, table_name)
        return {"success": True, "message": f"Table '{table_name}' deleted from Snowflake."}
    except Exception as e:
        logger.error(f"Error deleting table {table_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete table: {str(e)}") 