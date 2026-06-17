"""Power manager HTTP service and black-box client."""

from __future__ import annotations

import requests
from fastapi import FastAPI

from components.power_manager.models import PowerStateStatus
from components.power_manager.service import PowerManagerService
from components.thermal_manager.events import ThermalEvent
from framework.config import POWER_URL

_service = PowerManagerService()
app = FastAPI(title="Power Manager", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "component": "power_manager"}


@app.post("/thermal-event", response_model=PowerStateStatus)
def receive_thermal_event(event: ThermalEvent) -> PowerStateStatus:
    return _service.handle_thermal_event(event)


@app.get("/power-state", response_model=PowerStateStatus)
def get_power_state() -> PowerStateStatus:
    return _service.get_state()


class PowerApiClient:
    """Black-box client for power manager validation."""

    def __init__(self, base_url: str = POWER_URL) -> None:
        self.base_url = base_url.rstrip("/")

    def get_state(self) -> PowerStateStatus:
        response = requests.get(f"{self.base_url}/power-state", timeout=5.0)
        response.raise_for_status()
        return PowerStateStatus.model_validate(response.json())
