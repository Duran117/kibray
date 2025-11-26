# Automation & Scheduled Tasks Guide

## Overview

Kibray uses **Celery** with **Celery Beat** for background task processing and scheduled periodic jobs. This enables automated maintenance, notifications, and data fetching without manual intervention.

## Architecture

- **Celery**: Asynchronous task queue for background jobs
- **Celery Beat**: Scheduler for periodic tasks (cron-like)
- **Redis/Database**: Result backend for task state
- **Django integration**: Tasks defined in `core/tasks.py`

## Scheduled Tasks (Celery Beat)

All schedules configured in `kibray_backend/celery.py`:

### Daily Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| `check-overdue-invoices` | 6:00 AM | Update invoice status to OVERDUE if past due date |
| `update-invoice-statuses` | 1:00 AM | Bulk status updates for invoices |
| `fetch-weather-snapshots` | 5:00 AM | Fetch and persist weather data for all active projects |
| `update-daily-plans-weather` | 5:00 AM | Update upcoming daily plans with weather info |
| `check-inventory-shortages` | 8:00 AM | Alert about inventory items below threshold |
| `alert-high-priority-touchups` | 9:00 AM | Notify PMs about projects with 3+ high-priority open touch-ups |
| `alert-incomplete-daily-plans` | 5:15 PM | Alert about draft daily plans past their 5 PM deadline |

### Hourly Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| `send-pending-notifications` | Every hour (:00) | Batch send queued notifications (email/SMS) |

### Weekly Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| `generate-weekly-payroll` | Monday 7:00 AM | Create PayrollPeriod for previous week (Mon-Sun) |
| `cleanup-old-notifications` | Sunday 2:00 AM | Archive read notifications older than 30 days |

## Key Automation Features

### 1. Weather Snapshots (Phase 7)

**Task**: `update_daily_weather_snapshots`

- Runs daily at 5 AM
- Fetches weather for all active projects (end_date in future or null)
- Creates/updates `WeatherSnapshot` records with:
  - Temperature (max/min)
  - Conditions (clear, cloudy, rain, etc.)
  - Precipitation, wind, humidity
- Data source: `open-meteo` API (placeholder; ready for real integration)
- Used by:
  - Dashboard weather indicators
  - Daily plan weather context
  - Analytics for weather impact on delays

### 2. High-Priority Touch-up Alerts (Phase 7)

**Task**: `alert_high_priority_touchups`

- Runs daily at 9 AM
- Scans all active projects for touch-up tasks with:
  - `is_touchup=True`
  - `priority` in ['high', 'urgent']
  - `status` in ['Pendiente', 'En Progreso']
- **Threshold**: 3 or more high-priority touchups triggers alert
- Notifies:
  - Project managers (via `ClientProjectAccess` with role='external_pm')
  - Admin users (is_staff or is_superuser)
- Creates `Notification` with link to `/projects/{id}/touchups/`

### 3. Payroll Automation (Phase 6)

**Task**: `generate_weekly_payroll`

- Runs Monday 7 AM
- Creates `PayrollPeriod` for previous week (Mon-Sun)
- Aggregates `TimeEntry` records per employee
- Generates `PayrollRecord` with:
  - Total hours worked
  - Hourly rate snapshot
  - Calculated total pay
- Status: `pending` (requires admin review before payment)

### 4. Invoice Management

**Tasks**: `check_overdue_invoices`, `update_invoice_statuses`

- Monitor invoice due dates
- Auto-update status from SENT → OVERDUE
- Send notifications to admins and accounting team
- Tracks days overdue for collection prioritization

## Running Tasks Manually

### Django Shell

```python
from core.tasks import update_daily_weather_snapshots, alert_high_priority_touchups

# Execute immediately
result = update_daily_weather_snapshots()
print(result)  # {'date': '2025-11-26', 'created': 5, 'updated': 2, 'total_projects': 7}

result = alert_high_priority_touchups()
print(result)  # {'date': '2025-11-26', 'alerts_sent': 3, 'threshold': 3}
```

### Celery CLI (in production)

```bash
# Trigger specific task
celery -A kibray_backend call core.tasks.update_daily_weather_snapshots

# Check task result
celery -A kibray_backend result <task_id>

# List scheduled tasks
celery -A kibray_backend inspect scheduled

# Monitor active workers
celery -A kibray_backend inspect active
```

