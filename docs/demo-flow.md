# Demo Flow

## Quick Demo (2 minutes)

### Step 1: Open Dashboard
Navigate to `http://localhost:5173` — the React dashboard shows the digital twin home.

### Step 2: View Home State
Dashboard displays 5 rooms with real-time device states:
- Living Room: Light ON (80%), AC OFF, Temp 29.5°C
- Bedroom: Light OFF, AC OFF, Curtain OPEN, Motion detected
- Kitchen: Light ON, Leak sensor OK
- Study Room: Desk Light ON, Fan ON (speed 3)
- Hallway: Purifier OFF, Door sensor OK

### Step 3: Natural Language Control
Type in the chat box:
```
Prepare my home for sleep mode, save energy, but keep the bedroom comfortable.
```

### Step 4: MiMo Plans
The AI generates a structured plan:
1. 🟢 Living Room Light → OFF (sleep mode)
2. 🟢 Kitchen Light → OFF (sleep mode)
3. 🟢 Study Room Light → OFF (sleep mode)
4. 🟢 Hallway Light → OFF (sleep mode)
5. 🟢 Bedroom AC → ON, 25°C (comfort)
6. 🟢 Purifier → ON, sleep mode (air quality + quiet)
7. 🟢 Bedroom Curtain → CLOSED (darkness for sleep)

### Step 5: Review & Confirm
Dashboard shows dry-run preview with:
- Each action with risk level (🟢 low)
- Reasoning for each action
- Energy impact estimate

### Step 6: Execute
User clicks "Execute" — all actions run on the simulator.

### Step 7: Timeline Updates
Action timeline shows:
- Before/after state for each device
- MiMo explanation for each action
- Timestamp and risk classification

### Step 8: Export Report
Click "Export Report" to generate a markdown summary:
```markdown
## MiMo HomeOps Report — 2024-01-15 22:30

### Actions Executed (7)
- Living Room Light: ON → OFF (sleep mode)
- Bedroom AC: OFF → ON, 25°C (comfort)
...

### Energy Impact
- 4 lights turned off: ~200W saved
- AC set to eco: optimized cooling
- Purifier sleep mode: reduced power
```

## Alternative Prompts

| Prompt | Expected Behavior |
|--------|-------------------|
| "Matikan semua lampu kecuali ruang kerja" | All lights off except Study Room |
| "Kamar panas, nyalakan AC" | AC turns on in hot rooms |
| "Hemat energi" | Unnecessary plugs off, AC to eco |
| "Ada kebocoran?" | Check leak sensor status |
| "Status rumah" | Full home summary |

## Telegram Demo

Send commands to the bot:
```
/status          — Home summary
/sleep           — Sleep mode
/lights off      — All lights off
/energy          — Energy report
/plan <prompt>   — Custom plan
```
