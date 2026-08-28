"""
Skript, um die Beispiel-Datensätze automatisch gegen die laufende API zu prüfen. 
Jeder Fall in sample_data.json enthält neben dem Payload einen erwarteten Status-Code (expected_status) 
und optional erwartete Response-Felder (expected), die mit der tatsächlichen Antwort verglichen werden.

Voraussetzung: Die API läuft bereits, z.B. via
    uvicorn app.main:app --reload

oder im Docker-Container auf Port 8000.

Aufruf:
    python tests/try_sample_data.py

Exit-Code:
    0, wenn alle Fälle bestehen 
    1, wenn mindestens ein Fall fehlschlägt oder keine Verbindung zur API besteht
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import httpx

API_URL = "http://127.0.0.1:8000/normalize"
SAMPLE_FILE = Path(__file__).parent / "sample_data.json"


def check_expected_fields(response_body: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    """Vergleicht die erwarteten Felder mit der tatsächlichen Response.

    Args:
        response_body: Die per JSON dekodierte tatsächliche Antwort der API.
        expected: Die im Testfall hinterlegten erwarteten Feldwerte.

    Returns:
        Liste von Fehlerbeschreibungen. Leer, wenn alle Felder passen.
    """
    mismatches = []
    for key, expected_value in expected.items():
        actual_value = response_body.get(key)
        if actual_value != expected_value:
            mismatches.append(
                f"Feld '{key}': erwartet {expected_value!r}, erhalten {actual_value!r}"
            )
    return mismatches


def main() -> None:
    samples = json.loads(SAMPLE_FILE.read_text(encoding="utf-8"))

    passed = 0
    failed = 0

    with httpx.Client(timeout=5.0) as client:
        for i, sample in enumerate(samples, start=1):
            description = sample["description"]
            payload = sample["payload"]
            expected_status = sample.get("expected_status")
            expected_fields = sample.get("expected", {})

            print(f"\n[{i}] {description}")
            print(f"    Request: {payload}")

            try:
                response = client.post(API_URL, json=payload)
            except httpx.ConnectError:
                print("    FEHLER: Keine Verbindung zur API. Läuft sie auf Port 8000?")
                sys.exit(1)

            print(f"    Status: {response.status_code} (erwartet: {expected_status})")

            errors = []
            if expected_status is not None and response.status_code != expected_status:
                errors.append(
                    f"Status-Code: erwartet {expected_status}, erhalten {response.status_code}"
                )

            if response.status_code < 400:
                body = response.json()
                print(f"    Response: {body}")
                errors.extend(check_expected_fields(body, expected_fields))
            else:
                print(f"    Response: {response.text}")

            if errors:
                failed += 1
                print("    ERGEBNIS: FEHLGESCHLAGEN")
                for error in errors:
                    print(f"      - {error}")
            else:
                passed += 1
                print("    ERGEBNIS: BESTANDEN")

    total = passed + failed
    print("\n" + "=" * 50)
    print(f"Zusammenfassung: {passed}/{total} Fälle bestanden, {failed} fehlgeschlagen")
    print("=" * 50)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()