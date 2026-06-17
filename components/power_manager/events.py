"""Power manager event handling."""

from components.thermal_manager.models import ThermalState

THERMAL_TO_POWER: dict[ThermalState, str] = {
    ThermalState.NORMAL: "NORMAL",
    ThermalState.WARNING: "NORMAL",
    ThermalState.OVERHEAT: "THROTTLED",
    ThermalState.CRITICAL: "EMERGENCY",
}
