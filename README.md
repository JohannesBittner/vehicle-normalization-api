# Vehicle Normalization API

Kleiner Demonstrator einer typisierten Python-API zur Validierung und  Normalisierung strukturierter Fahrzeug-Stammdaten (Marke, Modell, Hubraum, Leistung, VIN) für PKW und Motorräder.
Dient als Portfolio-Projekt für praktische FastAPI-Grunderfahrung kombiniert mit Normalisierungslogik aus dem Record-Linkage-/Entity-Resolution-Umfeld.

## Zweck

In heterogenen Datenquellen tauchen Fahrzeug-Stammdaten oft in unterschiedlichen Schreibweisen auf ("vw" vs. "VW" vs. "Volkswagen") und
mit fahrzeugtypabhängig unterschiedlichen Plausibilitätsgrenzen (z.B. ist ein 125ccm-Hubraum bei einem Motorrad normal, bei einem PKW aber auffällig).
Diese API bietet einen einzelnen, typisierten Endpoint, der solche Datensätze normalisiert, ungültige Eingaben nachvollziehbar zurückweist und
Hubraum/Leistung gegen fahrzeugtypspezifische Plausibilitätsbereiche prüft.

## Voraussetzungen

- Python 3.13 (siehe `.python-version`)
- Optional für den containerisierten Betrieb: [Docker Desktop](https://www.docker.com/products/docker-desktop/) (inkl. WSL 2 unter Windows)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Start (lokal)

```bash
uvicorn app.main:app --reload
```

Danach ist die interaktive Doku unter [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) erreichbar.

## Start (Docker)

```bash
docker build -t vehicle-normalization-api .
docker run -d --name vna-container -p 8000:8000 vehicle-normalization-api
```

Den Container-Status prüfen (nach kurzer Anlaufzeit sollte `STATUS` auf `healthy` wechseln, da ein `HEALTHCHECK` gegen `/health` im Dockerfile konfiguriert ist):

```bash
docker ps
```

Container wieder stoppen:

```bash
docker stop vna-container
```

## Beispielrequest

```bash
curl -X POST http://127.0.0.1:8000/normalize \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_type": "car",
    "brand": "vw",
    "model": "golf   viii",
    "vin": "WVWZZZ1JZXW000001",
    "displacement_ccm": 1984,
    "power_kw": 150
  }'
```

Antwort:

```json
{
  "vehicle_type": "car",
  "brand": "Volkswagen",
  "model": "Golf Viii",
  "vin": "WVWZZZ1JZXW000001",
  "vin_valid": true,
  "displacement_ccm": 1984,
  "displacement_plausible": true,
  "power_kw": 150,
  "power_plausible": true
}
```

Für ein Motorrad genügt `"vehicle_type": "motorcycle"`.
Weitere Beispiele inklusive Grenzfällen liegen in `tests/sample_data.json` und
lassen sich mit `python tests/try_sample_data.py` (bei laufender API) automatisiert durchspielen.

## Tests

Unit- und API-Tests mit pytest ausführen:

```bash
python -m pytest -v
```

> **Hinweis:** Bitte `python -m pytest` statt nur `pytest` verwenden. Der reine `pytest`-Befehl fügt das Projektverzeichnis
> unter manchen Setups nicht automatisch zum Python-Suchpfad hinzu, was zu `ModuleNotFoundError: No module named 'app'` führt.
> `python -m pytest` löst das zuverlässig, da Python dabei automatisch das aktuelle Arbeitsverzeichnis einbindet.

End-to-End-Test gegen die laufende API (in einem zweiten Terminal, bei laufendem `uvicorn`):

```bash
python tests/try_sample_data.py
```

Dieses Skript sendet alle Beispiel- und Grenzfälle aus `tests/sample_data.json` per HTTP an die API und prüft automatisch
Status-Code und erwartete Response-Felder.

## Troubleshooting

Kurze Sammlung von Fehlern, über die man beim ersten Setup stolpern kann:

| Fehler | Ursache | Lösung |
|---|---|---|
| `ModuleNotFoundError: No module named 'app'` bei `pytest` | Projektverzeichnis wird nicht automatisch zum Python-Pfad hinzugefügt | `python -m pytest -v` statt `pytest` verwenden |
| `bash: docker: command not found` direkt nach der Docker-Installation | Terminal wurde vor der Installation gestartet und kennt den neuen `PATH`-Eintrag noch nicht | Terminal schließen und neu öffnen (ggf. VS Code neu starten) |

## Architekturentscheidung

- **FastAPI + Pydantic**:
  Typisierte Ein-/Ausgabemodelle machen die Schnittstelle selbstdokumentierend durch OpenAPI und fangen ungültige Eingaben bereits auf Framework-Ebene ab.
- **Discriminated Union für `vehicle_type`**:
  PKW und Motorrad teilen sich dieselben Basisfelder, aber unterschiedliche Plausibilitätsbereiche für Hubraum/Leistung.
  Statt eines einzelnen Schemas mit optionalen Feldern nutzt die API Pydantics `discriminator="vehicle_type"`. So wird ein unbekannter Typ sauber mit einer
  aussagekräftigen 422-Fehlermeldung (Unprocessable Content) abgelehnt, statt still durchzurutschen.
- **Plausibilität als Datenfeld, nicht als Request-Fehler**:
  `displacement_plausible`/`power_plausible` sind eigene Response-Felder statt HTTP-422-Ablehnungen, da ein unplausibler Wert (z.B. 125ccm bei einem PKW)
  ein fachlicher Hinweis ist, kein technisch ungültiger Request. Die Entscheidung, was damit passiert, bleibt beim Aufrufer.
- **Trennung von Layern**:
  - `main.py` (Routing/HTTP)
  - `service.py` (Bindeglied)
  - `schemas.py` (Pydantic-Modelle für Ein-/Ausgaben inkl. discriminated Union)
  - `normalization.py` (reine Fachlogik ohne Framework-Abhängigkeit)

  Dadurch lässt sich die Fachlogik isoliert und ohne HTTP-Overhead testen.
- **Bewusst kein Persistenzlayer**:
  Der Fokus liegt auf sauberer API-Struktur und Normalisierungslogik, nicht auf einer vollständigen Anwendung.
- **Pytest-idiomatische Tests statt `unittest`-Klassen**:
  Die Tests bestehen aus einfachen `test_*`-Funktionen mit reinem `assert` statt `TestCase`-Klassen mit `self.assertEqual(...)`.
- **Type Hints + Google-Style-Docstrings durchgängig**:
  Alle Funktionen sind vollständig typisiert und mit Docstrings im Google-Format (Args/Returns/Raises) versehen,
  für Wartbarkeit und bessere IDE-Unterstützung (Autovervollständigung, Type-Checking).
- **Dockerfile mit Layer-Caching und Healthcheck**:
  `requirements.txt` wird vor dem App-Code kopiert, damit `pip install` nicht bei jeder Code-Änderung neu ausgeführt werden muss.
  Ein `HEALTHCHECK` fragt periodisch `/health` ab, damit Docker (bzw. Orchestrierungswerkzeuge) erkennen, ob der Container
  wirklich funktionsfähig ist und nicht nur der Prozess läuft.