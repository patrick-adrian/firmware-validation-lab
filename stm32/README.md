# stm32/ — On-target expansion (future)

Placeholder for moving the same validation suite from the host (mock HAL) onto real
STM32 silicon. **The Python tests do not change** — only the transport and the HAL
implementation behind the `hw_*` hooks change.

## What stays the same
- `firmware/*.c` — the driver logic is target-agnostic. It already talks to the world
  only through the `hw_uart_*` / `hw_get_ticks()` hooks and caller-owned register structs.
- `tests/*.py` — same assertions, same vectors.

## What gets added here
- `hal/` — real implementations of the `hw_*` hooks against STM32 USART/TIM/GPIO
  peripheral registers (replacing `mocks/fake_*.c` at link time).
- A startup file + linker script + `arm-none-eabi-gcc` cross-build profile.
- A transport in `framework/cinterface.py`:
  - **Serial**: `pyserial` to a UART bridge running a command dispatcher on-target.
  - **GDB/RSP**: OpenOCD + `arm-none-eabi-gdb` for register/memory inspection over SWD,
    which reuses `framework/gdb.py` almost verbatim (just a remote target).

## Migration path (incremental)
1. Cross-compile `firmware/` for `thumbv7em` with the real `hal/` (no test changes).
2. Flash a tiny command-dispatch firmware that exposes the driver API over UART.
3. Point `cinterface.run_c_function` / `load_module` equivalents at the serial transport.
4. Wire `framework/gdb.py` to `arm-none-eabi-gdb` + OpenOCD for on-target backtraces.

The mock-vs-real choice is a build/transport decision; the validation logic is portable.
