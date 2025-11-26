import os
import time
import threading
import paho.mqtt.client as mqtt

ROOM = os.getenv("ROOM", "room1")
BROKER = "mqtt-broker"

# Tematy
TOPIC_CMD = f"{ROOM}/alarm/control"  # Komendy: ARM, DISARM, TRIGGERED
TOPIC_STATUS = f"{ROOM}/alarm/status" # Status systemu: DISARMED, ARMED, COUNTDOWN, ALARM

# Zmienne globalne stanu
current_state = "ARMED"
countdown_thread = None
stop_event = threading.Event()


def start_countdown_sequence(client):
    global current_state
    print("--- ROZPOCZYNAM ODLICZANIE (5s) ---")
    client.publish(TOPIC_STATUS, "COUNTDOWN")
    if not stop_event.wait(timeout=5.0):
        print("!!! ALARM URUCHOMIONY !!!")
        current_state = "ALARM"
        client.publish(TOPIC_STATUS, "ALARM")
    else:
        print("--- Odliczanie przerwane (Disarmed) ---")


def on_connect(client, userdata, flags, rc, properties=None):
    print(f"Alarm Controller connected to {TOPIC_CMD}")
    client.subscribe(TOPIC_CMD)
    client.publish(TOPIC_STATUS, current_state)


def on_message(client, userdata, msg):
    global current_state, countdown_thread, stop_event
    payload = msg.payload.decode()
    print(f"Otrzymano komendę: {payload}")

    if payload == "ARM":
        current_state = "ARMED"
        stop_event.set()
        client.publish(TOPIC_STATUS, "ARMED")
        print("System uzbrojony.")

    elif payload == "DISARM":
        current_state = "DISARMED"
        stop_event.set()
        client.publish(TOPIC_STATUS, "DISARMED")
        print("System rozbrojony.")

    elif payload == "TRIGGER":
        if current_state == "ARMED":
            stop_event.clear()
            client.publish(TOPIC_STATUS, "TRIGGERED")
            countdown_thread = threading.Thread(target=start_countdown_sequence, args=(client,))
            countdown_thread.start()
        elif current_state == "DISARMED":
            print("Ignoruję trigger - system rozbrojony.")


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

print(f"Łączenie z brokerem {BROKER}...")
try:
    client.connect(BROKER, 1883, 60)
    client.loop_forever()
except Exception as e:
    print(f"Błąd połączenia: {e}")