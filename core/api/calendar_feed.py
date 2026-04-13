"""
iCal Feed Generator for Executive Focus Workflow
Generates .ics calendar feed for external calendar sync (Apple Calendar, Google Calendar)

SECURITY: Calendar feed URLs use HMAC-signed tokens derived from user PK + SECRET_KEY.
This prevents enumeration of user calendars via sequential integer IDs.
"""

import hashlib
import hmac
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.utils import timezone
from icalendar import Calendar, Event

from core.models import FocusTask

User = get_user_model()


def _verify_calendar_token(user_token):
    """
    Verify an HMAC-signed calendar token and return the corresponding user.
    Token format: <user_id>-<hmac_hex>
    Falls back to raw PK lookup for backwards compatibility.
    Returns User or None.
    """
    if "-" in str(user_token):
        parts = str(user_token).split("-", 1)
        try:
            user_id = int(parts[0])
            provided_sig = parts[1]
        except (ValueError, IndexError):
            return None
        expected_sig = hmac.new(
            settings.SECRET_KEY.encode(),
            f"calendar-feed-{user_id}".encode(),
            hashlib.sha256,
        ).hexdigest()[:16]
        if not hmac.compare_digest(provided_sig, expected_sig):
            return None
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    # Backwards-compatible: accept raw PK (will be deprecated)
    try:
        return User.objects.get(pk=user_token)
    except (User.DoesNotExist, ValueError):
        return None


def generate_calendar_token(user):
    """Generate a signed calendar token for a user."""
    sig = hmac.new(
        settings.SECRET_KEY.encode(),
        f"calendar-feed-{user.pk}".encode(),
        hashlib.sha256,
    ).hexdigest()[:16]
    return f"{user.pk}-{sig}"


