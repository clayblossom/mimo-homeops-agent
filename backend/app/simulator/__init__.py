"""Digital Twin Home Simulator — Xiaomi-style smart home virtual devices."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config import HOME_STATE_PATH, SAMPLE_HOME_PATH
from ..db import (
    get_all_devices,
    get_device,
    load_devices_from_json,
    update_device,
    add_timeline_entry,
)


def init_simulator():
    """Load sample home JSON into DB if empty."""
    devices = get_all_devices()
    if not devices:
        # Try sample home first, then create a default one
        sample = SAMPLE_HOME_PATH
        if sample.exists():
            count = load_devices_from_json(sample)
        else:
            _create_default_home()
            count = load_devices_from_json(HOME_STATE_PATH)
        print(f"[simulator] Loaded {count} devices from home state")
    else:
        print(f"[simulator] {len(devices)} devices already in DB")


def _create_default_home():
    """Create a minimal default home state JSON."""
    default = {
        "home_name": "MiMo Demo Home",
        "rooms": [
            {
                "name": "Living Room",
                "devices": [
                    {
                        "id": "lr_light_1",
                        "name": "Main Light",
                        "type": "light",
                        "attributes": {"on": True, "brightness": 80, "color_temp": 4000},
                    },
                    {
                        "id": "lr_ac_1",
                        "name": "AC Living Room",
                        "type": "ac",
                        "attributes": {"on": False, "temperature": 26, "mode": "auto", "fan_speed": "auto"},
                    },
                    {
                        "id": "lr_sensor_temp",
                        "name": "Temperature Sensor",
                        "type": "sensor",
                        "attributes": {"value": 29.5, "unit": "°C"},
                    },
                    {
                        "id": "lr_sensor_humidity",
                        "name": "Humidity Sensor",
                        "type": "sensor",
                        "attributes": {"value": 65, "unit": "%"},
                    },
                    {
                        "id": "lr_sensor_motion",
                        "name": "Motion Sensor",
                        "type": "sensor",
                        "attributes": {"motion": False},
                    },
                ],
            },
            {
                "name": "Bedroom",
                "devices": [
                    {
                        "id": "br_light_1",
                        "name": "Bedroom Light",
                        "type": "light",
                        "attributes": {"on": False, "brightness": 50, "color_temp": 3000},
                    },
                    {
                        "id": "br_ac_1",
                        "name": "AC Bedroom",
                        "type": "ac",
                        "attributes": {"on": False, "temperature": 25, "mode": "cool", "fan_speed": "low"},
                    },
                    {
                        "id": "br_curtain_1",
                        "name": "Bedroom Curtain",
                        "type": "curtain",
                        "attributes": {"position": 100, "state": "open"},
                    },
                    {
                        "id": "br_sensor_temp",
                        "name": "Temperature Sensor",
                        "type": "sensor",
                        "attributes": {"value": 28.0, "unit": "°C"},
                    },
                    {
                        "id": "br_sensor_motion",
                        "name": "Motion Sensor",
                        "type": "sensor",
                        "attributes": {"motion": True},
                    },
                ],
            },
            {
                "name": "Kitchen",
                "devices": [
                    {
                        "id": "kt_light_1",
                        "name": "Kitchen Light",
                        "type": "light",
                        "attributes": {"on": True, "brightness": 100, "color_temp": 5000},
                    },
                    {
                        "id": "kt_plug_1",
                        "name": "Coffee Machine Plug",
                        "type": "plug",
                        "attributes": {"on": False, "power_w": 0},
                    },
                    {
                        "id": "kt_sensor_leak",
                        "name": "Leak Sensor",
                        "type": "sensor",
                        "attributes": {"leak": False},
                    },
                ],
            },
            {
                "name": "Study Room",
                "devices": [
                    {
                        "id": "sr_light_1",
                        "name": "Desk Light",
                        "type": "light",
                        "attributes": {"on": True, "brightness": 90, "color_temp": 4500},
                    },
                    {
                        "id": "sr_fan_1",
                        "name": "Ceiling Fan",
                        "type": "fan",
                        "attributes": {"on": True, "speed": 3, "max_speed": 5},
                    },
                    {
                        "id": "sr_plug_1",
                        "name": "Monitor Plug",
                        "type": "plug",
                        "attributes": {"on": True, "power_w": 45},
                    },
                ],
            },
            {
                "name": "Hallway",
                "devices": [
                    {
                        "id": "hw_light_1",
                        "name": "Hallway Light",
                        "type": "light",
                        "attributes": {"on": False, "brightness": 60, "color_temp": 3500},
                    },
                    {
                        "id": "hw_purifier_1",
                        "name": "Air Purifier",
                        "type": "purifier",
                        "attributes": {"on": False, "mode": "auto", "pm25": 35, "filter_life": 72},
                    },
                    {
                        "id": "hw_sensor_door",
                        "name": "Front Door Sensor",
                        "type": "sensor",
                        "attributes": {"open": False},
                    },
                ],
            },
        ],
    }
    HOME_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HOME_STATE_PATH, "w") as f:
        json.dump(default, f, indent=2)


# ── Action Execution ────────────────────────────────────────────────────────

def execute_action(device_id: str, action: str, parameters: dict[str, Any]) -> dict[str, Any]:
    """
    Execute an action on a simulated device.
    Returns the new device state.
    """
    device = get_device(device_id)
    if not device:
        raise ValueError(f"Device {device_id} not found")

    before = {**device["attributes"]}
    attrs = {**device["attributes"]}

    # Parse action: e.g. "light.on", "ac.set_temp"
    parts = action.split(".")
    if len(parts) != 2:
        raise ValueError(f"Invalid action format: {action}")

    domain, command = parts
    device_type = device["type"]

    # Validate domain matches device type
    if domain != device_type:
        raise ValueError(f"Action domain '{domain}' doesn't match device type '{device_type}'")

    # ── Light actions ──
    if domain == "light":
        if command == "on":
            attrs["on"] = True
        elif command == "off":
            attrs["on"] = False
        elif command == "brightness":
            attrs["brightness"] = max(0, min(100, parameters.get("brightness", 100)))
        elif command == "color_temp":
            attrs["color_temp"] = max(2000, min(6500, parameters.get("color_temp", 4000)))

    # ── AC actions ──
    elif domain == "ac":
        if command == "on":
            attrs["on"] = True
        elif command == "off":
            attrs["on"] = False
        elif command == "set_temp":
            attrs["temperature"] = max(16, min(30, parameters.get("temperature", 25)))
        elif command == "set_mode":
            mode = parameters.get("mode", "auto")
            if mode in ("auto", "cool", "heat", "dry", "fan"):
                attrs["mode"] = mode

    # ── Fan actions ──
    elif domain == "fan":
        if command == "on":
            attrs["on"] = True
        elif command == "off":
            attrs["on"] = False
        elif command == "set_speed":
            max_s = attrs.get("max_speed", 5)
            attrs["speed"] = max(1, min(max_s, parameters.get("speed", 3)))

    # ── Curtain actions ──
    elif domain == "curtain":
        if command == "open":
            attrs["position"] = 100
            attrs["state"] = "open"
        elif command == "close":
            attrs["position"] = 0
            attrs["state"] = "closed"
        elif command == "set_position":
            pos = max(0, min(100, parameters.get("position", 50)))
            attrs["position"] = pos
            attrs["state"] = "open" if pos > 0 else "closed"

    # ── Purifier actions ──
    elif domain == "purifier":
        if command == "on":
            attrs["on"] = True
        elif command == "off":
            attrs["on"] = False
        elif command == "set_mode":
            mode = parameters.get("mode", "auto")
            if mode in ("auto", "sleep", "turbo", "manual"):
                attrs["mode"] = mode

    # ── Vacuum actions ──
    elif domain == "vacuum":
        if command == "start":
            attrs["cleaning"] = True
        elif command == "stop":
            attrs["cleaning"] = False
        elif command == "return_home":
            attrs["cleaning"] = False
            attrs["docked"] = True

    # ── Plug actions ──
    elif domain == "plug":
        if command == "on":
            attrs["on"] = True
        elif command == "off":
            attrs["on"] = False
            attrs["power_w"] = 0

    else:
        raise ValueError(f"Unsupported device domain: {domain}")

    # Persist
    update_device(device_id, attrs)

    # Timeline entry
    entry = {
        "device_id": device_id,
        "device_name": device["name"],
        "action": action,
        "before_state": before,
        "after_state": attrs,
        "explanation": f"Executed {action} on {device['name']}",
        "risk_level": "low",
        "executed": True,
    }
    add_timeline_entry(entry)

    return {**device, "attributes": attrs}


def get_home_summary() -> dict[str, Any]:
    """Get a summary of the current home state."""
    devices = get_all_devices()
    rooms: dict[str, list] = {}
    for d in devices:
        rooms.setdefault(d["room"], []).append(d)

    active_count = sum(
        1 for d in devices
        if d["type"] != "sensor"
        and d["attributes"].get("on", d["attributes"].get("cleaning", False))
    )

    sensors_alert = []
    for d in devices:
        if d["type"] != "sensor":
            continue
        attrs = d["attributes"]
        if attrs.get("leak"):
            sensors_alert.append(f"⚠️ Leak detected: {d['room']} {d['name']}")
        if attrs.get("motion"):
            sensors_alert.append(f"🚶 Motion: {d['room']} {d['name']}")
        if attrs.get("open"):
            sensors_alert.append(f"🚪 Door open: {d['room']} {d['name']}")
        if attrs.get("value", 0) > 32:
            sensors_alert.append(f"🌡️ High temp: {d['room']} {attrs['value']}°C")

    return {
        "home_name": "MiMo Demo Home",
        "total_devices": len(devices),
        "active_devices": active_count,
        "rooms": {name: [_device_summary(d) for d in devs] for name, devs in rooms.items()},
        "sensor_alerts": sensors_alert,
    }


def _device_summary(device: dict) -> dict:
    attrs = device["attributes"]
    status = "unknown"
    if device["type"] == "sensor":
        status = ", ".join(f"{k}={v}" for k, v in attrs.items())
    elif "on" in attrs:
        status = "ON" if attrs["on"] else "OFF"
    elif "cleaning" in attrs:
        status = "CLEANING" if attrs["cleaning"] else "IDLE"
    return {
        "id": device["id"],
        "name": device["name"],
        "type": device["type"],
        "status": status,
        "online": device["online"],
    }