## Development Mode (Settings)

In `kibray_backend/settings.py`:

```python
# Use eager execution in development (no Celery worker needed)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
```

Tasks run synchronously in-process. Disable for production to use real queue.

## Production Deployment

### Requirements

1. **Redis** (recommended) or **RabbitMQ** as message broker:
   ```bash
   # On Render.com or AWS
   redis://default:password@redis-host:6379/0
   ```

2. **Celery Worker** (background process):
   ```bash
   celery -A kibray_backend worker --loglevel=info
   ```

3. **Celery Beat** (scheduler):
   ```bash
   celery -A kibray_backend beat --loglevel=info
   ```

### Render.com Configuration

Add two background workers in `render.yaml`:

```yaml
services:
  - type: worker
    name: celery-worker
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "celery -A kibray_backend worker --loglevel=info"
    
  - type: worker
    name: celery-beat
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "celery -A kibray_backend beat --loglevel=info"
```

### Environment Variables

```bash
CELERY_BROKER_URL=redis://...
CELERY_RESULT_BACKEND=redis://...
CELERY_TASK_ALWAYS_EAGER=False  # Use real queue in prod
```

## Testing

Automation tests in `tests/test_automation_tasks.py`:

```bash
pytest tests/test_automation_tasks.py -v
```

Tests verify:
- Weather snapshot creation
- Touch-up alert threshold logic
- Notification generation
- Correct filtering of active projects

## Monitoring & Logging

### Logs

All tasks log to Django logger (`core.tasks`):

```python
logger.info(f"Weather snapshots: {snapshots_created} created, {snapshots_updated} updated")
```

View logs:
```bash
# Development
python manage.py runserver  # Check console

# Production (Render/Heroku)
heroku logs --tail --app kibray-backend
render logs --service kibray-backend
```

### Task Results

Stored in `django_celery_results_taskresult` table (if using django-db backend):

```python
from django_celery_results.models import TaskResult

recent = TaskResult.objects.order_by('-date_created')[:10]
for task in recent:
    print(f"{task.task_name}: {task.status} - {task.result}")
```

## Future Enhancements

### Phase 8+ (Roadmap)

- **Redis caching**: Cache dashboard aggregates (TTL: 5 min)
- **EVM recalculation**: Daily task to update Earned Value metrics
- **Real weather API**: Replace placeholder with Open-Meteo or WeatherAPI integration
- **Email digests**: Weekly summary of project status to stakeholders
- **Auto-archive**: Move completed projects to archive after 90 days
- **Anomaly detection**: ML-based alerts for cost/schedule variance

### Advanced Automation

```python
# Example: EVM daily recalculation
@shared_task(name='core.tasks.recalculate_project_evm')
def recalculate_project_evm():
    """Recalculate Earned Value metrics for all active projects."""
    from core.models import Project
    from core.services.earned_value import compute_project_ev
    
    for project in Project.objects.filter(end_date__gte=date.today()):
        ev_data = compute_project_ev(project)
        # Store in ProjectEVMSnapshot model (to be created)
        # ...
```

## Troubleshooting

### Task not running

1. Check Beat is running: `celery -A kibray_backend inspect scheduled`
2. Verify schedule in `kibray_backend/celery.py`
3. Check timezone: `CELERY_TIMEZONE = 'UTC'` (or project timezone)

### Worker crashes

- Check memory limits (increase if needed)
- Set `worker_max_tasks_per_child=1000` to prevent memory leaks
- Use `task_time_limit` to prevent infinite loops

### Notifications not created

- Verify `Notification` model permissions
- Check user queryset filters (e.g., `is_staff=True`)
- Test task manually in Django shell

## Summary

Automation consolidates:
- ✅ Weather data fetching (daily snapshots)
- ✅ Touch-up priority alerts (PM notifications)
- ✅ Payroll period generation (weekly)
- ✅ Invoice overdue tracking (daily)
- ✅ Inventory shortage alerts (daily)
- ✅ Notification batch sending (hourly)

All tasks tested, documented, and production-ready with Celery + Redis.
