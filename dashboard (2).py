# dashboard.py
import streamlit as st
import paho.mqtt.client as mqtt
import pandas as pd
import json
import threading
import time
import plotly.express as px
import requests
from config import MQTT_BROKER, MQTT_PORT, MOCK_MAXIMO_URL

TOPIC_PRI = "kmrl/priority/ranked"
TOPIC_WO_EVENTS = "kmrl/workorders/events"  # event-driven
TOPIC_WO_SNAPSHOT = "kmrl/workorders/snapshot"  # ETL-style

# Global state
latest_ranked = []
latest_events = []
latest_snapshot = {"open": [], "closed": []}


# MQTT callback
def on_message(client, userdata, message):
    global latest_ranked, latest_events, latest_snapshot
    topic = message.topic
    payload = json.loads(message.payload.decode())

    if topic == TOPIC_PRI:
        latest_ranked = payload.get("ranked", [])
    elif topic == TOPIC_WO_EVENTS:
        latest_events.append(payload)
        latest_events[:] = latest_events[-100:]  # keep last 100
    elif topic == TOPIC_WO_SNAPSHOT:
        latest_snapshot = payload


# Background MQTT thread
def mqtt_thread():
    c = mqtt.Client()
    c.on_message = on_message
    c.connect(MQTT_BROKER, MQTT_PORT, 60)
    c.subscribe([(TOPIC_PRI, 0), (TOPIC_WO_EVENTS, 0), (TOPIC_WO_SNAPSHOT, 0)])
    c.loop_forever()


# Start MQTT listener in background
threading.Thread(target=mqtt_thread, daemon=True).start()

# Streamlit UI
st.set_page_config(page_title="KMRL Maintenance Dashboard", layout="wide")
st.title("🚇 KMRL AI‑Driven Maintenance — Live Dashboard")

col1, col2 = st.columns(2)

# ---------------------
# Left: Live priority ranking
# ---------------------
with col1:
    st.subheader("📊 Live Priority Ranking")
    if latest_ranked:
        df = pd.DataFrame(latest_ranked)
        st.dataframe(df.sort_values("priority", ascending=False), use_container_width=True)
    else:
        st.info("Waiting for priority data…")

# ---------------------
# Right: Work Order Event Stream
# ---------------------
with col2:
    st.subheader("🛠️ Work Orders (Event Stream)")
    if latest_events:
        evdf = pd.DataFrame(latest_events)
        st.dataframe(
            evdf[["id", "assetnum", "description", "priority", "status", "created_ts"]]
            .sort_values("created_ts", ascending=False),
            use_container_width=True
        )
    else:
        st.info("No events yet — create a work order by raising a priority.")

# ---------------------
# Maintenance schedule (based on priority)
# ---------------------
st.subheader("📅 Mock Maintenance Schedule (2h slots by priority)")
if latest_ranked:
    now = pd.Timestamp.now()
    sched = []
    for i, row in enumerate(sorted(latest_ranked, key=lambda r: r["priority"], reverse=True)):
        sched.append({
            "Coach": row["coach_id"],
            "Start": now + pd.Timedelta(hours=i * 2),
            "End": now + pd.Timedelta(hours=(i + 1) * 2)
        })
    sdf = pd.DataFrame(sched)
    fig = px.timeline(sdf, x_start="Start", x_end="End", y="Coach", color="Coach")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Schedule will appear after priorities are published.")

# ---------------------
# Technician control: Close work order
# ---------------------
st.subheader("🔧 Technician Action — Close a Work Order")
wo_id = st.text_input("Enter Work Order ID to close", "")
if st.button("Close Work Order"):
    if wo_id.strip():
        try:
            r = requests.patch(
                f"{MOCK_MAXIMO_URL}/workorders/{int(wo_id)}",
                params={"status": "CLOSED"},
                timeout=5
            )
            if r.ok:
                st.success(f"Closed WO #{wo_id}")
            else:
                st.error(f"Failed: {r.status_code} {r.text}")
        except Exception as e:
            st.error(str(e))
    else:
        st.warning("Please enter a numeric Work Order ID.")
