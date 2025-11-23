import paho.mqtt.client as mqtt
import logging
import time
import os

ROOM = os.environ.get("ROOM","room1")

BROKER = "mqtt-broker"

TOPIC_TEMP = f"{ROOM}/sensors/temperature"
TOPIC_FAN_STATE = f"{ROOM}/fan/state"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Temperature sensor")

# =============================
# ZMIENNE GLOBALNE
# =============================
fan_on = False
idle_sequence = [20, 20, 20, 20, 30, 30, 30, 30, 40, 40, 40, 40]
idle_index = 0

# maksymalny spadek temperatury, jaki może wywołać wentylator
max_cooling = 20

# aktualna temperatura publikowana
current_temperature = idle_sequence[0]

# aktualny efekt chłodzenia wentylatora (0..max_cooling)
current_cooling = 0

# ile stopni na sekundę schładza wentylator
fan_cooling_rate = 1

# =============================
# CALLBACKI MQTT
# =============================
def on_connect(client, userdata, flags, reason_code, properties):
    logger.info(f"Connected with result code {reason_code}")
    client.subscribe(TOPIC_FAN_STATE)

def on_message(client, userdata, msg):
    global fan_on
    payload = msg.payload.decode()
    if msg.topic == TOPIC_FAN_STATE:
        fan_on = (payload == "ON")
        logger.info(f"Fan state updated → {payload}")

# =============================
# KONFIGURACJA MQTT
# =============================
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message

mqttc.connect(BROKER, 1883, 60)
mqttc.loop_start()

# =============================
# GŁÓWNA PĘTLA
# =============================
while True:
    natural_temp = idle_sequence[idle_index]

    if not fan_on:
        # Wentylator wyłączony → idziemy sekwencją
        current_cooling = 0
        current_temperature = natural_temp
        idle_index = (idle_index + 1) % len(idle_sequence)
        logger.info(f"Fan OFF → Publishing idle temperature: {current_temperature}°C")
    else:
        # Wentylator włączony → stopniowo schładzamy
        if current_cooling < max_cooling:
            current_cooling += fan_cooling_rate
        current_temperature = max(natural_temp - current_cooling, 0)
        logger.info(f"Fan ON → Room cooled by {current_cooling}°C, current temperature: {current_temperature}°C")

    mqttc.publish(TOPIC_TEMP, current_temperature)
    time.sleep(1)
