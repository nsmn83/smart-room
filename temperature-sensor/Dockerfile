FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY temperature_sensor.py .

CMD ["python", "temperature_sensor.py"]