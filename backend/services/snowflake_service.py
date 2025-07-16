"""
Contains logic for interacting with the Snowflake database, including table creation, data insertion, table listing, row counting, and deletion. Used by routers to perform database operations.
"""
import os
from backend.tools.sql_wrapper import get_snowflake_engine
from sqlalchemy import text
import logging
import pandas as pd
import tempfile
import csv

logger = logging.getLogger(__name__)

def get_engine():
    """
    Get a SQLAlchemy engine for connecting to Snowflake.
    Returns:
        Engine: SQLAlchemy engine instance.
    """
    return get_snowflake_engine()

def create_table(engine, create_sql):
    with engine.begin() as conn:
        conn.execute(text(create_sql))

def insert_dataframe(engine, df, table_name, column_types):
    """
    Insert a pandas DataFrame into a Snowflake table.
    Args:
        engine: SQLAlchemy engine.
        df (pd.DataFrame): Data to insert.
        table_name (str): Name of the table.
        column_types (dict): Mapping of column names to SQLAlchemy types.
    Returns:
        int: Number of rows inserted.
    """
    with engine.begin() as conn:
        df.to_sql(
            name=table_name,
            con=conn,
            if_exists='append',
            index=False,
            method='multi',
            dtype=column_types
        )
        count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        row_count = count_result.fetchone()[0]
    return row_count

def insert_dataframe_with_date_parsing(engine, df, table_name, column_types, date_formats_dict):
    """
    Insert a pandas DataFrame into a Snowflake table with date parsing using TO_DATE.
    Args:
        engine: SQLAlchemy engine.
        df (pd.DataFrame): Data to insert.
        table_name (str): Name of the table.
        column_types (dict): Mapping of column names to SQLAlchemy types.
        date_formats_dict (dict): Mapping of column names to date formats.
    Returns:
        int: Number of rows inserted.
    """
    schema = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
    qualified_table_name = f'"{schema}"."{table_name}"'
    
    with engine.begin() as conn:
        # Create a temporary table to hold the raw data
        temp_table_name = f"temp_{table_name}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
        temp_qualified_table_name = f'"{schema}"."{temp_table_name}"'
        
        # Create temporary table with all columns as VARCHAR
        temp_column_types = {}
        for col_name in column_types.keys():
            from sqlalchemy import String
            temp_column_types[col_name] = String(16777216)
        
        # Create temp table SQL
        temp_columns = []
        for col_name in temp_column_types.keys():
            temp_columns.append(f'"{col_name}" VARCHAR(16777216)')
        temp_create_sql = f'CREATE OR REPLACE TABLE {temp_qualified_table_name} ({", ".join(temp_columns)})'
        
        logger.info(f"Creating temporary table: {temp_create_sql}")
        conn.execute(text(temp_create_sql))
        
        # Insert raw data into temporary table
        df.to_sql(
            name=temp_table_name,
            con=conn,
            if_exists='append',
            index=False,
            method='multi',
            dtype=temp_column_types
        )
        
        # Build INSERT INTO main table with date parsing
        column_names = list(column_types.keys())
        select_columns = []
        
        for col_name in column_names:
            if col_name in date_formats_dict:
                # Convert pandas date format to Snowflake format
                pandas_format = date_formats_dict[col_name]
                snowflake_format = convert_pandas_to_snowflake_format(pandas_format)
                select_columns.append(f'TO_DATE("{col_name}", \'{snowflake_format}\') AS "{col_name}"')
                logger.info(f"Converting column {col_name} from format {pandas_format} to Snowflake format {snowflake_format}")
            else:
                select_columns.append(f'"{col_name}"')
        
        # Insert from temp table to main table with date conversion
        insert_sql = f"""
        INSERT INTO {qualified_table_name} ({', '.join([f'"{col}"' for col in column_names])})
        SELECT {', '.join(select_columns)}
        FROM {temp_qualified_table_name}
        """
        
        logger.info(f"Inserting with date parsing: {insert_sql}")
        conn.execute(text(insert_sql))
        
        # Clean up temporary table
        conn.execute(text(f"DROP TABLE {temp_qualified_table_name}"))
        
        # Get row count
        count_result = conn.execute(text(f"SELECT COUNT(*) FROM {qualified_table_name}"))
        row_count = count_result.fetchone()[0]
    
    return row_count

def convert_pandas_to_snowflake_format(pandas_format):
    """
    Convert pandas date format to Snowflake date format.
    Args:
        pandas_format (str): Pandas date format (e.g., 'YYYY-MM-DD', 'MM/DD/YYYY')
    Returns:
        str: Snowflake date format (e.g., 'YYYY-MM-DD', 'MM/DD/YYYY')
    """
    # Most formats are the same between pandas and Snowflake
    # Just need to handle any specific differences
    format_mapping = {
        'YYYY-MM-DD': 'YYYY-MM-DD',
        'MM/DD/YYYY': 'MM/DD/YYYY',
        'DD-MM-YYYY': 'DD-MM-YYYY',
        'MM-DD-YYYY': 'MM-DD-YYYY',
        'YYYY/MM/DD': 'YYYY/MM/DD',
        'DD/MM/YYYY': 'DD/MM/YYYY'
    }
    
    return format_mapping.get(pandas_format, pandas_format)

def list_tables(engine, schema):
    with engine.connect() as conn:
        result = conn.execute(text(f"SHOW TABLES IN SCHEMA {schema}"))
        tables = []
        for row in result:
            table_info = {
                "name": row[1],
                "database": row[2],
                "schema": row[3],
                "kind": row[4],
                "comment": row[5] if row[5] else None
            }
            tables.append(table_info)
        return tables

def table_exists(engine, schema, table_name):
    """
    Check if a table exists in the specified schema.
    Args:
        engine: SQLAlchemy engine.
        schema (str): Schema name.
        table_name (str): Table name.
    Returns:
        bool: True if table exists, False otherwise.
    """
    tables = list_tables(engine, schema)
    return any(table["name"].upper() == table_name.upper() for table in tables)

def get_table_row_count(engine, schema, table_name):
    with engine.connect() as conn:
        count_result = conn.execute(text(f'SELECT COUNT(*) FROM "{schema}"."{table_name}"'))
        return count_result.fetchone()[0]

def drop_table(engine, schema, table_name):
    """
    Drop a table from Snowflake if it exists.
    Args:
        engine: SQLAlchemy engine.
        schema (str): Schema name.
        table_name (str): Table name.
    """
    with engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS \"{schema}\".\"{table_name}\"")) 