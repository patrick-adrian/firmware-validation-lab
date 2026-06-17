"""Fan controller event handling."""

from components.thermal_manager.models import ThermalState

THERMAL_TO_FAN: dict[ThermalState, str] = {
    ThermalState.NORMAL: "LOW",
    ThermalState.WARNING: "MEDIUM",
    ThermalState.OVERHEAT: "HIGH",
    ThermalState.CRITICAL: "MAX",
}
