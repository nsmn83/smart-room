FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY actuator_fan.py .

CMD ["python", "actuator_fan.py"]