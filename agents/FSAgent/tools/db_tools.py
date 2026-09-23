import logging
import re
from typing import Any, Dict

import pandas as pd
from google.adk.tools import ToolContext

from .db_connection import get_connection
from ..access_control.configure_tables import get_email_client_access

logger = logging.getLogger("fsagent")

_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|exec|execute|call|copy|merge|into)\b",
    re.IGNORECASE,
)


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


async def get_mapped_clients(tool_context: ToolContext) -> Dict[str, Any]:
    logger.info(f"get_mapped_clients {tool_context.user_id}")
    email_client_access = get_email_client_access()
    logger.info(f"get_mapped_clients {email_client_access}")
    clients = email_client_access.get(tool_context.user_id, [])
    if not clients:
        return {"status": "error", "message": f"unfortunately this user id {tool_context.user_id} has not been mapped to any clients. Please contact the administrator. "}
    return {"status": "success", "clients": sorted(clients)}
