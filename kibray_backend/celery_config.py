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

app.conf.beat_schedule = {
    # Calculate Earned Value daily at 6 PM (after employee clock out)
    "calculate-daily-ev": {
        "task": "core.tasks.calculate_all_projects_ev",
        "schedule": crontab(hour=18, minute=0),  # 6:00 PM daily
    },
    # Send invoice reminders for overdue invoices
    "send-invoice-reminders": {
        "task": "core.tasks.send_overdue_invoice_reminders",
        "schedule": crontab(hour=9, minute=0),  # 9:00 AM daily
    },
    # Check for low inventory and send alerts
    "check-low-inventory": {
        "task": "core.tasks.check_inventory_levels",
        "schedule": crontab(hour=8, minute=0),  # 8:00 AM daily
    },
    # Send daily plan notifications to employees
    "send-daily-plan-notifications": {
        "task": "core.tasks.send_daily_plan_notifications",
        "schedule": crontab(hour=6, minute=30),  # 6:30 AM daily
    },
    # Update weather forecasts for active projects
    "update-weather-forecasts": {
        "task": "core.tasks.update_project_weather",
        "schedule": crontab(hour="*/3"),  # Every 3 hours
    },
    # Auto-generate weekly payroll reminders
    "payroll-weekly-reminder": {
        "task": "core.tasks.send_payroll_reminder",
        "schedule": crontab(day_of_week="friday", hour=10, minute=0),  # Friday 10 AM
    },
    # Check for unanswered RFIs and send reminders
    "rfi-followup-reminders": {
        "task": "core.tasks.send_rfi_followup_reminders",
        "schedule": crontab(hour=14, minute=0),  # 2:00 PM daily
    },
    # Cleanup old notifications (keep last 90 days)
    "cleanup-old-notifications": {
        "task": "core.tasks.cleanup_old_notifications",
        "schedule": crontab(day_of_week="sunday", hour=2, minute=0),  # Sunday 2 AM
    },
    # Generate weekly project reports for PMs
    "weekly-project-reports": {
        "task": "core.tasks.generate_weekly_project_reports",
        "schedule": crontab(day_of_week="monday", hour=7, minute=0),  # Monday 7 AM
    },
    # Check for projects without activity and send alerts
    "inactive-project-check": {
        "task": "core.tasks.check_inactive_projects",
        "schedule": crontab(hour=11, minute=0),  # 11:00 AM daily
    },
    # Auto-update change order status based on approval deadlines
    "update-co-deadlines": {
        "task": "core.tasks.update_change_order_deadlines",
        "schedule": crontab(hour=10, minute=30),  # 10:30 AM daily
    },
    # Backup critical data to S3
    "daily-backup": {
        "task": "core.tasks.backup_database_to_s3",
        "schedule": crontab(hour=3, minute=0),  # 3:00 AM daily
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
