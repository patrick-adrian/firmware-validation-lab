"""HTML and JSON validation report generation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from framework.config import HTML_REPORT_DIR, JSON_REPORT_DIR, VALIDATION_REPORT_DIR
from framework.database import get_recent_events, get_recent_test_runs, get_test_run_summary
from framework.run_result import TestRunResult


def _ensure_report_dirs() -> None:
    for path in (HTML_REPORT_DIR, JSON_REPORT_DIR, VALIDATION_REPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)


def generate_reports(result: TestRunResult) -> dict[str, Path]:
    """Generate HTML and JSON validation reports from a test run."""
    _ensure_report_dirs()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary = get_test_run_summary()
    recent_runs = get_recent_test_runs(limit=20)
    recent_events = get_recent_events(limit=50)

    report_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "test_summary": {
            "pass_count": summary.get("PASS", 0),
            "fail_count": summary.get("FAIL", 0),
            "exit_code": result.exit_code,
            "execution_duration_seconds": round(result.duration, 3),
        },
        "failure_breakdown": [
            run for run in recent_runs if str(run.get("result", "")).upper() == "FAIL"
        ],
        "recent_test_runs": recent_runs,
        "recent_event_timeline": recent_events,
        "recorded_tests": result.recorded_tests,
    }

    json_path = JSON_REPORT_DIR / f"validation_report_{timestamp}.json"
    json_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")

    html_path = HTML_REPORT_DIR / f"validation_report_{timestamp}.html"
    html_path.write_text(_render_html(report_data), encoding="utf-8")

    validation_copy = VALIDATION_REPORT_DIR / json_path.name
    validation_copy.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")

    return {"json": json_path, "html": html_path, "validation": validation_copy}


def _render_html(report_data: dict) -> str:
    summary = report_data["test_summary"]
    failures = report_data["failure_breakdown"]
    events = report_data["recent_event_timeline"]

    failure_rows = "".join(
        f"<tr><td>{escape(str(item.get('test_name', '')))}</td>"
        f"<td>{escape(str(item.get('timestamp', '')))}</td></tr>"
        for item in failures
    ) or "<tr><td colspan='2'>No failures recorded</td></tr>"

    event_rows = "".join(
        f"<tr><td>{escape(str(item.get('timestamp', '')))}</td>"
        f"<td>{escape(str(item.get('component', '')))}</td>"
        f"<td>{escape(str(item.get('event_type', '')))}</td>"
        f"<td>{escape(str(item.get('details', '')))}</td></tr>"
        for item in events
    ) or "<tr><td colspan='4'>No events recorded</td></tr>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Firmware Validation Report</title>
  <style>
    body {{ font-family: sans-serif; margin: 2rem; color: #1a1a1a; }}
    h1, h2 {{ color: #0b3d91; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 1.5rem; }}
    th, td {{ border: 1px solid #ccc; padding: 0.5rem; text-align: left; }}
    th {{ background: #eef3fb; }}
    .summary {{ display: flex; gap: 2rem; }}
    .metric {{ background: #f7f7f7; padding: 1rem; border-radius: 6px; }}
  </style>
</head>
<body>
  <h1>Firmware Validation Report</h1>
  <p>Generated at {escape(report_data.get('generated_at', ''))}</p>
  <div class="summary">
    <div class="metric"><strong>Pass</strong><br>{summary.get('pass_count', 0)}</div>
    <div class="metric"><strong>Fail</strong><br>{summary.get('fail_count', 0)}</div>
    <div class="metric"><strong>Duration (s)</strong><br>{summary.get('execution_duration_seconds', 0)}</div>
  </div>
  <h2>Failure Breakdown</h2>
  <table>
    <thead><tr><th>Test</th><th>Timestamp</th></tr></thead>
    <tbody>{failure_rows}</tbody>
  </table>
  <h2>Recent Event Timeline</h2>
  <table>
    <thead><tr><th>Timestamp</th><th>Component</th><th>Event</th><th>Details</th></tr></thead>
    <tbody>{event_rows}</tbody>
  </table>
</body>
</html>"""
