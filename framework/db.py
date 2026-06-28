"""
db.py - SQLite results store.

Schema is intentionally IDENTICAL to the sibling firmware-validation-lab project
(tables: test_runs, events) so both validation tiers can write into one dashboard.
The schema is copied here rather than imported to keep lab2 dependency-free.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from framework import config

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


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_connection(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    path = db_path or config.DATABASE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_database(db_path: Path | None = None) -> None:
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA)


def record_test_run(test_name: str, result: str, execution_time: float, *,
                    db_path: Path | None = None, timestamp: str | None = None) -> int:
    ts = timestamp or _utc_now()
    with get_connection(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO test_runs (test_name, result, execution_time, timestamp) "
            "VALUES (?, ?, ?, ?)",
            (test_name, result, execution_time, ts),
        )
        return int(cur.lastrowid)


def record_event(component: str, event_type: str, details: str | None = None, *,
                 db_path: Path | None = None, timestamp: str | None = None) -> int:
    ts = timestamp or _utc_now()
    with get_connection(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO events (component, event_type, details, timestamp) "
            "VALUES (?, ?, ?, ?)",
            (component, event_type, details, ts),
        )
        return int(cur.lastrowid)


def get_recent_test_runs(limit: int = 50, *, db_path: Path | None = None) -> list[dict[str, Any]]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT id, test_name, result, execution_time, timestamp "
            "FROM test_runs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_recent_events(limit: int = 100, *, db_path: Path | None = None) -> list[dict[str, Any]]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT id, component, event_type, details, timestamp "
            "FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]
