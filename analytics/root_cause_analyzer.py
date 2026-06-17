"""Diagnose failed validation runs from logs and database events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from analytics.log_parser import parse_component_logs
from framework.database import get_recent_events, get_recent_test_runs


@dataclass
class FailureDiagnosis:
    """Structured root-cause analysis for a failed validation scenario."""

    test_name: str
    expected: str
    actual: str
    root_cause_candidate: str

    def format_report(self) -> str:
        return (
            "TEST FAILURE\n\n"
            f"Test: {self.test_name}\n\n"
            f"Expected:\n{self.expected}\n\n"
            f"Actual:\n{self.actual}\n\n"
            f"Root Cause Candidate:\n{self.root_cause_candidate}"
        )


def _find_thermal_event(event_type: str, logs: list[dict[str, Any]]) -> bool:
    return any(
        entry.get("component") == "thermal_manager" and entry.get("event") == event_type
        for entry in logs
    )


def _find_downstream_event(component: str, event_type: str, logs: list[dict[str, Any]]) -> bool:
    return any(
        entry.get("component") == component and entry.get("event") == event_type
        for entry in logs
    )


def analyze_failure(
    *,
    test_name: str,
    expected: str,
    actual: str,
    thermal_event: str,
) -> FailureDiagnosis:
    """Analyze a single failure and identify likely missing propagation."""
    logs = parse_component_logs()
    db_events = get_recent_events(limit=100)

    thermal_seen = _find_thermal_event(thermal_event, logs) or any(
        e.get("component") == "thermal_manager" and e.get("event_type") == thermal_event
        for e in db_events
    )
    fan_seen = _find_downstream_event("fan_controller", thermal_event, logs) or any(
        e.get("component") == "fan_controller" and e.get("event_type") == thermal_event
        for e in db_events
    )
    power_seen = _find_downstream_event("power_manager", thermal_event, logs) or any(
        e.get("component") == "power_manager" and e.get("event_type") == thermal_event
        for e in db_events
    )

    if thermal_seen and not fan_seen:
        root_cause = (
            f"{thermal_event} event received by thermal_manager "
            "but not observed by fan_controller"
        )
    elif thermal_seen and not power_seen:
        root_cause = (
            f"{thermal_event} event received by thermal_manager "
            "but not observed by power_manager"
        )
    elif not thermal_seen:
        root_cause = f"{thermal_event} event not observed in thermal_manager logs"
    else:
        root_cause = "Downstream components received events; mismatch may be timing or mapping logic"

    return FailureDiagnosis(
        test_name=test_name,
        expected=expected,
        actual=actual,
        root_cause_candidate=root_cause,
    )


def analyze_recent_failures(limit: int = 5) -> list[FailureDiagnosis]:
    """Generate diagnoses for recently failed tests stored in the database."""
    failures = [
        run for run in get_recent_test_runs(limit=50)
        if str(run.get("result", "")).upper() == "FAIL"
    ][:limit]

    diagnoses: list[FailureDiagnosis] = []
    for failure in failures:
        diagnoses.append(
            analyze_failure(
                test_name=str(failure.get("test_name", "unknown")),
                expected="See test specification",
                actual="See test logs",
                thermal_event="OVERHEAT",
            )
        )
    return diagnoses
