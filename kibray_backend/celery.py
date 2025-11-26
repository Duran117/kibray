"""
Celery configuration for Kibray construction management system.
Enables asynchronous task processing and scheduled periodic tasks.
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kibray_backend.settings')

# Create Celery app
app = Celery('kibray')

# Load config from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Configure periodic tasks (beat schedule)
app.conf.beat_schedule = {
    # Check for overdue invoices daily at 6 AM
    'check-overdue-invoices': {
        'task': 'core.tasks.check_overdue_invoices',
        'schedule': crontab(hour=6, minute=0),
    },
    
    # Check incomplete daily plans at 5:15 PM (after 5 PM deadline)
    'alert-incomplete-daily-plans': {
        'task': 'core.tasks.alert_incomplete_daily_plans',
        'schedule': crontab(hour=17, minute=15),
    },
    
    # Generate weekly payroll periods on Monday at 7 AM
    'generate-weekly-payroll': {
        'task': 'core.tasks.generate_weekly_payroll',
        'schedule': crontab(hour=7, minute=0, day_of_week=1),  # Monday
    },
    
    # Check inventory shortages daily at 8 AM
    'check-inventory-shortages': {
        'task': 'core.tasks.check_inventory_shortages',
        'schedule': crontab(hour=8, minute=0),
    },
    
    # Send pending notifications every hour
    'send-pending-notifications': {
        'task': 'core.tasks.send_pending_notifications',
        'schedule': crontab(minute=0),  # Every hour at :00
    },
    
    # Update invoice statuses (SENT -> OVERDUE) daily at 1 AM
    'update-invoice-statuses': {
        'task': 'core.tasks.update_invoice_statuses',
        'schedule': crontab(hour=1, minute=0),
    },
    
    # Update weather data for upcoming daily plans at 5 AM
    'update-daily-plans-weather': {
        'task': 'core.tasks.update_daily_plans_weather',
        'schedule': crontab(hour=5, minute=0),
    },
    
    # Fetch weather snapshots for all active projects at 5 AM (before daily plans)
    'fetch-weather-snapshots': {
        'task': 'core.tasks.update_daily_weather_snapshots',
        'schedule': crontab(hour=5, minute=0),
    },
    
    # Alert about high-priority touch-ups daily at 9 AM
    'alert-high-priority-touchups': {
        'task': 'core.tasks.alert_high_priority_touchups',
        'schedule': crontab(hour=9, minute=0),
    },
    
    # Cleanup old notifications weekly on Sunday at 2 AM
    'cleanup-old-notifications': {
        'task': 'core.tasks.cleanup_old_notifications',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Sunday
    },
}

# Celery configuration
app.conf.update(
    # Result backend (use Redis or database)
    result_backend='django-db',
    
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
    
    # Task execution
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max per task
    task_soft_time_limit=25 * 60,  # Soft limit at 25 minutes
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Test task for debugging Celery configuration"""
    print(f'Request: {self.request!r}')
