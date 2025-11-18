import time

import paho.mqtt.client as mqtt
import logging

BROKER = "mqtt-broker"
TOPIC_CONTROL = "fan/control"
TOPIC_STATE = "fan/state"

state = "OFF"

logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger("Fan")

def on_connect(client, userdata, flags, reason_code, properties=None):
    logger.info(f"Connected with result code: {reason_code}")
    mqttc.subscribe(TOPIC_CONTROL)
    
def on_message(client, userdata, message):
    global state
    command = message.payload.decode().strip()
    logger.info(f"Received message: '{command}' on topic '{message.topic}'")
    if command in ["ON", "OFF"]:
        state = command
        logger.info(f"Fan turned {state.lower()}")
        mqttc.publish(TOPIC_STATE, state)


mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.connect(BROKER, 1883, 60)
mqttc.loop_start()

while True:
    time.sleep(1)