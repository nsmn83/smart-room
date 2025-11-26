import paho.mqtt.client as mqtt
import logging
import time
import os

ROOM = os.environ.get("ROOM","room1")
BROKER = "mqtt-broker"
TOPIC_LIGHT = f"{ROOM}/sensors/light"
TOPIC_LAMP_STATE = f"{ROOM}/lamp/state"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Light sensor")

lamp_on = False  # aktualny stan lampy


def on_connect(client, userdata, flags, reason_code, properties):
    logger.info(f"Connected with result code {reason_code}")
    client.subscribe(TOPIC_LAMP_STATE)


def on_message(client, userdata, msg):
    global lamp_on
    payload = msg.payload.decode()

    if msg.topic == TOPIC_LAMP_STATE:
        lamp_on = (payload == "ON")
        logger.info(f"Lamp state updated → {payload}")


mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message

mqttc.connect(BROKER, 1883, 60)
mqttc.loop_start()

# cykl jasności
sequence = [20]*4 + [40]*4 + [70]*4
index = 0

while True:
    lightness = sequence[index]

    # wpływ lampy
    if lamp_on:
        lightness += 70

    lightness = min(lightness, 100)
    mqttc.publish(TOPIC_LIGHT, lightness)
    logger.info(f"Published light level: {lightness}%")

    # przejście do kolejnego elementu
    index = (index + 1) % len(sequence)

    time.sleep(2)