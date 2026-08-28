from app.normalization import (
    normalize_brand,
    normalize_model,
    normalize_vehicle_record,
    validate_displacement,
    validate_power,
    validate_vin,
)


def test_normalize_brand_alias_lowercase():
    """vw -> Volkswagen, ganz normaler Alias-Fall."""
    assert normalize_brand("vw") == "Volkswagen"


def test_normalize_brand_alias_mixed_case_with_whitespace():
    """Sollte auch mit Leerzeichen und ungewöhnlicher Schreibweise funktionieren."""
    assert normalize_brand(" Mercedes Benz ") == "Mercedes-Benz"


def test_normalize_brand_unknown_brand_falls_back_to_title_case():
    """Unbekannte Marken werden nicht abgelehnt, nur ordentlich formatiert."""
    assert normalize_brand("toyota") == "Toyota"


def test_normalize_brand_motorcycle_alias():
    assert normalize_brand("harley davidson") == "Harley-Davidson"


def test_normalize_brand_abbreviation_and_full_name_resolve_identically():
    # Abkürzung und ausgeschriebene Langform müssen auf dasselbe Ergebnis kommen
    assert normalize_brand("bmw") == "BMW"
    assert normalize_brand("Bayerische Motoren Werke") == "BMW"


def test_normalize_brand_strips_legal_suffix():
    """Rechtsformzusätze wie AG/GmbH sollen vor dem Alias-Abgleich wegfallen."""
    assert normalize_brand("Volkswagen AG") == "Volkswagen"
    assert normalize_brand("Harley-Davidson, Inc.") == "Harley-Davidson"


def test_normalize_model_collapses_internal_whitespace():
    assert normalize_model("golf   viii") == "Golf Viii"


def test_normalize_model_short_code_uppercased():
    # kurze Codes wie "a3" wird komplett groß, alles andere normal Title Case
    assert normalize_model("a3") == "A3"


def test_validate_vin_accepts_valid_format():
    is_valid, cleaned = validate_vin("wvwzzz1jzxw000001")
    assert is_valid is True
    assert cleaned == "WVWZZZ1JZXW000001"


def test_validate_vin_rejects_wrong_length():
    is_valid, _ = validate_vin("TOO-SHORT-VIN")
    assert is_valid is False


def test_validate_vin_rejects_forbidden_characters():
    # VINs dürfen kein I, O oder Q enthalten (Verwechslungsgefahr mit 1/0)
    is_valid, _ = validate_vin("WVWZZZ1JZXWI00001")
    assert is_valid is False


def test_validate_displacement_car_within_range():
    assert validate_displacement("car", 1984) is True


def test_validate_displacement_motorcycle_within_range():
    assert validate_displacement("motorcycle", 650) is True


def test_validate_displacement_motorcycle_value_implausible_for_car():
    # 125ccm ist für ein Motorrad normal, für einen PKW aber nicht
    assert validate_displacement("motorcycle", 125) is True
    assert validate_displacement("car", 125) is False


def test_validate_power_motorcycle_within_range():
    assert validate_power("motorcycle", 63) is True


def test_validate_power_car_implausibly_high():
    assert validate_power("car", 5000) is False


def test_normalize_vehicle_record_car_end_to_end():
    """Einmal alles zusammen durchspielen, nicht nur die einzelnen Bausteine."""
    result = normalize_vehicle_record(
        vehicle_type="car",
        brand="vw",
        model="golf viii",
        vin="WVWZZZ1JZXW000001",
        displacement_ccm=1984,
        power_kw=150,
    )
    assert result == {
        "vehicle_type": "car",
        "brand": "Volkswagen",
        "model": "Golf Viii",
        "vin": "WVWZZZ1JZXW000001",
        "vin_valid": True,
        "displacement_ccm": 1984,
        "displacement_plausible": True,
        "power_kw": 150,
        "power_plausible": True,
    }


def test_normalize_vehicle_record_motorcycle_end_to_end():
    result = normalize_vehicle_record(
        vehicle_type="motorcycle",
        brand="harley",
        model="street bob",
        vin="1HD1KB4197Y000001",
        displacement_ccm=1746,
        power_kw=63,
    )
    assert result == {
        "vehicle_type": "motorcycle",
        "brand": "Harley-Davidson",
        "model": "Street Bob",
        "vin": "1HD1KB4197Y000001",
        "vin_valid": True,
        "displacement_ccm": 1746,
        "displacement_plausible": True,
        "power_kw": 63,
        "power_plausible": True,
    }