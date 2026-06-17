"""Thermal manager HTTP service and black-box client."""

from __future__ import annotations

import requests
from fastapi import FastAPI

from components.thermal_manager.models import TemperatureUpdate, ThermalStatus
from components.thermal_manager.service import ThermalManagerService
from framework.config import THERMAL_URL

_service = ThermalManagerService()
app = FastAPI(title="Thermal Manager", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "component": "thermal_manager"}


@app.post("/temperature", response_model=ThermalStatus)
def set_temperature(update: TemperatureUpdate) -> ThermalStatus:
    return _service.set_temperature(update.temperature)


@app.get("/status", response_model=ThermalStatus)
def get_status() -> ThermalStatus:
    return _service.get_status()


class ThermalApiClient:
    """Black-box client for thermal manager validation."""

    def __init__(self, base_url: str = THERMAL_URL) -> None:
        self.base_url = base_url.rstrip("/")

    def set_temperature(self, temperature: float) -> ThermalStatus:
        response = requests.post(
            f"{self.base_url}/temperature",
            json={"temperature": temperature},
            timeout=5.0,
        )
        response.raise_for_status()
        return ThermalStatus.model_validate(response.json())

    def get_status(self) -> ThermalStatus:
        response = requests.get(f"{self.base_url}/status", timeout=5.0)
        response.raise_for_status()
        return ThermalStatus.model_validate(response.json())
