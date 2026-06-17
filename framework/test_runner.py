"""Regression test orchestration and result persistence."""

from __future__ import annotations

import subprocess
import time
from datetime import datetime, timezone

from framework.config import PROJECT_ROOT
from framework.database import init_database, record_test_run
from framework.logger import get_test_logger, log_structured
from framework.run_result import TestRunResult
from framework.report_generator import generate_reports

logger = get_test_logger("test_runner")


def _parse_pytest_nodeid(nodeid: str) -> str:
    parts = nodeid.split("::")
    if len(parts) >= 2:
        return parts[-1]
    return nodeid


def run_regression(
    *,
    test_path: str = "tests",
    record_individual_tests: bool = True,
) -> TestRunResult:
    """Execute pytest, persist results, and generate validation reports."""
    init_database()
    start = time.perf_counter()
    completed = subprocess.run(
        ["python", "-m", "pytest", test_path, "-v", "--tb=short"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    duration = time.perf_counter() - start
    log_structured(
        logger,
        "Regression run completed",
        event="REGRESSION_COMPLETE",
        exit_code=completed.returncode,
        duration=duration,
    )

    recorded: list[dict[str, str | float]] = []
    if record_individual_tests:
        recorded = _record_pytest_outcomes(completed.stdout, duration)

    result = TestRunResult(
        exit_code=completed.returncode,
        duration=duration,
        stdout=completed.stdout,
        stderr=completed.stderr,
        recorded_tests=recorded,
    )
    generate_reports(result)
    return result


def _record_pytest_outcomes(stdout: str, total_duration: float) -> list[dict[str, str | float]]:
    """Parse pytest verbose output and store per-test results."""
    per_test_duration = total_duration / max(stdout.count(" PASSED") + stdout.count(" FAILED"), 1)
    timestamp = datetime.now(timezone.utc).isoformat()
    recorded: list[dict[str, str | float]] = []

    for line in stdout.splitlines():
        stripped = line.strip()
        if " PASSED" in stripped:
            nodeid = stripped.split(" PASSED")[0].strip()
            test_name = _parse_pytest_nodeid(nodeid)
            record_test_run(test_name, "PASS", per_test_duration, timestamp=timestamp)
            recorded.append({"test_name": test_name, "result": "PASS"})
        elif " FAILED" in stripped:
            nodeid = stripped.split(" FAILED")[0].strip()
            test_name = _parse_pytest_nodeid(nodeid)
            record_test_run(test_name, "FAIL", per_test_duration, timestamp=timestamp)
            recorded.append({"test_name": test_name, "result": "FAIL"})

    if not recorded:
        overall = "PASS" if "failed" not in stdout.lower() or "0 failed" in stdout.lower() else "FAIL"
        record_test_run("regression_suite", overall, total_duration, timestamp=timestamp)
        recorded.append({"test_name": "regression_suite", "result": overall})

    return recorded
