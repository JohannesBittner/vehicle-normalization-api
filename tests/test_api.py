from fastapi.testclient import TestClient

from app.main import app

# TestClient startet die App im Speicher, man braucht also keinen echten uvicorn-Server für diese Tests.
client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_normalize_endpoint_car_success():
    response = client.post(
        "/normalize",
        json={
            "vehicle_type": "car",
            "brand": "vw",
            "model": "golf viii",
            "vin": "WVWZZZ1JZXW000001",
            "displacement_ccm": 1984,
            "power_kw": 150,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["brand"] == "Volkswagen"
    assert body["vehicle_type"] == "car"
    assert body["vin_valid"] is True
    assert body["displacement_plausible"] is True


def test_normalize_endpoint_motorcycle_success():
    response = client.post(
        "/normalize",
        json={
            "vehicle_type": "motorcycle",
            "brand": "harley",
            "model": "street bob",
            "vin": "1HD1KB4197Y000001",
            "displacement_ccm": 1746,
            "power_kw": 63,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["brand"] == "Harley-Davidson"
    assert body["vehicle_type"] == "motorcycle"
    assert body["displacement_plausible"] is True


def test_normalize_endpoint_flags_implausible_displacement_for_type():
    # 125ccm ist für ein Motorrad normal, aber für einen PKW ziemlich unrealistisch.
    # Trotzdem kein 422, weil die Zahl an sich ist ja gültig, nur unplausibel für "car".
    response = client.post(
        "/normalize",
        json={
            "vehicle_type": "car",
            "brand": "vw",
            "model": "golf",
            "vin": "WVWZZZ1JZXW000001",
            "displacement_ccm": 125,
            "power_kw": 150,
        },
    )
    assert response.status_code == 200
    assert response.json()["displacement_plausible"] is False


def test_normalize_endpoint_rejects_empty_brand():
    response = client.post(
        "/normalize",
        json={
            "vehicle_type": "car",
            "brand": " ",
            "model": "golf",
            "vin": "WVWZZZ1JZXW000001",
            "displacement_ccm": 1984,
            "power_kw": 150,
        },
    )
    assert response.status_code == 422


def test_normalize_endpoint_rejects_unknown_vehicle_type():
    # "truck" gibt es in der discriminated union nicht -> muss mit 422 abgelehnt werden
    response = client.post(
        "/normalize",
        json={
            "vehicle_type": "truck",
            "brand": "man",
            "model": "tgx",
            "vin": "WVWZZZ1JZXW000001",
            "displacement_ccm": 10000,
            "power_kw": 300,
        },
    )
    assert response.status_code == 422