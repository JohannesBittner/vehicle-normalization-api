"""
Normalisierungs-Logik für Fahrzeugdaten.
Hab das bewusst ohne FastAPI-Import geschrieben, damit ich die Funktionen auch ohne laufenden Server testen kann.
"""
from __future__ import annotations

import re
from typing import Any

# Mapping für unterschiedliche Schreibweisen der Hersteller.
# Eigentlich müsste das aus einer richtigen Stammdaten-Quelle kommen, aber für dieses Projekt reicht eine einfache dict.
_BRAND_ALIASES: dict[str, str] = {
    # PKW
    "vw": "Volkswagen",
    "volkswagen": "Volkswagen",
    "mercedes": "Mercedes-Benz",
    "mercedes-benz": "Mercedes-Benz",
    "mercedes benz": "Mercedes-Benz",
    "bmw": "BMW",
    "bayerische motoren werke": "BMW",  
    "audi": "Audi",
    "skoda": "Škoda",
    "škoda": "Škoda",
    "opel": "Opel",
    # Motorräder
    "harley": "Harley-Davidson",
    "harley davidson": "Harley-Davidson",
    "harley-davidson": "Harley-Davidson",
    "ducati": "Ducati",
    "ktm": "KTM",
    "kawasaki": "Kawasaki",
    "yamaha": "Yamaha",
    "honda": "Honda",
    "suzuki": "Suzuki",
    "triumph": "Triumph",
    "bmw motorrad": "BMW",
}

# Rechtsformzusätze, die manche Datenquellen an den Herstellernamen anhängen (z.B. "Volkswagen AG" oder "Harley-Davidson, Inc."). 
# Die will ich vor dem Alias-Abgleich wegschneiden, sonst matcht z.B. "Volkswagen AG" nicht mehr auf "volkswagen" in der Mapping-Tabelle oben.
# Liste ist nicht vollständig, sondern deckt nur ab, was mir in Testdaten untergekommen ist bzw. was in DE/EU/US am häufigsten vorkommt.
_LEGAL_SUFFIXES = [
    "gmbh & co. kg",
    "gmbh",
    "ag",
    "kg",
    "se",
    "co. kg",
    "ltd.",
    "ltd",
    "plc",
    "inc.",
    "inc",
    "corp.",
    "corporation",
    "llc",
    "s.a.",
    "sa",
    "s.p.a.",
    "spa",
    "n.v.",
    "b.v.",
    "group"
]

# Baut ein Regex, das einen der obigen Zusätze am Stringende erkennt, optional mit Komma/Leerzeichen davor. re.escape wegen der Punkte in "Ltd." etc.
_LEGAL_SUFFIX_PATTERN = re.compile(
    r"[,\s]+(" + "|".join(re.escape(s) for s in _LEGAL_SUFFIXES) + r")\s*$",
    re.IGNORECASE,
)

def _strip_legal_suffix(raw_brand: str) -> str:
    """
    Schneidet bekannte Rechtsformzusätze (GmbH, AG, Ltd, Inc, ...) ab.
    Macht das iterativ, falls mal zwei Zusätze hintereinander stehen
    (kam bei mir zwar nicht vor, wollte aber auf der sicheren Seite sein).
    """
    cleaned = raw_brand
    while True:
        new_cleaned = _LEGAL_SUFFIX_PATTERN.sub("", cleaned)
        if new_cleaned == cleaned:
            break
        cleaned = new_cleaned
    return cleaned.strip()


def normalize_brand(raw_brand: str) -> str:
    """
    Bringt den Markennamen in eine einheitliche Form.
    Entfernt zuerst Rechtsformzusätze wie "AG"/"GmbH"/"Ltd", damit z.B. "Volkswagen AG" genauso erkannt wird wie "vw" oder "Volkswagen".
    Unbekannte Marken werden nicht abgelehnt, sondern einfach mit Title Case zurückgegeben (z.B. "toyota motor corp" -> "Toyota Motor").
    """
    without_legal_suffix = _strip_legal_suffix(raw_brand.strip())
    key = without_legal_suffix.lower()
    if key in _BRAND_ALIASES:
        return _BRAND_ALIASES[key]
    return without_legal_suffix.title()


def normalize_model(raw_model: str) -> str:
    """Räumt Leerzeichen im Modellnamen auf und vereinheitlicht Groß-/Kleinschreibung."""
    cleaned = re.sub(r"\s+", " ", raw_model.strip())
    # kurze Modellcodes wie "a3" komplett groß, alles andere Title Case
    return cleaned.upper() if len(cleaned) <= 3 else cleaned.title()


def validate_vin(raw_vin: str) -> tuple[bool, str]:
    """
    Checkt nur das Format der VIN (17 Zeichen, kein I/O/Q).
    Keine echte Prüfsummenvalidierung, dafür hätte ich mehr Zeit gebraucht und es war für den Scope hier nicht nötig.
    """
    cleaned = raw_vin.strip().upper()
    is_valid = bool(_VIN_PATTERN.match(cleaned))
    return is_valid, cleaned


_VIN_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")

# Grobe Wertebereiche, nur um offensichtlichen Unsinn abzufangen (z.B. vertauschte Felder in der Eingabe). 
# Keine Ahnung, ob die Grenzen 100% korrekt sind, aber für den Zweck hier sollten sie reichen.
_DISPLACEMENT_RANGE_CCM: dict[str, tuple[int, int]] = {
    "car": (600, 8000),
    "motorcycle": (49, 2500),
}
_POWER_RANGE_KW: dict[str, tuple[int, int]] = {
    "car": (30, 1000),
    "motorcycle": (2, 200),
}


def validate_displacement(vehicle_type: str, displacement_ccm: int) -> bool:
    """True, wenn der Hubraum für den Fahrzeugtyp im plausiblen Bereich liegt."""
    low, high = _DISPLACEMENT_RANGE_CCM[vehicle_type]
    return low <= displacement_ccm <= high


def validate_power(vehicle_type: str, power_kw: int) -> bool:
    """True, wenn die Leistung für den Fahrzeugtyp im plausiblen Bereich liegt."""
    low, high = _POWER_RANGE_KW[vehicle_type]
    return low <= power_kw <= high


def normalize_vehicle_record(
    vehicle_type: str,
    brand: str,
    model: str,
    vin: str,
    displacement_ccm: int,
    power_kw: int,
) -> dict[str, Any]:
    """
    Führt alle Normalisierungs-/Validierungsschritte für einen Datensatz aus.
    Gibt am Ende ein dict zurück, das direkt ins Response-Schema passt.
    """
    vin_valid, vin_clean = validate_vin(vin)
    return {
        "vehicle_type": vehicle_type,
        "brand": normalize_brand(brand),
        "model": normalize_model(model),
        "vin": vin_clean,
        "vin_valid": vin_valid,
        "displacement_ccm": displacement_ccm,
        "displacement_plausible": validate_displacement(vehicle_type, displacement_ccm),
        "power_kw": power_kw,
        "power_plausible": validate_power(vehicle_type, power_kw),
    }