# Schlankes, offizielles Python-Image als Basis
FROM python:3.13-slim

# Arbeitsverzeichnis im Container
WORKDIR /code

# Erst nur requirements kopieren -> Docker-Layer-Caching:
# Wenn sich nur der App-Code ändert, muss "pip install" nicht neu laufen.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Jetzt den eigentlichen App-Code kopieren
COPY app ./app

# Dokumentation: Der Container lauscht auf Port 8000
EXPOSE 8000

# Healthcheck: Docker prüft alle 30s, ob /health erreichbar ist.
# Damit weiß Docker sowie auch z.B. docker-compose, ob der Container wirklich funktioniert, nicht nur ob der Prozess läuft.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Uvicorn als ASGI-Server starten, auf allen Interfaces (wichtig im Container)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]