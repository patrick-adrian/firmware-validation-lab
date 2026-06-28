"""
report.py - JSON (+ optional HTML) reports.

The JSON shape matches the sibling firmware-validation-lab project so a single dashboard
can ingest both tiers:

    {
      "generated_at": ...,
      "test_summary": {pass_count, fail_count, exit_code, execution_duration_seconds},
      "failure_breakdown": [...],
      "recent_test_runs": [...],
      "events": [...]                # lab2 extension: GDB backtraces, build warnings
    }
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

from framework import config


def build_report(results: list[dict[str, Any]], duration: float,
                 events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    pass_count = sum(1 for r in results if r["result"] == "PASS")
    fail_count = sum(1 for r in results if r["result"] == "FAIL")
    error_count = sum(1 for r in results if r["result"] == "ERROR")
    exit_code = 0 if (fail_count == 0 and error_count == 0) else 1
    failures = [r for r in results if r["result"] in ("FAIL", "ERROR")]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "test_summary": {
            "pass_count": pass_count,
            "fail_count": fail_count + error_count,
            "exit_code": exit_code,
            "execution_duration_seconds": round(duration, 2),
        },
        "failure_breakdown": [
            {"test_name": r["test_name"], "result": r["result"],
             "message": r.get("message", ""), "timestamp": r["timestamp"]}
            for r in failures
        ],
        "recent_test_runs": results,
        "events": events or [],
    }


def write_json(report: dict[str, Any], path: Path | None = None) -> Path:
    path = path or config.REPORT_JSON_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


def write_html(report: dict[str, Any], path: Path | None = None) -> Path:
    path = path or config.REPORT_HTML_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    s = report["test_summary"]
    rows = []
    for r in report["recent_test_runs"]:
        color = {"PASS": "#1a7f37", "FAIL": "#cf222e", "ERROR": "#9a6700",
                 "SKIP": "#57606a"}.get(r["result"], "#000")
        rows.append(
            f"<tr><td>{escape(r['test_name'])}</td>"
            f"<td style='color:{color};font-weight:600'>{r['result']}</td>"
            f"<td>{r['execution_time']:.4f}s</td>"
            f"<td><pre>{escape(str(r.get('message', '')))}</pre></td></tr>"
        )
    html = f"""<!doctype html><meta charset="utf-8">
<title>Firmware Validation Lab - Report</title>
<style>
 body{{font-family:system-ui,Segoe UI,sans-serif;margin:2rem;color:#1f2328}}
 table{{border-collapse:collapse;width:100%}} td,th{{border:1px solid #d0d7de;padding:.4rem .6rem;text-align:left;vertical-align:top}}
 th{{background:#f6f8fa}} pre{{margin:0;white-space:pre-wrap;font-size:.85em}}
 .summary{{display:flex;gap:1.5rem;margin-bottom:1rem}}
 .card{{padding:.8rem 1.2rem;border:1px solid #d0d7de;border-radius:8px}}
</style>
<h1>Firmware Validation Lab &mdash; Unit/Driver Tier</h1>
<p>Generated {escape(report['generated_at'])}</p>
<div class="summary">
 <div class="card">Pass: <b style="color:#1a7f37">{s['pass_count']}</b></div>
 <div class="card">Fail: <b style="color:#cf222e">{s['fail_count']}</b></div>
 <div class="card">Duration: <b>{s['execution_duration_seconds']}s</b></div>
 <div class="card">Exit: <b>{s['exit_code']}</b></div>
</div>
<table><thead><tr><th>Test</th><th>Result</th><th>Time</th><th>Detail</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
"""
    path.write_text(html, encoding="utf-8")
    return path
