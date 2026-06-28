# Firmware Validation Lab — Project Plan

> Status: **PLANNING** (no source created yet — this document is written first, per requirement).
> Target environment: **Linux** (WSL Ubuntu), `gcc`, `python3` (stdlib only), `gdb`, `make`.
> Philosophy: mirror a semiconductor-company validation team (AMD-style) — clarity,
> debuggability, reproducibility, low-level realism. **No heavy frameworks, no CI vendor lock-in.**

---

## 1. Goals & Non-Goals

### Goals
- Author **C firmware modules** (simulated drivers / low-level components).
- Validate them with a **pure-Python** test framework (stdlib only).
- Support three run modes:
  1. **Black-box** — run a compiled C executable, capture stdout/exit code, diff vs expected.
  2. **Mock-hardware** — load a C **shared library** (`.so`) via `ctypes`, swap real
     registers for in-memory mock structs, inject edge cases deterministically.
  3. **(future) On-target STM32** — same Python tests, different transport (OpenOCD/GDB/serial).
- First-class **GDB debugging**: run any test under GDB, auto-launch on segfault/crash,
  capture backtraces + register + memory state to the report.

### Non-Goals
- No pytest/CMake/Meson/Bazel. No Docker. No cloud CI as a hard dependency.
- No dynamic memory in firmware where avoidable (embedded discipline).

---

## 2. Directory Layout

```
firmware-validation-lab/
├── framework/              # Python test framework (core, stdlib only)
│   ├── __init__.py
│   ├── runner.py           # CLI + test execution engine (python -m framework.runner)
│   ├── logger.py           # structured per-test logging
│   ├── report.py           # JSON (+ optional HTML) reports
│   ├── build.py            # compile C modules -> runtime/ (.so and executables)
│   ├── config.py           # build flags + test configuration
│   ├── cinterface.py       # Python<->C glue: ctypes loader + subprocess runner
│   └── gdb.py              # GDB driver: backtrace/registers/memory capture
│
├── firmware/               # C modules (simulated embedded code)
│   ├── uart.c / uart.h     # buffered TX/RX over a ring buffer + mock data register
│   ├── gpio.c / gpio.h     # bit-banged registers (MODER/ODR/IDR style)
│   ├── timer.c / timer.h   # mocked tick counter, timeouts
│   ├── crc.c / crc.h       # CRC32 (IEEE 802.3, reflected)
│   └── ring_buffer.c / ring_buffer.h   # SPSC fixed-capacity ring buffer
│
├── mocks/                  # fake hardware layer (in-memory register banks)
│   ├── mock_hw.h           # shared mock register/types + injection hooks
│   ├── fake_uart.c         # backs uart.c's register accessors
│   ├── fake_gpio.c
│   └── fake_timer.c        # controllable tick source (no real delays)
│
├── tests/                  # Python test cases (one module per firmware unit)
│   ├── __init__.py
│   ├── test_uart.py
│   ├── test_gpio.py
│   ├── test_timer.py
│   ├── test_crc.py
│   └── test_ring_buffer.py
│
├── harness/                # C test entrypoints for black-box mode
│   └── crc_test.c          # tiny main() wrappers: argv in -> stdout out (diffable)
│
├── runtime/                # build artifacts (.so, executables, *.o) — gitignored
│
├── stm32/                  # FUTURE placeholder (HAL shim + transport notes)
│   └── README.md
│
├── Makefile                # primary build (mirrors framework/build.py flags)
├── build.sh                # thin wrapper for environments without make
└── PLAN.MD                 # this file
```

---

## 3. Python ↔ C Interaction (key design decision)

We use a **hybrid**, because real validation teams use both:

| Concern                          | Mechanism            | Why |
|----------------------------------|----------------------|-----|
| White-box, fine-grained, fast    | **ctypes + `.so`**   | Call individual functions, read/write mock register structs directly, inspect internal state, inject edge cases (overflow, NULL, corruption) in-process. Microsecond iteration. |
| Black-box, crash isolation, GDB  | **subprocess + exe** | A crashing test can't take down the Python runner. Captures stdout/exit/signal. Natural fit for GDB and (later) on-target runs. |

- **Mock-hardware mode** (default for unit tests): firmware is compiled into a `.so` *together
  with the `mocks/` layer*. Register accessors in firmware resolve to the fake in-memory banks.
  Python loads the `.so` with `ctypes`, declares `argtypes`/`restype`, and drives functions
  directly. Mock register banks are exported symbols Python can peek/poke for injection + assertions.
- **Black-box mode**: firmware + a `harness/*.c` `main()` compile to an executable. Python runs
  it via `subprocess`, feeds argv/stdin, captures stdout, and diffs against expected.
- A crash in either mode (non-zero/abnormal signal, or `--gdb`/`--debug` flag) triggers
  `framework/gdb.py` to re-run the binary under GDB in batch mode and attach the backtrace.

Helper exposed to tests:
```python
run_c_function("crc_test", input="1234")   # black-box convenience wrapper
lib = load_module("crc")                    # ctypes handle for white-box tests
```

---

## 4. C Firmware Module Designs (embedded style: structs, no malloc, mock registers)

- **ring_buffer** — `rb_t { uint8_t buf[N]; head; tail; count; }`; `rb_init/put/get/is_full/
  is_empty`. Foundation for UART. Edge cases: overflow, underflow, NULL handle.
- **crc32** — table-driven or bitwise IEEE 802.3 (reflected, poly 0xEDB88320, init 0xFFFFFFFF,
  final XOR). `crc32(const uint8_t*, size_t) -> uint32_t`. Edge cases: empty buffer, NULL.
