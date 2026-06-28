"""
runner.py - Test execution engine + CLI.

    python -m framework.runner                 # build + run all tests
    python -m framework.runner test_uart       # run one module
    python -m framework.runner --list          # list discovered tests
    python -m framework.runner --gdb test_crc  # run that module's binaries under GDB
    python -m framework.runner --debug         # auto-launch GDB on any crash
    python -m framework.runner --no-build       # skip the gcc step
    python -m framework.runner --report html    # also emit runtime/report.html
    python -m framework.runner --verbose
"""
from __future__ import annotations

import argparse
import importlib
import sys
import time
import traceback
from datetime import datetime, timezone
from types import ModuleType
from typing import Any, Callable

from framework import build, cinterface, config, db, report
from framework import gdb as gdbmod
from framework.logger import get_logger
from framework.testkit import SkipTest


def discover_modules(selector: str | None = None) -> list[str]:
    """Return sorted test module names (test_*) under tests/, optionally filtered."""
    names = sorted(p.stem for p in config.TESTS_DIR.glob("test_*.py"))
    if selector:
        # Accept "uart", "test_uart", or "tests/test_uart.py".
        stem = selector.replace(".py", "").split("/")[-1].split("\\")[-1]
        if not stem.startswith("test_"):
            stem = "test_" + stem
        names = [n for n in names if n == stem]
    return names


def _import_test_module(name: str) -> ModuleType:
    return importlib.import_module(f"tests.{name}")


def _collect_tests(mod: ModuleType) -> list[tuple[str, Callable[[], Any]]]:
    out = []
    for attr in sorted(dir(mod)):
        if attr.startswith("test_"):
            fn = getattr(mod, attr)
            if callable(fn):
                out.append((attr, fn))
    return out


def run_tests(modules: list[str], log, verbose: bool
              ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    results: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []

    for mod_name in modules:
        try:
            mod = _import_test_module(mod_name)
        except Exception as exc:  # import error counts as a module-level error
            ts = datetime.now(timezone.utc).isoformat()
            results.append({"test_name": mod_name, "result": "ERROR",
                            "execution_time": 0.0, "timestamp": ts,
                            "message": f"import failed: {exc}"})
            continue

        for test_name, fn in _collect_tests(mod):
            cinterface.LAST_CRASHES.clear()
            start = time.perf_counter()
            result = "PASS"
            message = ""
            try:
                fn()
            except SkipTest as exc:
                result, message = "SKIP", str(exc)
            except AssertionError as exc:
                result, message = "FAIL", str(exc)
            except Exception:
                result, message = "ERROR", traceback.format_exc()
            duration = time.perf_counter() - start
            ts = datetime.now(timezone.utc).isoformat()

            results.append({"test_name": test_name, "result": result,
                            "execution_time": duration, "timestamp": ts,
                            "message": message})
            log.log(test_name, level=("INFO" if result == "PASS" else "ERROR"),
                    result=result, duration=duration, message=message[:500])
            db.record_test_run(test_name, result, duration, timestamp=ts)

            # Fold any auto-captured GDB crash dumps into events + DB.
            for crash in cinterface.LAST_CRASHES:
                bt = gdbmod.format_report(crash["report"])
                events.append({"component": crash["binary"], "event_type": "CRASH",
                               "details": bt, "timestamp": ts})
                db.record_event(crash["binary"], "CRASH", bt, timestamp=ts)

            _print_line(test_name, result, duration, message, verbose)

    return results, events


def _print_line(name: str, result: str, duration: float, message: str, verbose: bool) -> None:
    badge = {"PASS": "PASS", "FAIL": "FAIL", "ERROR": "ERR ", "SKIP": "SKIP"}.get(result, "?")
    print(f"  [{badge}] {name} ({duration*1000:.1f} ms)")
    if result in ("FAIL", "ERROR") and message:
        for ln in message.strip().splitlines():
            print(f"        {ln}")
    elif result == "SKIP" and verbose and message:
        print(f"        ({message})")


def cmd_gdb(modules: list[str]) -> int:
    """Run the executables associated with the selected modules under GDB."""
    if not gdbmod.gdb_available():
        print("gdb is not installed / not on PATH.", file=sys.stderr)
        return 3
    any_run = False
    for mod_name in modules:
        for exe in config.TEST_ARTIFACTS.get(mod_name, {}).get("exes", []):
            any_run = True
            binary = cinterface.executable_path(exe)
            print(f"\n=== GDB: {exe} (CRASH input) ===")
            # Drive the known crash path so there is something to back-trace.
            rep = gdbmod.run_under_gdb(binary, ["CRASH"])
            print(gdbmod.format_report(rep))
    if not any_run:
        print("No black-box executables are associated with the selected module(s).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="framework.runner",
                                     description="Firmware Validation Lab test runner")
    parser.add_argument("module", nargs="?", help="test module to run (e.g. test_uart)")
    parser.add_argument("--list", action="store_true", help="list discovered tests and exit")
    parser.add_argument("--gdb", action="store_true",
                        help="run the module's black-box binaries under GDB and exit")
    parser.add_argument("--debug", action="store_true",
                        help="auto-launch GDB and capture a backtrace on any crash")
    parser.add_argument("--no-build", action="store_true", help="skip the gcc build step")
    parser.add_argument("--report", choices=["json", "html"], default="json",
                        help="report format (json always written; html adds HTML)")
    parser.add_argument("--verbose", "-v", action="store_true")
    opts = parser.parse_args(argv)

    modules = discover_modules(opts.module)
    if opts.module and not modules:
        print(f"No test module matched '{opts.module}'.", file=sys.stderr)
        return 2

    if opts.list:
        for m in modules:
            print(m)
        return 0

    if opts.gdb:
        # Ensure the binaries exist before debugging them.
        if not opts.no_build:
            build.build_for_tests(modules)
        return cmd_gdb(modules)

    log = get_logger("runner", verbose=opts.verbose)
    cinterface.DEBUG = opts.debug
    db.init_database()

    # ---- Build ----
    if not opts.no_build:
        print("Building C artifacts...")
        builds = build.build_for_tests(modules)
        failed = [b for b in builds if not b.ok]
        for b in builds:
            if b.warnings:
                print(f"  warnings in {b.artifact.name}:")
                for w in b.warnings:
                    print(f"    {w}")
        if failed:
            print("\nBUILD FAILED:", file=sys.stderr)
            for b in failed:
                print(f"  {b.artifact.name}", file=sys.stderr)
                print(b.stderr, file=sys.stderr)
            return 1
        print(f"  built {len(builds)} artifact(s).")

    # ---- Run ----
    print(f"\nRunning {len(modules)} module(s)...")
    start = time.perf_counter()
    results, events = run_tests(modules, log, opts.verbose)
    duration = time.perf_counter() - start

    # ---- Report ----
    rep = report.build_report(results, duration, events)
    report.write_json(rep)
    if opts.report == "html":
        report.write_html(rep)

    s = rep["test_summary"]
    print(f"\n{'='*48}")
    print(f"  PASS {s['pass_count']}   FAIL {s['fail_count']}   "
          f"({duration:.2f}s)")
    print(f"  report: {config.REPORT_JSON_PATH}")
    if opts.report == "html":
        print(f"  html:   {config.REPORT_HTML_PATH}")
    print("=" * 48)
    return s["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
