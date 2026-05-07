"""MiMo HomeOps Agent Pro — SQLite database layer."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import DB_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create all tables if they don't exist."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS device_states (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                room TEXT NOT NULL,
                type TEXT NOT NULL,
                online INTEGER DEFAULT 1,
                attributes TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS timeline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                device_id TEXT NOT NULL,
                device_name TEXT NOT NULL,
                action TEXT NOT NULL,
                before_state TEXT DEFAULT '{}',
                after_state TEXT DEFAULT '{}',
                explanation TEXT DEFAULT '',
                risk_level TEXT DEFAULT 'low',
                executed INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS automation_rules (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                conditions TEXT NOT NULL,
                actions TEXT NOT NULL,
                reason TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                device_id TEXT,
                resolved INTEGER DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_timeline_ts ON timeline(timestamp);
            CREATE INDEX IF NOT EXISTS idx_timeline_device ON timeline(device_id);
            CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents(severity);
        """)


# ── Device State CRUD ──────────────────────────────────────────────────────

def load_devices_from_json(path: Path):
    """Load device states from a JSON file into the DB."""
    with open(path) as f:
        data = json.load(f)

    devices = []
    for room in data.get("rooms", []):
        room_name = room["name"]
        for device in room.get("devices", []):
            devices.append({
                "id": device["id"],
                "name": device["name"],
                "room": room_name,
                "type": device["type"],
                "online": 1 if device.get("online", True) else 0,
                "attributes": json.dumps(device.get("attributes", {})),
            })

    with get_db() as conn:
        conn.executemany(
            """INSERT OR REPLACE INTO device_states
               (id, name, room, type, online, attributes)
               VALUES (:id, :name, :room, :type, :online, :attributes)""",
            devices,
        )
    return len(devices)


def get_all_devices() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM device_states").fetchall()
    return [_row_to_device(r) for r in rows]


def get_device(device_id: str) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM device_states WHERE id = ?", (device_id,)
        ).fetchone()
    return _row_to_device(row) if row else None


def update_device(device_id: str, attributes: dict[str, Any]) -> dict[str, Any]:
    """Merge-update a device's attributes and return the new state."""
    device = get_device(device_id)
    if not device:
        raise ValueError(f"Device {device_id} not found")

    merged = {**device["attributes"], **attributes}
    with get_db() as conn:
        conn.execute(
            "UPDATE device_states SET attributes = ? WHERE id = ?",
            (json.dumps(merged), device_id),
        )
    device["attributes"] = merged
    return device


def set_device_online(device_id: str, online: bool):
    with get_db() as conn:
        conn.execute(
            "UPDATE device_states SET online = ? WHERE id = ?",
            (1 if online else 0, device_id),
        )


# ── Timeline CRUD ──────────────────────────────────────────────────────────

def add_timeline_entry(entry: dict[str, Any]) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO timeline
               (timestamp, device_id, device_name, action, before_state,
                after_state, explanation, risk_level, executed)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.get("timestamp", datetime.utcnow().isoformat()),
                entry["device_id"],
                entry["device_name"],
                entry["action"],
                json.dumps(entry.get("before_state", {})),
                json.dumps(entry.get("after_state", {})),
                entry.get("explanation", ""),
                entry.get("risk_level", "low"),
                1 if entry.get("executed", True) else 0,
            ),
        )
        return cur.lastrowid


def get_timeline(limit: int = 50, device_id: str | None = None) -> list[dict]:
    with get_db() as conn:
        if device_id:
            rows = conn.execute(
                "SELECT * FROM timeline WHERE device_id = ? ORDER BY timestamp DESC LIMIT ?",
                (device_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM timeline ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [_row_to_timeline(r) for r in rows]


# ── Incidents CRUD ──────────────────────────────────────────────────────────

def add_incident(incident: dict[str, Any]) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO incidents
               (timestamp, severity, title, description, device_id, resolved)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                incident.get("timestamp", datetime.utcnow().isoformat()),
                incident["severity"],
                incident["title"],
                incident.get("description", ""),
                incident.get("device_id"),
                1 if incident.get("resolved", False) else 0,
            ),
        )
        return cur.lastrowid


def get_incidents(limit: int = 20, unresolved_only: bool = True) -> list[dict]:
    with get_db() as conn:
        if unresolved_only:
            rows = conn.execute(
                "SELECT * FROM incidents WHERE resolved = 0 ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM incidents ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [dict(r) for r in rows]


# ── Helpers ─────────────────────────────────────────────────────────────────

def _row_to_device(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "room": row["room"],
        "type": row["type"],
        "online": bool(row["online"]),
        "attributes": json.loads(row["attributes"]),
    }


def _row_to_timeline(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "timestamp": row["timestamp"],
        "device_id": row["device_id"],
        "device_name": row["device_name"],
        "action": row["action"],
        "before_state": json.loads(row["before_state"]),
        "after_state": json.loads(row["after_state"]),
        "explanation": row["explanation"],
        "risk_level": row["risk_level"],
        "executed": bool(row["executed"]),
    }
