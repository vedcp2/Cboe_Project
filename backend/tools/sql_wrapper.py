# backend/tools/sql_wrapper.py

import os
from dotenv import load_dotenv
from sqlalchemy.engine import URL, create_engine
from sqlalchemy import text

load_dotenv()

def get_snowflake_engine():
    url = URL.create(
        drivername="snowflake",
        username=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        host=os.getenv("SNOWFLAKE_ACCOUNT"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        query={
            "schema": os.getenv("SNOWFLAKE_SCHEMA"),
            "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
            "role": os.getenv("SNOWFLAKE_ROLE", "SYSADMIN")
        }
    )

    engine = create_engine(url)

    # Explicitly set warehouse for safety
    with engine.connect() as conn:
        conn.execute(text(f"USE WAREHOUSE {os.getenv('SNOWFLAKE_WAREHOUSE')}"))

    return engine
