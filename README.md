<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/4059a283-9495-49ec-b516-c2d43a6ac1ec" />
# MiMo HomeOps Agent Pro

AI automation copilot for Xiaomi-style smart homes.

Turn natural-language home goals into safe, explainable device actions, automation rules, incident alerts, and daily energy/comfort reports.

## Features

- 🏠 **Digital Twin Simulator** — 19 virtual Xiaomi devices across 5 rooms
- 🤖 **Natural Language Control** — "Prepare my home for sleep mode" → structured action plan
- 🔒 **Safety Guard** — Risk classification, action allowlist, confirmation for sensitive ops
- 📊 **Energy & Comfort Reports** — Daily analysis with waste alerts and savings suggestions
- 📱 **Interactive Dashboard** — React/Vite with real-time device controls (toggle, sliders)
- 💬 **Telegram Bot** — Control your home via chat commands
- 🏷️ **Explainable Timeline** — Before/after states with MiMo reasoning
- 🔌 **Home Assistant Connector** — Optional bridge to real devices (dry-run by default)

## Quick Start

```bash
# Clone
git clone <repo-url>
cd mimo-homeops-agent

# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy env template
cp ../.env.example .env
# Edit .env with your settings

# Run backend
uvicorn app.main:app --host 0.0.0.0 --port 8700 --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Environment Variables

See `.env.example` for all options. Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `MIMO_API_KEY` | (empty) | LLM API key (uses heuristic planner if empty) |
| `MIMO_API_BASE` | OpenAI | LLM API endpoint |
| `TELEGRAM_BOT_TOKEN` | (empty) | Telegram bot token |
| `TELEGRAM_CHAT_ID` | (empty) | Telegram chat ID |
| `HA_URL` | (empty) | Home Assistant URL |
| `HA_TOKEN` | (empty) | Home Assistant long-lived token |
| `HA_DRY_RUN` | true | Dry-run mode for HA connector |

## Telegram Bot Setup

1. Create a bot via @BotFather
2. Get the token
3. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`
4. Run: `python -m app.main --telegram`

### Bot Commands

- `/status` — Home summary
- `/devices` — List all devices
- `/timeline` — Recent actions
- `/report` — Daily energy report
- `/incidents` — Active incidents
- `/sleep` — Activate sleep mode
- `/lights` — Turn off all lights
- `/energy` — Energy saving mode

Or send natural language: "Kamar panas, nyalakan AC 25°C"

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/home/summary` | Home state summary |
| GET | `/api/devices` | List all devices |
| GET | `/api/devices/{id}` | Device detail |
| POST | `/api/devices/{id}/action` | Execute device action |
| POST | `/api/chat` | Natural language control |
| GET | `/api/timeline` | Action timeline |
| GET | `/api/incidents` | Incident list |
| GET | `/api/reports/daily` | Energy & comfort report |

## Example Prompts

```
Prepare my home for sleep mode, save energy, but keep the bedroom comfortable.
Matikan semua lampu kecuali ruang kerja.
Kamar panas, nyalakan AC 25°C eco.
Hemat energi, matikan yang tidak perlu.
Apa status rumah sekarang?
```

## Architecture

```
User / Telegram / Web Dashboard
  → FastAPI API
  → MiMo Reasoning Engine (LLM or heuristic)
  → Safety Policy + Action Planner
  → Digital Twin Simulator or Home Assistant Connector
  → State Store (SQLite)
  → Timeline + Reports
```

See `docs/architecture.md` for the full diagram.

## Project Structure

```
mimo-homeops-agent/
  backend/
    app/
      main.py              — FastAPI endpoints
      config.py            — Environment config
      models.py            — Pydantic models
      db.py                — SQLite layer
      mimo_client.py       — LLM client + heuristic planner
      safety.py            — Safety guard
      simulator/           — Digital twin
      connectors/          — Home Assistant bridge
      reports/             — Report generator
      telegram_bot/        — Telegram bot
    requirements.txt
  frontend/
    src/
      App.tsx              — Main app with tabs
      api.ts               — API client
      components/          — UI components
      pages/               — Reports page
    package.json
  docs/                    — Architecture, demo flow, safety
  examples/                — Sample home JSON, prompts
  scripts/                 — Dev runner, disk cleanup
```

## Disk Notes (VPS)

Target: ~5GB total. Avoid Docker, local ML models, video generation.

```bash
# Cleanup
./scripts/cleanup_disk.sh
```

## Roadmap

- [x] Milestone 1: Project skeleton
- [x] Milestone 2: Simulator + interactive dashboard controls
- [x] Milestone 3: MiMo planner + safety validation
- [x] Milestone 4: Execute + timeline + reports
- [x] Milestone 5: Telegram bot + polish
- [ ] Milestone 6: Home Assistant live connector

## License

MIT
