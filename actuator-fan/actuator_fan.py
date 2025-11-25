import time
import paho.mqtt.client as mqtt
import logging

BROKER = "mqtt-broker"
TOPIC_CONTROL = "fan/control"
TOPIC_STATE = "fan/state"
TOPIC_TARGET_TEMP = "config/target_temp"
TOPIC_TEMP_SENSOR = "sensors/temperature"

state = "OFF"
target_temp = 25.0
current_temp = None

logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger("Fan")

def on_connect(client, userdata, flags, reason_code, properties=None):
    logger.info(f"Connected with result code: {reason_code}")
    client.subscribe(TOPIC_CONTROL)
    client.subscribe(TOPIC_TARGET_TEMP)
    client.subscribe(TOPIC_TEMP_SENSOR)

def on_message(client, userdata, message):
    global state, target_temp, current_temp
    topic = message.topic
    payload = message.payload.decode().strip()
    logger.info(f"Received message: '{payload}' on topic '{topic}'")

    if topic == TOPIC_CONTROL:
        if payload in ["ON", "OFF"]:
            state = payload
            logger.info(f"Fan turned {state.lower()}")
            mqttc.publish(TOPIC_STATE, state)

    elif topic == TOPIC_TARGET_TEMP:
        try:
            target_temp = float(payload)
            logger.info(f"Target temperature updated: {target_temp}")
        except ValueError:
            logger.warning(f"Invalid target temperature: {payload}")

    elif topic == TOPIC_TEMP_SENSOR:
        try:
            current_temp = float(payload)
            logger.info(f"Current temperature: {current_temp}")
            if current_temp > target_temp and state != "ON":
                state = "ON"
                logger.info("Temperature exceeded target, turning fan ON")
                mqttc.publish(TOPIC_STATE, state)
            elif current_temp <= target_temp and state != "OFF":
                state = "OFF"
                logger.info("Temperature below target, turning fan OFF")
                mqttc.publish(TOPIC_STATE, state)
        except ValueError:
            logger.warning(f"Invalid sensor temperature: {payload}")

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.connect(BROKER, 1883, 60)
mqttc.loop_start()

while True:
    time.sleep(1)
