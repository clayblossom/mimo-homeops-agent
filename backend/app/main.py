"""MiMo HomeOps Agent Pro — Main FastAPI application."""
from __future__ import annotations

import asyncio
import json
import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import API_HOST, API_PORT, DEBUG, HA_URL, HA_DRY_RUN
from .db import init_db, get_timeline, get_incidents, get_db, add_incident
from .models import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    DeviceAction,
    AutomationRule,
    AutomationCondition,
    AutomationAction,
)
from .mimo_client import plan_actions
from .safety import validate_plan, dry_run_summary, SafetyViolation
from .simulator import (
    init_simulator,
    execute_action,
    get_home_summary,
    get_all_devices,
    get_device,
)


# ── App lifecycle ───────────────────────────────────────────────────────────

START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown events."""
    print("[mimo-homeops] Initializing database...")
    init_db()
    print("[mimo-homeops] Initializing simulator...")
    init_simulator()
    print(f"[mimo-homeops] Ready! http://{API_HOST}:{API_PORT}")
    yield
    print("[mimo-homeops] Shutting down.")


app = FastAPI(
    title="MiMo HomeOps Agent Pro",
    version="0.2.0",
    description="AI automation copilot for Xiaomi-style smart homes.",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ──────────────────────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse)
async def health():
    devices = get_all_devices()
    return HealthResponse(
        status="ok",
        version="0.2.0",
        uptime_seconds=round(time.time() - START_TIME, 1),
        device_count=len(devices),
    )


# ── Home State ──────────────────────────────────────────────────────────────

@app.get("/api/home/summary")
async def home_summary():
    """Get the current home state summary."""
    return get_home_summary()


@app.get("/api/devices")
async def list_devices():
    """List all devices."""
    return get_all_devices()


@app.get("/api/devices/{device_id}")
async def get_device_detail(device_id: str):
    """Get a specific device."""
    device = get_device(device_id)
    if not device:
        raise HTTPException(404, f"Device {device_id} not found")
    return device


# ── Chat / Control ──────────────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Process a natural-language home control request.
    Returns an action plan, optionally executes it.
    """
    home_state = get_home_summary()

    # Get action plan from MiMo
    try:
        plan = await plan_actions(req.message, home_state, dry_run=req.dry_run)
    except Exception as e:
        return ChatResponse(
            reply=f"Error generating plan: {e}",
            plan=None,
        )

    if not plan.actions:
        return ChatResponse(reply=plan.summary, plan=plan)

    # Validate safety
    validated_actions, warnings = validate_plan(plan.actions)
    plan.actions = validated_actions

    # Check if any action needs confirmation
    needs_confirm = any(a.requires_confirmation for a in validated_actions)

    if needs_confirm and not req.confirm:
        preview = dry_run_summary(validated_actions)
        return ChatResponse(
            reply=f"{plan.summary}\n\n{preview}\n\n⚠️ Some actions require confirmation. Send with `confirm: true` to execute.",
            plan=plan,
            needs_confirmation=True,
        )

    # Dry run — just preview
    if req.dry_run:
        preview = dry_run_summary(validated_actions)
        return ChatResponse(
            reply=f"{plan.summary}\n\n{preview}\n\n_(Dry run — no actions executed)_",
            plan=plan,
        )

    # Execute actions
    timeline_entries = []
    for action in validated_actions:
        try:
            execute_action(action.device_id, action.action, action.parameters)
            timeline_entries.append({
                "device_id": action.device_id,
                "action": action.action,
                "status": "executed",
            })
        except (ValueError, SafetyViolation) as e:
            warnings.append(f"❌ {action.device_id}: {e}")

    result_lines = [f"✅ Executed {len(timeline_entries)} actions."]
    if warnings:
        result_lines.append("\n⚠️ Warnings:")
        result_lines.extend(warnings)

    return ChatResponse(
        reply="\n".join(result_lines),
        plan=plan,
    )


# ── Timeline ────────────────────────────────────────────────────────────────

@app.get("/api/timeline")
async def timeline(limit: int = 50, device_id: str | None = None):
    """Get the action timeline."""
    return get_timeline(limit=limit, device_id=device_id)


# ── Incidents ───────────────────────────────────────────────────────────────

@app.get("/api/incidents")
async def incidents(limit: int = 20, unresolved_only: bool = True):
    """Get incidents."""
    return get_incidents(limit=limit, unresolved_only=unresolved_only)