- **uart** — `uart_t` with a TX ring buffer + RX ring buffer + a mock `DR` (data register) and
  `SR` (status register, TXE/RXNE bits). `uart_send/uart_recv/uart_flush`. Mock layer drains TX
  into a capture buffer Python can read; RX is fed by Python injecting bytes.
- **gpio** — `gpio_port_t { uint32_t MODER, ODR, IDR; }`. `gpio_set_pin/clear_pin/toggle_pin/
  read_pin/set_mode`. Pure bit manipulation; mock = the struct itself. Edge cases: pin index OOB.
- **timer** — `timer_t` over a mock tick source. `timer_start/elapsed/expired`. Ticks come from a
  controllable `mock_now()` so timing tests are **deterministic** (no `sleep`). Edge case: rollover.

Each module: `extern` register access goes through accessor functions/macros that the `mocks/`
layer implements, so the *same firmware source* links against either real HW (future) or mocks.

---

## 5. Build System

Two equivalent front-ends sharing one flag set (defined in `framework/config.py`):

- **Flags (debug-first, embedded-strict):** `-g -O0 -Wall -Wextra -Werror -std=c11`
  - `-g -O0` → reliable GDB symbols & line info (the GDB requirement).
  - `-Wall -Wextra -Werror` → no warnings tolerated, validation discipline.
- **Two artifact kinds per build:**
  - `runtime/lib<module>.so` (PIC, firmware + mocks) → ctypes white-box.
  - `runtime/<name>` executable (firmware + `harness/*.c` main) → black-box + GDB.
- `framework/build.py` shells out to `gcc`, returns structured pass/fail + captured warnings.
- `Makefile` mirrors it for humans / `make test`. `build.sh` for no-make boxes.

---

## 6. Test Framework Engine

- **Discovery:** import `tests/test_*.py`; collect functions named `test_*`. (No pytest — a small
  custom collector keeps deps at zero and behavior transparent.)
- **Execution:** each test runs isolated; framework times it (`time.perf_counter`), captures the
  per-test log, catches `AssertionError` (fail) vs exceptions (error) vs pass.
- **Assertions:** plain `assert` + a few helpers (`assert_eq`, `expect_crash`, `expect_signal`).
- **CLI (`python -m framework.runner`):**
  - `python -m framework.runner` — build + run all.
  - `python -m framework.runner test_uart` — run one module.
  - `python -m framework.runner --gdb test_uart` — run that module's binaries under GDB.
  - `python -m framework.runner --debug` — auto-launch GDB on any crash.
  - `--no-build`, `--report json|html`, `--verbose`, `--list`.
- **Reports (`report.py`):** JSON always (`runtime/report.json`): per-test status, duration,
  stdout/stderr, captured GDB backtrace on crash, build warnings. Optional self-contained HTML.

---

## 7. GDB Debugging (first-class requirement)

`framework/gdb.py` provides:
- `run_under_gdb(binary, args)` — batch-mode GDB (`gdb -batch -ex run -ex bt -ex "info
  registers" -ex "info locals" --args ...`), returns structured `{signal, backtrace, registers,
  frames}`.
- **Auto-trigger:** when a black-box subprocess exits via signal (SIGSEGV/SIGABRT) or the
  `--debug` flag is set, the runner re-runs the same binary under GDB and folds the backtrace +
  register dump + crash memory state into the test result and report.
- **Utilities:** `capture_backtrace`, `inspect_registers`, `dump_memory(addr,len)`.
- Requires the `-g -O0` build (already the default), so line numbers and locals are accurate.
- Detects missing `gdb` gracefully (skips with a clear message, doesn't fail the run).

---

## 8. Edge-Case / Fault Injection Catalog (what tests will actually exercise)

- Ring buffer **overflow** (put into full) and **underflow** (get from empty).
- **NULL pointer** handles passed to C APIs (verify defensive returns / or capture the crash via GDB).
- UART **RX corruption** (Python injects bad bytes) and **TX overflow**.
- Timer **rollover** and **mocked delays** (advance `mock_now()` — zero real wall-clock).
- CRC against **known vectors** (e.g. "123456789" → 0xCBF43926) + empty input.
- GPIO **out-of-range pin** index.

---

## 9. Build / Implementation Order

1. `PLAN.MD` (this).  ✅ first
2. `framework/config.py` (flags, paths) → `build.py` (gcc driver).
3. C: `ring_buffer` → `crc` → `gpio` → `timer` → `uart` (+ headers).
4. `mocks/` (`mock_hw.h`, `fake_*`).
5. `harness/crc_test.c` (black-box entry example).
6. `framework/`: `cinterface.py`, `logger.py`, `gdb.py`, `report.py`, `runner.py`.
7. `tests/` (all five).
8. `Makefile` + `build.sh`.
9. `stm32/README.md` placeholder.
10. Smoke run: `python -m framework.runner`; verify report + a deliberate crash → GDB backtrace.

---

## 10. Future Extensions

- **STM32 on-target:** keep the same Python tests; add a transport in `cinterface.py`
  (pyserial or OpenOCD+GDB-RSP). Firmware register accessors point at real MMIO via a HAL shim
  in `stm32/`. Mock vs real is a link-time/transport choice — tests don't change.
- **CI:** a thin `make test` is already CI-ready; add a GitHub Actions/GitLab job that runs it and
  uploads `runtime/report.json` + HTML as artifacts. (Deliberately not built now — avoid over-eng.)
- **Coverage:** `gcc --coverage` (gcov/lcov) wired through `build.py` flags.
- **Sanitizers:** optional `-fsanitize=address,undefined` build profile for deeper fault finding.
- **Property/fuzz:** feed ring buffer / CRC random vectors; compare `.so` (ctypes) vs golden.
```
