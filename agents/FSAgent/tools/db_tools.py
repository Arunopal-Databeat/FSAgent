import os
import re
from typing import Any, Dict, List

import psycopg2
import pandas as pd
from google.adk.tools import ToolContext

_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|exec|execute|call|copy|merge|into)\b",
    re.IGNORECASE,
)

# Agent runs on the same host as the Postgres container, which publishes its
# port directly (docker ps confirms 0.0.0.0:5433->5432/tcp) -- no SSH tunnel
# needed. This previously tunneled from a developer's laptop into a remote
# EC2 box; that's no longer the topology now that the agent itself runs on
# that box.
DB_HOST = os.environ["DB_HOST"]
DB_PORT = int(os.environ["DB_PORT"])
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]

_connection = None


def get_connection():
    global _connection
    if _connection is None or _connection.closed:
        _connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
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
    return ["public.financial_cp_portfolio_lead_mapped", "public.financial_db_actual_backlog", "public.financial_db_fy27_plan_target", "public.financial_mm_actual_backlog", "public.financial_mm_fy27_plan", "public.financial_mm_target_with_portfolio_fy27", "public.financial_taktical_actual_backlog", "public.financial_td_fy27_plan_target",
            "public.sales_account", "public.sales_opportunity", "public.sales_user"]


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
