import json
import logging

logger = logging.getLogger("fsagent")
from ..access_control.configure_masking import CLIENT_ALIAS, UNIQUE_CLIENTS


def mask_client_names(text):
    for client in sorted(UNIQUE_CLIENTS, key=len, reverse=True):
        alias = CLIENT_ALIAS.get(client)
        if alias:
            text = text.replace(client, alias)
    return text

def unmask_client_aliases(text):
    for client in sorted(UNIQUE_CLIENTS, key=len, reverse=True):
        alias = CLIENT_ALIAS.get(client)
        if alias:
            text = text.replace(alias, client)
    return text


def mask_before_agent_callback(callback_context):
    question = _content_text(callback_context.user_content)
    callback_context.user_content.parts[0].text = mask_client_names(question)
    logger.info("mask_before_agent_callback: %s", question)
    return None


def unmask_after_model_callback(callback_context, llm_response):
    if llm_response.content and llm_response.content.parts:
        for part in llm_response.content.parts:
            if getattr(part, "text", None):
                part.text = unmask_client_aliases(part.text)
    return llm_response


def unmask_after_agent_callback(callback_context):
    response_text = ""
    for event in reversed(callback_context.session.events):
        if event.invocation_id != callback_context.invocation_id:
            continue
        if event.author == "user" or event.partial:
            continue
        text = _content_text(event.content)
        if text:
            response_text = text
            break
    logger.info(callback_context.user_id)
    logger.info("AGENT RESPONSE: %s", response_text)
    logger.info("unmask_after_agent_callback: %s", response_text)
    return None


def unmask_before_tool_callback(tool, args, tool_context):
    # CALL run_query args={'sql_query': 'SELECT region, SUM(revenue) FROM sales_actuals GROUP BY region', 'table_name': 'public.sales_actuals'}
    if tool.name == "run_query":
        args["sql_query"] = unmask_client_aliases(args["sql_query"])
    elif tool.name == "generate_chart":
        args["sql_query"] = unmask_client_aliases(args["sql_query"])
        args["user_question"] = unmask_client_aliases(args["user_question"])
    logger.info(tool_context.user_id)
    logger.info("unmask_before_tool_callback %s args=%s", tool.name, args)
    return None


def mask_after_tool_callback(tool, args, tool_context, tool_response):
    # RETURN run_query args={'sql_query': 'SELECT region, SUM(revenue) FROM sales_actuals GROUP BY region', 'table_name': 'public.sales_actuals'} response={'status': 'success', 'columns': ['region', 'sum'], 'rows': [{'region': 'East', 'sum': 40000}], 'row_count': 1}
    if tool.name == "run_query":
        rows = tool_response.get("rows")
        if rows:
            tool_response["rows"] = json.loads(mask_client_names(json.dumps(rows, default=str)))
    elif tool.name == "get_mapped_clients":
        clients = tool_response.get("clients")
        if clients:
            tool_response["clients"] = json.loads(mask_client_names(json.dumps(clients, default=str)))
    logger.info(tool_context.user_id)
    logger.info("mask_after_tool_callback %s args=%s response=%s", tool.name, args, tool_response)
    return tool_response


def _content_text(content) -> str:
    if not content or not content.parts:
        return ""
    return "".join(part.text for part in content.parts if getattr(part, "text", None))



