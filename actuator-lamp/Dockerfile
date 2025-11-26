FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Uruchamiamy plik main.py / temperature_sensor.py - dostosuj nazwę
CMD ["python", "main.py"]
