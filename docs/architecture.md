# Architecture

## Components

```
THERMAL_MANAGER (8001)
       |
       |  POST /thermal-event
       +------> FAN_CONTROLLER (8002)
       |
       +------> POWER_MANAGER (8003)
```

## Thermal State Machine

| Temperature | State    |
|-------------|----------|
| < 70°C      | NORMAL   |
| 70–84°C     | WARNING  |
| 85–99°C     | OVERHEAT |
| ≥ 100°C     | CRITICAL |

## Downstream Mapping

**Fan Controller**

| Thermal | Fan    |
|---------|--------|
| NORMAL  | LOW    |
| WARNING | MEDIUM |
| OVERHEAT| HIGH   |
| CRITICAL| MAX    |

**Power Manager**

| Thermal  | Power     |
|----------|-----------|
| NORMAL   | NORMAL    |
| WARNING  | NORMAL    |
| OVERHEAT | THROTTLED |
| CRITICAL | EMERGENCY |

## Persistence

- Structured JSON logs: `logs/component_logs/`
- SQLite: `database/validation.db` (`test_runs`, `events`)

## Validation Framework

- `framework/test_runner.py` — pytest orchestration
- `framework/report_generator.py` — HTML/JSON reports
- `analytics/root_cause_analyzer.py` — failure diagnostics
