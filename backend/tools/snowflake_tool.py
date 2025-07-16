# Zboe-intelligence-hub/backend/tools/snowflake_tool.py

import os
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

def test_snowflake_connection():
    try:
        conn = snowflake.connector.connect(
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA")
        )

        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_VERSION()")
        version = cursor.fetchone()
        cursor.close()
        conn.close()

        return f"Snowflake connected! Version: {version[0]}"
    except Exception as e:
        return f"Snowflake connection failed: {e}"
