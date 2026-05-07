"""MiMo HomeOps Agent Pro — Telegram Bot."""
from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx

from ..config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from ..mimo_client import plan_actions
from ..safety import validate_plan, dry_run_summary
from ..simulator import execute_action, get_home_summary, get_all_devices
from ..reports import generate_daily_report
from ..db import get_timeline, get_incidents


class TelegramBot:
    """Simple Telegram bot for home control."""

    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.offset = 0

    async def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Send a message to the configured chat."""
        if not self.token or not self.chat_id:
            print("[telegram] Bot not configured, skipping message")
            return False

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                },
            )
            return resp.status_code == 200

    async def get_updates(self) -> list[dict]:
        """Get new messages from Telegram."""
        if not self.token:
            return []

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self.base_url}/getUpdates",
                params={"offset": self.offset, "timeout": 25},
            )
            if resp.status_code != 200:
                return []

            data = resp.json()
            if not data.get("ok"):
                return []

            updates = data.get("result", [])
            if updates:
                self.offset = updates[-1]["update_id"] + 1
            return updates

    async def handle_message(self, message: dict) -> str:
        """Process a Telegram message and return a response."""
        text = message.get("text", "").strip()
        if not text:
            return ""

        # ── Commands ──
        if text.startswith("/"):
            return await self._handle_command(text)

        # ── Natural language ──
        return await self._handle_chat(text)

    async def _handle_command(self, cmd: str) -> str:
        """Handle slash commands."""
        cmd = cmd.lower().split()[0]  # Take first word

        if cmd in ("/start", "/help"):
            return (
                "🏠 *MiMo HomeOps Agent Pro*\n\n"
                "Available commands:\n"
                "/status — Home summary\n"
                "/devices — List all devices\n"
                "/timeline — Recent actions\n"
                "/report — Daily energy report\n"
                "/incidents — Active incidents\n"
                "/sleep — Activate sleep mode\n"
                "/lights — Turn off all lights\n"
                "/energy — Energy saving mode\n\n"
                "Or just tell me what you want! 🤖\n"
                "Example: _Kamar panas, nyalakan AC_"
            )

        if cmd == "/status":
            return self._format_home_summary()

        if cmd == "/devices":
            return self._format_devices()

        if cmd == "/timeline":
            return self._format_timeline()

        if cmd == "/report":
            return self._format_report()

        if cmd == "/incidents":
            return self._format_incidents()

        if cmd == "/sleep":
            return await self._handle_chat("Prepare my home for sleep mode")

        if cmd == "/lights":
            return await self._handle_chat("Matikan semua lampu")

        if cmd == "/energy":
            return await self._handle_chat("Hemat energi, matikan yang tidak perlu")

        return f"Unknown command: {cmd}\nTry /help"

    async def _handle_chat(self, message: str) -> str:
        """Handle natural language with MiMo planner."""
        home_state = get_home_summary()

        try:
            plan = await plan_actions(message, home_state, dry_run=True)
        except Exception as e:
            return f"❌ Error: {e}"

        if not plan.actions:
            return plan.summary

        validated, warnings = validate_plan(plan.actions)
        if not validated:
            return f"❌ No valid actions:\n" + "\n".join(warnings)

        # Execute all actions
        results = []
        for action in validated:
            try:
                execute_action(action.device_id, action.action, action.parameters)
                results.append(f"✅ {action.device_id} → {action.action}")
            except Exception as e:
                results.append(f"❌ {action.device_id}: {e}")

        response_parts = [
            f"🤖 *{plan.summary}*",
            "",
            *results,
        ]
        if warnings:
            response_parts.append("\n⚠️ " + "; ".join(warnings))

        return "\n".join(response_parts)

    def _format_home_summary(self) -> str:
        home = get_home_summary()
        lines = [
            f"🏠 *{home['home_name']}*",
            f"📊 {home['total_devices']} devices, {home['active_devices']} active",
            "",
        ]

        for room, devices in home["rooms"].items():
            lines.append(f"*{room}*")
            for d in devices:
                icon = {"light": "💡", "ac": "❄️", "fan": "🌀", "curtain": "🪟",
                        "purifier": "🌬️", "vacuum": "🤖", "plug": "🔌", "sensor": "📡"}.get(d["type"], "❓")
                status = d["status"]
                if status in ("ON", "CLEANING"):
                    status = f"*{status}*"
                lines.append(f"  {icon} {d['name']}: {status}")
            lines.append("")

        if home["sensor_alerts"]:
            lines.append("⚠️ *Alerts*")
            for alert in home["sensor_alerts"]:
                lines.append(f"  {alert}")

        return "\n".join(lines)

    def _format_devices(self) -> str:
        devices = get_all_devices()
        by_type: dict[str, list] = {}
        for d in devices:
            by_type.setdefault(d["type"], []).append(d)

        lines = ["📱 *All Devices*\n"]
        for dtype, devs in by_type.items():
            lines.append(f"*{dtype}* ({len(devs)})")
            for d in devs:
                attrs = d["attributes"]
                status = "ON" if attrs.get("on", attrs.get("cleaning", False)) else "OFF"
                if d["type"] == "sensor":
                    status = ", ".join(f"{k}={v}" for k, v in list(attrs.items())[:2])
                lines.append(f"  • {d['name']} ({d['room']}): {status}")
            lines.append("")

        return "\n".join(lines)

    def _format_timeline(self) -> str:
        entries = get_timeline(limit=10)
        if not entries:
            return "📋 No actions yet."

        lines = ["📋 *Recent Actions*\n"]
        for e in entries:
            risk = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(e["risk_level"], "⚪")
            lines.append(f"{risk} {e['device_name']} → {e['action']}")
            if e["explanation"]:
                lines.append(f"   _{e['explanation']}_")
        return "\n".join(lines)

    def _format_report(self) -> str:
        report = generate_daily_report()
        s = report["summary"]
        lines = [
            f"📊 *Daily Report — {report['date']}*",
            "",
            f"🏠 {s['total_devices']} devices, {s['active_devices']} active",
            f"🌡️ Comfort: {s['comfort_score']}/100",
            f"⚡ Actions today: {s['actions_today']}",
            f"🚨 Incidents: {s['incidents']}",
        ]

        if report["energy_waste_alerts"]:
            lines.append("\n⚠️ *Energy Waste*")
            for alert in report["energy_waste_alerts"][:3]:
                lines.append(f"  {alert}")

        if report["savings_suggestions"]:
            lines.append("\n💡 *Suggestions*")
            for sug in report["savings_suggestions"][:3]:
                lines.append(f"  {sug}")

        return "\n".join(lines)

    def _format_incidents(self) -> str:
        incidents = get_incidents(limit=10, unresolved_only=False)
        if not incidents:
            return "🚨 No incidents."

        lines = ["🚨 *Incidents*\n"]
        for inc in incidents:
            icon = {"info": "ℹ️", "warning": "⚠️", "critical": "🔴"}.get(inc.get("severity", "info"), "❓")
            resolved = " ✅" if inc.get("resolved") else ""
            lines.append(f"{icon} {inc['title']}{resolved}")
            if inc.get("description"):
                lines.append(f"   {inc['description']}")
        return "\n".join(lines)

    async def run_polling(self):
        """Run the bot in polling mode."""
        if not self.token:
            print("[telegram] No bot token configured, skipping")
            return

        print(f"[telegram] Bot started, polling for updates...")
        await self.send_message("🤖 MiMo HomeOps Agent Pro is online!")

        while True:
            try:
                updates = await self.get_updates()
                for update in updates:
                    message = update.get("message", {})
                    if not message:
                        continue

                    response = await self.handle_message(message)
                    if response:
                        await self.send_message(response)

            except Exception as e:
                print(f"[telegram] Error: {e}")
                await asyncio.sleep(5)
