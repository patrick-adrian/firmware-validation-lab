"""Fan controller business logic."""

from __future__ import annotations

from components.fan_controller.events import THERMAL_TO_FAN
from components.fan_controller.models import FanSpeed, FanSpeedStatus
from components.thermal_manager.events import ThermalEvent
from components.thermal_manager.models import ThermalState
from framework.database import record_event
from framework.logger import get_component_logger, log_structured

logger = get_component_logger("fan_controller")


class FanControllerService:
    """Adjust fan speed in response to thermal events."""

    def __init__(self) -> None:
        self._speed = FanSpeed.OFF

    def handle_thermal_event(self, event: ThermalEvent) -> FanSpeedStatus:
        """Update fan speed based on a thermal event."""
        mapped = THERMAL_TO_FAN.get(event.event, FanSpeed.OFF.value)
        self._speed = FanSpeed(mapped)

        log_structured(
            logger,
            "Fan speed updated",
            event=event.event.value,
            fan_speed=self._speed.value,
            temperature=event.temperature,
        )
        record_event(
            "fan_controller",
            event.event.value,
            details=f"fan_speed={self._speed.value}",
        )
        return self.get_speed()

    def get_speed(self) -> FanSpeedStatus:
        """Return the current fan speed."""
        return FanSpeedStatus(speed=self._speed)

    def bootstrap_from_thermal_state(self, state: ThermalState) -> FanSpeedStatus:
        """Set initial fan speed from a thermal state without logging propagation."""
        mapped = THERMAL_TO_FAN.get(state, FanSpeed.OFF.value)
        self._speed = FanSpeed(mapped)
        return self.get_speed()
