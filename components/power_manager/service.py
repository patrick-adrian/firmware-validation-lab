"""Power manager business logic."""

from __future__ import annotations

from components.power_manager.events import THERMAL_TO_POWER
from components.power_manager.models import PowerState, PowerStateStatus
from components.thermal_manager.events import ThermalEvent
from components.thermal_manager.models import ThermalState
from framework.database import record_event
from framework.logger import get_component_logger, log_structured

logger = get_component_logger("power_manager")


class PowerManagerService:
    """Throttle performance in response to thermal events."""

    def __init__(self) -> None:
        self._state = PowerState.NORMAL

    def handle_thermal_event(self, event: ThermalEvent) -> PowerStateStatus:
        """Update power state based on a thermal event."""
        mapped = THERMAL_TO_POWER.get(event.event, PowerState.NORMAL.value)
        self._state = PowerState(mapped)

        log_structured(
            logger,
            "Power state updated",
            event=event.event.value,
            power_state=self._state.value,
            temperature=event.temperature,
        )
        record_event(
            "power_manager",
            event.event.value,
            details=f"power_state={self._state.value}",
        )
        return self.get_state()

    def get_state(self) -> PowerStateStatus:
        """Return the current power state."""
        return PowerStateStatus(state=self._state)

    def bootstrap_from_thermal_state(self, state: ThermalState) -> PowerStateStatus:
        """Set initial power state from a thermal state."""
        mapped = THERMAL_TO_POWER.get(state, PowerState.NORMAL.value)
        self._state = PowerState(mapped)
        return self.get_state()
