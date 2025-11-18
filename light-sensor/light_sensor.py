import paho.mqtt.client as mqtt
import logging
import time
import random

BROKER = "mqtt-broker"
TOPIC = "sensors/light"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Light sensor")

def on_connect(client, userdata, flags, reason_code, properties):
    logger.info(f"Connected with result code {reason_code}")

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.connect(BROKER, 1883, 60)

while True:
    lightness = round(random.uniform(0.0, 100.0),2)
    mqttc.publish(TOPIC, lightness)
    logger.info(f"Published light level: {lightness}%")
    time.sleep(2)