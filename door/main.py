import time
import paho.mqtt.client as mqtt
import logging
import os

ROOM = os.environ.get("ROOM","room1")
BROKER = "mqtt-broker"
TOPIC_CONTROL = f"{ROOM}/door/control"  # FIXED: Changed from movement to door
TOPIC_STATE = f"{ROOM}/door/state"      # FIXED: Changed from movement to door

state = "CLOSED"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Door")

def on_connect(client, userdata, flags, reason_code, properties):
    mqttc.subscribe(TOPIC_CONTROL, 0)
    logger.info(f"Connected with result code {reason_code}")
    # Publish initial state
    mqttc.publish(TOPIC_STATE, state)

def on_message(client, userdata, msg):
    global state
    command = msg.payload.decode()
    if command in ["OPEN", "CLOSED"]:
        state = command
        logger.info(f"Door is {state.lower()}")
        mqttc.publish(TOPIC_STATE, state)

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.connect(BROKER, 1883, 60)
mqttc.loop_start()

while True:
    time.sleep(1)