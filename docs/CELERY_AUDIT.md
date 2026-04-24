# Celery Tasks Audit (Phase C — Automation)

**Date:** 2026-04-24  
**Scope:** `core/tasks.py`, `kibray_backend/celery_config.py`, `kibray_backend/celery.py`  
**Outcome:** 1 critical bug found and fixed, 1 dead-code module removed,
beat_schedule consolidated to reference only real tasks.

---

## TL;DR

| Item | Status |
|---|---|
| Celery app modules found | **2** (one was dead code) |
| Real `@shared_task` definitions in `core/tasks.py` | 21 |
| Active beat_schedule entries (before) | 12 — **all referenced non-existent tasks** |
| Active beat_schedule entries (after) | 13 — all reference real, registered tasks |
| Dead modules removed | `kibray_backend/celery.py` |
| Tests after change | 1,271 passed, 0 regressions |

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

### Final beat_schedule (13 entries, all verified)

| Schedule | Task | Cadence |
|---|---|---|
| check-overdue-invoices | `check_overdue_invoices` | daily 06:00 |
| alert-incomplete-daily-plans | `alert_incomplete_daily_plans` | daily 17:15 |
| generate-weekly-payroll | `generate_weekly_payroll` | Mon 07:00 |
| check-inventory-shortages | `check_inventory_shortages` | daily 08:00 |
| send-pending-notifications | `send_pending_notifications` | hourly :00 |
| update-invoice-statuses | `update_invoice_statuses` | daily 01:00 |
| update-daily-plans-weather | `update_daily_plans_weather` | daily 05:00 |
| fetch-weather-snapshots | `update_daily_weather_snapshots` | daily 05:00 |
| alert-high-priority-touchups | `alert_high_priority_touchups` | daily 09:00 |
| cleanup-old-notifications | `cleanup_old_notifications` | Sun 02:00 |
| cleanup-stale-user-status | `cleanup_stale_user_status` | every 5 min |
| cleanup-old-assignments | `cleanup_old_assignments` | Sun 03:00 |
| collect-websocket-metrics | `collect_websocket_metrics` | every 15 min |

## 4. Inventory of all 21 Real Tasks

Source: `core/tasks.py` (1,388 LOC). Status after fix:

| # | Task | Status | Notes |
|---|---|---|---|
| 1 | `check_inventory_shortages` | 🟢 scheduled | daily 08:00 |
| 2 | `check_overdue_invoices` | 🟢 scheduled | daily 06:00 |
| 3 | `alert_incomplete_daily_plans` | 🟢 scheduled | daily 17:15 |
| 4 | `generate_weekly_payroll` | 🟢 scheduled | Mon 07:00 |
| 5 | `update_daily_weather_snapshots` | 🟢 scheduled | daily 05:00 |
| 6 | `alert_high_priority_touchups` | 🟢 scheduled | daily 09:00 |
| 7 | `update_daily_weather_snapshots_legacy` | ⚠️ legacy orphan | candidate for deletion next pass |
| 8 | `send_pending_notifications` | 🟢 scheduled | hourly |
| 9 | `update_invoice_statuses` | 🟢 scheduled | daily 01:00 |
| 10 | `cleanup_old_notifications` | 🟢 scheduled | Sun 02:00 |
| 11 | `generate_daily_plan_reminders` | ⚠️ orphan | not scheduled, no callsites — review intended use |
| 12 | `update_daily_plans_weather` | 🟢 scheduled | daily 05:00 |
| 13 | `fetch_weather_for_plan` | 🔵 on-demand | called from `DailyPlan.save()` |
| 14 | `cleanup_stale_user_status` | 🟢 scheduled | every 5 min |
| 15 | `send_websocket_notification` | 🔵 on-demand candidate | currently no callsites — review |
| 16 | `collect_websocket_metrics` | 🟢 scheduled | every 15 min (now) |
| 17 | `cleanup_old_websocket_metrics` | ⚠️ orphan | not scheduled — TODO add weekly entry |
| 18 | `process_signature_post_tasks` | 🔵 on-demand | called from `misc_views.py`, `changeorder_views.py` |
| 19 | `cleanup_old_assignments` | 🟢 scheduled | Sun 03:00 |
| 20 | `process_sop_image` | 🔵 on-demand | called from `sop_api.py` |
| 21 | `process_changeorder_photos` | ⚠️ orphan | not scheduled, no callsites — review |

Legend: 🟢 scheduled · 🔵 on-demand (real callsite) · ⚠️ orphan (not wired)

## 5. Remaining Backlog (non-blocking)

1. **Decide fate of orphans** (4 tasks, ~150 LOC):
   - `update_daily_weather_snapshots_legacy` — explicit "legacy" in name; safe to delete
     after one release cycle of confirmation.
   - `generate_daily_plan_reminders` — review intent vs. `send_pending_notifications`.
   - `send_websocket_notification` — likely meant to be invoked from signals; verify.
   - `process_changeorder_photos` — likely meant to mirror `process_sop_image`; check
     ChangeOrder photo upload flow.
   - `cleanup_old_websocket_metrics` — add weekly schedule (Sun 02:30).
2. **Split `core/tasks.py` (1,388 LOC)** by domain (financial, weather, notifications,
   websocket, processing). Currently a single hard-to-navigate file.
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
