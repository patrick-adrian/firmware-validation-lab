"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import subprocess
import sys
import time
from collections.abc import Generator

import pytest
import requests

from api.fan_api import FanApiClient
from api.power_api import PowerApiClient
from api.thermal_api import ThermalApiClient
from framework.config import (
    EVENT_PROPAGATION_DELAY,
    FAN_PORT,
    POWER_PORT,
    PROJECT_ROOT,
    SERVICE_STARTUP_TIMEOUT,
    THERMAL_PORT,
)
from framework.database import init_database


def _health_check(url: str) -> bool:
    try:
        response = requests.get(url, timeout=1.0)
        return response.status_code == 200
    except requests.RequestException:
        return False


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
    raise RuntimeError("Services are not running. Start them with scripts/start_system.sh")


@pytest.fixture(scope="session", autouse=True)
def database_initialized() -> None:
    init_database()


@pytest.fixture(scope="session")
def services_running() -> Generator[None, None, None]:
    """Ensure component services are available before black-box tests run."""
    urls = [
        f"http://127.0.0.1:{THERMAL_PORT}/health",
        f"http://127.0.0.1:{FAN_PORT}/health",
        f"http://127.0.0.1:{POWER_PORT}/health",
    ]
    if all(_health_check(url) for url in urls):
        yield
        return

    processes = [
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "api.thermal_api:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(THERMAL_PORT),
                "--log-level",
                "warning",
            ],
            cwd=PROJECT_ROOT,
        ),
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "api.fan_api:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(FAN_PORT),
                "--log-level",
                "warning",
            ],
            cwd=PROJECT_ROOT,
        ),
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "api.power_api:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(POWER_PORT),
                "--log-level",
                "warning",
            ],
            cwd=PROJECT_ROOT,
        ),
    ]
    try:
        _wait_for_services()
        yield
    finally:
        for process in processes:
            process.terminate()
            process.wait(timeout=5)


@pytest.fixture
def thermal_api(services_running: None) -> ThermalApiClient:
    return ThermalApiClient()


@pytest.fixture
def fan_api(services_running: None) -> FanApiClient:
    return FanApiClient()


@pytest.fixture
def power_api(services_running: None) -> PowerApiClient:
    return PowerApiClient()


@pytest.fixture
def propagate_delay() -> float:
    return EVENT_PROPAGATION_DELAY
