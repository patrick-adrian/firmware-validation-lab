"""Shared datatypes for the validation framework."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TestRunResult:
    """Summary of a pytest execution."""

    exit_code: int
    duration: float
    stdout: str
    stderr: str
    recorded_tests: list[dict[str, str | float]] = field(default_factory=list)
