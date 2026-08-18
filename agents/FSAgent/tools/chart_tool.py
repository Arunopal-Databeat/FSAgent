import hashlib
import io
import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional

import litellm
import matplotlib.pyplot as plt
import pandas as pd
from google.adk.tools import ToolContext
from google.genai import types

from .db_tools import run_sql_query

CHART_CODE_MODEL = "anthropic/claude-sonnet-5"


def make_cache_key(prefix: str, params: Dict[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(params, sort_keys=True, default=str).encode()).hexdigest()
    return f"{prefix}:{digest}"


def df_to_serializable(df: pd.DataFrame) -> Dict[str, Any]:
    try:
        df_json = df.to_json(orient="split", date_format="iso")
        preview = df.head(10).to_dict(orient="records")
        dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
        return {"df_json": df_json, "preview": preview, "columns": list(df.columns), "dtypes": dtypes, "rows": len(df)}
    except Exception as e:
        logging.warning("df_to_serializable failed: %s", e)
        return {"df_json": None, "preview": [], "columns": [], "dtypes": {}, "rows": 0}


def df_from_serializable(serialized: Dict[str, Any]) -> Optional[pd.DataFrame]:
    if not isinstance(serialized, dict):
        return None

    df_json = serialized.get("df_json")
    if df_json:
        try:
            return pd.read_json(df_json, orient="split")
        except Exception as e:
            logging.warning("Failed to read df_json: %s", e)

    preview = serialized.get("preview")
    if preview and isinstance(preview, list) and len(preview) > 0:
        try:
            return pd.DataFrame(preview)
        except Exception as e:
            logging.warning("Failed to build DataFrame from preview: %s", e)

    result = serialized.get("result")
    if isinstance(result, list) and result and isinstance(result[0], dict):
        try:
            return pd.DataFrame(result)
        except Exception as e:
            logging.warning("Failed to build DataFrame from result: %s", e)

    return None


def _extract_python_code(llm_output: str) -> str:
    match = re.search(r"```(?:python\s*)?\n?(.*?)\n?```", llm_output, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return llm_output.strip()


def execute_python_chart_code(code_string: str, data_df: pd.DataFrame) -> tuple[Optional[bytes], Optional[str]]:
    img_buffer = io.BytesIO()
    error_message: Optional[str] = None
    image_bytes: Optional[bytes] = None

    restricted_code = re.sub(
        r"(os\.|subprocess\.|shutil\.|requests\.|urllib\.|socket\.|eval\(|exec\(|open\()",
        "# Blocked",
        code_string,
    )
    restricted_code = restricted_code.replace(
        "plt.show()", "# plt.show() disabled"
    )
    restricted_code = re.sub(
        r"plt\.savefig\s*\(.*?\)", "# plt.savefig disabled", restricted_code
    )
    restricted_code = restricted_code.replace("plt.ticker", "ticker")

    global_scope = {
        "pd": pd,
        "plt": plt,
        "df": data_df,
        "io": io,
        "img_buffer": img_buffer,
    }

    full_code_to_exec = f"""
import pandas as pd
import numpy as np
import matplotlib as matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import io
plt.figure(figsize=(10, 6))
{restricted_code}
if plt.get_fignums():
    plt.savefig(img_buffer, format='png', bbox_inches='tight')
plt.close('all')
        """

    try:
        exec(full_code_to_exec, global_scope)
        img_buffer.seek(0)
        image_data = img_buffer.read()
        if image_data:
            image_bytes = image_data
        else:
            error_message = "Chart code executed, but no image was generated."
    except Exception as e:
        logging.error(
            f"Error executing chart code: {e}\nCode was:\n{restricted_code}"
        )
        error_message = f"Error during chart generation: {type(e).__name__}: {e}"
    finally:
        img_buffer.close()
    return image_bytes, error_message


async def generate_chart(sql_query: str, user_question: str, tool_context: ToolContext) -> Dict[str, Any]:
    try:
        cache_key = make_cache_key('execute_sql', {'query': sql_query})
        cached = tool_context.state.get(cache_key)
        df = None

        if cached:
            df = df_from_serializable(cached)
            if df is not None and not df.empty:
                logging.info("[CACHE HIT] Reconstructed DataFrame from cache (rows=%d).", len(df))
            else:
                logging.info("[CACHE HIT] Cache present but no usable DF; will run query to refresh.")

        if df is None or df.empty:
            logging.info("Running SQL (fresh): %s", sql_query if len(sql_query) < 500 else sql_query[:500] + "...")
            df = run_sql_query(sql_query)
            serial = df_to_serializable(df)
            tool_context.state[cache_key] = serial
            logging.info("[CACHE STORE] Stored serializable query result (rows=%d) under %s", serial.get("rows", 0), cache_key)

        if df is None or df.empty:
            rows_cached = cached.get("rows") if isinstance(cached, dict) else None
            preview_info = cached.get("preview")[:3] if isinstance(cached, dict) and cached.get("preview") else None
            logging.warning("No data available for charting. cached_rows=%s preview_sample=%s", rows_cached, preview_info)
            return {"result": f"Error: Query returned no data for charting. (cached_rows={rows_cached})"}

        df_preview = df.head(5).to_string()
        column_info = "\n".join([f"- '{col}' (dtype: {str(df[col].dtype)})" for col in df.columns])

        code_generation_prompt = f"""
        You are an expert Python data visualization assistant. Generate Python code to create a Matplotlib chart.
        User's Question: "{user_question}"
        DataFrame 'df' Preview:
        {df_preview}
        DataFrame Columns:
        {column_info}
        Instructions:
        1. Data is in a pandas DataFrame named 'df'.
        2. Use 'matplotlib.pyplot' as 'plt'.
        3. Generate only the Python code for the plot. Do NOT include imports, 'plt.show()', or 'plt.savefig()'.
        4. Create a title and clear labels. Rotate x-axis labels if needed.
        5. Respond ONLY with the raw Python code (no markdown fences).
        6. tick_params does not support ha (horizontal alignment), instead set alignment on the tick labels example:
        axes[0].tick_params(axis='x', rotation=45)
        for label in axes[0].get_xticklabels():
            label.set_ha('right')
        """

        response = await litellm.acompletion(
            model=CHART_CODE_MODEL,
            messages=[{"role": "user", "content": code_generation_prompt}],
        )
        llm_output = response.choices[0].message.content or ""
        python_code = _extract_python_code(llm_output)

        if not python_code:
            return {"result": "Error: The language model did not generate any code."}

        image_bytes, error = execute_python_chart_code(python_code, df)
        if error:
            return {"result": f"Error: {error}"}

        if not image_bytes:
            return {"result": "Error: Chart generation failed - no image data produced."}

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chart_{timestamp}.png"

        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")

        version = await tool_context.save_artifact(filename=filename, artifact=image_part)
        artifact_id = f"{filename}_v{version}"

        return {
            "status": "success",
            "message": f"Chart generated successfully",
            "filename": filename,
            "version": version,
            "artifact_id": artifact_id,
            "preview": f"Chart saved as artifact"
        }

    except Exception as e:
        logging.exception("Unexpected error in generate_chart_tool_wrapper")
        return {
            "status": "error",
            "message": f"Unexpected error in chart generation: {type(e).__name__}: {e}"
        }
