"""
gdb.py - First-class GDB debugging support.

Runs a black-box binary under GDB in batch mode and captures a structured crash dump:
backtrace, register state, local variables, and the faulting frame. Used both on-demand
(--gdb) and automatically when a test binary dies by signal (--debug / auto-trigger).

Requires the -g -O0 build (the framework default) for accurate line info and locals.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GdbReport:
    available: bool
    raw: str = ""
    backtrace: str = ""
    registers: str = ""
    locals: str = ""
    signal: str = ""
    sections: dict[str, str] = field(default_factory=dict)


def gdb_available() -> bool:
    return shutil.which("gdb") is not None


# Sentinels let us slice GDB's batch output back into named sections.
_MARK = "===FVLAB_SECTION==="

_BATCH_COMMANDS = [
    "set pagination off",
    "set confirm off",
    "run",
    f'echo \\n{_MARK}signal\\n',
    "print $_siginfo.si_signo",
    f'echo \\n{_MARK}backtrace\\n',
    "backtrace full",
    f'echo \\n{_MARK}registers\\n',
    "info registers",
    f'echo \\n{_MARK}locals\\n',
    "info locals",
    f'echo \\n{_MARK}args\\n',
    "info args",
    "quit",
]


def _split_sections(raw: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current = "preamble"
    buf: list[str] = []
    for line in raw.splitlines():
        if line.startswith(_MARK):
            sections[current] = "\n".join(buf).strip()
            current = line[len(_MARK):].strip()
            buf = []
        else:
            buf.append(line)
    sections[current] = "\n".join(buf).strip()
    return sections


def run_under_gdb(binary: Path, args: list[str] | None = None,
                  timeout: float = 30.0) -> GdbReport:
    """Run `binary args` under GDB and return a structured crash report."""
    if not gdb_available():
        return GdbReport(available=False, raw="gdb not found on PATH")

    args = args or []
    cmd = ["gdb", "-q", "-batch", "-nx"]
    for c in _BATCH_COMMANDS:
        cmd += ["-ex", c]
    cmd += ["--args", str(binary), *args]

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    raw = proc.stdout + ("\n" + proc.stderr if proc.stderr else "")
    sections = _split_sections(raw)
    return GdbReport(
        available=True,
        raw=raw,
        signal=sections.get("signal", ""),
        backtrace=sections.get("backtrace", ""),
        registers=sections.get("registers", ""),
        locals=sections.get("locals", ""),
        sections=sections,
    )


def capture_backtrace(binary: Path, args: list[str] | None = None) -> str:
    """Convenience: just the backtrace string (empty if gdb missing)."""
    return run_under_gdb(binary, args).backtrace


def format_report(report: GdbReport, max_lines: int = 40) -> str:
    """Human-readable condensation for the console / report (registers truncated)."""
    if not report.available:
        return "GDB unavailable: " + report.raw
    regs = "\n".join(report.registers.splitlines()[:8])
    parts = [
        f"signal: {report.signal}".strip(),
        "--- backtrace ---",
        "\n".join(report.backtrace.splitlines()[:max_lines]),
        "--- registers (top) ---",
        regs,
    ]
    if report.locals:
        parts += ["--- locals ---", report.locals]
    return "\n".join(p for p in parts if p)
