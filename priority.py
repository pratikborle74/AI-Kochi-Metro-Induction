# priority_service.py (fixed for Colab/Jupyter)

import json
import requests
import paho.mqtt.client as mqtt
from datetime import datetime
from config import MQTT_BROKER, MQTT_PORT, PRIORITY_THRESHOLD, MOCK_MAXIMO_URL

TOPIC_COND = "kmrl/coach/+/condition"
TOPIC_PRIORITIES = "kmrl/priority/ranked"

# weights for scoring formula
W1, W2, W3, W4 = 0.45, 0.2, 0.15, 0.2

coach_data = {}  # coach_id -> latest record with priority


# Compute weighted priority (higher = more urgent)
def compute_priority(cond_score, severity, criticality, time_since_maint):
    sev_map = {"Low": 10, "Medium": 40, "High": 70, "Critical": 100}
    sev_val = sev_map.get(severity, 40)
    pr = (W1 * (100 - cond_score) +
          W2 * criticality +
          W3 * time_since_maint +
          W4 * sev_val)
    return round(pr, 1)


# Publish sorted list to MQTT for dashboard
def publish_priorities(client):
    ranked = sorted(coach_data.values(), key=lambda x: x["priority"], reverse=True)
    msg = {"timestamp": datetime.utcnow().isoformat(), "ranked": ranked}
    client.publish(TOPIC_PRIORITIES, json.dumps(msg))
    print("Published ranked:", [r["coach_id"] for r in ranked])


# Optionally auto-create job card in Mock Maximo
def maybe_create_job_card(entry):
    if entry["priority"] < PRIORITY_THRESHOLD:
        return

    payload = {
        "assetnum": entry["coach_id"],
        "description": f"Auto: severity={entry['fault_severity']}, cond={entry['condition_score']}",
        "priority": max(1, min(5, int(6 - (entry['priority'] // 20)))),
        "status": "OPEN"
    }

    try:
        r = requests.post(f"{MOCK_MAXIMO_URL}/workorders", json=payload, timeout=5)
        if r.ok:
            print(f"Created work order for {entry['coach_id']} →", r.json())
        else:
            print("Failed to create work order:", r.status_code, r.text)
    except Exception as e:
        print("Work order creation error:", e)


# MQTT callbacks
def on_message(client, userdata, message):
    payload = json.loads(message.payload.decode())
    coach_id = payload["coach_id"]

    pr = compute_priority(
        payload["condition_score"],
        payload["fault_severity"],
        payload["criticality"],
        payload["time_since_maint"]
    )

    entry = {
        "coach_id": coach_id,
        "condition_score": payload["condition_score"],
        "fault_severity": payload["fault_severity"],
        "criticality": payload["criticality"],
        "time_since_maint": payload["time_since_maint"],
        "priority": pr
    }

    coach_data[coach_id] = entry
    publish_priorities(client)
    maybe_create_job_card(entry)


def on_connect(client, userdata, flags, rc, properties=None):
    print("Priority service connected:", rc)
    client.subscribe(TOPIC_COND)


# MQTT setup (use modern API)
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Non-blocking loop (better for Colab/Jupyter)
client.loop_start()
print("Priority service is running… (use client.loop_stop() to stop)")
