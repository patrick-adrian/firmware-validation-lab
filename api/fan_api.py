"""Fan controller HTTP service and black-box client."""

from __future__ import annotations

import requests
from fastapi import FastAPI

from components.fan_controller.models import FanSpeedStatus
from components.fan_controller.service import FanControllerService
from components.thermal_manager.events import ThermalEvent
from framework.config import FAN_URL

_service = FanControllerService()
app = FastAPI(title="Fan Controller", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "component": "fan_controller"}


@app.post("/thermal-event", response_model=FanSpeedStatus)
def receive_thermal_event(event: ThermalEvent) -> FanSpeedStatus:
    return _service.handle_thermal_event(event)


@app.get("/fan-speed", response_model=FanSpeedStatus)
def get_fan_speed() -> FanSpeedStatus:
    return _service.get_speed()


class FanApiClient:
    """Black-box client for fan controller validation."""

    def __init__(self, base_url: str = FAN_URL) -> None:
        self.base_url = base_url.rstrip("/")

    def get_speed(self) -> FanSpeedStatus:
        response = requests.get(f"{self.base_url}/fan-speed", timeout=5.0)
        response.raise_for_status()
        return FanSpeedStatus.model_validate(response.json())
