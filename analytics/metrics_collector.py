"""Collect validation metrics from logs and database."""

from __future__ import annotations

from typing import Any

from analytics.log_parser import parse_component_logs
from framework.database import get_recent_events, get_test_run_summary


def collect_metrics() -> dict[str, Any]:
    """Aggregate high-level validation metrics."""
    component_logs = parse_component_logs()
    events = get_recent_events(limit=200)
    summary = get_test_run_summary()

    event_counts: dict[str, int] = {}
    for entry in component_logs:
        event = str(entry.get("event", "UNKNOWN"))
        event_counts[event] = event_counts.get(event, 0) + 1

    return {
        "test_summary": summary,
        "component_log_entries": len(component_logs),
        "database_events": len(events),
        "event_counts": event_counts,
        "recent_events": events[:20],
    }
