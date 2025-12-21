"""
iCal Feed Generator for Executive Focus Workflow
Generates .ics calendar feed for external calendar sync (Apple Calendar, Google Calendar)
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.utils import timezone
from icalendar import Calendar, Event

from core.models import FocusTask

User = get_user_model()


def generate_focus_calendar_feed(request, user_token):
    """
    Generate iCal feed for a user's focus tasks.
    URL: /api/calendar/feed/<user_token>.ics

    The user_token is the user's primary key (for now).
    In production, should use a secure random token stored in Profile.
    """
    try:
        # For now, user_token is the user_id
        # TODO: Implement secure random token in User Profile
        user = User.objects.get(pk=user_token)
    except (User.DoesNotExist, ValueError):
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
    try:
        user = User.objects.get(pk=user_token)
    except (User.DoesNotExist, ValueError):
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
        due_date__gte=date_range_start.date(), due_date__lte=date_range_end.date(), is_paid=False
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

    # Generate response
    response = HttpResponse(cal.to_ical(), content_type="text/calendar; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="kibray_master_{user.username}.ics"'
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"

    return response
