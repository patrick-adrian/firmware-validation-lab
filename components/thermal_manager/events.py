"""Thermal event definitions."""

from pydantic import BaseModel

from components.thermal_manager.models import ThermalState


class ThermalEvent(BaseModel):
    """Event broadcast when thermal state changes."""

    event: ThermalState
    temperature: float
    previous_state: ThermalState | None = None
