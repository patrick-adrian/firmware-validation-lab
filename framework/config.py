"""
Central configuration: paths, compiler flags, and the C source map.

Both the Python build driver (framework/build.py) and the Makefile read the same
flag set conceptually; keep them in sync if you edit one.
"""
from __future__ import annotations

import os
from pathlib import Path

# ---- Paths ---------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
FIRMWARE_DIR = ROOT / "firmware"
MOCKS_DIR = ROOT / "mocks"
HARNESS_DIR = ROOT / "harness"
TESTS_DIR = ROOT / "tests"
RUNTIME_DIR = ROOT / "runtime"

# SQLite results store. Shares the schema (not the file) with the sibling
# firmware-validation-lab project so both tiers can feed one dashboard.
DATABASE_DIR = RUNTIME_DIR
DATABASE_PATH = RUNTIME_DIR / "validation.db"

REPORT_JSON_PATH = RUNTIME_DIR / "report.json"
REPORT_HTML_PATH = RUNTIME_DIR / "report.html"
LOG_DIR = RUNTIME_DIR / "logs"

# ---- Compiler ------------------------------------------------------------
CC = os.environ.get("CC", "gcc")

# Debug-first, embedded-strict. -g -O0 keeps GDB line info and locals accurate;
# -Werror enforces the no-warnings discipline of a validation team.
CFLAGS = [
    "-g",
    "-O0",
    "-std=c11",
    "-Wall",
    "-Wextra",
    "-Werror",
    f"-I{FIRMWARE_DIR}",
    f"-I{MOCKS_DIR}",
]

# Optional hardening profile, enabled with FVLAB_SANITIZE=1.
SANITIZE_FLAGS = ["-fsanitize=address,undefined", "-fno-omit-frame-pointer"]


def cflags() -> list[str]:
    flags = list(CFLAGS)
    if os.environ.get("FVLAB_SANITIZE") == "1":
        flags += SANITIZE_FLAGS
    return flags


# ---- C source map --------------------------------------------------------
# Shared libraries loaded in-process via ctypes (white-box / mock-hardware mode).
# Each value is the list of .c files (relative to ROOT) linked into lib<name>.so.
LIBRARIES: dict[str, list[str]] = {
    "ring_buffer": ["firmware/ring_buffer.c"],
    "crc": ["firmware/crc.c"],
    "gpio": ["firmware/gpio.c", "mocks/fake_gpio.c"],
    "timer": ["firmware/timer.c", "mocks/fake_timer.c"],
    "uart": ["firmware/uart.c", "firmware/ring_buffer.c", "mocks/fake_uart.c"],
}

# Standalone executables for black-box mode (subprocess + GDB).
EXECUTABLES: dict[str, list[str]] = {
    "crc_test": ["harness/crc_test.c", "firmware/crc.c"],
}

# Maps a test module (tests/test_X.py) to the artifacts it needs built first.
TEST_ARTIFACTS: dict[str, dict[str, list[str]]] = {
    "test_ring_buffer": {"libs": ["ring_buffer"], "exes": []},
    "test_crc": {"libs": ["crc"], "exes": ["crc_test"]},
    "test_gpio": {"libs": ["gpio"], "exes": []},
    "test_timer": {"libs": ["timer"], "exes": []},
    "test_uart": {"libs": ["uart"], "exes": []},
}
