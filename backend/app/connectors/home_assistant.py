"""Home Assistant REST Connector (optional)."""
from __future__ import annotations

from typing import Any

import httpx

from ..config import HA_URL, HA_TOKEN, HA_DRY_RUN


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
    """
    Call a Home Assistant service.
    Respects HA_DRY_RUN setting.
    """
    if not HA_URL:
        return False

    if HA_DRY_RUN:
        print(f"[ha-connector] DRY RUN: {domain}.{service}({data})")
        return True

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{HA_URL}/api/services/{domain}/{service}",
            headers={"Authorization": f"Bearer {HA_TOKEN}"},
            json=data,
        )
        resp.raise_for_status()
        return True


def map_ha_entity(entity: dict[str, Any]) -> dict[str, Any] | None:
    """Map an HA entity to our internal device schema."""
    eid = entity.get("entity_id", "")
    state = entity.get("state", "unknown")
    attrs = entity.get("attributes", {})

    domain = eid.split(".")[0] if "." in eid else ""

    mapping = {
        "light": {
            "type": "light",
            "attributes": {
                "on": state == "on",
                "brightness": attrs.get("brightness", 255) * 100 // 255,
                "color_temp": attrs.get("color_temp", 4000),
            },
        },
        "climate": {
            "type": "ac",
            "attributes": {
                "on": state != "off",
                "temperature": attrs.get("temperature", 25),
                "mode": attrs.get("hvac_mode", "auto"),
            },
        },
        "fan": {
            "type": "fan",
            "attributes": {
                "on": state == "on",
                "speed": attrs.get("percentage", 50) // 20,
            },
        },
        "cover": {
            "type": "curtain",
            "attributes": {
                "position": attrs.get("current_position", 50),
                "state": state,
            },
        },
    }

    if domain not in mapping:
        return None

    m = mapping[domain]
    return {
        "id": eid.replace(".", "_"),
        "name": attrs.get("friendly_name", eid),
        "type": m["type"],
        "attributes": m["attributes"],
        "ha_entity_id": eid,
    }
