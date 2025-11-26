import os
import time
import paho.mqtt.client as mqtt

ROOM = os.getenv("ROOM", "room1")
BROKER = "mqtt-broker"

ALARM_START_TOPIC = f"{ROOM}/alarm/start"
ALARM_DISARM_TOPIC = f"{ROOM}/alarm/disarm"
ALARM_TRIGGER_TOPIC = f"{ROOM}/alarm/trigger"

countdown_active = False
disarmed = False

def on_connect(client, userdata, flags, rc, properties=None):
    print("Alarm sensor connected!")
    client.subscribe(ALARM_START_TOPIC)
    client.subscribe(ALARM_DISARM_TOPIC)

def on_message(client, userdata, msg):
    global countdown_active, disarmed

    topic = msg.topic
    payload = msg.payload.decode()

    if topic == ALARM_START_TOPIC:
        print("Alarm start received — starting countdown 5s")
        countdown_active = True
        disarmed = False

        # countdown
        for i in range(5, 0, -1):
            if disarmed:
                print("Alarm disarmed during countdown — OK")
                return
            print(f"Alarm countdown: {i}s")
            time.sleep(1)

        if not disarmed:
            print("ALARM TRIGGERED!")
            client.publish(ALARM_TRIGGER_TOPIC, "ALARM")

    elif topic == ALARM_DISARM_TOPIC:
        print("Alarm DISARM received")
        disarmed = True
        countdown_active = False


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, 1883, 60)
client.loop_forever()
