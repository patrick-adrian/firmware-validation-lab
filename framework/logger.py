"""
logger.py - Structured JSONL logging, compatible with the sibling lab's format.

One JSON object per line: {timestamp, level, component, event, ...extra}. Easy to grep,
tail, and feed to the analytics/dashboard layer.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

from framework import config


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class StructuredLogger:
    def __init__(self, component: str, log_file: Path | None = None,
                 echo: TextIO | None = None) -> None:
        self.component = component
        self.log_file = log_file
        self.echo = echo
        if log_file is not None:
            log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: str, level: str = "INFO", **extra: Any) -> None:
        record: dict[str, Any] = {
            "timestamp": _utc_now(),
            "level": level,
            "component": self.component,
            "event": event,
        }
        record.update(extra)
        line = json.dumps(record)
        if self.log_file is not None:
            with self.log_file.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        if self.echo is not None:
            self.echo.write(line + "\n")

    def info(self, event: str, **extra: Any) -> None:
        self.log(event, "INFO", **extra)

    def warning(self, event: str, **extra: Any) -> None:
        self.log(event, "WARNING", **extra)

    def error(self, event: str, **extra: Any) -> None:
        self.log(event, "ERROR", **extra)


def get_logger(component: str, verbose: bool = False) -> StructuredLogger:
    log_file = config.LOG_DIR / f"{component}.jsonl"
    return StructuredLogger(component, log_file, echo=sys.stderr if verbose else None)
