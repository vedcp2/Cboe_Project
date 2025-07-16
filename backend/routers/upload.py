"""
Defines the /upload-csv endpoint for uploading CSV files and creating corresponding tables in Snowflake. 
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from typing import Optional
import pandas as pd
import io
import os
import logging
from backend.models.schemas import ChartDataRequest
from backend.services.csv_utils import sanitize_table_name, infer_column_types, create_table_sql
from backend.services.snowflake_service import get_engine, create_table, insert_dataframe_with_date_parsing, table_exists
import re
import json

router = APIRouter()
logger = logging.getLogger(__name__)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

@router.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    table_name: Optional[str] = Form(None),
    date_formats: Optional[str] = Form(None)
):
    """
    Upload a CSV file and create a corresponding table in Snowflake.
    Validates the file, parses CSV, infers column types, creates the table, and inserts data.
    Args:
        file (UploadFile): The uploaded CSV file.
        table_name (Optional[str]): Optional custom table name.
        date_formats (Optional[str]): JSON string of date formats for detected date columns.
    Returns:
        dict: Information about the created table and upload status.
    Raises:
        HTTPException: If validation or upload fails.
    """
    logger.info(f"Starting CSV upload: {file.filename}")
    try:
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB")
        try:
            df = pd.read_csv(io.BytesIO(content))
            logger.info(f"CSV parsed successfully. Shape: {df.shape}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")
        if df.empty:
            raise HTTPException(status_code=400, detail="CSV file is empty")
        original_columns = df.columns.tolist()
        df.columns = [re.sub(r'[^a-zA-Z0-9_]', '_', str(col)) for col in df.columns]
        df.columns = ['col_' + col if not col[0].isalpha() else col for col in df.columns]
        logger.info(f"Columns cleaned: {original_columns} → {df.columns.tolist()}")
        schema = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
        final_table_name = sanitize_table_name(table_name or file.filename)
        qualified_table_name = f'"{schema}"."{final_table_name}"'
        try:
            engine = get_engine()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Snowflake connection failed: {str(e)}")
        
        # Check if table already exists
        if table_exists(engine, schema, final_table_name):
            raise HTTPException(status_code=400, detail=f"Table '{final_table_name}' already exists. Please choose a different name or delete the existing table first.")
        
        try:
            # Detect potential date columns
            date_columns = [col for col in df.columns if any(keyword in col.lower() for keyword in ["date", "timestamp", "time"])]
            if date_columns and not date_formats:
                # Prompt user for date format
                date_format_prompts = {col: f"We detected a date column named {col}. Please specify its format (e.g., MM-DD-YYYY, YYYY-MM-DD)." for col in date_columns}
                return {
                    "message": "Date format required",
                    "date_format_prompts": date_format_prompts
                }
            
            # Parse date formats if provided
            date_formats_dict = {}
            if date_formats:
                try:
                    date_formats_dict = json.loads(date_formats)
                    logger.info(f"Date formats provided: {date_formats_dict}")
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Invalid date_formats: {str(e)}")
            
            logger.info("Starting column type inference...")
            column_types = infer_column_types(df)
            logger.info(f"Inferred column types: {column_types}")
            
            # Force date columns to be Date type if user provided formats
            if date_formats_dict:
                from sqlalchemy import Date
                for col in date_formats_dict.keys():
                    if col in column_types:
                        column_types[col] = Date()
                        logger.info(f"Set column {col} to Date type")
            
            create_sql = create_table_sql(qualified_table_name, column_types)
            logger.info(f"Creating table with SQL: {create_sql}")
            create_table(engine, create_sql)
            
            # Insert data with date parsing
            row_count = insert_dataframe_with_date_parsing(engine, df, final_table_name, column_types, date_formats_dict)
            logger.info(f"Successfully inserted {row_count} rows")
            
            preview_data = df.head(5).to_dict('records')
            column_types_response = {}
            type_mapping = {
                'String': 'VARCHAR(16777216)',
                'Integer': 'BIGINT',
                'Float': 'DOUBLE',
                'Boolean': 'BOOLEAN',
                'DateTime': 'TIMESTAMP_NTZ',
                'Date': 'DATE',
                'Time': 'TIME'
            }
            for col_name, sqlalchemy_type in column_types.items():
                type_name = sqlalchemy_type.__class__.__name__
                snowflake_type = type_mapping.get(type_name, 'VARCHAR(16777216)')
                column_types_response[col_name] = snowflake_type
            return {
                "message": f"Successfully uploaded and inserted {row_count} rows into {qualified_table_name}",
                "preview_data": preview_data,
                "column_types": column_types_response,
                "table_name": final_table_name,
                "qualified_table_name": qualified_table_name,
                "row_count": row_count
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload CSV: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in upload_csv: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}") 