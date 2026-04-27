"""
Celery tasks for Kibray construction management system.
Handles automated background jobs and scheduled maintenance tasks.

Created during comprehensive automation implementation.
"""

from datetime import date, timedelta
from decimal import Decimal
import logging

from celery import shared_task
from django.conf import settings
from django.db.models import Q, Sum
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name="core.tasks.check_inventory_shortages")
def check_inventory_shortages():
    """
    Check for low inventory levels and send alerts.
    Runs daily at 8 AM.

    Scans all active items with thresholds, aggregates quantities
    across all locations, and creates notifications for items below threshold.
    """
    from django.contrib.auth import get_user_model
    from django.db.models import Q

    from core.models import InventoryItem, Notification, ProjectInventory

    user_model = get_user_model()
    from datetime import date as _date

    today = _date.today()

    # Get active items with thresholds
    items = InventoryItem.objects.filter(active=True, no_threshold=False).filter(
        Q(low_stock_threshold__isnull=False) | Q(default_threshold__isnull=False)
    )

    low_stock_items = []

    for item in items:
        threshold = item.get_effective_threshold()
        if not threshold:
            continue

        # Get total quantity across all locations
        total_qty = ProjectInventory.objects.filter(item=item).aggregate(total=Sum("quantity"))[
            "total"
        ] or Decimal("0")

        if total_qty < threshold:
            shortage = threshold - total_qty
            low_stock_items.append(
                {
                    "item": item,
                    "current_qty": total_qty,
                    "threshold": threshold,
                    "shortage": shortage,
                }
            )

    # Send notifications to admins and managers
    if low_stock_items:
        recipients = user_model.objects.filter(Q(is_staff=True) | Q(is_superuser=True))

        # Create summary notification
        item_list = ", ".join(
            [
                f"{item_data['item'].name} ({item_data['current_qty']}/{item_data['threshold']})"
                for item_data in low_stock_items[:5]  # First 5 items
            ]
        )

        if len(low_stock_items) > 5:
            item_list += f" ... and {len(low_stock_items) - 5} more"

        for user in recipients:
            Notification.objects.create(
                user=user,
                notification_type="task_alert",
                title=f"Low Inventory Alert: {len(low_stock_items)} items",
                message=f"Items below threshold: {item_list}",
                link_url="/inventory/",
                related_object_type="inventory",
                related_object_id=None,
            )

    logger.info(f"Inventory check: {len(low_stock_items)} items below threshold")

    return {
        "date": str(today),
        "low_stock_count": len(low_stock_items),
        "items_checked": items.count(),
    }


@shared_task(name="core.tasks.check_overdue_invoices")
def check_overdue_invoices():
    """
    Check for overdue invoices and update their status.
    Runs daily at 6 AM.

    Updates invoices with status SENT/VIEWED/APPROVED to OVERDUE
    if they're past their due date.
    """
    from core.models import Invoice

    # Use timezone.localdate() to align with Django's configured local date and tests
    # Compute both local date and naive date to cover test environments that use date.today()
    local_today = timezone.localdate()
    date.today()
    # Use local_today as primary, but also ensure snapshots exist for naive_today if different
    today = local_today

    # Find invoices that are past due date and not yet marked overdue
    overdue_invoices = Invoice.objects.filter(
        due_date__lt=today, status__in=["SENT", "VIEWED", "APPROVED", "PARTIAL"]
    )

    count = 0
    for invoice in overdue_invoices:
        # Calculate days overdue
        days_overdue = (today - invoice.due_date).days

        # Update status
        invoice.status = "OVERDUE"
        invoice.save(update_fields=["status"])

        # Send notification to admin
        try:
            from core.notifications import notify_invoice_overdue

            notify_invoice_overdue(invoice, days_overdue)
        except Exception as e:
            logger.error(f"Failed to send overdue notification for invoice {invoice.id}: {e}")

        count += 1

    logger.info(f"Marked {count} invoices as OVERDUE")
    return {"updated": count, "date": str(today)}


@shared_task(name="core.tasks.alert_incomplete_daily_plans")
def alert_incomplete_daily_plans():
    """
    Alert about daily plans not completed before deadline (5 PM day before).
    Runs at 5:15 PM daily.

    Finds DRAFT plans past their completion deadline and sends alerts.
    """
    from django.contrib.auth import get_user_model

    from core.models import DailyPlan, Notification

    user_model = get_user_model()
    now = timezone.now()

    # Find overdue draft plans
    overdue_plans = DailyPlan.objects.filter(
        status="DRAFT", completion_deadline__lt=now
    ).select_related("project", "created_by")

    count = 0
    for plan in overdue_plans:
        # Notify creator and admins
        recipients = [plan.created_by] if plan.created_by else []
        admins = user_model.objects.filter(Q(is_staff=True) | Q(is_superuser=True))
        recipients.extend(admins)

        for user in set(recipients):
            Notification.objects.create(
                user=user,
                notification_type="alert",
                title=f"Daily Plan Overdue: {plan.project.name}",
                message=f"Daily plan for {plan.plan_date} was due at 5 PM yesterday and is still in DRAFT status.",
                link_url=f"/daily-plan/{plan.id}/edit/",
            )

        count += 1

    logger.info(f"Sent alerts for {count} overdue daily plans")
    return {"alerted": count, "time": str(now)}


@shared_task(name="core.tasks.generate_weekly_payroll")
def generate_weekly_payroll():
    """
    Generate PayrollPeriod records for the previous week.
    Runs on Monday at 7 AM.

    Creates payroll period for Mon-Sun of previous week,
    aggregates time entries, and creates PayrollRecord for each employee.
    """
    from django.contrib.auth import get_user_model

    from core.models import Employee, PayrollPeriod, PayrollRecord, TimeEntry

    user_model = get_user_model()
    today = date.today()

    # Calculate previous week (Mon-Sun)
    days_since_monday = today.weekday()
    last_monday = today - timedelta(days=days_since_monday + 7)
    last_sunday = last_monday + timedelta(days=6)

    # Check if period already exists
    existing = PayrollPeriod.objects.filter(week_start=last_monday, week_end=last_sunday).first()

    if existing:
        logger.info(f"Payroll period for {last_monday} - {last_sunday} already exists")
        return {"status": "exists", "period_id": existing.id}

    # Get first admin user as creator
    creator = user_model.objects.filter(Q(is_superuser=True) | Q(is_staff=True)).first()

    # Create payroll period
    period = PayrollPeriod.objects.create(
        week_start=last_monday, week_end=last_sunday, status="pending", created_by=creator
    )

    # Create records for each active employee
    employees = Employee.objects.filter(is_active=True)
    records_created = 0

    for employee in employees:
        # Aggregate time entries
        time_entries = TimeEntry.objects.filter(
            employee=employee, date__range=(last_monday, last_sunday)
        )

        total_hours = sum(entry.hours_worked or 0 for entry in time_entries)

        # Create payroll record
        PayrollRecord.objects.create(
            period=period,
            employee=employee,
            week_start=last_monday,
            week_end=last_sunday,
            hourly_rate=employee.hourly_rate,
            total_hours=total_hours,
            total_pay=total_hours * employee.hourly_rate,
            reviewed=False,
        )

        records_created += 1

    logger.info(f"Created payroll period {period.id} with {records_created} records")
    return {
        "period_id": period.id,
        "week": f"{last_monday} - {last_sunday}",
        "records": records_created,
    }


