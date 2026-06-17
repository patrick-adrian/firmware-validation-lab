# Test Strategy

## Principles

1. **Black-box only** — tests call public HTTP APIs, never internal variables.
2. **Observable behavior** — assertions on fan speed and power state after temperature stimulus.
3. **Event traceability** — logs and database must reconstruct propagation chains.

## Test Layers

| Layer      | Location           | Purpose                          |
|------------|--------------------|----------------------------------|
| Regression | `tests/regression/` | Plan-defined baseline scenarios |
| System     | `tests/system/`     | Boundaries, recovery, throttling |

## Execution

```bash
pytest tests/ -v
./scripts/run_regression.sh
```

Services auto-start via `tests/conftest.py` when not already running.

## Failure Analysis

```bash
python main.py analyze
```

Uses component logs and database events to identify missing propagation.
