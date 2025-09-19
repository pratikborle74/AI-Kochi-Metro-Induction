from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import time
import json
import paho.mqtt.client as mqtt
from contextlib import contextmanager
from config import MQTT_BROKER, MQTT_PORT


DB_PATH = "workorders.db"
MQTT_TOPIC_EVENTS = "kmrl/workorders/events"


# ----------------------------
# Data models
# ----------------------------
class WorkOrderIn(BaseModel):
    assetnum: str
    description: str
    priority: int = 3  # 1 (highest) .. 5 (lowest)
    status: str = "OPEN"  # OPEN, INPRG, CLOSED


class WorkOrderOut(WorkOrderIn):
    id: int
    created_ts: float


# ----------------------------
# Init SQLite DB and Connection Management
# ----------------------------
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS workorders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assetnum TEXT,
                description TEXT,
                priority INTEGER,
                status TEXT,
                created_ts REAL
            )
            """
        )
        conn.commit()


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


# ----------------------------
# MQTT client for publishing events
# ----------------------------
mq = mqtt.Client()
mq.connect(MQTT_BROKER, MQTT_PORT, 60)


# ----------------------------
# FastAPI app
# ----------------------------
app = FastAPI(title="Mock Maximo API", on_startup=[init_db])


# Helper functions
def json_dumps(obj):
    return json.dumps(obj, default=str)


def row_to_out(r):
    return {
        "id": r[0],
        "assetnum": r[1],
        "description": r[2],
        "priority": r[3],
        "status": r[4],
        "created_ts": r[5]
    }


# API Endpoints
@app.post("/workorders", response_model=WorkOrderOut)
def create_wo(wo: WorkOrderIn):
    with get_db() as conn:
        ts = time.time()
        c = conn.execute(
            "INSERT INTO workorders "
            "(assetnum, description, priority, status, created_ts) "
            "VALUES (?, ?, ?, ?, ?)",
            (wo.assetnum, wo.description, wo.priority, wo.status, ts)
        )
        new_id = c.lastrowid
        conn.commit()

    out = {"id": new_id, **wo.dict(), "created_ts": ts}
    mq.publish(MQTT_TOPIC_EVENTS, json_dumps(out))
    return out


@app.get("/workorders", response_model=list[WorkOrderOut])
def list_wos(status: str | None = None):
    with get_db() as conn:
        if status:
            rows = conn.execute(
                "SELECT id,assetnum,description,priority,status,created_ts "
                "FROM workorders WHERE status=? ORDER BY created_ts DESC",
                (status,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id,assetnum,description,priority,status,created_ts "
                "FROM workorders ORDER BY created_ts DESC"
            ).fetchall()

    return [row_to_out(r) for r in rows]


@app.patch("/workorders/{wo_id}", response_model=WorkOrderOut)
def update_wo(wo_id: int, status: str):
    with get_db() as conn:
        cur = conn.execute(
            "SELECT id FROM workorders WHERE id=?",
            (wo_id,)
        ).fetchone()

        if not cur:
            raise HTTPException(404, "Work order not found")

        conn.execute(
            "UPDATE workorders SET status=? WHERE id=?",
            (status, wo_id)
        )
        conn.commit()

        row = conn.execute(
            "SELECT id, assetnum, description, priority, status, created_ts "
            "FROM workorders WHERE id=?",
            (wo_id,)
        ).fetchone()

    out = row_to_out(row)
    mq.publish(MQTT_TOPIC_EVENTS, json_dumps(out))
    return out
return 0