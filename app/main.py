"""FastAPI-Einstiegspunkt für Routing und Fehlerbehandlung."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from app.schemas import (
    HealthResponse,
    VehicleNormalizeRequest,
    VehicleNormalizeResponse,
)
from app.service import normalize as normalize_service

app = FastAPI(
    title="Vehicle Normalization API",
    description=(
        "Kleiner Demonstrator zur Normalisierung von Fahrzeug-Stammdaten (Marke, Modell, Hubraum, Leistung, VIN) für PKW und Motorräder. "
        "Portfolio-Projekt für FastAPI + Pydantic (inkl. discriminated unions) und pytest."
    ),
    version="0.1.0",
)


@app.get("/health", response_model=HealthResponse, tags=["Meta"])
def health() -> HealthResponse:
    """Einfacher Check, ob die API überhaupt läuft."""
    return HealthResponse()


@app.post("/normalize", response_model=VehicleNormalizeResponse, tags=["Normalization"])
def normalize_vehicle(payload: VehicleNormalizeRequest) -> VehicleNormalizeResponse:
    """Nimmt einen Fahrzeug-Datensatz entgegen und gibt die normalisierte Version zurück."""
    try:
        return normalize_service(payload)
    except ValidationError as exc:
        # Lieber ein sauberer 422 mit Fehlermeldung als ein nackter 500er.
        raise HTTPException(status_code=422, detail=str(exc)) from exc