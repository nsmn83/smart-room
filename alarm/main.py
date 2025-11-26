import os
import time
import threading
import logging
import paho.mqtt.client as mqtt

ROOM = os.getenv("ROOM", "room1")
BROKER = "mqtt-broker"

# Tematy
TOPIC_CMD = f"{ROOM}/alarm/control"  # Komendy: ARM, DISARM, TRIGGERED
TOPIC_STATUS = f"{ROOM}/alarm/status" # Status systemu: DISARMED, ARMED, COUNTDOWN, ALARM

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Alarm")

# Zmienne globalne stanu
current_state = "ARMED"
countdown_thread = None
stop_event = threading.Event()


def start_countdown_sequence(client):
    global current_state
    logger.info("--- ROZPOCZYNAM ODLICZANIE (5s) ---")
    client.publish(TOPIC_STATUS, "TRIGGERED")
    if not stop_event.wait(timeout=5.0):
        logger.info("!!! ALARM URUCHOMIONY !!!")
        current_state = "ALARM"
        client.publish(TOPIC_STATUS, "ALARM")
    else:
        logger.info("--- Odliczanie przerwane (Disarmed) ---")


def on_connect(client, userdata, flags, rc, properties=None):
    logger.info(f"Alarm Controller connected to {TOPIC_CMD}")
    client.subscribe(TOPIC_CMD)
    client.publish(TOPIC_STATUS, current_state)


def on_message(client, userdata, msg):
    global current_state, countdown_thread, stop_event
    payload = msg.payload.decode()
    logger.info(f"Otrzymano wiadomosc {payload}.")

    if payload == "ARM":
        current_state = "ARMED"
        stop_event.set()
        client.publish(TOPIC_STATUS, "ARMED")
        logger.info("Alarm uzbrojony przez uzytkownika.")

    elif payload == "DISARM":
        current_state = "DISARMED"
        stop_event.set()
        client.publish(TOPIC_STATUS, "DISARMED")
        logger.info("Alarm rozbrojony przez uzytkownika.")

    elif payload == "TRIGGER":
        if current_state == "ARMED":
            stop_event.clear()
            client.publish(TOPIC_STATUS, "TRIGGERED")
            countdown_thread = threading.Thread(target=start_countdown_sequence, args=(client,))
            countdown_thread.start()
            logger.info("Alarm aktywowany - uruchamiam odliczanie.")
        elif current_state == "DISARMED":
            logger.info("Alarm rozbroiony, nie uruchamiam odliczania.")


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, 1883, 60)
client.loop_start()


while True:
    time.sleep(1)
    logger.info("Alarm system running...")