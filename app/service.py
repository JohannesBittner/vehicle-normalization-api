"""
Verbindet die API-Schemas mit der eigentlichen Normalisierungslogik.

Ist bewusst dünn gehalten, weil die ganze Fachlogik in normalization.py steckt.
Hier wird nur zwischen Pydantic-Modell und Fachlogik übersetzt.
"""
from __future__ import annotations

from app.normalization import normalize_vehicle_record
from app.schemas import (
    CarNormalizeRequest,
    MotorcycleNormalizeRequest,
    VehicleNormalizeResponse,
)


def normalize(request: CarNormalizeRequest | MotorcycleNormalizeRequest) -> VehicleNormalizeResponse:
    """Normalisiert einen Fahrzeug-Request und packt das Ergebnis ins Response-Schema."""
    result = normalize_vehicle_record(
        vehicle_type=request.vehicle_type,
        brand=request.brand,
        model=request.model,
        vin=request.vin,
        displacement_ccm=request.displacement_ccm,
        power_kw=request.power_kw
    )
    return VehicleNormalizeResponse(**result)