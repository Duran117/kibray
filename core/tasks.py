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
                related_url=f"/daily-plan/{plan.id}/edit/",
                priority="high",
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


@shared_task(name="core.tasks.update_daily_weather_snapshots_legacy")
def update_daily_weather_snapshots_legacy():
    """Daily task to snapshot weather for active projects (Module 30 skeleton)."""
    from core.models import Notification, Project
    from core.services.weather_service import get_weather_service

    svc = get_weather_service()
    now = timezone.now()
    projects = (
        Project.objects.filter(is_active=True)
        if hasattr(Project, "is_active")
        else Project.objects.all()
    )
    count = 0
    for project in projects:
        # Placeholder: using project.name as location key
        data = svc.get_weather(project.name)
        # For now, just notify admins with snapshot (will later persist to model)
        Notification.objects.create(
            user=None,
            notification_type="weather_snapshot",
            title=f"Weather Snapshot {project.name}",
            message=f"{data.condition} {data.temperature_c}°C",
            related_object_type="project",
            related_object_id=project.id,
        )
        count += 1
    logger.info(f"Weather snapshots generated for {count} projects at {now}")
    return {"snapshots": count, "timestamp": str(now)}


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
                    related_url="/employee/morning/",
                    priority="normal",
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
                rate_info = f"Labor Rate: ${document.get_effective_billing_rate():.2f} | Material Markup: {document.material_markup_pct}%"
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

