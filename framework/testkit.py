"""
testkit.py - Helpers tests import. Keeps test files terse and intent-revealing.

Tests are plain functions named test_* in tests/test_*.py. Raise AssertionError to fail,
raise SkipTest to skip (e.g. when gdb is unavailable). Everything here is stdlib only.
"""
from __future__ import annotations

import ctypes
from typing import Any

# Re-export the bridge so tests do `from framework.testkit import load_module, run_c_function`.
from framework.cinterface import load_module, run_c_function, executable_path, ProcResult  # noqa: F401


class SkipTest(Exception):
    """Raise to skip a test (reported as SKIP, not a failure)."""


def assert_eq(actual: Any, expected: Any, msg: str = "") -> None:
    if actual != expected:
        detail = f"{msg}: " if msg else ""
        raise AssertionError(f"{detail}expected {expected!r}, got {actual!r}")


def assert_true(cond: bool, msg: str = "condition was false") -> None:
    if not cond:
        raise AssertionError(msg)


def assert_signal(result: ProcResult, signo: int, msg: str = "") -> None:
    """Assert a black-box run died by a specific signal (e.g. 11 == SIGSEGV)."""
    detail = f"{msg}: " if msg else ""
    if result.signal != signo:
        raise AssertionError(
            f"{detail}expected termination by signal {signo}, got "
            f"signal={result.signal} returncode={result.returncode}"
        )


def carray(values: bytes | bytearray) -> ctypes.Array:
    """Build a (uint8_t[]) ctypes buffer from bytes for passing into C."""
    arr = (ctypes.c_ubyte * len(values))()
    for i, b in enumerate(values):
        arr[i] = b
    return arr
