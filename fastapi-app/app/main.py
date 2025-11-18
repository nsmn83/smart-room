from fastapi import FastAPI, Form, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
import paho.mqtt.client as mqtt
import logging

BROKER = "mqtt-broker"

TOPIC_LIGHT = "sensors/light"
TOPIC_TEMP = "sensors/temperature"
TOPIC_FAN = "fan/control"
TOPIC_LAMP = "lamp/control"
TOPIC_FAN_STATE = "fan/state"
TOPIC_LAMP_STATE = "lamp/state"

sensor_data = {
    "temperature": None,
    "light": None,
    "fan": "OFF",
    "lamp": "OFF"
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SensorDashboard")

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
    payload = msg.payload.decode()
    if topic == TOPIC_TEMP:
        sensor_data["temperature"] = payload
    elif topic == TOPIC_LIGHT:
        sensor_data["light"] = payload
    elif topic == TOPIC_FAN_STATE:
        sensor_data["fan"] = payload
    elif topic == TOPIC_LAMP_STATE:
        sensor_data["lamp"] = payload
    logger.info(f"Received {topic}: {payload}")

mqttc = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.connect(BROKER, 1883, 60)
mqttc.loop_start()


app = FastAPI()
templates = Jinja2Templates(directory="templates")

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
