# Firmware Validation Lab

Black-box validation framework for simulated firmware components: thermal manager, fan controller, and power manager.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run full regression (starts services, executes tests, writes reports)
./scripts/run_regression.sh

# Or start services manually
./scripts/start_system.sh
```

## Architecture

Three independent FastAPI services communicate over HTTP:

| Component        | Port | Endpoints                          |
|------------------|------|------------------------------------|
| Thermal Manager  | 8001 | `POST /temperature`, `GET /status` |
| Fan Controller   | 8002 | `GET /fan-speed`                   |
| Power Manager    | 8003 | `GET /power-state`                 |

Thermal state changes propagate to fan and power managers via `POST /thermal-event`.

## Black-Box Testing

Tests use HTTP clients only — never internal component state:

```python
thermal_api.set_temperature(95)
fan_speed = fan_api.get_speed()
power_state = power_api.get_state()
```

## Database

SQLite database at `database/validation.db` stores:

- `test_runs` — pytest results
- `events` — component event timeline

Initialize manually:

```python
from framework.database import init_database
init_database()
```

## Reports

After regression runs, HTML and JSON reports are written to:

- `reports/html/`
- `reports/json/`
- `reports/validation_reports/`

## Commands

```bash
python main.py start       # Start all services
python main.py regression  # Start services and run regression
python main.py metrics     # Print validation metrics
python main.py analyze     # Analyze recent failures
pytest tests/ -v           # Run tests directly (services auto-start)
```

## Project Layout

See `plan.md` for the full specification. Dashboard/Grafana integration is deferred; database wiring is included.
