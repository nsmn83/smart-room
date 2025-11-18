import paho.mqtt.client as mqtt
import logging
import time
import random

BROKER = "mqtt-broker"
TOPIC = "sensors/temperature"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Temperature sensor")

def on_connect(client, userdata, flags, reason_code, properties):
    logger.info(f"Connected with result code {reason_code}")

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.connect(BROKER, 1883, 60)

while True:
    temperature = round(random.uniform(0.0, 30.0),2)
    mqttc.publish(TOPIC, temperature)
    logger.info(f"Published temperature: {temperature}°C")
    time.sleep(2)