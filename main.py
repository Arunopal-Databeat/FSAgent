import logging
import os
import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
import google.auth
from follow_questions import router as follow_questions_router
from dotenv import load_dotenv
load_dotenv(".env", override=True)

_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.ERROR)
_file_handler = logging.FileHandler("app.log")
_file_handler.setLevel(logging.DEBUG)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[_console_handler, _file_handler],
)
logging.getLogger("google_adk").setLevel(logging.DEBUG)
logging.getLogger("paramiko.transport").setLevel(logging.WARNING)
logging.getLogger("graphviz._tools").setLevel(logging.WARNING)

DB_CONNECTION_MODE = os.environ.get("DB_CONNECTION_MODE", "ssh_tunnel")

if DB_CONNECTION_MODE == "direct":
    _session_db_host = os.environ["DB_HOST"]
    _session_db_port = int(os.environ["DB_PORT"])
else:
    from sshtunnel import SSHTunnelForwarder

    _session_tunnel = SSHTunnelForwarder(
        (os.environ["DB_SSH_HOST"], int(os.environ["DB_SSH_PORT"])),
        ssh_username=os.environ["DB_SSH_USERNAME"],
        ssh_pkey=os.environ["DB_SSH_PKEY"],
        remote_bind_address=("localhost", int(os.environ["DB_REMOTE_PORT"])),
    )
    _session_tunnel.start()
    _session_db_host = "localhost"
    _session_db_port = _session_tunnel.local_bind_port

SESSION_SERVICE_URI = (
    f"postgresql+asyncpg://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
    f"@{_session_db_host}:{_session_db_port}/{os.environ['DB_NAME']}"
)

from agents.FSAgent.tools.db_connection import get_connection as _get_agent_db_connection
_get_agent_db_connection()
import litellm
litellm._turn_on_debug()

import litellm
import litellm.types.utils as litellm_types
from litellm.types.llms.openai import ChatCompletionReasoningSummaryTextBlock

_extra_types = {"ChatCompletionReasoningSummaryTextBlock": ChatCompletionReasoningSummaryTextBlock}

for _cls_name in ("Message", "Choices", "ModelResponse", "Delta", "StreamingChoices"):
    _cls = getattr(litellm_types, _cls_name, None)
    if _cls is not None and hasattr(_cls, "model_rebuild"):
        try:
            _cls.model_rebuild(force=True, _types_namespace=_extra_types)
        except Exception as _e:
            print(f"[main.py] model_rebuild failed for {_cls_name}: {_e}")

# Some shells/terminals inherit a stale ANTHROPIC_API_KEY with a trailing
# newline baked in, which Anthropic's HTTP client rejects as a "control
# character" in the x-api-key header. Strip it defensively.
for _key in ("ANTHROPIC_API_KEY", "GEMINI_API_KEY"):
    if _key in os.environ:
        os.environ[_key] = os.environ[_key].strip()
        print(os.environ[_key])

# Get the directory where main.py is located
AGENT_DIR = "agents"

ALLOWED_ORIGINS = ["http://localhost", "http://localhost:8080", "*"]
# Set web=True if you intend to serve a web interface, False otherwise
SERVE_WEB_INTERFACE = True

print(" [main.py] Trying default creds...")
# creds, _ = google.auth.default() 

# Call the function to get the FastAPI app instance
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
    session_service_uri=SESSION_SERVICE_URI,
)

app.include_router(follow_questions_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8010)))