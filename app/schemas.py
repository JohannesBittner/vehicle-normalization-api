"""
Pydantic-Modelle für Requests und Responses der API.

Nutze hier eine discriminated union über "vehicle_type", weil PKWs und Motorräder zwar dieselben Basisfelder haben, 
aber unterschiedliche Plausibilitätsgrenzen brauchen (siehe normalization.py).
"""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator


class _VehicleBase(BaseModel):
    """Felder, die PKW und Motorrad gemeinsam haben."""
    brand: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    vin: str = Field(..., min_length=1)
    displacement_ccm: int = Field(..., gt=0, description="Hubraum in Kubikzentimeter")
    power_kw: int = Field(..., gt=0, description="Leistung in Kilowatt")

    @field_validator("brand", "model", "vin")
    @classmethod
    def not_blank(cls, value: str) -> str:
        """Wirft einen Fehler, wenn das Feld leer ist oder nur aus Leerzeichen besteht."""
        if not value.strip():
            raise ValueError("Feld darf nicht leer oder nur Whitespace sein")
        return value


class CarNormalizeRequest(_VehicleBase):
    """Request für einen PKW-Datensatz."""
    vehicle_type: Literal["car"] = "car"


class MotorcycleNormalizeRequest(_VehicleBase):
    """Request für einen Motorrad-Datensatz."""
    vehicle_type: Literal["motorcycle"] = "motorcycle"


# Discriminator sorgt dafür, dass FastAPI anhand von "vehicle_type" automatisch das richtige Schema (Car oder Motorcycle) auswählt.
VehicleNormalizeRequest = Annotated[
    CarNormalizeRequest | MotorcycleNormalizeRequest,
    Field(discriminator="vehicle_type"),
]


class VehicleNormalizeResponse(BaseModel):
    """Was die API nach der Normalisierung zurückgibt."""

    vehicle_type: Literal["car", "motorcycle"]
    brand: str
    model: str
    vin: str
    vin_valid: bool
    displacement_ccm: int
    displacement_plausible: bool
    power_kw: int
    power_plausible: bool


class HealthResponse(BaseModel):
    """Simple Antwort für den Health-Check-Endpoint."""
    status: str = "ok"
