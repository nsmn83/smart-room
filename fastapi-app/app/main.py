from fastapi import FastAPI, Form, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
import paho.mqtt.client as mqtt
import logging
from pathlib import Path

# MQTT Broker
BROKER = "mqtt-broker"

# MQTT topics
TOPIC_LIGHT = "sensors/light"
TOPIC_TEMP = "sensors/temperature"
TOPIC_FAN = "fan/control"
TOPIC_LAMP = "lamp/control"
TOPIC_FAN_STATE = "fan/state"
TOPIC_LAMP_STATE = "lamp/state"
TOPIC_TARGET_TEMP = "config/target_temp"

BASE_DIR = Path(__file__).resolve().parent
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("SensorDashboard")

sensor_data = {
    "temperature": None,
    "light": None,
    "fan": "OFF",
    "lamp": "OFF",
    "target_temp": 25.0
}


app = FastAPI()
templates = Jinja2Templates(directory=BASE_DIR / "templates")

def on_connect(client, userdata, flags, reason_code, properties=None):
    logger.info(f"Connected to MQTT broker with code {reason_code}")
    client.subscribe([
        (TOPIC_LIGHT, 0),
        (TOPIC_TEMP, 0),
        (TOPIC_FAN_STATE, 0),
        (TOPIC_LAMP_STATE, 0)
    ])

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode().strip()
    if topic == TOPIC_TEMP:
        try:
            sensor_data["temperature"] = float(payload)
        except ValueError:
            sensor_data["temperature"] = payload
    elif topic == TOPIC_LIGHT:
        try:
            sensor_data["light"] = float(payload)
        except ValueError:
            sensor_data["light"] = payload
    elif topic == TOPIC_FAN_STATE:
        sensor_data["fan"] = payload
    elif topic == TOPIC_LAMP_STATE:
        sensor_data["lamp"] = payload
    elif topic == TOPIC_FAN_STATE:
        sensor_data["fan"] = payload
    logger.info(f"Received {topic}: {payload}")

def on_publish(client, userdata, mid, reason_code, properties=None):
    logger.info(f"Message {mid} published successfully")

mqttc = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.on_publish = on_publish
mqttc.connect(BROKER, 1883, 60)
mqttc.loop_start()


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/data")
async def get_data():
    return JSONResponse(sensor_data)

@app.post("/control")
async def control(device: str = Form(...)):
    if device == "fan_on":
        mqttc.publish(TOPIC_FAN, "ON")
    elif device == "fan_off":
        mqttc.publish(TOPIC_FAN, "OFF")
    elif device == "lamp_on":
        mqttc.publish(TOPIC_LAMP, "ON")
    elif device == "lamp_off":
        mqttc.publish(TOPIC_LAMP, "OFF")
    logger.info(f"Sent command: {device}")
    return {"status": "ok"}

@app.post("/set_target")
async def set_target_temp(target: str = Form(...)):
    try:
        val = float(target)
        sensor_data["target_temp"] = val
        mqttc.publish(TOPIC_TARGET_TEMP, str(val))
        logger.info(f"Set target temperature to: {val}")
        return {"status": "ok", "target": val}
    except ValueError:
        return {"status": "error", "message": "Invalid number"}
