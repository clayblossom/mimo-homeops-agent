# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interfaces                         │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ Telegram │  │ Web Dashboard│  │ API (curl/scripts)    │  │
│  │   Bot    │  │  React/Vite  │  │                       │  │
│  └────┬─────┘  └──────┬───────┘  └───────────┬───────────┘  │
│       │               │                      │              │
│       └───────────────┼──────────────────────┘              │
│                       │                                     │
│              ┌────────▼────────┐                            │
│              │   FastAPI API   │                            │
│              │   (port 8700)   │                            │
│              └────────┬────────┘                            │
│                       │                                     │
│       ┌───────────────┼───────────────┐                     │
│       │               │               │                     │
│  ┌────▼─────┐  ┌──────▼──────┐  ┌────▼──────┐             │
│  │  Safety  │  │   MiMo      │  │ Scheduler │             │
│  │  Guard   │  │  Planner    │  │  Engine   │             │
│  └────┬─────┘  └──────┬──────┘  └────┬──────┘             │
│       │               │               │                     │
│       └───────────────┼───────────────┘                     │
│                       │                                     │
│       ┌───────────────┼───────────────┐                     │
│       │               │               │                     │
│  ┌────▼─────┐  ┌──────▼──────┐  ┌────▼──────┐             │
│  │ Digital  │  │ Home Assst. │  │  SQLite   │             │
│  │  Twin    │  │ Connector   │  │   DB      │             │
│  │Simulator │  │ (optional)  │  │           │             │
│  └──────────┘  └─────────────┘  └───────────┘             │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### FastAPI API (`backend/app/main.py`)
- REST endpoints for home state, devices, chat, timeline, incidents
- CORS enabled for frontend
- Lifespan initializes DB and simulator

### Safety Guard (`backend/app/safety.py`)
- Validates all actions against allowlist
- Classifies risk levels (low/medium/high/critical)
- Blocks dangerous actions
- Requires confirmation for sensitive actions

### MiMo Planner (`backend/app/mimo_client.py`)
- Sends user message + home state to LLM
- Parses structured action plan JSON
- Falls back to heuristic planner when no API key

### Digital Twin Simulator (`backend/app/simulator/`)
- JSON-backed virtual Xiaomi smart home
- 5 rooms, 18 devices (lights, AC, fans, curtains, purifier, vacuum, plugs, sensors)
- Executes actions by updating device attributes
- Logs all actions to timeline

### Home Assistant Connector (`backend/app/connectors/home_assistant.py`)
- Optional bridge to real HA instance
- REST API calls (list entities, read states, call services)
- Dry-run by default

### SQLite (`backend/app/db.py`)
- Tables: device_states, timeline, automation_rules, incidents
- WAL mode for concurrent reads

## Data Flow

1. User sends natural-language request (via chat API, Telegram, or dashboard)
2. MiMo planner generates structured action plan
3. Safety guard validates each action
4. If dry-run: preview actions to user
5. If confirmed: execute on simulator or HA connector
6. Log before/after states to timeline
7. Return result with explanation

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLite
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **LLM**: MiMo-compatible API (OpenAI chat completions format)
- **Optional**: Home Assistant REST API, Telegram Bot API
