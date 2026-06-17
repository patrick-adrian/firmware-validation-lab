# Validation Plan

## Scope

Validate thermal, fan, and power firmware component interactions using black-box HTTP APIs.

## Test Matrix

| Case    | Temperature | Expected Fan | Expected Power |
|---------|-------------|--------------|----------------|
| Normal  | 60°C        | LOW          | NORMAL         |
| Warning | 80°C        | MEDIUM       | NORMAL         |
| Overheat| 95°C        | HIGH         | THROTTLED      |
| Critical| 105°C       | MAX          | EMERGENCY      |

## Regression

Run `./scripts/run_regression.sh` after each change. Results persist to SQLite and reports.

## Exit Criteria

- All regression and system tests pass
- Event propagation visible in component logs and database
- Validation reports generated for each regression run
