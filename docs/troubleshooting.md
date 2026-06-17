# Troubleshooting

## Services Not Starting

```bash
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8002/health
curl http://127.0.0.1:8003/health
```

If unhealthy, check for port conflicts on 8001–8003.

## Tests Fail with Connection Errors

Start services first:

```bash
./scripts/start_system.sh
```

Or let pytest auto-start them (requires uvicorn installed).

## Fan/Power State Mismatch

1. Check component logs in `logs/component_logs/`
2. Query events: `python main.py metrics`
3. Run root cause analysis: `python main.py analyze`

## Reset Artifacts

```bash
./scripts/cleanup.sh
```

Removes logs, database, and report outputs for a clean run.
