 # workorder_sync.py
import time
import requests
import json
import paho.mqtt.client as mqtt
from config import MQTT_BROKER, MQTT_PORT, MOCK_MAXIMO_URL

OUT_TOPIC = "kmrl/workorders/snapshot"

# Initialize MQTT client
mq = mqtt.Client()
mq.connect(MQTT_BROKER, MQTT_PORT, 60)

# Continuous polling loop
while True:
    try:
        # Fetch open and closed work orders
        open_wos = requests.get(
            f"{MOCK_MAXIMO_URL}/workorders",
            params={"status": "OPEN"},
            timeout=5
        ).json()

        closed_wos = requests.get(
            f"{MOCK_MAXIMO_URL}/workorders",
            params={"status": "CLOSED"},
            timeout=5
        ).json()

        # Compose snapshot payload
        payload = {"open": open_wos, "closed": closed_wos}

        # Publish to MQTT
        mq.publish(OUT_TOPIC, json.dumps(payload))
        print(f"Published workorder snapshot: open={len(open_wos)}, closed={len(closed_wos)}")

    except Exception as e:
        print("Sync error:", e)

    # Wait before next poll
    time.sleep(5)  # poll every 5 seconds
