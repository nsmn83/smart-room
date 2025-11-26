import os
import json
import logging
from fastapi import FastAPI, Form, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
import paho.mqtt.client as mqtt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

# lista pokoi - każy ma czujnik ruchu, lampe, wentylator oraz sensory - temperatury i jasności
ROOMS = ["room1", "room2", "room3"]
BROKER = "mqtt-broker"


#Funkcja pomocnicza do ustawienia nazyw tematów MQTT
def t(room, *parts):
    return "/".join([room] + list(parts))


#Początkowe wartości sensorów i urządzeń w pomieszczeniu
sensor_data = {}
for r in ROOMS:
    sensor_data[r] = {
        "temperature": None,
        "light": None,
        "fan": "OFF",
        "lamp": "OFF",
        "door": "CLOSED",
        "alarm": "SAFE"
    }


# Ustawienie docelowaj temperatury dla pokoi
def load_config():
    if not os.path.exists(CONFIG_PATH):
        # default config with realistic temperatures
        cfg = {r: {"target_temperature": 22} for r in ROOMS}
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=4)
        return cfg
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=4)


config = load_config()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Web app")


# MQTT client and subscription to all rooms' topics
def on_connect(client, userdata, flags, rc, properties=None):
    logger.info(f"Connected to MQTT broker with code {rc}")
    subs = []
    for room in ROOMS:
        subs += [
            (t(room, "sensors", "temperature"), 0),
            (t(room, "sensors", "light"), 0),
            (t(room, "fan", "state"), 0),
            (t(room, "lamp", "state"), 0),
            (t(room, "door", "state"), 0),
        ]
    subs += [("room1/alarm/status", 0)]
    client.subscribe(subs)
    logger.info(f"Subscribed to {len(subs)} topics")


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    # parse room from topic
    parts = topic.split("/")
    if len(parts) < 3:
        return
    room = parts[0]
    if topic == "room1/alarm/status":
        if payload == "ALARM":
            sensor_data["room1"]["alarm"] = "ALARM"
            logger.info("ALARM TRIGGERED!")

        elif payload == "TRIGGERED":
            sensor_data["room1"]["alarm"] = "TRIGGERED"
            logger.info("Alarm countdown started")

        elif payload == "ARMED":
            sensor_data["room1"]["alarm"] = "ARMED"
            logger.info("Alarm armed")

        elif payload == "DISARMED":
            sensor_data["room1"]["alarm"] = "DISARMED"
            logger.info("Alarm disarmed")


        return
    if room not in sensor_data:
        return

    suffix = "/".join(parts[1:])
    if suffix == "sensors/temperature":
        sensor_data[room]["temperature"] = payload
    elif suffix == "sensors/light":
        sensor_data[room]["light"] = payload
    elif suffix == "fan/state":
        sensor_data[room]["fan"] = payload
    elif suffix == "lamp/state":
        sensor_data[room]["lamp"] = payload
    elif suffix == "door/state":
        sensor_data[room]["door"] = payload
        logger.info(f"Received {topic}: {payload}")
        #Jeśli pokój pierwszy to włączamy alarm
        if room == "room1" and payload == "OPEN":
            mqttc.publish("room1/alarm/control", "TRIGGER")

        #Jeśli zamykamy drzwi to uzbrajamy alarm
        if room == "room1" and payload == "CLOSED":
            logger.info(f"Alarm uzbrajany bo drzwi zamknięte")
            mqttc.publish("room1/alarm/control", "ARM")

   # logger.info(f"Received {topic}: {payload}")
    apply_room_logic(room)


def apply_room_logic(room):
    data = sensor_data[room]
    temp = float(data["temperature"]) if data["temperature"] else None
    light = float(data["light"]) if data["light"] else None
    door = data["door"]
    target = config.get(room, {}).get("target_temperature", 22)

    # fan auto
    if temp is not None:
        if temp > target and data["fan"] != "ON":
            mqttc.publish(t(room, "fan", "control"), "ON")
      #      logger.info(f"AUTO[{room}]: Temp {temp} > {target} -> FAN ON")
        elif temp <= target and data["fan"] != "OFF":
            mqttc.publish(t(room, "fan", "control"), "OFF")
      #      logger.info(f"AUTO[{room}]: Temp {temp} <= {target} -> FAN OFF")

    # light auto (when someone inside)
    if door == "OPEN" and light is not None:
        if light < 70 and data["lamp"] != "ON":
            mqttc.publish(t(room, "lamp", "control"), "ON")
    #        logger.info(f"AUTO[{room}]: Light {light} < 70 & door OPEN -> LAMP ON")
        elif light >= 70 and data["lamp"] != "OFF":
            mqttc.publish(t(room, "lamp", "control"), "OFF")
    #        logger.info(f"AUTO[{room}]: Light {light} >= 70 & door OPEN -> LAMP OFF")

    # if room empty -> lamp off
    if door == "CLOSED" and data["lamp"] != "OFF":
        mqttc.publish(t(room, "lamp", "control"), "OFF")
    #    logger.info(f"AUTO[{room}]: Door CLOSED -> LAMP OFF")


# MQTT client
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.connect(BROKER, 1883, 60)
mqttc.loop_start()

# FastAPI app
app = FastAPI()
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "template"))


@app.get("/")
async def home(request: Request):
    #Przesłanie danych z sensorów do szablonu
    return templates.TemplateResponse("index.html", {
        "request": request,
        "sensor_data": sensor_data,
        "config": config,
        "rooms": ROOMS
    })


@app.get("/data")
async def get_data():
    return JSONResponse(sensor_data)

#Sterowanie alarmem
@app.post("/disarm")
async def disarm():

    mqttc.publish("room1/alarm/control", "DISARM")
    logger.info("ROZBROJENIE ALARMU - wysłano informacje do alarmu")
    return {"status": "disarmed"}

# Sterowanie obecnością osoby w danym pomieszczeniu
@app.post("/control")
async def control(room: str = Form(...), device: str = Form(...)):
    if room not in ROOMS:
        return {"error": "unknown room"}

    # Door control
    if device == "door_open":
        mqttc.publish(t(room, "door", "control"), "OPEN")
        return {"status": "ok", "action": "door_open"}

    elif device == "door_close":
        mqttc.publish(t(room, "door", "control"), "CLOSED")
        return {"status": "ok", "action": "door_close"}


#Ustawienie temperatury w danym pomieszczeniu
@app.post("/set-config")
async def set_config(room: str = Form(...), target_temperature: int = Form(...)):
    if room not in ROOMS:
        return {"error": "unknown room"}
    config[room]["target_temperature"] = int(target_temperature)
    save_config(config)
    return {"status": "saved", "room": room, "target_temperature": target_temperature}