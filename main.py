import os
import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
import google.auth
from dotenv import load_dotenv
load_dotenv(".env", override=True)
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
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8010)))