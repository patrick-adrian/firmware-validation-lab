"""Parse structured component and test logs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from framework.config import COMPONENT_LOG_DIR, TEST_LOG_DIR


def _parse_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def parse_component_logs(component: str | None = None) -> list[dict[str, Any]]:
    """Load structured JSON logs for one or all components."""
    if component:
        return _parse_jsonl(COMPONENT_LOG_DIR / f"{component}.jsonl")

    entries: list[dict[str, Any]] = []
    if COMPONENT_LOG_DIR.exists():
        for path in sorted(COMPONENT_LOG_DIR.glob("*.jsonl")):
            entries.extend(_parse_jsonl(path))
    entries.sort(key=lambda item: item.get("timestamp", ""))
    return entries


def parse_test_logs(name: str = "test_runner") -> list[dict[str, Any]]:
    """Load structured test runner logs."""
    return _parse_jsonl(TEST_LOG_DIR / f"{name}.jsonl")
