import logging
from typing import Any

from pythonjsonlogger.json import JsonFormatter

SENSITIVE_KEYS = frozenset({"text", "raw_input", "note", "authorization", "token", "password"})


class RedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        for key in SENSITIVE_KEYS:
            if hasattr(record, key):
                setattr(record, key, "[REDACTED]")
        if isinstance(record.args, dict):
            record.args = redact(record.args)
        return True


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if key.lower() in SENSITIVE_KEYS else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(
        JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s")
    )
    handler.addFilter(RedactionFilter())
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
