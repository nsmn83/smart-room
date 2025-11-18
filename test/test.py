import time

import paho.mqtt.client as mqtt
import logging

BROKER = "mqtt-broker"
TOPIC_CONTROL = "lamp/control"
TOPIC_STATE = "lamp/state"

state = "OFF"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Lamp")

def on_connect(client, userdata, flags, reason_code, properties):
    logger.info(f"Connected with result code {reason_code}")

def on_message(client, userdata, msg):
    global state
    command = msg.payload.decode()
    if command in ["ON", "OFF"]:
        state = command
        logger.info(f"Lamp turned {state.lower()}")
        mqttc.publish(TOPIC_STATE, state)



mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.connect(BROKER, 1883, 60)
mqttc.subscribe(TOPIC_CONTROL)
mqttc.loop_start()




while True:
    time.sleep(1)