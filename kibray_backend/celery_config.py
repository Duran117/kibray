# ==============================================
# CELERY CONFIGURATION FOR KIBRAY
# Handles all async tasks: emails, notifications,
# EV calculations, report generation, etc.
# ==============================================

import os

from celery import Celery
from celery.schedules import crontab

# Set default Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kibray_backend.settings")

app = Celery("kibray")

# Load config from Django settings with 'CELERY_' prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# ============================================
# PERIODIC TASKS SCHEDULE
# ============================================

# NOTE: Every entry below MUST reference a real @shared_task defined in
# core/tasks.py. A previous version of this file referenced 12 ghost tasks
# that never existed, so beat fired NotRegistered errors silently for months.
# See docs/CELERY_AUDIT.md (Phase C) for the full audit. If you add a new
# entry, run:
#   python -c "from kibray_backend.celery_config import app; import core.tasks; \
#     [print(n,'->',e['task'] in app.tasks) for n,e in app.conf.beat_schedule.items()]"
app.conf.beat_schedule = {
    # ---- Financial automations ----
    "check-overdue-invoices": {
        "task": "core.tasks.check_overdue_invoices",
        "schedule": crontab(hour=6, minute=0),  # daily 06:00
    },
    "update-invoice-statuses": {
        "task": "core.tasks.update_invoice_statuses",
        "schedule": crontab(hour=1, minute=0),  # daily 01:00 (SENT -> OVERDUE)
    },
    "generate-weekly-payroll": {
        "task": "core.tasks.generate_weekly_payroll",
        "schedule": crontab(hour=7, minute=0, day_of_week=1),  # Monday 07:00
    },
    # ---- Operations / planning ----
    "alert-incomplete-daily-plans": {
        "task": "core.tasks.alert_incomplete_daily_plans",
        "schedule": crontab(hour=17, minute=15),  # daily 17:15 (after 17:00 deadline)
    },
    "check-inventory-shortages": {
        "task": "core.tasks.check_inventory_shortages",
        "schedule": crontab(hour=8, minute=0),  # daily 08:00
    },
    "alert-high-priority-touchups": {
        "task": "core.tasks.alert_high_priority_touchups",
        "schedule": crontab(hour=9, minute=0),  # daily 09:00
    },
    # ---- Weather ingestion ----
    "update-daily-plans-weather": {
        "task": "core.tasks.update_daily_plans_weather",
        "schedule": crontab(hour=5, minute=0),  # daily 05:00
    },
    "fetch-weather-snapshots": {
        "task": "core.tasks.update_daily_weather_snapshots",
        "schedule": crontab(hour=5, minute=0),  # daily 05:00 (parallel to plans)
    },
    # ---- Notifications ----
    "send-pending-notifications": {
        "task": "core.tasks.send_pending_notifications",
        "schedule": crontab(minute=0),  # hourly :00
    },
    "cleanup-old-notifications": {
        "task": "core.tasks.cleanup_old_notifications",
        "schedule": crontab(hour=2, minute=0, day_of_week=0),  # Sunday 02:00
    },
    "generate-daily-plan-reminders": {
        "task": "core.tasks.generate_daily_plan_reminders",
        "schedule": crontab(hour=16, minute=0),  # daily 16:00 (afternoon prep)
    },
    # ---- WebSocket / presence maintenance ----
    "cleanup-stale-user-status": {
        "task": "core.tasks.cleanup_stale_user_status",
        "schedule": 300.0,  # every 5 minutes
        "kwargs": {"threshold_minutes": 5},
    },
    "collect-websocket-metrics": {
        "task": "core.tasks.collect_websocket_metrics",
        "schedule": 900.0,  # every 15 minutes
    },
    "cleanup-old-websocket-metrics": {
        "task": "core.tasks.cleanup_old_websocket_metrics",
        "schedule": crontab(hour=2, minute=30, day_of_week=0),  # Sunday 02:30
    },
    # ---- Resource cleanup ----
    "cleanup-old-assignments": {
        "task": "core.tasks.cleanup_old_assignments",
        "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Sunday 03:00
        "kwargs": {"days": 30},
    },
}

# ============================================
# CELERY CONFIGURATION
# ============================================

app.conf.update(
    # Timezone
    timezone="America/New_York",
    enable_utc=True,
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Task execution
    task_always_eager=False,  # Set True for testing without Redis
    task_eager_propagates=True,
    # Results backend - Memory optimized
    result_expires=1800,  # 30 minutes (reduced from 1 hour)
    result_backend_transport_options={
        "retry_policy": {"max_retries": 3},
    },
    # Task routes
    task_routes={
        "core.tasks.send_email_*": {"queue": "emails"},
        "core.tasks.generate_*": {"queue": "reports"},
        "core.tasks.calculate_*": {"queue": "analytics"},
    },
    # Worker settings - Memory optimized
    worker_prefetch_multiplier=1,  # Reduced from 4 - less memory per worker
    worker_max_tasks_per_child=200,  # Reduced from 1000 - more aggressive restart
    worker_concurrency=2,  # Limit concurrent tasks
    broker_pool_limit=3,  # Limit Redis connections
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to test Celery is working"""
    print(f"Request: {self.request!r}")
