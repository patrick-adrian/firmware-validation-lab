"""Validation assertion helpers."""

from __future__ import annotations

from typing import Any


class ValidationAssertionError(AssertionError):
    """Raised when observed behavior does not match expected behavior."""


def assert_equal(
    actual: Any,
    expected: Any,
    *,
    label: str,
) -> None:
    """Assert two values are equal with a descriptive label."""
    if actual != expected:
        raise ValidationAssertionError(
            f"{label}: expected {expected!r}, got {actual!r}",
        )


def assert_state(actual: str, expected: str, *, component: str) -> None:
    """Assert a component state matches the expected value."""
    assert_equal(actual, expected, label=f"{component} state")
