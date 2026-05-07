"""Home Assistant REST Connector — Full integration layer."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import httpx

from ..config import HA_URL, HA_TOKEN, HA_DRY_RUN
from ..db import get_db


# ── Entity Mapping ──────────────────────────────────────────────────────────

# Maps HA domains to our internal device types
DOMAIN_MAP: dict[str, dict[str, Any]] = {
    "light": {
        "type": "light",
        "state_fn": lambda s, a: {
            "on": s == "on",
            "brightness": round(a.get("brightness", 255) * 100 / 255),
            "color_temp": a.get("color_temp", 4000),
        },
        "services": {
            "light.on": ("light", "turn_on", {}),
            "light.off": ("light", "turn_off", {}),
            "light.brightness": ("light", "turn_on", lambda p: {"brightness": p.get("brightness", 100) * 255 // 100}),
            "light.color_temp": ("light", "turn_on", lambda p: {"color_temp": p.get("color_temp", 4000)}),
        },
    },
    "climate": {
        "type": "ac",
        "state_fn": lambda s, a: {
            "on": s not in ("off", "unknown"),
            "temperature": a.get("temperature", 25),
            "mode": a.get("hvac_mode", a.get("hvac_modes", ["auto"])[0] if a.get("hvac_modes") else "auto"),
            "fan_mode": a.get("fan_mode", "auto"),
        },
        "services": {
            "ac.on": ("climate", "turn_on", {}),
            "ac.off": ("climate", "turn_off", {}),
            "ac.set_temp": ("climate", "set_temperature", lambda p: {"temperature": p.get("temperature", 25)}),
            "ac.set_mode": ("climate", "set_hvac_mode", lambda p: {"hvac_mode": p.get("mode", "auto")}),
        },
    },
    "fan": {
        "type": "fan",
        "state_fn": lambda s, a: {
            "on": s == "on",
            "speed": a.get("percentage", 50) // 20 if a.get("percentage") else a.get("speed", 3),
            "max_speed": 5,
        },
        "services": {
            "fan.on": ("fan", "turn_on", {}),
            "fan.off": ("fan", "turn_off", {}),
            "fan.set_speed": ("fan", "set_percentage", lambda p: {"percentage": p.get("speed", 3) * 20}),
        },
    },
    "cover": {
        "type": "curtain",
        "state_fn": lambda s, a: {
            "position": a.get("current_position", 50),
            "state": "open" if a.get("current_position", 0) > 0 else "closed",
        },
        "services": {
            "curtain.open": ("cover", "open_cover", {}),
            "curtain.close": ("cover", "close_cover", {}),
            "curtain.set_position": ("cover", "set_cover_position",
                                     lambda p: {"position": p.get("position", 50)}),
        },
    },
    "switch": {
        "type": "plug",
        "state_fn": lambda s, a: {"on": s == "on", "power_w": a.get("current_power_w", 0)},
        "services": {
            "plug.on": ("switch", "turn_on", {}),
            "plug.off": ("switch", "turn_off", {}),
        },
    },
    "vacuum": {
        "type": "vacuum",
        "state_fn": lambda s, a: {
            "cleaning": s == "cleaning",
            "docked": s == "docked",
            "battery": a.get("battery_level", 100),
        },
        "services": {
            "vacuum.start": ("vacuum", "start", {}),
            "vacuum.stop": ("vacuum", "stop", {}),
            "vacuum.return_home": ("vacuum", "return_to_base", {}),
        },
    },
    "sensor": {
        "type": "sensor",
        "state_fn": lambda s, a: {
            "value": float(s) if s.replace(".", "").replace("-", "").isdigit() else s,
            "unit": a.get("unit_of_measurement", ""),
        },
        "services": {},
    },
    "binary_sensor": {
        "type": "sensor",
        "state_fn": lambda s, a: {
            "value": s == "on" or s == "open" or s == "detected",
            "device_class": a.get("device_class", ""),
        },
        "services": {},
    },
}


# ── API Functions ────────────────────────────────────────────────────────────

async def list_entities() -> list[dict[str, Any]]:
    """List all HA entities."""
    if not HA_URL:
        return []
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{HA_URL}/api/states",
            headers={"Authorization": f"Bearer {HA_TOKEN}"},
        )
        resp.raise_for_status()
        return resp.json()


async def get_state(entity_id: str) -> dict[str, Any] | None:
    """Get state of a specific HA entity."""
    if not HA_URL:
        return None
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{HA_URL}/api/states/{entity_id}",
            headers={"Authorization": f"Bearer {HA_TOKEN}"},
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()


async def call_service(domain: str, service: str, data: dict[str, Any]) -> bool:
    """Call a Home Assistant service. Respects HA_DRY_RUN."""
    if not HA_URL:
        return False

    if HA_DRY_RUN:
        print(f"[ha-connector] DRY RUN: {domain}.{service}({json.dumps(data)})")
        return True

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{HA_URL}/api/services/{domain}/{service}",
            headers={
                "Authorization": f"Bearer {HA_TOKEN}",
                "Content-Type": "application/json",
            },
            json=data,
        )
        resp.raise_for_status()
        return True


# ── Entity Mapping ──────────────────────────────────────────────────────────

def map_ha_entity(entity: dict[str, Any]) -> dict[str, Any] | None:
    """Map an HA entity to our internal device schema."""
    eid = entity.get("entity_id", "")
    state = entity.get("state", "unknown")
    attrs = entity.get("attributes", {})

    domain = eid.split(".")[0] if "." in eid else ""

    if domain not in DOMAIN_MAP:
        return None

    m = DOMAIN_MAP[domain]
    return {
        "id": eid.replace(".", "_"),
        "name": attrs.get("friendly_name", eid),
        "room": _extract_room(attrs, eid),
        "type": m["type"],
        "online": state != "unavailable",
        "attributes": m["state_fn"](state, attrs),
        "ha_entity_id": eid,
    }


def _extract_room(attrs: dict, entity_id: str) -> str:
    """Try to extract room from HA entity attributes or friendly name."""
    # HA doesn't have a standard room attribute, try common patterns
    friendly = attrs.get("friendly_name", "")
    # Some integrations use area_id
    if "area" in attrs:
        return attrs["area"]
    # Guess from friendly name (e.g. "Living Room Light")
    for room in ["Living Room", "Bedroom", "Kitchen", "Study", "Hallway", "Bathroom", "Garage"]:
        if room.lower() in friendly.lower():
            return room
    # Guess from entity_id
    for room in ["living", "bedroom", "kitchen", "study", "hallway", "bathroom", "garage"]:
        if room in entity_id.lower():
            return room.title()
    return "Unknown"


# ── Sync ────────────────────────────────────────────────────────────────────

async def sync_entities() -> dict[str, Any]:
    """
    Sync all HA entities into our local DB.
    Returns sync summary.
    """
    if not HA_URL:
        return {"error": "Home Assistant not configured", "synced": 0}

    ha_entities = await list_entities()
    mapped = []
    skipped = []

    for entity in ha_entities:
        result = map_ha_entity(entity)
        if result:
            mapped.append(result)
        else:
            skipped.append(entity.get("entity_id", ""))

    # Store mapped devices in DB
    with get_db() as conn:
        for device in mapped:
            conn.execute(
                """INSERT OR REPLACE INTO device_states
                   (id, name, room, type, online, attributes)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    device["id"],
                    device["name"],
                    device["room"],
                    device["type"],
                    1 if device["online"] else 0,
                    json.dumps(device["attributes"]),
                ),
            )

    return {
        "synced": len(mapped),
        "skipped": len(skipped),
        "devices": [d["id"] for d in mapped],
        "ha_entities_total": len(ha_entities),
    }


