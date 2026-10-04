import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from asgi_correlation_id import correlation_id

_STANDARD_ATTRS = frozenset(vars(logging.LogRecord("", 0, "", 0, "", (), None))) | {
    "message",
    "asctime",
    "taskName",
}


class JsonFormatter(logging.Formatter):
    def __init__(self, static_fields: dict[str, str]) -> None:
        super().__init__()
        self._static_fields = static_fields

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "time": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            **self._static_fields,
        }
        if request_id := correlation_id.get():
            payload["request_id"] = request_id
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    def __init__(self) -> None:
        super().__init__("%(asctime)s %(levelname)-5s %(name)s %(request_id)s %(message)s")

    def format(self, record: logging.LogRecord) -> str:
        record.request_id = correlation_id.get() or "-"
        return super().format(record)


def configure_logging(*, fmt: str, level: str, static_fields: dict[str, str]) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter(static_fields) if fmt == "json" else TextFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    for name in ("uvicorn", "uvicorn.error"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
    logging.getLogger("uvicorn.access").disabled = True