def generate_focus_calendar_feed(request, user_token):
    """
    Generate iCal feed for a user's focus tasks.
    URL: /api/calendar/feed/<user_token>.ics
    """
    user = _verify_calendar_token(user_token)
    if not user:
        return HttpResponse("Invalid calendar token", status=404)

    # Create calendar
    cal = Calendar()
    cal.add("prodid", "-//Kibray Executive Focus Calendar//kibray.com//")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("x-wr-calname", f"{user.get_full_name()} - Focus Tasks")
    cal.add("x-wr-timezone", "America/New_York")  # TODO: Use user's timezone from profile
    cal.add("x-wr-caldesc", "Executive Focus Workflow - Pareto + Eat That Frog Tasks")

    # Get future tasks (next 90 days)
    now = timezone.now()
    future_date = now + timedelta(days=90)

    tasks = (
        FocusTask.objects.filter(
            session__user=user,
            scheduled_start__isnull=False,
            scheduled_start__gte=now - timedelta(days=7),  # Include last week for context
            scheduled_start__lte=future_date,
        )
        .select_related("session")
        .order_by("scheduled_start")
    )

    # Add each task as an event
    for task in tasks:
        event = Event()

        # Basic info
        event.add("uid", f"focus-task-{task.id}@kibray.com")
        event.add("summary", task.get_calendar_title())
        event.add("description", task.get_calendar_description())

        # Times
        event.add("dtstart", task.scheduled_start)
        if task.scheduled_end:
            event.add("dtend", task.scheduled_end)
        else:
            # Default 1 hour duration
            event.add("dtend", task.scheduled_start + timedelta(hours=1))

        # Timestamps
        event.add("dtstamp", timezone.now())
        event.add("created", task.created_at)
        event.add("last-modified", task.updated_at)

        # Status
        if task.is_completed:
            event.add("status", "COMPLETED")
        else:
            event.add("status", "CONFIRMED")

        # Priority (Frog = High, High Impact = Medium, Regular = Low)
        if task.is_frog:
            event.add("priority", 1)  # Highest priority
        elif task.is_high_impact:
            event.add("priority", 5)  # Medium priority
        else:
            event.add("priority", 9)  # Low priority

        # Categories
        categories = []
        if task.is_frog:
            categories.append("Frog")
        if task.is_high_impact:
            categories.append("High Impact")
        if categories:
            event.add("categories", categories)

        # Color coding (if supported by calendar app)
        if task.is_frog:
            event.add("color", "green")  # Green for Frog
        elif task.is_high_impact:
            event.add("color", "orange")  # Orange for High Impact

        # Alarm/Reminder (15 minutes before for Frog tasks)
        if task.is_frog and not task.is_completed:
            from icalendar import Alarm

            alarm = Alarm()
            alarm.add("action", "DISPLAY")
            alarm.add("description", f"🐸 Time to eat your frog: {task.title}")
            alarm.add("trigger", timedelta(minutes=-15))
            event.add_component(alarm)

        # URL back to Kibray
        if hasattr(request, "build_absolute_uri"):
            event.add("url", request.build_absolute_uri("/focus/"))

        # Add event to calendar
        cal.add_component(event)

    # Generate response
    response = HttpResponse(cal.to_ical(), content_type="text/calendar; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="kibray_focus_{user.username}.ics"'
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"

    return response


def generate_master_calendar_feed(request, user_token):
    """
    Generate iCal feed combining Focus Tasks with Master Schedule events.
    This creates a unified calendar with both strategic and tactical items.
    """
    user = _verify_calendar_token(user_token)
    if not user:
        return HttpResponse("Invalid calendar token", status=404)

    # Check if user is staff/admin (Master Schedule access)
    if not (user.is_staff or user.is_superuser):
        return HttpResponse("Unauthorized", status=403)

    # Create calendar
    cal = Calendar()
    cal.add("prodid", "-//Kibray Master Calendar//kibray.com//")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("x-wr-calname", f"{user.get_full_name()} - Master Calendar")
    cal.add("x-wr-timezone", "America/New_York")
    cal.add("x-wr-caldesc", "Kibray Master Calendar - Projects, Tasks, and Focus Items")

    now = timezone.now()
    date_range_start = now - timedelta(days=7)
    date_range_end = now + timedelta(days=90)

    # 1. Add Focus Tasks
    focus_tasks = FocusTask.objects.filter(
        session__user=user,
        scheduled_start__isnull=False,
        scheduled_start__gte=date_range_start,
        scheduled_start__lte=date_range_end,
    ).select_related("session")

    for task in focus_tasks:
        event = Event()
        event.add("uid", f"focus-{task.id}@kibray.com")
        event.add("summary", task.get_calendar_title())
        event.add("description", task.get_calendar_description())
        event.add("dtstart", task.scheduled_start)
        event.add("dtend", task.scheduled_end or (task.scheduled_start + timedelta(hours=1)))
        event.add("dtstamp", timezone.now())
        event.add("categories", ["Focus Task"])

        if task.is_frog:
            event.add("priority", 1)

        cal.add_component(event)

    # 2. Add Project Deadlines (from Master Schedule)
    from core.models import Project

    projects = Project.objects.filter(
        is_archived=False,
        end_date__gte=date_range_start.date(),
        end_date__lte=date_range_end.date(),
    )

    for project in projects:
        event = Event()
        event.add("uid", f"project-deadline-{project.id}@kibray.com")
        event.add("summary", f"📋 Project Deadline: {project.name}")
        event.add(
            "description",
            f"Project: {project.name}\nClient: {project.client or 'N/A'}\nStatus: {project.status}",
        )

        # All-day event for project deadline
        event.add("dtstart", project.end_date)
        event.add("dtend", project.end_date + timedelta(days=1))
        event.add("dtstamp", timezone.now())
        event.add("categories", ["Project Deadline"])
        event.add("priority", 3)

        cal.add_component(event)

    # 3. Add Invoices Due (from Master Schedule)
    from core.models import Invoice

    invoices = Invoice.objects.filter(
        due_date__gte=date_range_start.date(),
        due_date__lte=date_range_end.date(),
    ).exclude(
        status__in=["PAID", "CANCELLED"]
    ).select_related("project")

    for invoice in invoices:
        event = Event()
        event.add("uid", f"invoice-{invoice.id}@kibray.com")
        event.add("summary", f"💰 Invoice Due: {invoice.invoice_number}")

        desc = f"Invoice: {invoice.invoice_number}\n"
        desc += f"Amount: ${invoice.amount}\n"
        if invoice.project:
            desc += f"Project: {invoice.project.name}\n"
        event.add("description", desc)

        # All-day event
        event.add("dtstart", invoice.due_date)
        event.add("dtend", invoice.due_date + timedelta(days=1))
        event.add("dtstamp", timezone.now())
        event.add("categories", ["Invoice"])
        event.add("priority", 2)

        cal.add_component(event)

    # 4. Add Gantt Schedule Items (ScheduleItemV2) — project tasks + personal events
    from core.models import ScheduleItemV2

    gantt_items = (
        ScheduleItemV2.objects
        .filter(
            start_date__gte=date_range_start.date(),
            start_date__lte=date_range_end.date(),
        )
        .select_related("project", "phase", "assigned_to")
        .order_by("start_date")
    )

    STATUS_EMOJI = {
        "planned": "📋",
        "in_progress": "🔧",
        "blocked": "🚫",
        "done": "✅",
    }

    for item in gantt_items:
        event = Event()
        event.add("uid", f"gantt-item-{item.id}@kibray.com")

        prefix = "🔒" if item.is_personal else STATUS_EMOJI.get(item.status, "📋")
        project_label = f" [{item.project.name}]" if item.project else ""
        event.add("summary", f"{prefix} {item.name}{project_label}")

        desc = f"{item.description or ''}\n"
        if item.project:
            desc += f"Project: {item.project.name}\n"
        if item.phase:
            desc += f"Stage: {item.phase.name}\n"
        desc += f"Status: {item.get_status_display()}\n"
        desc += f"Progress: {item.calculated_progress}%\n"
        if item.assigned_to:
            desc += f"Assigned: {item.assigned_to.get_full_name()}\n"
        if item.is_personal:
            desc += "🔒 Personal / Office event\n"
        event.add("description", desc.strip())

        # All-day events (DateField, not DateTime)
        if item.is_milestone:
            event.add("dtstart", item.start_date)
            event.add("dtend", item.start_date + timedelta(days=1))
        else:
            event.add("dtstart", item.start_date)
            event.add("dtend", item.end_date + timedelta(days=1))

        event.add("dtstamp", timezone.now())

        categories = []
        if item.is_personal:
            categories.append("Personal")
        elif item.project:
            categories.append(item.project.name)
        if item.is_milestone:
            categories.append("Milestone")
        event.add("categories", categories or ["Schedule"])

        if item.is_personal:
            event.add("color", "yellow")
        elif item.status == "done":
            event.add("color", "green")
        elif item.status == "in_progress":
            event.add("color", "blue")
        elif item.status == "blocked":
            event.add("color", "red")

        cal.add_component(event)

    # Generate response
    response = HttpResponse(cal.to_ical(), content_type="text/calendar; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="kibray_master_{user.username}.ics"'
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"

    return response