async def execute_ha_action(device_id: str, action: str, parameters: dict[str, Any]) -> bool:
    """
    Execute an action on a HA device.
    Maps our internal action to HA service call.
    """
    if not HA_URL:
        return False

    # Find the device in DB to get ha_entity_id
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM device_states WHERE id = ?", (device_id,)
        ).fetchone()

    if not row:
        return False

    attrs = json.loads(row["attributes"]) if isinstance(row["attributes"], str) else row["attributes"]
    ha_entity_id = attrs.get("ha_entity_id")

    if not ha_entity_id:
        return False

    # Find the right service mapping
    domain = ha_entity_id.split(".")[0]
    if domain not in DOMAIN_MAP:
        return False

    services = DOMAIN_MAP[domain].get("services", {})
    if action not in services:
        return False

    svc_domain, svc_service, svc_data = services[action]

    # Resolve data (might be a lambda)
    if callable(svc_data):
        data = svc_data(parameters)
    else:
        data = {**svc_data}

    # Add entity_id to data
    data["entity_id"] = ha_entity_id

    return await call_service(svc_domain, svc_service, data)


# ── Status ──────────────────────────────────────────────────────────────────

async def ha_status() -> dict[str, Any]:
    """Get Home Assistant connection status."""
    if not HA_URL:
        return {
            "configured": False,
            "connected": False,
            "url": None,
            "dry_run": HA_DRY_RUN,
        }

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"{HA_URL}/api/",
                headers={"Authorization": f"Bearer {HA_TOKEN}"},
            )
            connected = resp.status_code == 200
            info = resp.json() if connected else {}
    except Exception:
        connected = False
        info = {}

    return {
        "configured": True,
        "connected": connected,
        "url": HA_URL,
        "dry_run": HA_DRY_RUN,
        "ha_version": info.get("message", "unknown"),
    }