@app.post("/api/incidents/{incident_id}/resolve")
async def resolve_incident(incident_id: int):
    """Mark an incident as resolved."""
    with get_db() as conn:
        conn.execute("UPDATE incidents SET resolved = 1 WHERE id = ?", (incident_id,))
    return {"status": "resolved", "id": incident_id}


# ── Direct Device Control ───────────────────────────────────────────────────

@app.post("/api/devices/{device_id}/action")
async def device_action(device_id: str, action: str, parameters: dict | None = None):
    """Directly execute an action on a device (for dashboard controls)."""
    da = DeviceAction(device_id=device_id, action=action, parameters=parameters or {})
    try:
        from .safety import validate_action
        da = validate_action(da)
        if da.requires_confirmation:
            raise HTTPException(403, "This action requires confirmation")
        result = execute_action(device_id, action, parameters or {})
        return result
    except SafetyViolation as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))


# ── Reports ────────────────────────────────────────────────────────────────

@app.get("/api/reports/daily")
async def daily_report(date: str | None = None):
    """Generate a daily energy & comfort report."""
    from .reports import generate_daily_report, save_report
    report = generate_daily_report(date)
    md_path = save_report(report)
    return {**report, "markdown_path": str(md_path)}


# ── Home Assistant Connector ────────────────────────────────────────────────

@app.get("/api/ha/status")
async def ha_status():
    """Get Home Assistant connection status."""
    from .connectors.home_assistant import ha_status as get_ha_status
    return await get_ha_status()


@app.post("/api/ha/sync")
async def ha_sync():
    """Sync devices from Home Assistant into local DB."""
    from .connectors.home_assistant import sync_entities
    result = await sync_entities()
    return result


@app.post("/api/ha/devices/{device_id}/action")
async def ha_device_action(device_id: str, action: str, parameters: dict | None = None):
    """Execute an action via Home Assistant connector."""
    from .connectors.home_assistant import execute_ha_action
    try:
        success = await execute_ha_action(device_id, action, parameters or {})
        if not success:
            raise HTTPException(400, "HA action failed — check HA connection and entity mapping")
        return {"status": "executed", "device_id": device_id, "action": action, "via": "home_assistant"}
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Automation Rules ────────────────────────────────────────────────────────

@app.get("/api/automations")
async def list_automations():
    """List all automation rules."""
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM automation_rules ORDER BY created_at DESC").fetchall()
    rules = []
    for r in rows:
        rules.append({
            "id": r["id"],
            "name": r["name"],
            "enabled": bool(r["enabled"]),
            "conditions": json.loads(r["conditions"]),
            "actions": json.loads(r["actions"]),
            "reason": r["reason"],
            "created_at": r["created_at"],
        })
    return rules


@app.post("/api/automations")
async def create_automation(rule: AutomationRule):
    """Create a new automation rule."""
    import uuid
    rule_id = rule.id or str(uuid.uuid4())[:8]
    with get_db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO automation_rules
               (id, name, enabled, conditions, actions, reason, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                rule_id,
                rule.name,
                1 if rule.enabled else 0,
                json.dumps([c.model_dump() for c in rule.conditions]),
                json.dumps([a.model_dump() for a in rule.actions]),
                rule.reason,
                rule.created_at.isoformat(),
            ),
        )
    return {"id": rule_id, "status": "created"}


