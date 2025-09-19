# realtime_consumer.py

import json
from collections import deque
import numpy as np
from sklearn.ensemble import IsolationForest
import paho.mqtt.client as mqtt
from config import MQTT_BROKER, MQTT_PORT

TOPIC_IN = "kmrl/coach/+/telemetry"
COND_TOPIC_TEMPLATE = "kmrl/coach/{coach_id}/condition"
WINDOW_SIZE = 30  # number of samples to learn a baseline per coach

coach_windows = {}  # coach_id -> deque of feature vectors
models = {}         # coach_id -> IsolationForest model

client = mqtt.Client()

# -----------------------------
# Feature extraction from telemetry JSON
# -----------------------------
def extract_features(msg):
    s = msg["sensors"]
    # compact feature set for realtime speed
    vib_rms = (s["vibration_axle_1"]**2 + s["vibration_axle_2"]**2)**0.5
    return np.array([
        vib_rms,
        s["bearing_temp_1"],
        s["motor_temp"],
        s["door_motor_current"]
    ])

# -----------------------------
# Heuristic condition score
# -----------------------------
def compute_condition_score(is_anomaly, feature_vector):
    if is_anomaly:
        return 20
    vib, btemp, mtemp, dcurr = feature_vector
    score = 100 - ((vib * 1000) + max(0, btemp - 50) * 1.2 + max(0, mtemp - 55) * 0.8)
    return max(0, min(100, round(score, 1)))

# -----------------------------
# Severity label mapping
# -----------------------------
def map_severity(score):
    if score > 75:
        return "Low"
    elif score > 50:
        return "Medium"
    elif score > 30:
        return "High"
    else:
        return "Critical"

# -----------------------------
# MQTT Callbacks
# -----------------------------
def on_message(client, userdata, message):
    payload = json.loads(message.payload.decode())
    coach = payload["coach_id"]
    fv = extract_features(payload)

    # Init coach window if not exists
    if coach not in coach_windows:
        coach_windows[coach] = deque(maxlen=WINDOW_SIZE)

    coach_windows[coach].append(fv)
    arr = np.array(coach_windows[coach])

    # Warm-up until we have enough samples
    if arr.shape[0] < max(10, WINDOW_SIZE // 2):
        print(f"[{coach}] Warming up ({arr.shape[0]} samples)")
        return

    # Train/update Isolation Forest model
    if coach not in models:
        m = IsolationForest(contamination=0.02, random_state=42)
        m.fit(arr)
        models[coach] = m
    else:
        if arr.shape[0] == WINDOW_SIZE:
            models[coach].fit(arr)

    is_anom = (models[coach].predict(fv.reshape(1, -1))[0] == -1)
    condition_score = compute_condition_score(is_anom, fv)
    severity = map_severity(condition_score)

    # Static placeholders
    criticality = 70
    time_since_maint = 40

    out = {
        "coach_id": coach,
        "condition_score": condition_score,
        "fault_severity": severity,
        "criticality": criticality,
        "time_since_maint": time_since_maint
    }

    cond_topic = COND_TOPIC_TEMPLATE.format(coach_id=coach)
    client.publish(cond_topic, json.dumps(out))
    print(f"[{coach}] Published condition → {out}")

def on_connect(client, userdata, flags, rc):
    print("Consumer connected:", rc)
    client.subscribe(TOPIC_IN)

# -----------------------------
# MQTT Setup
# -----------------------------
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()