@shared_task(name="core.tasks.update_daily_weather_snapshots")
def update_daily_weather_snapshots():
    """
    Fetch and persist weather data for all active projects.
    Runs daily at 5 AM (before daily plan updates).

    Creates WeatherSnapshot records using Open-Meteo API.
    Uses project latitude/longitude (from address geocoding) for accuracy.
    Falls back to default coordinates if address is not geocoded.
    """
    import logging

    from django.db.models import Q
    import requests

    from core.models import Project, WeatherSnapshot

    logger = logging.getLogger(__name__)

    # Compute both local and naive dates
    local_today = timezone.localdate()
    date.today()
    # Use local_today as primary
    today = local_today

    # Only active projects: no end date or end date in the future
    active_projects = Project.objects.filter(Q(end_date__isnull=True) | Q(end_date__gte=today))

    snapshots_created = 0
    snapshots_updated = 0
    project_snapshot_ids = {}
    errors = []

    for project in active_projects:
        # Fetch weather first; only create/update snapshot on success
        try:
            # Get coordinates (default to San Francisco Bay Area if not set)
            # In production, use geocoding service to convert project.address → lat/lon
            latitude = getattr(project, "latitude", 37.7749)  # Default: SF
            longitude = getattr(project, "longitude", -122.4194)

            # Open-Meteo API call (free, no API key required)
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "windspeed_10m_max",
                    "weathercode",
                ],
                "timezone": "America/Los_Angeles",
                "forecast_days": 1,  # Only today
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            api_data = response.json()
            daily = api_data.get("daily", {})

            # Weather code mapping (WMO Weather interpretation codes)
            # https://open-meteo.com/en/docs#weathervariables
            weather_codes = {
                0: "Clear sky",
                1: "Mainly clear",
                2: "Partly cloudy",
                3: "Overcast",
                45: "Foggy",
                48: "Depositing rime fog",
                51: "Light drizzle",
                53: "Moderate drizzle",
                55: "Dense drizzle",
                61: "Slight rain",
                63: "Moderate rain",
                65: "Heavy rain",
                71: "Slight snow",
                73: "Moderate snow",
                75: "Heavy snow",
                77: "Snow grains",
                80: "Slight rain showers",
                81: "Moderate rain showers",
                82: "Violent rain showers",
                85: "Slight snow showers",
                86: "Heavy snow showers",
                95: "Thunderstorm",
                96: "Thunderstorm with slight hail",
                99: "Thunderstorm with heavy hail",
            }

            # Extract data (indices [0] for today)
            temp_max = daily.get("temperature_2m_max", [None])[0]
            temp_min = daily.get("temperature_2m_min", [None])[0]
            precipitation = daily.get("precipitation_sum", [0])[0]
            wind_speed = daily.get("windspeed_10m_max", [0])[0]
            weather_code = daily.get("weathercode", [0])[0]

            conditions_text = weather_codes.get(weather_code, "Unknown")

            # Calculate humidity estimate (not provided by free tier)
            # Use heuristic: higher precipitation → higher humidity
            if precipitation > 5:
                humidity_estimate = 80
            elif precipitation > 1:
                humidity_estimate = 65
            else:
                humidity_estimate = 50

            weather_data = {
                "temperature_max": temp_max,
                "temperature_min": temp_min,
                "conditions_text": conditions_text,
                "precipitation_mm": precipitation,
                "wind_kph": wind_speed * 1.60934,  # Convert km/h to mph (or keep as km/h)
                "humidity_percent": humidity_estimate,
                "weather_code": weather_code,
                "latitude": latitude,
                "longitude": longitude,
            }
        except (requests.RequestException, Exception) as e:
            logger.error(f"Weather API error for {project.name}: {e}")
            errors.append(f"{project.name}: {str(e)}")
            # Skip snapshot creation on API error per tests
            continue

        # Create or update snapshot for today
        snapshot, created = WeatherSnapshot.objects.update_or_create(
            project=project,
            date=today,
            source="open-meteo",
            defaults={
                "temperature_max": weather_data["temperature_max"],
                "temperature_min": weather_data["temperature_min"],
                "conditions_text": weather_data["conditions_text"],
                "precipitation_mm": weather_data["precipitation_mm"],
                "wind_kph": weather_data["wind_kph"],
                "humidity_percent": weather_data["humidity_percent"],
                "raw_json": weather_data,
                "provider_url": f"https://open-meteo.com/en/docs?latitude={weather_data['latitude']}&longitude={weather_data['longitude']}",
            },
        )
        project_snapshot_ids[project.id] = snapshot.id
        if created:
            snapshots_created += 1
        else:
            snapshots_updated += 1

    logger.info(f"Weather snapshots: {snapshots_created} created, {snapshots_updated} updated")
    if errors:
        logger.warning(f"Weather fetch errors: {len(errors)} projects failed")

    # Return summary with convenience snapshot id
    latest_snapshot = (
        WeatherSnapshot.objects.filter(date=today).order_by("-fetched_at", "-id").first()
    )
    return {
        "date": str(today),
        "created": snapshots_created,
        "updated": snapshots_updated,
        "total_projects": active_projects.count(),
        "errors": errors,
        "snapshot_id": latest_snapshot.id if latest_snapshot else None,
        "project_snapshot_ids": project_snapshot_ids,
    }


