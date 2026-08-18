import os
import re
from typing import Any, Dict, List

import psycopg2
import pandas as pd
from google.adk.tools import ToolContext
from sshtunnel import SSHTunnelForwarder

_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|exec|execute|call|copy|merge|into)\b",
    re.IGNORECASE,
)

SSH_HOST = os.environ["DB_SSH_HOST"]
SSH_PORT = int(os.environ["DB_SSH_PORT"])
SSH_USERNAME = os.environ["DB_SSH_USERNAME"]
SSH_PKEY = os.environ["DB_SSH_PKEY"]
DB_REMOTE_PORT = int(os.environ["DB_REMOTE_PORT"])
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]

_tunnel = None
_connection = None


def get_connection():
    global _tunnel, _connection
    if _tunnel is None or not _tunnel.is_active:
        _tunnel = SSHTunnelForwarder(
            (SSH_HOST, SSH_PORT),
            ssh_username=SSH_USERNAME,
            ssh_pkey=SSH_PKEY,
            remote_bind_address=("localhost", DB_REMOTE_PORT),
        )
        _tunnel.start()
        _connection = None

    if _connection is None or _connection.closed:
        _connection = psycopg2.connect(
            host="localhost",
            port=_tunnel.local_bind_port,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=10,
        )
    return _connection


def run_sql_query(sql_query: str, params=None) -> pd.DataFrame:
    return pd.read_sql_query(sql_query, get_connection(), params=params)


async def run_query(sql_query: str, table_name: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Run a read-only SELECT query against a single Postgres table.

    Args:
        sql_query: A SELECT query. May only reference table_name.
        table_name: The (schema-qualified) table the query is allowed to read from.
    """
    if _FORBIDDEN_KEYWORDS.search(sql_query.strip()):
        return {"status": "error", "message": "Query contains a disallowed keyword."}
    try:
        df = run_sql_query(sql_query)
        return {
            "status": "success",
            "columns": list(df.columns),
            "rows": df.head(50).to_dict(orient="records"),
            "row_count": len(df),
        }
    except Exception as e:
        return {"status": "error", "message": f"{type(e).__name__}: {e}"}


async def get_tables(tool_context: ToolContext) -> List[str]:
    return ["public.sales_salesrawtable", "public.financial_financialrawtab"]


async def get_columns(table_name: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Return the column names and data types for a table.

    Args:
        table_name: The (schema-qualified) table to inspect, e.g. "public.sales_salesrawtable".
    """
    schema, _, name = table_name.rpartition(".")
    schema = schema or "public"
    try:
        df = run_sql_query(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
            """,
            params=(schema, name),
        )
        if df.empty:
            return {"status": "error", "message": f"No columns found for table '{table_name}'."}
        return {"status": "success", "columns": df.to_dict(orient="records")}
    except Exception as e:
        return {"status": "error", "message": f"{type(e).__name__}: {e}"}
