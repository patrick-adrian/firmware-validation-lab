"""Structured JSON logging for firmware components and tests."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from framework.config import COMPONENT_LOG_DIR, TEST_LOG_DIR


def _ensure_log_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON objects."""

    def __init__(self, component: str) -> None:
        super().__init__()
        self.component = component

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            "component": self.component,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, "event"):
            payload["event"] = record.event
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            payload.update(record.extra_fields)
        return json.dumps(payload)


def get_component_logger(name: str) -> logging.Logger:
    """Return a logger that writes structured JSON to component log files."""
    _ensure_log_dir(COMPONENT_LOG_DIR)
    logger = logging.getLogger(f"component.{name}")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(COMPONENT_LOG_DIR / f"{name}.jsonl")
    handler.setFormatter(JsonFormatter(name))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def get_test_logger(name: str = "test_runner") -> logging.Logger:
    """Return a logger for test execution output."""
    _ensure_log_dir(TEST_LOG_DIR)
    logger = logging.getLogger(f"test.{name}")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(TEST_LOG_DIR / f"{name}.jsonl")
    handler.setFormatter(JsonFormatter(name))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def log_structured(
    logger: logging.Logger,
    message: str,
    *,
    event: str | None = None,
    **fields: Any,
) -> None:
    """Emit a structured log entry with optional event metadata."""
    record = logger.makeRecord(
        logger.name,
        logging.INFO,
        "(structured)",
        0,
        message,
        (),
        None,
    )
    if event is not None:
        record.event = event
    if fields:
        record.extra_fields = fields
    logger.handle(record)