@shared_task(name="core.tasks.alert_high_priority_touchups")
def alert_high_priority_touchups():
    """
    Alert project managers about high-priority open touch-ups.
    Runs daily at 9 AM.

    Scans all projects for touch-up tasks with priority=high/urgent
    that are still pending or in progress. Sends notifications if
    count exceeds threshold (default: 3).
    """
    from django.contrib.auth import get_user_model
    from django.db.models import Q

    from core.models import Notification, Project

    user_model = get_user_model()
    threshold = 3  # Alert if 3+ high-priority touchups

    today = timezone.now().date()

    # Get active projects
    active_projects = Project.objects.filter(Q(end_date__isnull=True) | Q(end_date__gte=today))

    alerts_sent = 0

    for project in active_projects:
        # Count high-priority open touch-ups
        high_priority_touchups = project.tasks.filter(
            is_touchup=True,
            priority__in=["high", "urgent"],
            status__in=["Pending", "In Progress"],
        )

        touchup_count = high_priority_touchups.count()

    if touchup_count >= threshold:
        # Get project managers and admins
        recipients = []

        # Find users with PM role who have access to this project
        try:
            from core.models import ClientProjectAccess

            pm_accesses = ClientProjectAccess.objects.filter(
                project=project, role="external_pm"
            ).select_related("user")
            recipients.extend([access.user for access in pm_accesses])
        except Exception:
            pass

        # Add admin users
        admins = user_model.objects.filter(Q(is_staff=True) | Q(is_superuser=True))
        recipients.extend(admins)

        # Remove duplicates
        recipients = list(set(recipients))

        # Create notifications
        for user in recipients:
            Notification.objects.create(
                user=user,
                notification_type="task_alert",
                title=f"High-Priority Touch-ups Alert: {project.name}",
                message=f"{touchup_count} high-priority touch-up tasks require attention.",
                link_url=f"/projects/{project.id}/touchups/",
                related_object_type="project",
                related_object_id=project.id,
            )

        alerts_sent += len(recipients)
        logger.info(
            f"Sent {len(recipients)} alerts for {touchup_count} touchups in project {project.id}"
        )

    return {"date": str(today), "alerts_sent": alerts_sent, "threshold": threshold}


# NOTE: `update_daily_weather_snapshots_legacy` was removed on 2026-04-24
# (Phase C). It was a Module 30 skeleton with placeholder logic
# ("will later persist to model") and was fully superseded by
# `update_daily_weather_snapshots` (line ~260) which writes to a real
# DailyWeatherSnapshot model. No callsites and not in beat_schedule.
# See docs/CELERY_AUDIT.md.


@shared_task(name="core.tasks.send_pending_notifications")
def send_pending_notifications():
    """
    Send pending email notifications.
    Runs every hour.

    Finds unsent notifications and sends them via email.
    """
    from core.models import Notification
    from core.services.email_service import KibrayEmailService

    # Get notifications marked for email but not yet sent
    pending = Notification.objects.filter(
        sent_via_email=False,
        created_at__gte=timezone.now() - timedelta(hours=24),  # Last 24h only
    ).select_related("user")[:100]  # Batch of 100

    sent_count = 0
    error_count = 0

    for notification in pending:
        try:
            email_sent = KibrayEmailService.send_simple_notification(
                to_emails=[notification.user.email],
                subject=notification.title,
                message=notification.message,
                fail_silently=False,
            )

            if email_sent:
                notification.sent_via_email = True
                notification.save(update_fields=["sent_via_email"])
                sent_count += 1
            else:
                error_count += 1

        except Exception as e:
            logger.error(f"Failed to send email notification {notification.id}: {e}")
            error_count += 1

    logger.info(f"Sent {sent_count} email notifications, {error_count} errors")
    return {"sent": sent_count, "errors": error_count}


@shared_task(name="core.tasks.update_invoice_statuses")
def update_invoice_statuses():
    """
    Update invoice statuses based on due dates.
    Runs daily at 1 AM.
    """
    from core.models import Invoice

    today = timezone.now().date()
    updated = 0

    # Mark as OVERDUE if past due and still active
    invoices = Invoice.objects.filter(
        due_date__lt=today, status__in=["SENT", "VIEWED", "APPROVED", "PARTIAL"]
    )

    for invoice in invoices:
        invoice.status = "OVERDUE"
        invoice.save(update_fields=["status"])
        updated += 1

    logger.info(f"Updated {updated} invoice statuses to OVERDUE")
    return {"updated": updated}


@shared_task(name="core.tasks.cleanup_old_notifications")
def cleanup_old_notifications():
    """
    Delete old read notifications to keep database clean.
    Runs weekly on Sunday at 2 AM.

    Deletes notifications older than 30 days that have been read.
    """
    from core.models import Notification

    cutoff = timezone.now() - timedelta(days=30)

    deleted_count, _ = Notification.objects.filter(is_read=True, created_at__lt=cutoff).delete()

    logger.info(f"Deleted {deleted_count} old notifications")
    return {"deleted": deleted_count, "cutoff": str(cutoff)}


@shared_task(name="core.tasks.generate_daily_plan_reminders")
def generate_daily_plan_reminders():
    """
    Send reminders for tomorrow's daily plans.
    Runs at 4 PM daily.
    """
    from core.models import DailyPlan, Notification

    tomorrow = timezone.now().date() + timedelta(days=1)

    # Get plans for tomorrow
    plans = (
        DailyPlan.objects.filter(plan_date=tomorrow, status__in=["SUBMITTED", "APPROVED"])
        .select_related("project")
        .prefetch_related("assigned_employees")
    )

    sent = 0
    for plan in plans:
        # Notify assigned employees
        for employee in plan.assigned_employees.all():
            if hasattr(employee, "user") and employee.user:
                Notification.objects.create(
                    user=employee.user,
                    notification_type="reminder",
                    title=f"Tomorrow: {plan.project.name}",
                    message=f"You have {plan.activities.count()} activities scheduled for tomorrow at {plan.project.address}",
                    link_url="/employee/morning/",
                )
                sent += 1

    logger.info(f"Sent {sent} daily plan reminders for {tomorrow}")
    return {"sent": sent, "date": str(tomorrow)}


