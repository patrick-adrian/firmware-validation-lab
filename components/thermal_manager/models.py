"""Thermal state models."""

from enum import Enum

from pydantic import BaseModel, Field


class ThermalState(str, Enum):
    """Discrete thermal operating states."""

    NORMAL = "NORMAL"
    WARNING = "WARNING"
    OVERHEAT = "OVERHEAT"
    CRITICAL = "CRITICAL"


class TemperatureUpdate(BaseModel):
    """Incoming temperature sample."""

    temperature: float = Field(..., ge=-40.0, le=150.0)


class ThermalStatus(BaseModel):
    """Published thermal status."""

    temperature: float
    state: ThermalState
