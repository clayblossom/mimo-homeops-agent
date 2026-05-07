# MiMo HomeOps Agent Pro — GitHub Project Plan

Status: idea saved for later continuation via Telegram on vps-1.
Target host: vps-1 AWS worker (ubuntu@54.156.126.227)
Disk target: heavy-but-mepet for current vps-1 root disk; avoid Docker first.

## One-line pitch
MiMo HomeOps Agent Pro is an AI smart-home command center for Xiaomi Home-style ecosystems: it turns natural-language home goals into safe, explainable device actions, automation rules, incident alerts, and daily energy/comfort reports.

## Tagline
An AI command center for Xiaomi smart homes.

## Why this fits Xiaomi MiMo 100T
- Strong Xiaomi ecosystem alignment: smart home, devices, automation.
- Not a generic chatbot: agentic control, state reasoning, scheduling, reports.
- Shows MiMo reasoning/tool-use through real or simulated home devices.
- Demoable without real devices via a Xiaomi Home digital twin simulator.
- Can later connect to real devices via Home Assistant REST API, python-miio, or Xiaomi/Mi Home adapters.

## Recommended scope for vps-1
Build the Pro version, but no local Home Assistant Docker at first.

Included:
1. FastAPI backend
2. React/Vite dashboard
3. SQLite state/history DB
4. Xiaomi Home simulator / digital twin
5. Home Assistant REST connector (optional/live)
6. Telegram command bot
7. Scheduler automation engine
8. MiMo reasoning engine
9. Markdown/HTML report generator
10. Browser QA-light for screenshots/demo only

Avoid initially:
- Local Home Assistant Docker
- Android emulator
- Local ML models
- Video generation
- Long-running browser test cache

## Disk budget
Current target dev usage: 4.5–5.5GB.

Breakdown estimate:
- Backend venv: 700MB–1.2GB
- Frontend node_modules/build: 800MB–1.5GB
- Browser QA/screenshot tooling: 700MB–1.2GB
- DB/log/demo assets: 300MB–800MB
- Repo/docs/screenshots: 200MB–500MB
- Temporary package/build cache: up to 1GB+

Rules to avoid filling disk:
- Screenshot retention max 200 files.
- SQLite auto-vacuum/vacuum command.
- No long videos in repo.
- No Docker in MVP.
- Push to GitHub, then prune caches.
- Do not commit node_modules, venv, .env, logs, DB runtime files, screenshots cache.

## Core features

### 1. Digital Twin Home Simulator
A JSON-backed simulated Xiaomi Home:
- rooms
- lights
- AC/fan
- curtains
- purifier
- vacuum
- plugs
- sensors: temperature, humidity, motion, door, leak/smoke mock

Example state:
- Living Room: 29°C, humid, light on, motion inactive
- Bedroom: 28°C, motion active, AC off
- Purifier: standby
- Curtain: open

### 2. Natural-language control
Examples:
- “Matikan semua lampu kecuali ruang kerja.”
- “Prepare my home for sleep mode, save energy, but keep the bedroom comfortable.”
- “Kalau kamar panas dan ada orang, nyalakan AC 25°C eco dan purifier sleep mode.”

MiMo returns structured action JSON:
- target device
- action
- parameters
- reason
- risk/safety level
- requires_confirmation boolean

### 3. AI Automation Builder
Prompt → automation rule.

Example:
User: “Buat automation supaya kamar nyaman saat malam.”
Output:
IF time > 22:00 AND bedroom_motion = true AND bedroom_temp > 27
THEN AC 25°C eco + purifier sleep + bedroom light warm 20%
Reason: maintain comfort while reducing energy usage.

### 4. Explainable Action Timeline
Each executed action logs:
- timestamp
- command
- device
- before state
- after state
- MiMo explanation
- safety status

### 5. Energy & Comfort Report
Daily/one-shot report:
- active devices
- comfort score
- likely energy waste
- routines that saved energy
- suggested automations

### 6. Incident Mode
For abnormal sensor events:
- leak detected
- smoke detected
- door left open
- device offline
- unusual power usage

