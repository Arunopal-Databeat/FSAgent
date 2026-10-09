import logging
from pathlib import Path

_APP_LOG_PATH = str(Path(__file__).resolve().parents[2] / "app.log")

_root_logger = logging.getLogger()
_needs_setup = not any(
    isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", None) == _APP_LOG_PATH
    for h in _root_logger.handlers
)

if _needs_setup:
    _file_handler = logging.FileHandler(_APP_LOG_PATH, encoding="utf-8")
    _file_handler.setLevel(logging.DEBUG)
    _file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    _root_logger.addHandler(_file_handler)

    logging.getLogger("paramiko.transport").setLevel(logging.WARNING)
    logging.getLogger("graphviz._tools").setLevel(logging.WARNING)

    import litellm  # noqa: F401

    for _logger_name in (None, "LiteLLM", "LiteLLM Router", "LiteLLM Proxy"):
        _target_logger = _root_logger if _logger_name is None else logging.getLogger(_logger_name)
        for _h in _target_logger.handlers:
            if not isinstance(_h, logging.FileHandler) and _h.level < logging.ERROR:
                _h.setLevel(logging.ERROR)

    if _root_logger.level == logging.NOTSET or _root_logger.level > logging.DEBUG:
        _root_logger.setLevel(logging.DEBUG)
    logging.getLogger("google_adk").setLevel(logging.DEBUG)

from . import agent