@shared_task(name="core.tasks.update_daily_plans_weather")
def update_daily_plans_weather():
    """
    Update weather data for upcoming daily plans.
    Runs daily at 5 AM.

    Fetches weather for:
    - Today's plans without recent weather data
    - Tomorrow's plans without weather data

    Uses WeatherService with cache, rate limiting, and circuit breaker.
    """
    from core.models import DailyPlan

    now = timezone.now()
    today = now.date()
    tomorrow = today + timedelta(days=1)

    # Target plans: today and tomorrow, not in SKIPPED/CANCELLED
    target_plans = DailyPlan.objects.filter(
        plan_date__in=[today, tomorrow], status__in=["DRAFT", "PUBLISHED", "IN_PROGRESS"]
    ).select_related("project")

    updated = 0
    skipped_no_address = 0
    skipped_stale = 0
    errors = 0

    for plan in target_plans:
        # Skip if no project address (can't geocode)
        if not plan.project.address:
            skipped_no_address += 1
            continue

        # Check if weather data is recent (< 2 hours old)
        if plan.weather_fetched_at:
            age = (now - plan.weather_fetched_at).total_seconds() / 3600
            if age < 2:  # Skip if fetched within last 2 hours
                skipped_stale += 1
                continue

        # Attempt weather fetch
        try:
            plan.fetch_weather()
            updated += 1
            logger.info(
                f"Updated weather for DailyPlan {plan.id} ({plan.project.name}, {plan.plan_date})"
            )
        except Exception as e:
            errors += 1
            logger.error(f"Failed to fetch weather for DailyPlan {plan.id}: {e}")

    result = {
        "updated": updated,
        "skipped_no_address": skipped_no_address,
        "skipped_recent": skipped_stale,
        "errors": errors,
        "timestamp": str(now),
    }

    logger.info(f"Weather update complete: {result}")
    return result


@shared_task(name="core.tasks.fetch_weather_for_plan")
def fetch_weather_for_plan(plan_id):
    """
    Fetch weather data for a specific DailyPlan (async task).
    Called automatically when plan is created/updated.

    Args:
        plan_id: DailyPlan primary key

    Returns:
        dict with status and weather data summary
    """
    from core.models import DailyPlan

    try:
        plan = DailyPlan.objects.get(id=plan_id)
    except DailyPlan.DoesNotExist:
        logger.error(f"DailyPlan {plan_id} not found for weather fetch")
        return {"status": "not_found", "plan_id": plan_id}

    if not plan.project.address:
        logger.warning(f"DailyPlan {plan_id} has no project address, skipping weather fetch")
        return {"status": "no_address", "plan_id": plan_id}

    try:
        weather_data = plan.fetch_weather()
        if weather_data:
            logger.info(f"Weather fetched successfully for DailyPlan {plan_id}")
            return {
                "status": "success",
                "plan_id": plan_id,
                "temperature": weather_data.get("temperature"),
                "condition": weather_data.get("condition"),
            }
        else:
            logger.warning(f"Weather fetch returned no data for DailyPlan {plan_id}")
            return {"status": "no_data", "plan_id": plan_id}
    except Exception as e:
        logger.error(f"Error fetching weather for DailyPlan {plan_id}: {e}")
        return {"status": "error", "plan_id": plan_id, "error": str(e)}


# ============================================================================
# PHASE 6: Real-Time WebSocket Tasks
# ============================================================================


