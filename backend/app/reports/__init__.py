"""MiMo HomeOps Agent Pro — Energy & Comfort Report Generator."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config import REPORTS_DIR
from ..db import get_all_devices, get_timeline, get_incidents


def generate_daily_report(date_str: str | None = None) -> dict[str, Any]:
    """Generate an energy & comfort report for the given date."""
    if not date_str:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")

    devices = get_all_devices()
    timeline = get_timeline(limit=200)
    incidents = get_incidents(limit=50, unresolved_only=False)

    # ── Active devices analysis ──
    active_devices = []
    inactive_devices = []
    for d in devices:
        if d["type"] == "sensor":
            continue
        attrs = d["attributes"]
        is_on = attrs.get("on", attrs.get("cleaning", False))
        if is_on:
            active_devices.append(d)
        else:
            inactive_devices.append(d)

    # ── Energy waste detection ──
    waste_alerts = []
    for d in active_devices:
        attrs = d["attributes"]
        room = d["room"]

        # AC running with no motion detected
        if d["type"] == "ac" and attrs.get("on"):
            motion_sensor = _find_sensor(devices, room, "motion")
            if motion_sensor and not motion_sensor["attributes"].get("motion", False):
                waste_alerts.append(
                    f"❄️ {room} AC is ON but no motion detected — consider turning off"
                )

        # Light on in empty room
        if d["type"] == "light" and attrs.get("on"):
            motion_sensor = _find_sensor(devices, room, "motion")
            if motion_sensor and not motion_sensor["attributes"].get("motion", False):
                waste_alerts.append(
                    f"💡 {room} light is ON but no motion detected"
                )

        # AC set very low
        if d["type"] == "ac" and attrs.get("temperature", 25) < 22:
            waste_alerts.append(
                f"❄️ {room} AC set to {attrs['temperature']}°C — very low, high energy usage"
            )

        # High brightness in daytime (rough check)
        if d["type"] == "light" and attrs.get("brightness", 100) > 90:
            waste_alerts.append(
                f"💡 {room} light at {attrs['brightness']}% — consider reducing for energy savings"
            )

    # ── Comfort score ──
    comfort_score = _calculate_comfort_score(devices)

    # ── Savings suggestions ──
    suggestions = []
    if waste_alerts:
        suggestions.append("Create automation to turn off devices in empty rooms")
    for d in devices:
        if d["type"] == "ac" and d["attributes"].get("temperature", 25) > 26:
            suggestions.append(f"Consider setting {d['room']} AC to eco mode (26°C+)")
            break
    if not suggestions:
        suggestions.append("Your home is running efficiently! 👍")

    # ── Timeline summary ──
    actions_today = len(timeline)

    report = {
        "date": date_str,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_devices": len(devices),
            "active_devices": len(active_devices),
            "inactive_devices": len(inactive_devices),
            "actions_today": actions_today,
            "comfort_score": comfort_score,
            "incidents": len(incidents),
        },
        "active_devices": [
            {"name": d["name"], "room": d["room"], "type": d["type"]}
            for d in active_devices
        ],
        "energy_waste_alerts": waste_alerts,
        "comfort_details": _comfort_details(devices),
        "savings_suggestions": suggestions,
        "recent_actions": timeline[:10],
        "incidents": incidents[:5],
    }

    return report


def _find_sensor(devices: list[dict], room: str, sensor_keyword: str) -> dict | None:
    for d in devices:
        if d["room"] == room and d["type"] == "sensor" and sensor_keyword in d["id"]:
            return d
    return None


def _calculate_comfort_score(devices: list[dict]) -> float:
    """Calculate a comfort score 0-100 based on temperature, humidity, air quality."""
    scores = []

    for d in devices:
        if d["type"] != "sensor":
            continue
        attrs = d["attributes"]

        # Temperature comfort (ideal: 23-26°C)
        if "value" in attrs and attrs.get("unit") == "°C":
            temp = attrs["value"]
            if 23 <= temp <= 26:
                scores.append(100)
            elif 20 <= temp < 23 or 26 < temp <= 28:
                scores.append(75)
            elif 18 <= temp < 20 or 28 < temp <= 30:
                scores.append(50)
            else:
                scores.append(25)

        # Humidity comfort (ideal: 40-60%)
        if "value" in attrs and attrs.get("unit") == "%":
            hum = attrs["value"]
            if 40 <= hum <= 60:
                scores.append(100)
            elif 30 <= hum < 40 or 60 < hum <= 70:
                scores.append(70)
            else:
                scores.append(40)

    return round(sum(scores) / len(scores), 1) if scores else 75.0


def _comfort_details(devices: list[dict]) -> list[dict]:
    """Get detailed comfort readings from sensors."""
    details = []
    for d in devices:
        if d["type"] != "sensor":
            continue
        attrs = d["attributes"]
        if "value" in attrs:
            details.append({
                "room": d["room"],
                "sensor": d["name"],
                "value": attrs["value"],
                "unit": attrs.get("unit", ""),
                "status": _comfort_status(attrs["value"], attrs.get("unit", "")),
            })
    return details


def _comfort_status(value: float, unit: str) -> str:
    if unit == "°C":
        if 23 <= value <= 26:
            return "ideal"
        elif 20 <= value <= 28:
            return "acceptable"
        return "uncomfortable"
    if unit == "%":
        if 40 <= value <= 60:
            return "ideal"
        elif 30 <= value <= 70:
            return "acceptable"
        return "uncomfortable"
    return "ok"


def save_report(report: dict[str, Any]) -> Path:
    """Save report as JSON and markdown."""
    date_str = report["date"]

    # Save JSON
    json_path = REPORTS_DIR / f"report_{date_str}.json"
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    # Save Markdown
    md_path = REPORTS_DIR / f"report_{date_str}.md"
    md = _render_markdown(report)
    with open(md_path, "w") as f:
        f.write(md)

    return md_path


def _render_markdown(report: dict[str, Any]) -> str:
    s = report["summary"]
    lines = [
        f"# MiMo HomeOps Report — {report['date']}",
        f"",
        f"*Generated: {report['generated_at']}*",
        f"",
        f"## Summary",
        f"- **Total devices**: {s['total_devices']}",
        f"- **Active devices**: {s['active_devices']}",
        f"- **Actions today**: {s['actions_today']}",
        f"- **Comfort score**: {s['comfort_score']}/100",
        f"- **Incidents**: {s['incidents']}",
        f"",
    ]

    if report["active_devices"]:
        lines.append("## Active Devices")
        for d in report["active_devices"]:
            lines.append(f"- {d['room']}: {d['name']} ({d['type']})")
        lines.append("")

    if report["energy_waste_alerts"]:
        lines.append("## ⚠️ Energy Waste Alerts")
        for alert in report["energy_waste_alerts"]:
            lines.append(f"- {alert}")
        lines.append("")

    if report["comfort_details"]:
        lines.append("## Comfort Details")
        for c in report["comfort_details"]:
            icon = "🟢" if c["status"] == "ideal" else "🟡" if c["status"] == "acceptable" else "🔴"
            lines.append(f"- {icon} {c['room']} {c['sensor']}: {c['value']}{c['unit']} ({c['status']})")
        lines.append("")

    if report["savings_suggestions"]:
        lines.append("## 💡 Savings Suggestions")
        for sug in report["savings_suggestions"]:
            lines.append(f"- {sug}")
        lines.append("")

    if report.get("incidents"):
        lines.append("## 🚨 Incidents")
        for inc in report["incidents"]:
            lines.append(f"- [{inc.get('severity', 'info')}] {inc.get('title', '')} — {inc.get('description', '')}")
        lines.append("")

    lines.append("---")
    lines.append("*Report by MiMo HomeOps Agent Pro*")
    return "\n".join(lines)
