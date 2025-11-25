import paho.mqtt.client as mqtt
import logging
import time
import random

BROKER = "mqtt-broker"
TOPIC = "sensors/temperature"
values = [10.0, 20.0, 30.0, 40.0, 50.0]
index = 0
index_two = 0

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Temperature sensor")

def on_connect(client, userdata, flags, reason_code, properties):
    logger.info(f"Connected with result code {reason_code}")

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.connect(BROKER, 1883, 60)

while True:
    for value in values:
        for _ in range(4):
            mqttc.publish(TOPIC, value)
            logger.info(f"Published temperature: {value}°C")
            time.sleep(2)