@app.put("/api/automations/{rule_id}/toggle")
async def toggle_automation(rule_id: str):
    """Toggle an automation rule on/off."""
    with get_db() as conn:
        row = conn.execute("SELECT enabled FROM automation_rules WHERE id = ?", (rule_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Automation not found")
        new_state = 0 if row["enabled"] else 1
        conn.execute("UPDATE automation_rules SET enabled = ? WHERE id = ?", (new_state, rule_id))
    return {"id": rule_id, "enabled": bool(new_state)}


@app.delete("/api/automations/{rule_id}")
async def delete_automation(rule_id: str):
    """Delete an automation rule."""
    with get_db() as conn:
        conn.execute("DELETE FROM automation_rules WHERE id = ?", (rule_id,))
    return {"id": rule_id, "status": "deleted"}


@app.post("/api/automations/check")
async def check_automations():
    """Check all enabled automations and execute matching ones."""
    devices = get_all_devices()
    device_map = {d["id"]: d for d in devices}

    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM automation_rules WHERE enabled = 1"
        ).fetchall()

    triggered = []
    for row in rows:
        conditions = json.loads(row["conditions"])
        actions = json.loads(row["actions"])

        # Check all conditions
        all_met = True
        for cond in conditions:
            if not _check_condition(cond, devices, device_map):
                all_met = False
                break

        if all_met:
            # Execute actions
            for act in actions:
                try:
                    execute_action(act["device_id"], act["action"], act.get("parameters", {}))
                    triggered.append({
                        "rule": row["name"],
                        "device": act["device_id"],
                        "action": act["action"],
                    })
                except Exception as e:
                    triggered.append({
                        "rule": row["name"],
                        "device": act["device_id"],
                        "error": str(e),
                    })

    return {"checked": len(rows), "triggered": len(triggered), "actions": triggered}


def _check_condition(cond: dict, devices: list, device_map: dict) -> bool:
    """Check a single automation condition."""
    field = cond["field"]
    op = cond["operator"]
    value = cond["value"]

    # Time condition
    if field == "time":
        now = datetime.utcnow().strftime("%H:%M")
        if op == ">":
            return now > str(value)
        if op == "<":
            return now < str(value)
        if op == ">=":
            return now >= str(value)
        if op == "<=":
            return now <= str(value)
        return now == str(value)

    # Device attribute condition (e.g. "br_sensor_temp.value", "br_sensor_motion.motion")
    parts = field.split(".")
    if len(parts) == 2:
        device_id, attr = parts
        device = device_map.get(device_id)
        if not device:
            return False

        # Check sensor values
        actual = device["attributes"].get(attr)
        if actual is None:
            return False

        try:
            actual = float(actual)
            value = float(value)
        except (ValueError, TypeError):
            pass

        if op == ">":
            return actual > value
        if op == "<":
            return actual < value
        if op == ">=":
            return actual >= value
        if op == "<=":
            return actual <= value
        if op == "==":
            return actual == value
        if op == "!=":
            return actual != value

    return False


# ── Incident Detection ──────────────────────────────────────────────────────

@app.post("/api/incidents/check")
async def check_incidents():
    """Scan sensors for anomalies and create incidents."""
    devices = get_all_devices()
    new_incidents = []

    for d in devices:
        if d["type"] != "sensor":
            continue
        attrs = d["attributes"]

        # Leak detection
        if attrs.get("leak") is True:
            inc_id = add_incident({
                "severity": "critical",
                "title": f"Leak detected in {d['room']}",
                "description": f"Sensor {d['name']} reports water leak",
                "device_id": d["id"],
            })
            new_incidents.append({"id": inc_id, "severity": "critical", "title": f"Leak in {d['room']}"})

        # Smoke detection
        if attrs.get("smoke") is True:
            inc_id = add_incident({
                "severity": "critical",
                "title": f"Smoke detected in {d['room']}",
                "description": f"Sensor {d['name']} reports smoke",
                "device_id": d["id"],
            })
            new_incidents.append({"id": inc_id, "severity": "critical", "title": f"Smoke in {d['room']}"})

        # Door left open
        if attrs.get("open") is True:
            inc_id = add_incident({
                "severity": "warning",
                "title": f"Door open in {d['room']}",
                "description": f"Sensor {d['name']} reports door open",
                "device_id": d["id"],
            })
            new_incidents.append({"id": inc_id, "severity": "warning", "title": f"Door open: {d['room']}"})

        # High temperature
        if attrs.get("unit") == "°C" and isinstance(attrs.get("value"), (int, float)):
            if attrs["value"] > 35:
                inc_id = add_incident({
                    "severity": "warning",
                    "title": f"High temperature in {d['room']}",
                    "description": f"{attrs['value']}°C detected by {d['name']}",
                    "device_id": d["id"],
                })
                new_incidents.append({"id": inc_id, "severity": "warning", "title": f"High temp: {d['room']}"})

    return {"scanned": len(devices), "new_incidents": len(new_incidents), "incidents": new_incidents}


# ── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import uvicorn

    if "--telegram" in sys.argv:
        from .telegram_bot import TelegramBot
        bot = TelegramBot()
        asyncio.run(bot.run_polling())
    else:
        uvicorn.run("app.main:app", host=API_HOST, port=API_PORT, reload=DEBUG)