Output:
- Telegram alert
- dashboard incident card
- markdown incident report

### 7. Safety Guard
- Dry-run mode by default for live connectors.
- Allowlist actions.
- Confirmation required for sensitive actions.
- Never execute unlock/security/camera/privacy actions without explicit approval.
- Full audit log.

### 8. Home Assistant REST Connector
Optional live bridge:
- list entities
- read states
- call services for safe allowed domains
- map HA entities to internal device schema

## Demo flow
1. Open dashboard.
2. Home digital twin shows simulated Xiaomi smart home.
3. Prompt: “Prepare my home for sleep mode, save energy, but keep the bedroom comfortable.”
4. MiMo plans:
   - turn off living room lights
   - set bedroom AC 25°C eco
   - purifier sleep mode
   - close curtain 80%
   - arm non-sensitive presence/security mock
5. User approves execution.
6. Timeline updates with before/after states and explanations.
7. Telegram sends concise summary.
8. Export GitHub-ready markdown report.

## Architecture
User / Telegram / Web Dashboard
→ FastAPI API
→ MiMo Reasoning Engine
→ Safety Policy + Action Planner
→ Digital Twin Simulator or Home Assistant Connector
→ State Store SQLite
→ Timeline + Reports

## Suggested repository name
mimo-homeops-agent

Alternative names:
- mimo-smarthome-commander
- mimo-home-copilot
- homeops-agent-pro

## Initial folder structure
mimo-homeops-agent/
  backend/
    app/
      main.py
      config.py
      models.py
      db.py
      mimo_client.py
      safety.py
      planner.py
      simulator/
      connectors/
        home_assistant.py
      reports/
      telegram_bot.py
    requirements.txt
  frontend/
    src/
      App.tsx
      api.ts
      components/
      pages/
    package.json
  docs/
    architecture.md
    demo-flow.md
    safety-model.md
  examples/
    home.sample.json
    prompts.md
  scripts/
    run_dev.sh
    cleanup_disk.sh
  README.md
  .gitignore

## MVP milestones

### Milestone 1 — skeleton
- Create repo structure.
- FastAPI health endpoint.
- React dashboard shell.
- SQLite initialized.
- Sample home JSON loaded.

### Milestone 2 — simulator
- Device registry.
- Read/update simulated device state.
- Action timeline.
- Basic dashboard cards.

### Milestone 3 — MiMo planner
- MiMo-compatible API client.
- Prompt → structured JSON action plan.
- Safety validation.
- Dry-run preview.

### Milestone 4 — execute + report
- Execute simulator actions.
- Before/after timeline.
- Markdown report export.
- Energy/comfort daily summary.

### Milestone 5 — Telegram + polish
- Telegram command bot.
- Screenshot/demo assets.
- README with architecture diagram.
- GitHub-ready project description.

### Milestone 6 — optional live connector
- Home Assistant REST connector.
- Entity mapping.
- Dry-run/live toggle.

## README positioning
Title: MiMo HomeOps Agent Pro
Subtitle: AI automation copilot for Xiaomi-style smart homes.

README must include:
- Problem statement
- Solution overview
- Demo GIF/screenshots
- Architecture diagram
- Safety model
- Example prompts
- Local setup
- VPS disk notes
- Roadmap

## Implementation notes for later agent
- Work in ~/workspace/mimo-homeops-agent on vps-1.
- Keep disk cleanup script from day one.
- Use SQLite, not Postgres, for MVP.
- Use simulator-first; do not block on real Xiaomi auth.
- Keep Home Assistant connector optional and dry-run by default.
- Store secrets only in .env, never commit.
- Before installing browser tools, check df -h /.

## GitHub .gitignore essentials
.env
.venv/
venv/
node_modules/
dist/
build/
.next/
*.db
*.sqlite
logs/
runtime/
screenshots/cache/
reports/generated/
__pycache__/
.pytest_cache/
.cache/

## Final recommendation
Build MiMo HomeOps Agent Pro with simulator-first + optional Home Assistant connector. It is heavy enough to be impressive, Xiaomi-aligned, and still feasible on vps-1 if Docker/video/local models are avoided initially.
