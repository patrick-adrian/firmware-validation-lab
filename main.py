"""Entry point for the Firmware Validation Lab."""

from __future__ import annotations

import argparse
import multiprocessing
import time

import requests
import uvicorn

from analytics.metrics_collector import collect_metrics
from analytics.root_cause_analyzer import analyze_recent_failures
from framework.config import (
    FAN_PORT,
    POWER_PORT,
    SERVICE_STARTUP_TIMEOUT,
    THERMAL_PORT,
)
from framework.database import init_database
from framework.test_runner import run_regression


def _run_uvicorn(app_path: str, port: int) -> None:
    uvicorn.run(app_path, host="127.0.0.1", port=port, log_level="warning")


def start_services() -> list[multiprocessing.Process]:
    """Launch all firmware component APIs."""
    init_database()
    specs = [
        ("api.thermal_api:app", THERMAL_PORT),
        ("api.fan_api:app", FAN_PORT),
        ("api.power_api:app", POWER_PORT),
    ]
    processes: list[multiprocessing.Process] = []
    for app_path, port in specs:
        process = multiprocessing.Process(
            target=_run_uvicorn,
            args=(app_path, port),
            daemon=True,
        )
        process.start()
        processes.append(process)
    _wait_for_services()
    return processes


def _wait_for_services() -> None:
    urls = [
        f"http://127.0.0.1:{THERMAL_PORT}/health",
        f"http://127.0.0.1:{FAN_PORT}/health",
        f"http://127.0.0.1:{POWER_PORT}/health",
    ]
    deadline = time.time() + SERVICE_STARTUP_TIMEOUT
    while time.time() < deadline:
        if all(_health_check(url) for url in urls):
            return
        time.sleep(0.2)
    raise RuntimeError("Timed out waiting for firmware component services")


def _health_check(url: str) -> bool:
    try:
        response = requests.get(url, timeout=1.0)
        return response.status_code == 200
    except requests.RequestException:
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Firmware Validation Lab")
    parser.add_argument(
        "command",
        choices=("start", "regression", "metrics", "analyze"),
        help="Operation to perform",
    )
    args = parser.parse_args()

    if args.command == "start":
        processes = start_services()
        print("Firmware Validation Lab services running:")
        print(f"  Thermal Manager: http://127.0.0.1:{THERMAL_PORT}")
        print(f"  Fan Controller:  http://127.0.0.1:{FAN_PORT}")
        print(f"  Power Manager:   http://127.0.0.1:{POWER_PORT}")
        print("Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            for process in processes:
                process.terminate()
    elif args.command == "regression":
        processes = start_services()
        try:
            result = run_regression()
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            raise SystemExit(result.exit_code)
        finally:
            for process in processes:
                process.terminate()
    elif args.command == "metrics":
        init_database()
        metrics = collect_metrics()
        for key, value in metrics.items():
            print(f"{key}: {value}")
    elif args.command == "analyze":
        init_database()
        for diagnosis in analyze_recent_failures():
            print(diagnosis.format_report())
            print("-" * 40)


if __name__ == "__main__":
    main()
