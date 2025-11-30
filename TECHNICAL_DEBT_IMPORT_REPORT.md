# Technical Debt Import Report

Date: November 29, 2025
Command: `python manage.py import_technical_debt`

## Summary
- Scanned repository for TODO/FIXME/PENDING/BUG across .py, .html, .js, .css
- Exclusions: `.venv/`, `node_modules/`, `__pycache__/`, `core/migrations/`, `core/management/commands/`, `frontend/dist/`
- Found 61 tagged comments, 41 unique titles
- Created 41 PowerActions under LifeVision "System Perfection"
- Each task is linked to a Daily Ritual Session for today and includes micro-steps

## Implementation Notes
- PowerActions use the Strategic Planning models:
  - `linked_vision` set to LifeVision "System Perfection"
  - `session` set to the default user's DailyRitualSession for today (auto-created if missing)
  - `status` initialized as `DRAFT`
  - `micro_steps` format: `{ "text": string, "done": boolean }`

## Re-run / Maintenance
- Dry run (no DB writes):
  - `python manage.py import_technical_debt --dry-run`
- Full run:
  - `python manage.py import_technical_debt`
- Deduplication is by PowerAction title; titles already present are skipped.

## Next Steps
- Migrate any remaining silenced `print(...)` to structured logging via Python `logging` and Django log config.
- Optional CI check: add a lightweight job to scan the repo and report counts of TODO/FIXME/PENDING/BUG on PRs.
- Periodically re-run this importer to capture new technical debt into actionable tasks.

## Troubleshooting
- Ensure virtualenv Python path is used when running commands:
  - `/Users/jesus/Documents/kibray/.venv/bin/python manage.py import_technical_debt`
- If no users exist, LifeVision creation may fail; create an admin user or seed a default user.
