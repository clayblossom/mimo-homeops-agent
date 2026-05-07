# Safety Model

## Core Principles

1. **Default Deny** — Only explicitly allowed actions can be executed
2. **Dry-run First** — All plans are previewed before execution
3. **Risk Classification** — Every action gets a risk level
4. **Confirmation Required** — High-risk actions need explicit user approval
5. **Full Audit** — Every action is logged with before/after states

## Risk Levels

| Level | Icon | Description | Examples |
|-------|------|-------------|---------|
| Low | 🟢 | Safe, reversible, common | Light on/off, curtain open/close |
| Medium | 🟡 | Energy impact, comfort change | AC set temp, purifier mode |
| High | 🔴 | Autonomous movement, significant | Vacuum start |
| Critical | ⛔ | Security/privacy sensitive | Camera on, door unlock |

## Allowed Actions

The system maintains an allowlist of safe actions:

**Lights**: on, off, brightness, color_temp
**AC**: on, off, set_temp (16-30°C), set_mode
**Fan**: on, off, set_speed
**Curtain**: open, close, set_position
**Purifier**: on, off, set_mode
**Vacuum**: start, stop, return_home
**Plug**: on, off

## Blocked Actions (always rejected)

- Camera on/off/record
- Door lock/unlock
- Security system arm/disarm
- Any action not in the allowlist

## Confirmation Flow

```
User request → MiMo plan → Safety validation
                                │
                    ┌───────────┼───────────┐
                    │           │           │
                 All low     Some high    Critical
                    │           │           │
                 Auto-execute  Ask confirm  Always ask
```

## Dry-Run Mode

By default, all requests are dry-run. The system shows:
1. What actions would be executed
2. Risk level for each action
3. Reasoning for each action
4. Which actions need confirmation

User must explicitly set `dry_run: false` and `confirm: true` to execute.

## Home Assistant Safety

When connected to real devices:
- **Always dry-run by default** (`HA_DRY_RUN=true`)
- Only call services for allowed domains
- Never execute security-sensitive HA services
- Log all HA API calls

## Incident Detection

The simulator monitors sensors for:
- Leak detected → CRITICAL incident
- Smoke detected → CRITICAL incident
- Door left open → WARNING
- Device offline → INFO
- High temperature → WARNING
- Unusual power usage → WARNING

Incidents trigger:
1. Dashboard alert card
2. Timeline entry
3. Optional Telegram notification
