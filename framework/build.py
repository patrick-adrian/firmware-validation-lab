"""
build.py - gcc driver. Compiles firmware (+ mocks) into ctypes shared libraries and
black-box executables, capturing warnings/errors as structured results.

All artifacts land in runtime/. Shared libs are built with -fPIC -shared.
"""
from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from framework import config


@dataclass
class BuildResult:
    name: str
    artifact: Path
    ok: bool
    command: list[str]
    stderr: str = ""
    warnings: list[str] = field(default_factory=list)


def _shared_lib_name(name: str) -> str:
    # Linux: lib<name>.so ; macOS: lib<name>.dylib (kept for dev portability).
    ext = "dylib" if platform.system() == "Darwin" else "so"
    return f"lib{name}.{ext}"


def _collect_warnings(stderr: str) -> list[str]:
    return [ln for ln in stderr.splitlines() if "warning:" in ln]


def _run(cmd: list[str]) -> tuple[bool, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode == 0, proc.stderr


def build_library(name: str) -> BuildResult:
    """Compile lib<name> as a PIC shared object for ctypes loading."""
    sources = [str(config.ROOT / s) for s in config.LIBRARIES[name]]
    out = config.RUNTIME_DIR / _shared_lib_name(name)
    cmd = [config.CC, *config.cflags(), "-fPIC", "-shared", *sources, "-o", str(out)]
    ok, stderr = _run(cmd)
    return BuildResult(name, out, ok, cmd, stderr, _collect_warnings(stderr))


def build_executable(name: str) -> BuildResult:
    """Compile a standalone executable for black-box / GDB runs."""
    sources = [str(config.ROOT / s) for s in config.EXECUTABLES[name]]
    out = config.RUNTIME_DIR / name
    cmd = [config.CC, *config.cflags(), *sources, "-o", str(out)]
    ok, stderr = _run(cmd)
    return BuildResult(name, out, ok, cmd, stderr, _collect_warnings(stderr))


def build_all() -> list[BuildResult]:
    config.RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    results = [build_library(n) for n in config.LIBRARIES]
    results += [build_executable(n) for n in config.EXECUTABLES]
    return results


def build_for_tests(test_modules: list[str]) -> list[BuildResult]:
    """Build only the artifacts the given test modules declare in TEST_ARTIFACTS."""
    config.RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    libs: set[str] = set()
    exes: set[str] = set()
    for mod in test_modules:
        spec = config.TEST_ARTIFACTS.get(mod, {})
        libs.update(spec.get("libs", []))
        exes.update(spec.get("exes", []))
    results = [build_library(n) for n in sorted(libs)]
    results += [build_executable(n) for n in sorted(exes)]
    return results


if __name__ == "__main__":
    import sys

    rs = build_all()
    failed = [r for r in rs if not r.ok]
    for r in rs:
        status = "OK " if r.ok else "ERR"
        print(f"[{status}] {r.artifact.name}")
        if not r.ok:
            print(r.stderr)
    sys.exit(1 if failed else 0)
