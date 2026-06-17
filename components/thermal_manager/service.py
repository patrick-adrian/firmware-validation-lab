"""Thermal manager business logic."""

from __future__ import annotations

import requests

from components.thermal_manager.events import ThermalEvent
from components.thermal_manager.models import ThermalState, ThermalStatus
from framework.config import FAN_URL, POWER_URL
from framework.database import record_event
from framework.logger import get_component_logger, log_structured

logger = get_component_logger("thermal_manager")


def classify_temperature(temperature: float) -> ThermalState:
    """Map a temperature reading to a thermal state."""
    if temperature >= 100:
        return ThermalState.CRITICAL
    if temperature >= 85:
        return ThermalState.OVERHEAT
    if temperature >= 70:
        return ThermalState.WARNING
    return ThermalState.NORMAL


class ThermalManagerService:
    """Monitor temperature and publish thermal state changes."""

    def __init__(self, fan_url: str = FAN_URL, power_url: str = POWER_URL) -> None:
        self._temperature = 25.0
        self._state = ThermalState.NORMAL
        self._fan_url = fan_url
        self._power_url = power_url

    def set_temperature(self, temperature: float) -> ThermalStatus:
        """Update temperature and propagate state changes to downstream components."""
        previous_state = self._state
        self._temperature = temperature
        self._state = classify_temperature(temperature)

        log_structured(
            logger,
            "Temperature updated",
            event=self._state.value,
            temperature=temperature,
        )
        record_event(
            "thermal_manager",
            self._state.value,
            details=f"temperature={temperature}",
        )

        event = ThermalEvent(
            event=self._state,
            temperature=temperature,
            previous_state=previous_state if self._state != previous_state else None,
        )
        self._propagate_event(event)

        return self.get_status()

    def get_status(self) -> ThermalStatus:
        """Return the current thermal status."""
        return ThermalStatus(temperature=self._temperature, state=self._state)

    def _propagate_event(self, event: ThermalEvent) -> None:
        """Notify fan and power managers of a thermal state change."""
        payload = event.model_dump(mode="json")
        for target, name in ((self._fan_url, "fan_controller"), (self._power_url, "power_manager")):
            try:
                response = requests.post(
                    f"{target}/thermal-event",
                    json=payload,
                    timeout=2.0,
                )
                response.raise_for_status()
                log_structured(
                    logger,
                    f"Propagated {event.event.value} to {name}",
                    event=event.event.value,
                    target=name,
                )
            except requests.RequestException as exc:
                log_structured(
                    logger,
                    f"Failed to propagate event to {name}",
                    event="PROPAGATION_FAILURE",
                    target=name,
                    error=str(exc),
                )
