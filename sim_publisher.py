# mock_maximo_api.py
from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel, Field, constr
import sqlite3
import time
import json
import threading
from typing import Optional, List
import paho.mqtt.client as mqtt
from config import DB_PATH, MQTT_BROKER, MQTT_PORT, MQTT_TOPIC_EVENTS, MQTT_CLIENT_ID

# -------------------------
# Pydantic models
# -------------------------
class WorkOrderIn(BaseModel):
    assetnum: constr(strip_whitespace=True, min_length=1)
    description: constr(strip_whitespace=True, min_length=1)
    priority: int = Field(3, ge=1, le=5, description="1 = highest, 5 = lowest")
    status: str = Field("OPEN", description="OPEN, INPRG, CLOSED")

class WorkOrderOut(WorkOrderIn):
    id: int
    created_ts: float

class WorkOrderUpdate(BaseModel):
    description: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[str] = None

# -------------------------
# DB helpers (sqlite3)
# -------------------------
_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
_conn.row_factory = sqlite3.Row
_cursor = _conn.cursor()

_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS workorders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        assetnum TEXT NOT NULL,
        description TEXT NOT NULL,
        priority INTEGER NOT NULL,
        status TEXT NOT NULL,
        created_ts REAL NOT NULL
    )
    """
)
_conn.commit()

def row_to_out(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "assetnum": row["assetnum"],
        "description": row["description"],
        "priority": row["priority"],
        "status": row["status"],
        "created_ts": row["created_ts"]
    }

# -------------------------
# MQTT client (background)
# -------------------------
mq = mqtt.Client(client_id=MQTT_CLIENT_ID)
try:
    mq.connect(MQTT_BROKER, MQTT_PORT, 60)
except Exception as e:
    # do not crash: log and proceed (useful during demo if broker starts later)
    print(f"[MQTT] connect failed: {e}")

def publish_event(obj: dict):
    try:
        mq.publish(MQTT_TOPIC_EVENTS, json.dumps(obj, default=str))
    except Exception as e:
        print("[MQTT] publish error:", e)

# -------------------------
# FastAPI app
# -------------------------
app = FastAPI(title="Mock Maximo (Job Card) API - KMRL")

@app.post("/workorders", response_model=WorkOrderOut, status_code=201)
def create_workorder(wo: WorkOrderIn):
    ts = time.time()
    with _conn:
        c = _conn.execute(
            "INSERT INTO workorders (assetnum, description, priority, status, created_ts) VALUES (?, ?, ?, ?, ?)",
            (wo.assetnum, wo.description, wo.priority, wo.status, ts)
        )
        new_id = c.lastrowid
    out = {"id": new_id, **wo.dict(), "created_ts": ts}
    # publish event asynchronously to avoid blocking
    threading.Thread(target=publish_event, args=(out,), daemon=True).start()
    return out

@app.get("/workorders/{wo_id}", response_model=WorkOrderOut)
def get_workorder(wo_id: int):
    row = _conn.execute("SELECT * FROM workorders WHERE id = ?", (wo_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Work order not found")
    return row_to_out(row)

@app.get("/workorders", response_model=List[WorkOrderOut])
def list_workorders(
    status: Optional[str] = Query(None, description="Filter by status"),
    assetnum: Optional[str] = Query(None, description="Filter by asset number"),
    q: Optional[str] = Query(None, description="Full-text-ish search in description"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    sql = "SELECT * FROM workorders"
    params = []
    clauses = []
    if status:
        clauses.append("status = ?"); params.append(status)
    if assetnum:
        clauses.append("assetnum = ?"); params.append(assetnum)
    if q:
        clauses.append("description LIKE ?"); params.append(f"%{q}%")
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY created_ts DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = _conn.execute(sql, tuple(params)).fetchall()
    return [row_to_out(r) for r in rows]

@app.patch("/workorders/{wo_id}", response_model=WorkOrderOut)
def patch_workorder(wo_id: int, update: WorkOrderUpdate = Body(...)):
    cur = _conn.execute("SELECT * FROM workorders WHERE id = ?", (wo_id,)).fetchone()
    if not cur:
        raise HTTPException(status_code=404, detail="Work order not found")
    # existing values
    cur_data = dict(cur)
    new_description = update.description if update.description is not None else cur_data["description"]
    new_priority = update.priority if update.priority is not None else cur_data["priority"]
    new_status = update.status if update.status is not None else cur_data["status"]

    with _conn:
        _conn.execute(
            "UPDATE workorders SET description = ?, priority = ?, status = ? WHERE id = ?",
            (new_description, new_priority, new_status, wo_id)
        )
    row = _conn.execute("SELECT * FROM workorders WHERE id = ?", (wo_id,)).fetchone()
    out = row_to_out(row)
    threading.Thread(target=publish_event, args=(out,), daemon=True).start()
    return out

@app.delete("/workorders/{wo_id}", status_code=204)
def delete_workorder(wo_id: int):
    cur = _conn.execute("SELECT id FROM workorders WHERE id = ?", (wo_id,)).fetchone()
    if not cur:
        raise HTTPException(status_code=404, detail="Work order not found")
    with _conn:
        _conn.execute("DELETE FROM workorders WHERE id = ?", (wo_id,))
    # publish a small tombstone event
    threading.Thread(target=publish_event, args=({"id": wo_id, "deleted": True},), daemon=True).start()
    return

# Health endpoint for demos
@app.get("/health")
def health():
    return {"status": "ok", "mqtt_connected": mq.is_connected()}
