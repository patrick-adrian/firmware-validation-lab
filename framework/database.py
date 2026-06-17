"""SQLite persistence for test runs and component events."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from framework.config import DATABASE_DIR, DATABASE_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS test_runs (
    id INTEGER PRIMARY KEY,
    test_name TEXT NOT NULL,
    result TEXT NOT NULL,
    execution_time REAL NOT NULL,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    component TEXT NOT NULL,
    event_type TEXT NOT NULL,
    details TEXT,
    timestamp TEXT NOT NULL
);
"""


def _ensure_database_dir() -> None:
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Open a SQLite connection with row factory enabled."""
    _ensure_database_dir()
    path = db_path or DATABASE_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_database(db_path: Path | None = None) -> None:
    """Create database tables if they do not exist."""
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA)


def record_test_run(
    test_name: str,
    result: str,
    execution_time: float,
    *,
    db_path: Path | None = None,
    timestamp: str | None = None,
) -> int:
    """Insert a test run record and return its row id."""
    ts = timestamp or datetime.now(timezone.utc).isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO test_runs (test_name, result, execution_time, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (test_name, result, execution_time, ts),
        )
        return int(cursor.lastrowid)


def record_event(
    component: str,
    event_type: str,
    details: str | None = None,
    *,
    db_path: Path | None = None,
    timestamp: str | None = None,
) -> int:
    """Insert a component event and return its row id."""
    ts = timestamp or datetime.now(timezone.utc).isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO events (component, event_type, details, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (component, event_type, details, ts),
        )
        return int(cursor.lastrowid)


def get_recent_test_runs(limit: int = 50, *, db_path: Path | None = None) -> list[dict[str, Any]]:
    """Return the most recent test run records."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, test_name, result, execution_time, timestamp
            FROM test_runs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_recent_events(limit: int = 100, *, db_path: Path | None = None) -> list[dict[str, Any]]:
    """Return the most recent component events."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, component, event_type, details, timestamp
            FROM events
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_test_run_summary(*, db_path: Path | None = None) -> dict[str, int]:
    """Return pass/fail counts from stored test runs."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT result, COUNT(*) AS count
            FROM test_runs
            GROUP BY result
            """
        ).fetchall()
    summary = {"PASS": 0, "FAIL": 0}
    for row in rows:
        result = str(row["result"]).upper()
        if result in summary:
            summary[result] = int(row["count"])
    return summary


if __name__ == "__main__":
    init_database()
    print("Database initialized.")
