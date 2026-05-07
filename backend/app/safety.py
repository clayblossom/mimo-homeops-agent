"""MiMo HomeOps Agent Pro — Safety guard module."""
from __future__ import annotations

from typing import Any

from .config import ALLOWED_ACTIONS, CONFIRM_SENSITIVE
from .models import DeviceAction


# ── Risk classification ─────────────────────────────────────────────────────

HIGH_RISK_ACTIONS = {
    "vacuum.start",  # autonomous movement
}

SENSITIVE_ACTIONS = {
    # Security/privacy actions that always need confirmation
    "camera.on", "camera.record",
    "lock.unlock", "lock.lock",
}

MEDIUM_RISK_ACTIONS = {
    "ac.set_temp",  # energy impact
    "purifier.set_mode",
}


def classify_risk(action: str) -> str:
    """Classify the risk level of an action."""
    if action in SENSITIVE_ACTIONS:
        return "critical"
    if action in HIGH_RISK_ACTIONS:
        return "high"
    if action in MEDIUM_RISK_ACTIONS:
        return "medium"
    return "low"


def requires_confirmation(action: str) -> bool:
    """Check if an action requires user confirmation."""
    if action in SENSITIVE_ACTIONS:
        return True
    if CONFIRM_SENSITIVE and action in HIGH_RISK_ACTIONS:
        return True
    return False


# ── Validation ──────────────────────────────────────────────────────────────

class SafetyViolation(Exception):
    """Raised when an action violates safety policy."""
    pass


def validate_action(action: DeviceAction) -> DeviceAction:
    """
    Validate an action against safety policies.
    Returns the action with risk_level and requires_confirmation set.
    Raises SafetyViolation for blocked actions.
    """
    # Check allowlist
    if action.action not in ALLOWED_ACTIONS:
        raise SafetyViolation(
            f"Action '{action.action}' is not in the allowed actions list. "
            f"Blocked for safety."
        )

    # Set risk level
    action.risk_level = classify_risk(action.action)

    # Check confirmation requirement
    if requires_confirmation(action.action):
        action.requires_confirmation = True

    return action


def validate_plan(actions: list[DeviceAction]) -> tuple[list[DeviceAction], list[str]]:
    """
    Validate a full action plan.
    Returns (validated_actions, warnings).
    """
    validated = []
    warnings = []

    for action in actions:
        try:
            validated.append(validate_action(action))
        except SafetyViolation as e:
            warnings.append(f"❌ {action.device_id}: {e}")

    return validated, warnings


# ── Dry-run preview ─────────────────────────────────────────────────────────

def dry_run_summary(actions: list[DeviceAction]) -> str:
    """Generate a human-readable dry-run summary."""
    lines = ["🔍 **Dry Run Preview:**\n"]
    for i, action in enumerate(actions, 1):
        risk_icon = {"low": "🟢", "medium": "🟡", "high": "🔴", "critical": "⛔"}.get(
            action.risk_level, "⚪"
        )
        confirm = " ⚠️ *needs confirmation*" if action.requires_confirmation else ""
        lines.append(
            f"{i}. {risk_icon} `{action.device_id}` → {action.action}"
            + (f" ({action.parameters})" if action.parameters else "")
            + f"\n   💡 {action.reason}{confirm}"
        )
    return "\n".join(lines)
