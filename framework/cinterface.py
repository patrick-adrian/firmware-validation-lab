"""
cinterface.py - The Python <-> C bridge.

Two mechanisms, matching the two run modes:

  * load_module(name)      -> ctypes.CDLL for white-box / mock-hardware tests.
                              Call C functions directly, peek/poke mock register banks.
  * run_c_function(name)   -> subprocess execution of a black-box executable; captures
                              stdout, exit code, and the terminating signal (for GDB).
"""
from __future__ import annotations

import ctypes
import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path

from framework import config

_LIB_CACHE: dict[str, ctypes.CDLL] = {}

# When True, any black-box run that dies by signal is automatically re-run under GDB
# and the crash report attached to the ProcResult. Set by the runner's --debug flag.
DEBUG = False

# Crash reports captured during the current test (runner clears between tests).
LAST_CRASHES: list = []


def _shared_lib_path(name: str) -> Path:
    ext = "dylib" if platform.system() == "Darwin" else "so"
    return config.RUNTIME_DIR / f"lib{name}.{ext}"


def load_module(name: str) -> ctypes.CDLL:
    """Load (and cache) a compiled module as a ctypes handle.

    Callers are expected to set .argtypes/.restype on the functions they use; this
    keeps the bridge honest about the C ABI and lets ctypes marshal correctly.
    """
    if name in _LIB_CACHE:
        return _LIB_CACHE[name]
    path = _shared_lib_path(name)
    if not path.exists():
        raise FileNotFoundError(
            f"Shared library not built: {path}. Run the build first "
            f"(python -m framework.build or python -m framework.runner)."
        )
    lib = ctypes.CDLL(str(path))
    _LIB_CACHE[name] = lib
    return lib


@dataclass
class ProcResult:
    """Outcome of a black-box subprocess run."""

    args: list[str]
    returncode: int
    stdout: str
    stderr: str
    gdb: object | None = None   # GdbReport attached when DEBUG and the run crashed

    @property
    def signal(self) -> int | None:
        """The terminating signal number if the process died by signal, else None.

        POSIX convention: a negative returncode from subprocess means -signal.
        """
        return -self.returncode if self.returncode < 0 else None

    @property
    def crashed(self) -> bool:
        return self.signal is not None


def executable_path(name: str) -> Path:
    return config.RUNTIME_DIR / name


def run_c_function(name: str, input: str | None = None, args: list[str] | None = None,
                   timeout: float = 10.0) -> ProcResult:
    """Run a black-box executable.

    `input` is passed as the program's first argv argument (matches the harness style,
    e.g. crc_test <string>); `args` overrides with an explicit argv list; `input` is
    also written to stdin so either convention works.
    """
    exe = executable_path(name)
    if not exe.exists():
        raise FileNotFoundError(f"Executable not built: {exe}")
    argv = [str(exe)]
    if args is not None:
        argv += args
    elif input is not None:
        argv.append(input)
    proc = subprocess.run(
        argv,
        input=input if args is not None else None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    result = ProcResult(argv, proc.returncode, proc.stdout, proc.stderr)

    # Auto-trigger GDB on an unexpected signal death when debugging is enabled.
    if DEBUG and result.crashed:
        from framework import gdb  # local import avoids a load-time cycle
        report = gdb.run_under_gdb(exe, argv[1:])
        result.gdb = report
        LAST_CRASHES.append({"binary": name, "args": argv[1:], "report": report})
    return result
