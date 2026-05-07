"""MiMo HomeOps Agent Pro — MiMo LLM client."""
from __future__ import annotations

import json
from typing import Any

import httpx

from .config import MIMO_API_BASE, MIMO_API_KEY, MIMO_MODEL
from .models import ActionPlan, DeviceAction


SYSTEM_PROMPT = """You are MiMo HomeOps Agent, an AI assistant that controls a Xiaomi-style smart home.

When the user gives a home automation goal, you must respond with a structured JSON action plan.

Available device types and actions:
- light: on, off, brightness (0-100), color_temp (2000-6500K)
- ac: on, off, set_temp (16-30°C), set_mode (auto/cool/heat/dry/fan)
- fan: on, off, set_speed (1-max)
- curtain: open, close, set_position (0-100%)
- purifier: on, off, set_mode (auto/sleep/turbo/manual)
- vacuum: start, stop, return_home
- plug: on, off

Response format (JSON only):
{
  "goal": "user's goal restated",
  "actions": [
    {
      "device_id": "device_id_here",
      "action": "domain.command",
      "parameters": {},
      "reason": "why this action",
      "risk_level": "low|medium|high|critical",
      "requires_confirmation": false
    }
  ],
  "summary": "human-readable summary of what will be done",
  "estimated_energy_impact": "description of energy impact"
}

Safety rules:
- Never unlock doors, turn on cameras, or access security devices without explicit approval
- Default to energy-saving modes when possible
- Consider comfort alongside energy efficiency
- Always explain your reasoning
"""


async def plan_actions(
    user_message: str,
    home_state: dict[str, Any],
    dry_run: bool = True,
) -> ActionPlan:
    """
    Send user message + home state to MiMo LLM and get an action plan.
    Falls back to a simple heuristic planner if API key is not set.
    """
    if not MIMO_API_KEY:
        return _heuristic_planner(user_message, home_state)

    home_context = json.dumps(home_state, indent=2)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Current home state:\n{home_context}\n\nUser request: {user_message}",
        },
    ]

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{MIMO_API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {MIMO_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MIMO_MODEL,
                "messages": messages,
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            },
        )
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"]
    plan_data = json.loads(content)
    return ActionPlan(**plan_data)


def _heuristic_planner(user_message: str, home_state: dict[str, Any]) -> ActionPlan:
    """
    Simple keyword-based planner for demo purposes when no LLM API is available.
    """
    msg = user_message.lower()
    actions: list[DeviceAction] = []

    # Get rooms from home_state
    rooms = home_state.get("rooms", {})

    # ── Sleep mode ──
    if "sleep" in msg or "tidur" in msg or "malam" in msg:
        # Turn off all lights except bedroom
        for room_name, devices in rooms.items():
            for d in devices:
                if d["type"] == "light" and "bedroom" not in room_name.lower():
                    if "ON" in d.get("status", ""):
                        actions.append(DeviceAction(
                            device_id=d["id"],
                            action="light.off",
                            reason=f"Sleep mode: turning off {room_name} light",
                        ))
        # Bedroom AC comfort
        actions.append(DeviceAction(
            device_id="br_ac_1",
            action="ac.set_temp",
            parameters={"temperature": 25},
            reason="Sleep mode: set bedroom AC to 25°C for comfort",
        ))
        actions.append(DeviceAction(
            device_id="br_ac_1",
            action="ac.on",
            reason="Sleep mode: ensure AC is on",
        ))
        # Purifier sleep
        actions.append(DeviceAction(
            device_id="hw_purifier_1",
            action="purifier.set_mode",
            parameters={"mode": "sleep"},
            reason="Sleep mode: purifier to sleep/quiet mode",
        ))
        actions.append(DeviceAction(
            device_id="hw_purifier_1",
            action="purifier.on",
            reason="Sleep mode: turn on purifier",
        ))
        # Close curtains
        actions.append(DeviceAction(
            device_id="br_curtain_1",
            action="curtain.close",
            reason="Sleep mode: close bedroom curtains",
        ))

    # ── All lights off ──
    elif "matikan semua lampu" in msg or ("all lights" in msg and "off" in msg):
        for room_name, devices in rooms.items():
            for d in devices:
                if d["type"] == "light" and "ON" in d.get("status", ""):
                    # Exception: "kecuali" (except)
                    if "kecuali" in msg or "except" in msg:
                        # Skip if room mentioned as exception
                        skip = False
                        for keyword in ["study", "kerja", "kantor"]:
                            if keyword in msg and keyword in room_name.lower():
                                skip = True
                                break
                        if skip:
                            continue
                    actions.append(DeviceAction(
                        device_id=d["id"],
                        action="light.off",
                        reason=f"Turning off {d['name']} in {room_name}",
                    ))

    # ── Cool down ──
    elif any(w in msg for w in ["panas", "hot", "cool", "dingin", "sejuk"]):
        temp = 24 if "dingin" in msg or "cool" in msg else 25
        for room_name, devices in rooms.items():
            for d in devices:
                if d["type"] == "ac":
                    actions.append(DeviceAction(
                        device_id=d["id"],
                        action="ac.on",
                        reason=f"Activating AC in {room_name}",
                    ))
                    actions.append(DeviceAction(
                        device_id=d["id"],
                        action="ac.set_temp",
                        parameters={"temperature": temp},
                        reason=f"Setting {room_name} AC to {temp}°C",
                    ))

    # ── Energy save ──
    elif any(w in msg for w in ["hemat", "energy", "save", "eco"]):
        for room_name, devices in rooms.items():
            for d in devices:
                if d["type"] == "plug" and "ON" in d.get("status", ""):
                    actions.append(DeviceAction(
                        device_id=d["id"],
                        action="plug.off",
                        reason=f"Energy saving: turning off plug {d['name']}",
                    ))
                if d["type"] == "ac" and "ON" in d.get("status", ""):
                    actions.append(DeviceAction(
                        device_id=d["id"],
                        action="ac.set_temp",
                        parameters={"temperature": 27},
                        reason=f"Energy saving: raise AC to 27°C in {room_name}",
                    ))

    # ── Fallback ──
    if not actions:
        return ActionPlan(
            goal=user_message,
            actions=[],
            summary="I couldn't determine a specific action for that request. Try: 'sleep mode', 'turn off all lights', 'cool down the house', or 'save energy'.",
        )

    goal = user_message
    summary = f"Planned {len(actions)} actions based on your request."
    return ActionPlan(goal=goal, actions=actions, summary=summary)
