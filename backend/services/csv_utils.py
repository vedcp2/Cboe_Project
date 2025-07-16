"""
Provides utility functions for handling CSV files, including sanitizing table names, inferring column types for Snowflake, and generating SQL for table creation. Used by upload endpoints and services.
"""
import re
import pandas as pd
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Date, Time

def sanitize_table_name(filename: str) -> str:
    """
    Convert a filename to a valid Snowflake table name.
    Replaces invalid characters and ensures the name starts with a letter.
    Args:
        filename (str): The original filename (usually from an uploaded CSV).
    Returns:
        str: A sanitized table name suitable for Snowflake.
    """
    name = re.sub(r'\.csv$', '', filename, flags=re.IGNORECASE)
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    if name and not name[0].isalpha():
        name = 'table_' + name
    return name[:128]

def infer_column_types(df: pd.DataFrame) -> dict:
    """
    Infer Snowflake-compatible column types from a pandas DataFrame.
    Args:
        df (pd.DataFrame): The DataFrame to analyze.
    Returns:
        dict: Mapping of column names to SQLAlchemy types for Snowflake.
    """
    type_mapping = {
        'object': String(16777216),
        'string': String(16777216),
        'int64': Integer,
        'int32': Integer,
        'int16': Integer,
        'int8': Integer,
        'float64': Float,
        'float32': Float,
        'bool': Boolean,
        'datetime64[ns]': DateTime,
        'datetime64[ns, UTC]': DateTime,
        'date': Date,
        'time': Time
    }
    column_types = {}
    for column, dtype in df.dtypes.items():
        clean_column = re.sub(r'[^a-zA-Z0-9_]', '_', str(column))
        if not clean_column[0].isalpha():
            clean_column = 'col_' + clean_column
        pandas_type = str(dtype)
        sqlalchemy_type = type_mapping.get(pandas_type, String(16777216))
        column_types[clean_column] = sqlalchemy_type
    return column_types

def create_table_sql(table_name: str, column_types: dict) -> str:
    """
    Generate a CREATE TABLE SQL statement for Snowflake based on column types.
    Args:
        table_name (str): The name of the table to create.
        column_types (dict): Mapping of column names to SQLAlchemy types.
    Returns:
        str: The CREATE TABLE SQL statement.
    """
    snowflake_type_mapping = {
        'String': 'VARCHAR(16777216)',
        'Integer': 'BIGINT',
        'Float': 'DOUBLE',
        'Boolean': 'BOOLEAN',
        'DateTime': 'TIMESTAMP_NTZ',
        'Date': 'DATE',
        'Time': 'TIME'
    }
    columns = []
    for col_name, sqlalchemy_type in column_types.items():
        type_name = sqlalchemy_type.__class__.__name__
        snowflake_type = snowflake_type_mapping.get(type_name, 'VARCHAR(16777216)')
        columns.append(f'"{col_name}" {snowflake_type}')
    return f'CREATE OR REPLACE TABLE {table_name} ({", ".join(columns)})' 