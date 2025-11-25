import paho.mqtt.client as mqtt
import logging
import time

BROKER = "mqtt-broker"
TOPIC = "sensors/light"
TOPIC_LAMP = "lamp/state"
values = [10, 20, 30, 40, 50]

lamp_on = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Light sensor")

def on_connect(client, userdata, flags, reason_code, properties=None):
    logger.info(f"Connected with result code {reason_code}")
    client.subscribe(TOPIC_LAMP)

def on_message(client, userdata, message):
    global lamp_on
    payload = message.payload.decode().strip()
    lamp_on = payload.upper() == "ON"
    logger.info(f"Lamp state: {payload}, lamp_on={lamp_on}")

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.connect(BROKER, 1883, 60)
mqttc.loop_start()

while True:
    for value in values:
        for _ in range(4):
            lightness = value + 50 if lamp_on else value
            mqttc.publish(TOPIC, lightness)
            logger.info(f"Published light level: {lightness}%")
            time.sleep(2)
