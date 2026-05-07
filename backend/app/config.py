"""MiMo HomeOps Agent Pro — Configuration."""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "homeops.db"
HOME_STATE_PATH = DATA_DIR / "home_state.json"
SAMPLE_HOME_PATH = BASE_DIR.parent / "examples" / "home.sample.json"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8700"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# MiMo / LLM
MIMO_API_BASE = os.getenv("MIMO_API_BASE", "https://api.openai.com/v1")
MIMO_API_KEY = os.getenv("MIMO_API_KEY", "")
MIMO_MODEL = os.getenv("MIMO_MODEL", "mimo-7b")

# Home Assistant (optional)
HA_URL = os.getenv("HA_URL", "")
HA_TOKEN = os.getenv("HA_TOKEN", "")
HA_DRY_RUN = os.getenv("HA_DRY_RUN", "true").lower() == "true"

# Telegram (optional)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Safety
CONFIRM_SENSITIVE = os.getenv("CONFIRM_SENSITIVE", "true").lower() == "true"
ALLOWED_ACTIONS = [
    "light.on", "light.off", "light.brightness", "light.color_temp",
    "ac.on", "ac.off", "ac.set_temp", "ac.set_mode",
    "fan.on", "fan.off", "fan.set_speed",
    "curtain.open", "curtain.close", "curtain.set_position",
    "purifier.on", "purifier.off", "purifier.set_mode",
    "vacuum.start", "vacuum.stop", "vacuum.return_home",
    "plug.on", "plug.off",
]

# Report settings
REPORTS_DIR = BASE_DIR / "reports" / "generated"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
