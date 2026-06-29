# Firmware Validation Lab — Unit/Driver Tier

A modular lab that validates **real compiled C firmware** with a **pure-Python (stdlib-only)**
framework. It mirrors how a semiconductor validation team tests low-level drivers: build with
strict warnings + debug symbols, run in mock-hardware and black-box modes, and drop into GDB the
moment something crashes.

> This is the **driver/unit tier**. Its sibling project `firmware-validation-lab` is the
> **system/behavioral tier**. They are separate codebases that share one results contract
> (same SQLite schema + report JSON), so both feed a single dashboard. See [PLAN.MD](PLAN.MD) §11.

## Requirements

- Linux (WSL Ubuntu is fine), `gcc`, `python3` (3.10+), and `gdb`. No pip packages.

## Quick start

```bash
python3 -m framework.runner            # build all needed C artifacts + run every test
python3 -m framework.runner test_uart  # one module
python3 -m framework.runner --list     # list tests
python3 -m framework.runner --report html
make && make test                      # equivalent via Make
```

## Debugging with GDB

```bash
python3 -m framework.runner --gdb test_crc   # run the module's binaries under GDB
python3 -m framework.runner --debug          # auto-capture a backtrace on ANY crash
```

The `crc_test CRASH` input deliberately dereferences NULL so you can see the automatic
SIGSEGV → GDB backtrace capture land in the report as a `CRASH` event.

## How Python talks to C

Two mechanisms, two modes (see `framework/cinterface.py`):


| Mode                          | Mechanism                 | Use                                                                                                        |
| ----------------------------- | ------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **Mock-hardware** (white-box) | `ctypes` + `lib<mod>.so`  | Call C functions directly, poke mock register banks, inject edge cases in-process. Default for unit tests. |
| **Black-box**                 | `subprocess` + executable | Run a real binary, diff stdout, isolate crashes, attach GDB.                                               |


The driver sources never touch real hardware directly — they go through `hw_`* hooks that the
`mocks/` layer implements in memory (and that a real STM32 HAL would implement against MMIO). The
firmware source is identical in both worlds; only the link target changes.

## Layout

```
framework/   Python framework: runner, build (gcc), cinterface (ctypes+subprocess),
             gdb, db (SQLite), report, logger, config, testkit
firmware/    C drivers: ring_buffer, crc, gpio, timer, uart
mocks/       Fake hardware: fake_uart/timer/gpio + mock_hw.h control surface
harness/     Black-box C entrypoints (crc_test.c)
tests/       Python tests (one per firmware module)
runtime/     Build artifacts + validation.db + report.json (gitignored)
stm32/       Future on-target expansion notes
```

## Modules under test

- **ring_buffer** — fixed-capacity SPSC FIFO; overflow/underflow/wrap/NULL.
- **crc** — CRC-32 (IEEE 802.3); known vector `0xCBF43926`, corruption, crash injection.
- **gpio** — STM32-style MODER/ODR/IDR bit-banging; range defense.
- **timer** — software timer over a mock tick source; deterministic, rollover-safe.
- **uart** — buffered TX/RX over ring buffers; back-pressure, overflow, RX injection.

See [PLAN.MD](PLAN.MD) for the full architecture and rationale.