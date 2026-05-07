"""MiMo HomeOps Agent Pro — Main FastAPI application."""
from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import API_HOST, API_PORT, DEBUG
from .db import init_db, get_timeline, get_incidents
from .models import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    DeviceAction,
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
    version="0.1.0",
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
        version="0.1.0",
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


# ── Direct Device Control ───────────────────────────────────────────────────

@app.post("/api/devices/{device_id}/action")
async def device_action(device_id: str, action: str, parameters: dict | None = None):
    """Directly execute an action on a device (for dashboard controls)."""
    from .models import DeviceAction as DA
    da = DA(device_id=device_id, action=action, parameters=parameters or {})
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


# ── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import uvicorn

    if "--telegram" in sys.argv:
        # Run Telegram bot
        from .telegram_bot import TelegramBot
        bot = TelegramBot()
        asyncio.run(bot.run_polling())
    else:
        uvicorn.run("app.main:app", host=API_HOST, port=API_PORT, reload=DEBUG)
