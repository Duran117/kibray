# Celery Tasks Audit (Phase C — Automation)

**Date:** 2026-04-24 (Pass 2: orphan resolution)
**Scope:** `core/tasks.py`, `kibray_backend/celery_config.py`
**Outcome:** Pass 1 fixed 12 ghost tasks + removed dead duplicate app.
Pass 2 resolved orphans: 1 deleted, 2 newly scheduled, 2 confirmed as
on-demand utilities.

---

## TL;DR (post Pass 2)

| Item | Status |
|---|---|
| Real `@shared_task` definitions in `core/tasks.py` | **22** (was 23, deleted 1 legacy) |
| Active beat_schedule entries | **15** (was 13 in Pass 1) |
| On-demand tasks with real callsites | 5 |
| On-demand utilities (no callers yet) | 2 (kept, flagged) |
| True orphans remaining | **0** |
| Tests after change | **1280 passed**, 17 skipped, 0 regressions |

---

## 1. Critical Finding — Ghost beat_schedule

`kibray_backend/__init__.py` loads `celery_config.py`:

```python
from .celery_config import app as celery_app
```

`celery_config.py` defined a `beat_schedule` with **12 entries**, all pointing to
task names that **do not exist** anywhere in the codebase:

| Beat entry | Task name | Real? |
|---|---|---|
| calculate-daily-ev | `core.tasks.calculate_all_projects_ev` | ❌ |
| send-invoice-reminders | `core.tasks.send_overdue_invoice_reminders` | ❌ |
| check-low-inventory | `core.tasks.check_inventory_levels` | ❌ |
| send-daily-plan-notifications | `core.tasks.send_daily_plan_notifications` | ❌ |
| update-weather-forecasts | `core.tasks.update_project_weather` | ❌ |
| payroll-weekly-reminder | `core.tasks.send_payroll_reminder` | ❌ |
| rfi-followup-reminders | `core.tasks.send_rfi_followup_reminders` | ❌ |
| cleanup-old-notifications | `core.tasks.cleanup_old_notifications` | ✅ |
| weekly-project-reports | `core.tasks.generate_weekly_project_reports` | ❌ |
| inactive-project-check | `core.tasks.check_inactive_projects` | ❌ |
| update-co-deadlines | `core.tasks.update_change_order_deadlines` | ❌ |
| daily-backup | `core.tasks.backup_database_to_s3` | ❌ |

**Effect in production:** every time celery-beat fired one of these (every few
minutes/hours), the worker logged `NotRegistered` and silently dropped the job.
Eleven scheduled automations that never ran since this file was introduced.

`grep` proves the names appear ONLY in `celery_config.py` and nowhere else
(no `.delay()` / `.apply_async()` callsites either).

## 2. Critical Finding — Duplicate Celery App (Dead Code)

`kibray_backend/celery.py` defined a **second** `Celery("kibray")` app with a
DIFFERENT `beat_schedule` containing **13 entries that DO reference real tasks**.
But nothing imports it — `__init__.py` only loads `celery_config.py`.

So we had:
- The "good" schedule (real tasks) sitting in dead code, never executed.
- The "bad" schedule (ghost tasks) loaded and dispatching to nowhere.

## 3. Fix Applied

1. **Deleted** `kibray_backend/celery.py` (dead module, never imported).
2. **Rewrote** `celery_config.py::beat_schedule` to reference only real tasks,
   merging the useful entries from the deleted file.

### Final beat_schedule (15 entries, all verified)

| Schedule | Task | Cadence |
|---|---|---|
| check-overdue-invoices | `check_overdue_invoices` | daily 06:00 |
| update-invoice-statuses | `update_invoice_statuses` | daily 01:00 |
| generate-weekly-payroll | `generate_weekly_payroll` | Mon 07:00 |
| alert-incomplete-daily-plans | `alert_incomplete_daily_plans` | daily 17:15 |
| check-inventory-shortages | `check_inventory_shortages` | daily 08:00 |
| alert-high-priority-touchups | `alert_high_priority_touchups` | daily 09:00 |
| update-daily-plans-weather | `update_daily_plans_weather` | daily 05:00 |
| fetch-weather-snapshots | `update_daily_weather_snapshots` | daily 05:00 |
| send-pending-notifications | `send_pending_notifications` | hourly :00 |
| cleanup-old-notifications | `cleanup_old_notifications` | Sun 02:00 |
| **generate-daily-plan-reminders** *(new Pass 2)* | `generate_daily_plan_reminders` | **daily 16:00** |
| cleanup-stale-user-status | `cleanup_stale_user_status` | every 5 min |
| collect-websocket-metrics | `collect_websocket_metrics` | every 15 min |
| **cleanup-old-websocket-metrics** *(new Pass 2)* | `cleanup_old_websocket_metrics` | **Sun 02:30** |
| cleanup-old-assignments | `cleanup_old_assignments` | Sun 03:00 |