@shared_task(name="core.tasks.cleanup_stale_user_status")
def cleanup_stale_user_status(threshold_minutes=5):
    """
    Mark users as offline if their last heartbeat is older than threshold.
    Runs every 5 minutes to keep online status accurate.

    Args:
        threshold_minutes: Minutes without heartbeat before marking offline

    Returns:
        dict: Status with count of users marked offline
    """
    from core.models import UserStatus

    try:
        count = UserStatus.cleanup_stale_online_status(threshold_minutes=threshold_minutes)
        logger.info(f"Cleaned up {count} stale user status records")
        return {
            "status": "success",
            "users_marked_offline": count,
            "threshold_minutes": threshold_minutes,
        }
    except Exception as e:
        logger.error(f"Error cleaning up user status: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


@shared_task(name="core.tasks.send_websocket_notification")
def send_websocket_notification(user_id, title, message, category="info", url=""):
    """
    Send a notification via WebSocket to a specific user.
    Falls back to database-only if WebSocket fails.

    Args:
        user_id: Target user ID
        title: Notification title
        message: Notification message
        category: Notification category (info/success/warning/error/task/chat)
        url: Optional URL to link

    Returns:
        dict: Status of notification delivery
    """
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
    from django.contrib.auth import get_user_model

    from core.models import NotificationLog

    user_model = get_user_model()
    channel_layer = get_channel_layer()

    try:
        user = user_model.objects.get(id=user_id)

        # Create notification log
        notification = NotificationLog.objects.create(
            user=user,
            title=title,
            message=message,
            category=category,
            url=url,
        )

        # Try to send via WebSocket
        try:
            async_to_sync(channel_layer.group_send)(
                f"notifications_{user_id}",
                {
                    "type": "send_notification",
                    "notification": {
                        "id": notification.id,
                        "title": title,
                        "message": message,
                        "category": category,
                        "url": url,
                        "created_at": notification.created_at.isoformat(),
                    },
                },
            )
            notification.mark_as_delivered()
            logger.info(f"WebSocket notification sent to user {user_id}: {title}")
            return {
                "status": "success",
                "user_id": user_id,
                "notification_id": notification.id,
                "delivered_via_websocket": True,
            }
        except Exception as ws_error:
            logger.warning(
                f"WebSocket send failed for user {user_id}, stored in DB only: {ws_error}"
            )
            return {
                "status": "partial",
                "user_id": user_id,
                "notification_id": notification.id,
                "delivered_via_websocket": False,
                "error": str(ws_error),
            }

    except user_model.DoesNotExist:
        logger.error(f"User {user_id} not found for notification")
        return {
            "status": "error",
            "error": "User not found",
            "user_id": user_id,
        }
    except Exception as e:
        logger.error(f"Error sending notification to user {user_id}: {e}")
        return {
            "status": "error",
            "error": str(e),
            "user_id": user_id,
        }


# ============================================================================
# WEBSOCKET METRICS TASKS (Phase 6 - Improvement #17)
# ============================================================================


@shared_task(name="core.tasks.collect_websocket_metrics")
def collect_websocket_metrics():
    """
    Collect and store WebSocket metrics every 5 minutes

    Stores metrics in cache with timestamp key for historical tracking.
    Metrics are kept for 24 hours.
    """
    from django.core.cache import cache
    from django.utils import timezone

    from core.websocket_metrics import get_metrics_summary

    try:
        # Get current metrics
        metrics = get_metrics_summary()

        # Store with timestamp key
        timestamp = timezone.now()
        cache_key = f"ws_metrics_{timestamp.strftime('%Y%m%d%H%M')}"

        # Store for 24 hours
        cache.set(cache_key, metrics, timeout=86400)

        # Also update the latest summary
        cache.set("ws_metrics_summary", metrics, timeout=3600)

        logger.info(f"WebSocket metrics collected and stored: {cache_key}")

        return {
            "status": "success",
            "timestamp": timestamp.isoformat(),
            "connections": metrics["connections"]["total"],
            "message_rate": metrics["messages"]["rate_1m"],
        }

    except Exception as e:
        logger.error(f"Error collecting WebSocket metrics: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


@shared_task(name="core.tasks.cleanup_old_websocket_metrics")
def cleanup_old_websocket_metrics():
    """
    Clean up old WebSocket metrics from cache

    Runs daily to remove metrics older than 7 days.
    """
    from datetime import timedelta

    from django.core.cache import cache
    from django.utils import timezone

    try:
        timezone.now() - timedelta(days=7)
        deleted_count = 0

        # Generate keys for last 7 days
        for day_offset in range(8, 365):  # Check up to a year back
            check_date = timezone.now() - timedelta(days=day_offset)

            # Check each 5-minute interval
            for hour in range(24):
                for minute in range(0, 60, 5):
                    timestamp_str = check_date.replace(hour=hour, minute=minute, second=0).strftime(
                        "%Y%m%d%H%M"
                    )
                    cache_key = f"ws_metrics_{timestamp_str}"

                    if cache.get(cache_key):
                        cache.delete(cache_key)
                        deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} old WebSocket metrics entries")

        return {
            "status": "success",
            "deleted_count": deleted_count,
        }

    except Exception as e:
        logger.error(f"Error cleaning up WebSocket metrics: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


@shared_task(name="core.tasks.process_signature_post_tasks")
def process_signature_post_tasks(document_type: str, document_id: int, signer_name: str, customer_email: str = None):
    """
    Process post-signature tasks in background:
    - Send email notifications
    - Generate signed PDF
    - Auto-save to project files
    
    This prevents the signature page from blocking while these operations complete.
    """
    try:
        from django.contrib.auth import get_user_model
        from django.core.files.base import ContentFile
        from django.utils import timezone
        
        User = get_user_model()
        
        if document_type == "changeorder":
            from core.models import ChangeOrder
            document = ChangeOrder.objects.get(id=document_id)
            project_name = document.project.name if document.project else '-'
            
            # Determine amount/rate info for email
            amount_str = None
            rate_info = None
            if document.pricing_type == "T_AND_M":
                rate_info = f"Labor Rate: ${document.get_effective_billing_rate():.2f} | Material Markup: {document.material_markup_percent}%"
            else:
                amount_str = f"{document.amount:.2f}" if document.amount else None
            
            # --- Email notifications ---
            from core.services.email_service import KibrayEmailService
            
            internal_recipients = list(
                User.objects.filter(is_staff=True, is_active=True).values_list("email", flat=True)
            )
            internal_recipients = [e for e in internal_recipients if e]
            
            if internal_recipients:
                try:
                    KibrayEmailService.send_changeorder_signed_notification(
                        to_emails=internal_recipients,
                        co_number=document.id,
                        project_name=project_name,
                        description=document.description,
                        pricing_type=document.pricing_type,
                        signed_by=signer_name,
                        signed_at=timezone.localtime(document.signed_at).strftime('%Y-%m-%d %H:%M:%S') if document.signed_at else '',
                        amount=amount_str,
                        rate_info=rate_info,
                    )
                    logger.info(f"CO #{document_id}: Internal notification emails sent")
                except Exception as e:
                    logger.warning(f"CO #{document_id}: Failed to send internal emails: {e}")
            
            # Send to customer if provided
            if customer_email:
                try:
                    KibrayEmailService.send_signature_confirmation(
                        to_email=customer_email,
                        document_type="Change Order",
                        document_number=str(document.id),
                        signed_by=signer_name,
                        signed_at=timezone.localtime(document.signed_at).strftime('%Y-%m-%d %H:%M:%S') if document.signed_at else '',
                        project_name=project_name,
                    )
                    logger.info(f"CO #{document_id}: Customer confirmation email sent to {customer_email}")
                except Exception as e:
                    logger.warning(f"CO #{document_id}: Failed to send customer email: {e}")
            
            # --- PDF Generation ---
            try:
                from core.services.pdf_service import generate_signed_changeorder_pdf
                
                pdf_bytes = generate_signed_changeorder_pdf(document)
                if pdf_bytes:
                    document.signed_pdf = ContentFile(
                        pdf_bytes, name=f"co_{document.id}_signed.pdf"
                    )
                    document.save(update_fields=["signed_pdf"])
                    logger.info(f"CO #{document_id}: Signed PDF generated")
            except Exception as e:
                logger.warning(f"CO #{document_id}: PDF generation failed: {e}")
            
            # --- Auto-save to project files ---
            try:
                from core.services.document_storage_service import auto_save_changeorder_pdf
                auto_save_changeorder_pdf(document, user=None, overwrite=True)
                logger.info(f"CO #{document_id}: PDF auto-saved to project files")
            except Exception as e:
                logger.warning(f"CO #{document_id}: Failed to auto-save PDF: {e}")
        
        elif document_type == "color_sample":
            from core.models import ColorSample
            document = ColorSample.objects.get(id=document_id)
            project_name = document.project.name if document.project else '-'
            
            # --- Email notifications ---
            from core.services.email_service import KibrayEmailService
            
            internal_recipients = list(
                User.objects.filter(is_staff=True, is_active=True).values_list("email", flat=True)
            )
            internal_recipients = [e for e in internal_recipients if e]
            
            # Send to each internal recipient
            for recipient_email in internal_recipients:
                try:
                    KibrayEmailService.send_colorsample_signed_notification(
                        to_email=recipient_email,
                        color_name=document.name or "Color Sample",
                        color_code=document.code or str(document.id),
                        project_name=project_name,
                        signed_by=signer_name,
                        signed_at=timezone.localtime(document.client_signed_at).strftime('%Y-%m-%d %H:%M:%S') if document.client_signed_at else '',
                        client_ip=document.client_signed_ip or '',
                        location=document.room_location or 'N/A',
                    )
                    logger.info(f"Color Sample #{document_id}: Notification sent to {recipient_email}")
                except Exception as e:
                    logger.warning(f"Color Sample #{document_id}: Failed to send email to {recipient_email}: {e}")
            
            # Send to customer if provided
            if customer_email:
                try:
                    KibrayEmailService.send_signature_confirmation(
                        to_email=customer_email,
                        document_type="Color Sample",
                        document_number=document.code or str(document.id),
                        signed_by=signer_name,
                        signed_at=timezone.localtime(document.client_signed_at).strftime('%Y-%m-%d %H:%M:%S') if document.client_signed_at else '',
                        project_name=project_name,
                    )
                    logger.info(f"Color Sample #{document_id}: Customer confirmation email sent")
                except Exception as e:
                    logger.warning(f"Color Sample #{document_id}: Failed to send customer email: {e}")
            
            # --- PDF Generation ---
            try:
                from core.services.pdf_service import generate_signed_color_sample_pdf
                
                pdf_bytes = generate_signed_color_sample_pdf(document)
                if pdf_bytes:
                    document.signed_pdf = ContentFile(
                        pdf_bytes, name=f"color_sample_{document.id}_signed.pdf"
                    )
                    document.save(update_fields=["signed_pdf"])
                    logger.info(f"Color Sample #{document_id}: Signed PDF generated")
            except Exception as e:
                logger.warning(f"Color Sample #{document_id}: PDF generation failed: {e}")
            
            # --- Auto-save to project files ---
            try:
                from core.services.document_storage_service import auto_save_colorsample_pdf
                auto_save_colorsample_pdf(document, user=None, overwrite=True)
                logger.info(f"Color Sample #{document_id}: PDF auto-saved to project files")
            except Exception as e:
                logger.warning(f"Color Sample #{document_id}: Failed to auto-save PDF: {e}")
        
        return {
            "status": "success",
            "document_type": document_type,
            "document_id": document_id,
        }
        
    except Exception as e:
        logger.error(f"Error in process_signature_post_tasks: {e}")
        return {"status": "error", "error": str(e)}


@shared_task(name="core.tasks.cleanup_old_assignments")
def cleanup_old_assignments(days: int = 30):
    """
    Elimina asignaciones de empleados anteriores a X días.
    Reduce costos de almacenamiento sin afectar funcionalidad.
    
    Se ejecuta semanalmente (configurar en Celery Beat).
    """
    from core.models import ResourceAssignment
    
    try:
        cutoff_date = timezone.localdate() - timedelta(days=days)
        
        old_assignments = ResourceAssignment.objects.filter(date__lt=cutoff_date)
        count = old_assignments.count()
        
        if count == 0:
            logger.info("cleanup_old_assignments: No hay asignaciones antiguas para eliminar.")
            return {"status": "success", "deleted": 0}
        
        deleted, _ = old_assignments.delete()
        logger.info(f"cleanup_old_assignments: Eliminadas {deleted} asignaciones anteriores a {cutoff_date}")
        
        return {
            "status": "success",
            "deleted": deleted,
            "cutoff_date": str(cutoff_date),
        }
        
    except Exception as e:
        logger.error(f"Error en cleanup_old_assignments: {e}")
        return {"status": "error", "error": str(e)}


@shared_task(name="core.tasks.process_sop_image")
def process_sop_image(sop_id: int, image_data: str):
    """
    Process and save SOP reference photo in background.
    This allows the SOP creation to return immediately while
    the image is being processed and uploaded.
    
    Args:
        sop_id: ID of the ActivityTemplate (SOP) to update
        image_data: Base64 encoded image data string
    """
    import base64
    import uuid
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage
    
    from core.models import ActivityTemplate
    
    try:
        sop = ActivityTemplate.objects.get(id=sop_id)
        
        if not image_data or ";base64," not in image_data:
            logger.warning(f"process_sop_image: Invalid image data for SOP {sop_id}")
            return {"status": "skipped", "reason": "invalid_image_data"}
        
        # Decode and save image
        format_part, imgstr = image_data.split(";base64,")
        ext = format_part.split("/")[-1]
        if ext not in ["png", "jpg", "jpeg", "gif", "webp"]:
            ext = "png"  # Default to PNG for canvas exports
        
        filename = f"sop_images/{uuid.uuid4()}.{ext}"
        file_data = ContentFile(base64.b64decode(imgstr), name=filename)
        file_path = default_storage.save(filename, file_data)
        
        # Update SOP with the image URL
        image_url = default_storage.url(file_path)
        current_photos = sop.reference_photos or []
        current_photos.append(image_url)
        sop.reference_photos = current_photos
        sop.save(update_fields=["reference_photos"])
        
        logger.info(f"process_sop_image: Successfully saved image for SOP {sop_id}")
        return {
            "status": "success",
            "sop_id": sop_id,
            "image_url": image_url,
        }
        
    except ActivityTemplate.DoesNotExist:
        logger.error(f"process_sop_image: SOP {sop_id} not found")
        return {"status": "error", "error": "SOP not found"}
    except Exception as e:
        logger.error(f"process_sop_image: Error processing image for SOP {sop_id}: {e}")
        return {"status": "error", "error": str(e)}


@shared_task(name="core.tasks.process_changeorder_photos")
def process_changeorder_photos(changeorder_id: int, photo_data_list: list):
    """
    Process Change Order photos in background to prevent UI blocking.
    
    Args:
        changeorder_id: ID of the ChangeOrder
        photo_data_list: List of dicts with 'file_path', 'description', 'order'
                        file_path is the temporary storage path
    """
    import uuid
    from django.core.files.storage import default_storage
    from core.models import ChangeOrder, ChangeOrderPhoto
    
    try:
        changeorder = ChangeOrder.objects.get(id=changeorder_id)
        
        processed_count = 0
        for photo_info in photo_data_list:
            try:
                temp_path = photo_info.get('file_path')
                description = photo_info.get('description', '')
                order = photo_info.get('order', 0)
                
                if temp_path and default_storage.exists(temp_path):
                    # Read from temp location
                    with default_storage.open(temp_path, 'rb') as f:
                        file_content = f.read()
                    
                    # Create the photo with the content
                    from django.core.files.base import ContentFile
                    filename = f"changeorder_photos/{changeorder_id}/{uuid.uuid4()}.jpg"
                    
                    photo = ChangeOrderPhoto(
                        change_order=changeorder,
                        description=description,
                        order=order,
                    )
                    photo.image.save(filename.split('/')[-1], ContentFile(file_content), save=True)
                    
                    # Clean up temp file
                    try:
                        default_storage.delete(temp_path)
                    except Exception:
                        pass
                    
                    processed_count += 1
                    
            except Exception as e:
                logger.warning(f"process_changeorder_photos: Error processing photo for CO {changeorder_id}: {e}")
                continue
        
        logger.info(f"process_changeorder_photos: Processed {processed_count} photos for CO {changeorder_id}")
        return {
            "status": "success",
            "changeorder_id": changeorder_id,
            "photos_processed": processed_count,
        }
        
    except ChangeOrder.DoesNotExist:
        logger.error(f"process_changeorder_photos: CO {changeorder_id} not found")
        return {"status": "error", "error": "ChangeOrder not found"}
    except Exception as e:
        logger.error(f"process_changeorder_photos: Error for CO {changeorder_id}: {e}")
        return {"status": "error", "error": str(e)}


@shared_task(name="core.tasks.process_changeorder_creation")
def process_changeorder_creation(changeorder_id: int):
    """
    Post-creation tasks for Change Order (notifications, indexing, etc.)
    Run in background to keep UI responsive.
    """
    from core.models import ChangeOrder
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    try:
        changeorder = ChangeOrder.objects.select_related('project').get(id=changeorder_id)
        
        # Send notification to project managers
        try:
            from core.models import Notification
            
            # Get PMs assigned to this project
            pm_users = User.objects.filter(
                profile__role__in=['admin', 'pm'],
                is_active=True
            )
            
            for pm in pm_users:
                Notification.objects.create(
                    user=pm,
                    message=f"New Change Order #{changeorder_id} created for {changeorder.project.name if changeorder.project else 'Unknown Project'}",
                    notification_type="changeorder",
                    link=f"/changeorder/{changeorder_id}/",
                    project=changeorder.project,
                )
            
            logger.info(f"process_changeorder_creation: Notifications sent for CO {changeorder_id}")
        except Exception as e:
            logger.warning(f"process_changeorder_creation: Failed to send notifications for CO {changeorder_id}: {e}")
        
        return {"status": "success", "changeorder_id": changeorder_id}
        
    except ChangeOrder.DoesNotExist:
        logger.error(f"process_changeorder_creation: CO {changeorder_id} not found")
        return {"status": "error", "error": "ChangeOrder not found"}
    except Exception as e:
        logger.error(f"process_changeorder_creation: Error for CO {changeorder_id}: {e}")
        return {"status": "error", "error": str(e)}


@shared_task(name="core.tasks.process_contract_generation")
def process_contract_generation(contract_id: int, user_id: int = None, regenerate: bool = False):
    """
    Generate contract PDF in background and save it to the contract/project files.
    If `regenerate` is True then force regeneration/overwrite.
    """
    try:
        from django.contrib.auth import get_user_model
        from core.services.contract_service import ContractService
        from core.models import Contract

        contract = Contract.objects.select_related('project').get(id=contract_id)
        user = None
        if user_id:
            User = get_user_model()
            user = User.objects.filter(id=user_id).first()

        # Call the ContractService to (re)generate and save the PDF
        ContractService.generate_contract_pdf(contract, user)
        logger.info(f"process_contract_generation: Generated PDF for contract {contract_id}")
        return {"status": "success", "contract_id": contract_id}
    except Contract.DoesNotExist:
        logger.error(f"process_contract_generation: Contract {contract_id} not found")
        return {"status": "error", "error": "Contract not found"}
    except Exception as e:
        logger.error(f"process_contract_generation: Error for contract {contract_id}: {e}")
        return {"status": "error", "error": str(e)}


# ============================================================================
# GENERIC ASYNC REPORT TASK (Phase C / Reports)
# ============================================================================
# This task is the worker counterpart of `core.services.report_registry`.
# Any registered report (see `core.services.report_generators`) can be
# generated here without adding new tasks.
#
# Storage: writes to `default_storage` under `reports/<user_id>/<report>_<ts>.<ext>`
# Notification: creates a `Notification` row on success/failure so the
#   requesting user gets a link in the bell icon.
# Routing: `task_routes` already sends `core.tasks.generate_*` to the
#   `reports` queue (see kibray_backend/celery_config.py).
# ============================================================================


@shared_task(name="core.tasks.generate_report_async", bind=True, max_retries=2, default_retry_delay=30)
def generate_report_async(self, report_name: str, user_id: int, **kwargs):
    """
    Generate a registered report in the background and notify the user.

    Args:
        report_name: registry key (e.g. "estimate_pdf")
        user_id: PK of the user requesting the report (used for permission
            check + notification target + storage namespace)
        **kwargs: passed through to the generator (e.g. estimate_id=123)

    Returns:
        dict with status, file path, and notification_id on success;
        or status=error + reason on failure.
    """
    from django.contrib.auth import get_user_model
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage

    from core.models import Notification
    from core.services import report_generators  # noqa: F401  (auto-registers)
    from core.services.report_registry import (
        ReportNotFound,
        ReportPermissionDenied,
        get as get_report,
        render as render_report,
    )

    User = get_user_model()

    # Resolve user once — needed for both perm-check and notification.
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.error(f"generate_report_async: user {user_id} not found")
        return {"status": "error", "error": "user_not_found", "user_id": user_id}

    try:
        spec = get_report(report_name)
    except ReportNotFound:
        logger.error(f"generate_report_async: unknown report {report_name!r}")
        Notification.objects.create(
            user=user,
            notification_type="system",
            title="Report unavailable",
            message=f"Requested report {report_name!r} is not registered.",
        )
        return {"status": "error", "error": "report_not_found", "report": report_name}

    # Permission gate (mirrors render() but lets us surface a friendlier
    # message via Notification before bubbling).
    try:
        pdf_bytes = render_report(report_name, user=user, **kwargs)
    except ReportPermissionDenied as exc:
        logger.warning(f"generate_report_async: {exc}")
        Notification.objects.create(
            user=user,
            notification_type="system",
            title="Report denied",
            message=f"You are not allowed to generate {report_name!r}.",
        )
        return {"status": "error", "error": "permission_denied", "report": report_name}
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"generate_report_async: generator failed for {report_name}: {exc}")
        # Retry transient failures (e.g. DB hiccup, S3 blip) up to 2x.
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            Notification.objects.create(
                user=user,
                notification_type="system",
                title="Report failed",
                message=f"Could not generate {report_name!r}: {exc}",
            )
            return {
                "status": "error",
                "error": "generation_failed",
                "report": report_name,
                "exception": str(exc),
            }

    # Persist + notify
    ts = timezone.now().strftime("%Y%m%d_%H%M%S")
    relpath = f"reports/{user_id}/{report_name}_{ts}.{spec.file_extension}"
    saved_path = default_storage.save(relpath, ContentFile(pdf_bytes))
    download_url = default_storage.url(saved_path) if hasattr(default_storage, "url") else saved_path

    notification = Notification.objects.create(
        user=user,
        notification_type="system",
        title="Report ready",
        message=f"Your {report_name!r} report is ready to download.",
        link_url=download_url,
        related_object_type="report",
    )
    logger.info(
        f"generate_report_async: stored {saved_path} for user={user_id} report={report_name}"
    )
    return {
        "status": "success",
        "report": report_name,
        "user_id": user_id,
        "path": saved_path,
        "download_url": download_url,
        "notification_id": notification.id,
        "size_bytes": len(pdf_bytes),
    }



@shared_task(
    name="core.tasks.generate_signed_contract_pdf_async",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def generate_signed_contract_pdf_async(self, contract_id: int, user_id: int = None):
    """Render the signed-contract PDF off the request thread.

    Mirrors the inline path in :meth:`ContractService.sign_contract` (heavy
    ReportLab render → ``ProjectFile`` → ``contract.signed_pdf_file``) but
    runs in the ``reports`` queue so HTTP responses stay snappy.

    Args:
        contract_id: PK of the contract that was just signed.
        user_id: PK of the staff user (countersigner) — optional.

    Returns:
        dict with ``contract_id`` and either ``project_file_id`` on success
        or an ``error`` key on failure (no retry).
    """
    from django.contrib.auth import get_user_model

    from core.models import Contract, Notification
    from core.services.contract_service import ContractService

    try:
        contract = Contract.objects.get(pk=contract_id)
    except Contract.DoesNotExist:
        logger.error(
            f"generate_signed_contract_pdf_async: contract {contract_id} not found"
        )
        return {"error": "contract_not_found", "contract_id": contract_id}

    user = None
    if user_id:
        User = get_user_model()
        user = User.objects.filter(pk=user_id).first()

    try:
        project_file = ContractService.generate_signed_contract_pdf(contract, user)
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            f"generate_signed_contract_pdf_async: render failed for contract {contract_id}: {exc}"
        )
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            if user is not None:
                Notification.objects.create(
                    user=user,
                    notification_type="system",
                    title="Signed contract PDF failed",
                    message=(
                        f"Could not generate signed PDF for contract "
                        f"{contract.contract_number}: {exc}"
                    ),
                )
            return {
                "error": "generation_failed",
                "contract_id": contract_id,
                "exception": str(exc),
            }

    if project_file is None:
        logger.warning(
            f"generate_signed_contract_pdf_async: generator returned None for "
            f"contract {contract_id}"
        )
        return {"contract_id": contract_id, "project_file_id": None}

    contract.signed_pdf_file = project_file
    contract.save(update_fields=["signed_pdf_file"])

    if user is not None:
        Notification.objects.create(
            user=user,
            notification_type="system",
            title="Signed contract PDF ready",
            message=(
                f"Signed PDF for contract {contract.contract_number} has been "
                f"generated."
            ),
            related_object_type="contract",
            related_object_id=contract.id,
        )

    logger.info(
        f"generate_signed_contract_pdf_async: contract={contract_id} "
        f"project_file={project_file.id}"
    )
    return {"contract_id": contract_id, "project_file_id": project_file.id}


# ============================================================================
# Generic auto-save PDF task — moves the heavy ReportLab/xhtml2pdf renders
# triggered by status-changes (estimate approved, invoice sent, etc.) off
# the request thread. Dispatch with ``transaction.on_commit`` so the worker
# never races the parent transaction.
# ============================================================================

# (kind, model_label, helper, accepted_opts)
_AUTO_SAVE_PDF_DISPATCH = {
    "invoice": ("core.Invoice", "auto_save_invoice_pdf", {"overwrite"}),
    "estimate": ("core.Estimate", "auto_save_estimate_pdf", {"overwrite", "as_contract"}),
    "changeorder": ("core.ChangeOrder", "auto_save_changeorder_pdf", {"overwrite"}),
    "colorsample": ("core.ColorSample", "auto_save_colorsample_pdf", {"overwrite"}),
}


@shared_task(
    name="core.tasks.auto_save_pdf_async",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def auto_save_pdf_async(self, doc_kind: str, doc_id: int, user_id: int = None, **opts):
    """Off-thread wrapper around the ``auto_save_*_pdf`` helpers.

    Args:
        doc_kind: one of ``invoice``, ``estimate``, ``changeorder``,
            ``colorsample`` — selects which helper + model to use.
        doc_id: PK of the source document.
        user_id: PK of the user attribution (optional).
        **opts: forwarded to the helper. Only options listed in
            ``_AUTO_SAVE_PDF_DISPATCH`` are passed through (defensive
            filter — extra keys from upstream callers are ignored, never
            raised).

    Returns:
        dict with ``project_file_id`` on success, ``None`` if the helper
        returned None (e.g. unsigned change order), or ``error`` key on
        unrecoverable failure.
    """
    from django.apps import apps
    from django.contrib.auth import get_user_model

    from core.services import document_storage_service as dss

    if doc_kind not in _AUTO_SAVE_PDF_DISPATCH:
        logger.error(f"auto_save_pdf_async: unknown doc_kind {doc_kind!r}")
        return {"error": "unknown_doc_kind", "doc_kind": doc_kind}

    model_label, helper_name, allowed_opts = _AUTO_SAVE_PDF_DISPATCH[doc_kind]
    app_label, model_name = model_label.split(".")
    model = apps.get_model(app_label, model_name)
    try:
        instance = model.objects.get(pk=doc_id)
    except model.DoesNotExist:
        logger.error(f"auto_save_pdf_async: {model_label}({doc_id}) not found")
        return {"error": "doc_not_found", "doc_kind": doc_kind, "doc_id": doc_id}

    user = None
    if user_id:
        User = get_user_model()
        user = User.objects.filter(pk=user_id).first()

    helper = getattr(dss, helper_name)
    safe_opts = {k: v for k, v in opts.items() if k in allowed_opts}

    try:
        project_file = helper(instance, user=user, **safe_opts)
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            f"auto_save_pdf_async: helper {helper_name} failed for "
            f"{doc_kind}({doc_id}): {exc}"
        )
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {
                "error": "generation_failed",
                "doc_kind": doc_kind,
                "doc_id": doc_id,
                "exception": str(exc),
            }

    pf_id = getattr(project_file, "id", None) if project_file is not None else None
    logger.info(
        f"auto_save_pdf_async: {doc_kind}({doc_id}) -> project_file={pf_id}"
    )
    return {"doc_kind": doc_kind, "doc_id": doc_id, "project_file_id": pf_id}


@shared_task(name="core.tasks.generate_daily_ev_snapshots")
def generate_daily_ev_snapshots():
    """Phase D3 — daily Earned Value snapshot generator.

    Persists one ``EVSnapshot`` per project per day so the UI / forecasting
    dashboards have a trended history. Idempotent: re-running the same day
    overwrites existing rows. Scheduled at 18:00 (after employee clock-out)
    via ``kibray_backend/celery_config.py``.
    """
    from core.services.ev_snapshots import bulk_create_snapshots

    snaps = bulk_create_snapshots()
    logger.info("generate_daily_ev_snapshots: created/updated %s snapshots", len(snaps))
    return {"snapshots": len(snaps)}
