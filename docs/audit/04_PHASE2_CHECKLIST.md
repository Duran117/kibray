# PHASE 2 — IMPLEMENTATION & REMEDIATION CHECKLIST

Generated: 2025-11-28

Goal
- Execute initial low-risk remediation and prepare the project for deeper security and functional work (backups, baselines, targeted fixes, CI gating).

Actions (high level)
1. Backup & safety
   - Create a DB backup: `python manage.py dumpdata --natural-foreign --natural-primary > backups/initial_data.json`
   - Export a copy of `db.sqlite3` to `backups/db_backup_YYYYMMDD.sqlite3` (developer to run locally if DB contains secrets)

2. Secrets baseline
   - Generate `./.secrets.baseline` using `detect-secrets` with curated ignores for vendor and .venv directories.
   - Commit `.secrets.baseline` to repo and add CI check to fail only on new secrets.

3. Security remediations (low-risk)
   - Review Bandit findings in `reports/bandit_core.json`; fix obvious issues (e.g., avoid bare excepts where possible).
   - Confirm `requirements.txt` upgrades are pushed (Django, requests) and that `pip-audit` reports clean.

4. Functional checks
   - Run the dev server and validate these flows manually: Task CRUD, Daily Plan → Task conversion, Site Photo upload, Material request flow.
   - Start frontend dev server (`npm install` then `npm run dev`) and verify Gantt and language switcher.

5. Create Issues & PRs
   - Create issues for P0/P1 items in `docs/audit/03_GAPS_BACKLOG.md` (digital signature, payroll advanced rules, inventory valuation).
   - Triage and assign P0 to owner for an architecture spike.

6. CI/Gating
   - Add detect-secrets check with baseline to CI and mark as non-blocking until baseline approved.
   - Add Bandit and pip-audit steps (already present in `.github/workflows/ci.yml`) — iterate if false positives remain.

Notes
- Some checklist steps require running commands locally (DB dump, frontend dev server). Where elevated permissions or secrets exist, do not commit real secrets.