## 4. Inventory of all 22 Real Tasks (post Pass 2)

Source: `core/tasks.py`. Status legend:
🟢 scheduled · 🔵 on-demand (real callsite) · ⚪ on-demand utility (no callers yet, kept intentionally)

| # | Task | Status | Notes |
|---|---|---|---|
| 1 | `check_inventory_shortages` | 🟢 | daily 08:00 |
| 2 | `check_overdue_invoices` | 🟢 | daily 06:00 |
| 3 | `alert_incomplete_daily_plans` | 🟢 | daily 17:15 |
| 4 | `generate_weekly_payroll` | 🟢 | Mon 07:00 |
| 5 | `update_daily_weather_snapshots` | 🟢 | daily 05:00 |
| 6 | `alert_high_priority_touchups` | 🟢 | daily 09:00 |
| 7 | `send_pending_notifications` | 🟢 | hourly |
| 8 | `update_invoice_statuses` | 🟢 | daily 01:00 |
| 9 | `cleanup_old_notifications` | 🟢 | Sun 02:00 |
| 10 | `generate_daily_plan_reminders` | 🟢 | **Pass 2: scheduled daily 16:00** |
| 11 | `update_daily_plans_weather` | 🟢 | daily 05:00 |
| 12 | `fetch_weather_for_plan` | 🔵 | called from `DailyPlan.save()` |
| 13 | `cleanup_stale_user_status` | 🟢 | every 5 min |
| 14 | `send_websocket_notification` | ⚪ | utility for signals/views; no current callers — keep |
| 15 | `collect_websocket_metrics` | 🟢 | every 15 min |
| 16 | `cleanup_old_websocket_metrics` | 🟢 | **Pass 2: scheduled Sun 02:30** |
| 17 | `process_signature_post_tasks` | 🔵 | `misc_views.py`, `changeorder_views.py` |
| 18 | `cleanup_old_assignments` | 🟢 | Sun 03:00 |
| 19 | `process_sop_image` | 🔵 | `sop_api.py` |
| 20 | `process_changeorder_photos` | ⚪ | utility for CO photo flow; no current callers — keep |
| 21 | `process_changeorder_creation` | 🔵 | `changeorder_views.py:518` |
| 22 | `process_contract_generation` | 🔵 | `financial_views.py:1172,1223` |

**Removed in Pass 2:** `update_daily_weather_snapshots_legacy` — Module 30
skeleton with placeholder logic, fully superseded by
`update_daily_weather_snapshots`.

## 5. Remaining Backlog (non-blocking)

1. **Wire the two on-demand utilities** (`send_websocket_notification`,
   `process_changeorder_photos`) when their respective UI flows land,
   or delete them if the UI is no longer planned.
2. **Split `core/tasks.py`** (now 1,355 LOC) by domain
   (financial / weather / notifications / websocket / processing).
3. **Add task-level metrics** to Sentry / Prometheus once observability is wired.
4. **Add a beat-schedule integration test** that imports the celery app and asserts
   every entry's `task` field resolves to a registered task — would have caught this
   bug at CI time.

## 6. Verification

```bash
# Confirm no NotRegistered tasks in beat_schedule
python -c "
from kibray_backend.celery_config import app
import core.tasks  # noqa: ensure tasks register
registered = set(app.tasks.keys())
for name, entry in app.conf.beat_schedule.items():
    task = entry['task']
    assert task in registered, f'GHOST: {name} -> {task}'
    print(f'OK  {name:35} -> {task}')
print('All beat entries resolve to registered tasks.')
"

# Full test suite — no regressions
python -m pytest -q --no-cov
# expected: 1271 passed, 17 skipped
```
