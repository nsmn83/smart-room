import time

import paho.mqtt.client as mqtt
import logging

BROKER = "mqtt-broker"
TOPIC_CONTROL = "fan/control"
TOPIC_STATE = "fan/state"

state = "OFF"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Fan")

def on_connect(client, userdata, flags, reason_code, properties):
    logger.info(f"Connected with result code {reason_code}")

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.connect(BROKER, 1883, 60)
mqttc.loop_start()
mqttc.loop_start()

def on_message(client, userdata, msg):
    global state
    command = msg.payload.decode()
    if command in ["ON", "OFF"]:
        state = command
        logger.info(f"Fan turned {state.lower()}")
        mqttc.publish(TOPIC_STATE, state)

while True:
    time.sleep(1)