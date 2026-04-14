"""
HOA Resident Portal Views.

Public views (no login required) that allow HOA residents to:
  1. Self-identify (name, unit, email/phone)
  2. View their project dashboard (touch-ups, status, photos)
  3. Create new touch-ups with photos and optional floor plan pin
  4. Track status of their reported issues

Staff management views (login required) for PMs:
  - Create/edit/toggle portals
  - Manage units (CRUD, bulk add)
  - View portal sessions/activity

URL pattern: /portal/<uuid:token>/
"""

import json
from decimal import Decimal, InvalidOperation

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from core.models import (
    FloorPlan,
    Notification,
    Project,
    ProjectUnit,
    ResidentPortal,
    ResidentSession,
    TouchUp,
    TouchUpPhoto,
)


# ─── helpers ────────────────────────────────────────────────────────────────

def _get_portal_or_404(token):
    """Get active portal by token, or 404."""
    return get_object_or_404(ResidentPortal, token=token, is_active=True)


def _get_resident_session(request, portal):
    """Get or return None for a resident session from cookie."""
    session_key = request.COOKIES.get(f"portal_{portal.token}")
    if session_key:
        try:
            session = ResidentSession.objects.get(
                portal=portal, session_key=session_key
            )
            # Update last_active
            session.save(update_fields=["last_active"])
            return session
        except ResidentSession.DoesNotExist:
            pass
    return None


def _notify_staff_new_touchup(portal, touchup):
    """Notify PMs and admins about a new resident-submitted touch-up."""
    from django.contrib.auth.models import User
    from django.db.models import Q

    project = portal.project
    staff = (
        User.objects.filter(is_active=True)
        .filter(Q(is_superuser=True) | Q(profile__role__in=["admin", "project_manager"]))
        .distinct()
    )
    for user in staff:
        Notification.objects.create(
            user=user,
            project=project,
            notification_type="touchup",
            title=_("New resident touch-up: %(title)s") % {"title": touchup.title[:60]},
            message=_("%(name)s (%(unit)s) reported an issue via the resident portal") % {
                "name": touchup.resident_name or _("Unknown"),
                "unit": touchup.resident_unit or _("N/A"),
            },
            related_object_type="TouchUp",
            related_object_id=touchup.id,
            link_url=f"/projects/{project.id}/touchups-v2/{touchup.id}/",
        )


# ─── views ──────────────────────────────────────────────────────────────────

def portal_landing(request, token):
    """
    Portal entry point.
    - If resident has a valid session cookie → go to dashboard.
    - Otherwise → show identification form.
    """
    portal = _get_portal_or_404(token)
    session = _get_resident_session(request, portal)

    if session:
        return redirect("portal_dashboard", token=token)

    # Show identification form
    project = portal.project
    units = ProjectUnit.objects.filter(project=project).order_by("identifier")

    return render(request, "core/portal/portal_identify.html", {
        "portal": portal,
        "project": project,
        "units": units,
    })


def portal_identify(request, token):
    """Process the identification form and create a ResidentSession."""
    portal = _get_portal_or_404(token)

    if request.method != "POST":
        return redirect("portal_landing", token=token)

    name = request.POST.get("name", "").strip()
    unit = request.POST.get("unit", "").strip()
    email = request.POST.get("email", "").strip()
    phone = request.POST.get("phone", "").strip()

    # Validation
    errors = []
    if not name:
        errors.append(_("Name is required."))
    if portal.require_unit and not unit:
        errors.append(_("Unit/address is required."))
    if portal.require_email and not email:
        errors.append(_("Email is required."))
    if portal.require_phone and not phone:
        errors.append(_("Phone is required."))

    if errors:
        project = portal.project
        units = ProjectUnit.objects.filter(project=project).order_by("identifier")
        return render(request, "core/portal/portal_identify.html", {
            "portal": portal,
            "project": project,
            "units": units,
            "errors": errors,
            "form_name": name,
            "form_unit": unit,
            "form_email": email,
            "form_phone": phone,
        })

    # Create session
    import secrets
    session_key = secrets.token_urlsafe(32)

    session = ResidentSession.objects.create(
        portal=portal,
        name=name,
        unit=unit,
        email=email,
        phone=phone,
        session_key=session_key,
    )

    response = redirect("portal_dashboard", token=token)
    # Set cookie (30 days, httpOnly, SameSite=Lax)
    response.set_cookie(
        f"portal_{portal.token}",
        session_key,
        max_age=60 * 60 * 24 * 30,  # 30 days
        httponly=True,
        samesite="Lax",
    )
    return response


def portal_dashboard(request, token):
    """Resident dashboard: their touch-ups, project info, create new."""
    portal = _get_portal_or_404(token)
    session = _get_resident_session(request, portal)

    if not session:
        return redirect("portal_landing", token=token)

    project = portal.project

    # Get touch-ups created by this resident (match by name + unit)
    resident_touchups = TouchUp.objects.filter(
        project=project,
        resident_name=session.name,
        resident_unit=session.unit,
    ).select_related("floor_plan", "assigned_to").prefetch_related("photos").order_by("-created_at")

    active_touchups = resident_touchups.filter(status__in=["open", "in_progress", "review"])
    closed_touchups = resident_touchups.filter(status="closed")[:20]

    # Floor plans for touch-up creation
    floor_plans = FloorPlan.objects.filter(project=project, is_current=True).order_by("level")
    floor_plans_data = [
        {
            "id": fp.id,
            "name": fp.name,
            "level": fp.level,
            "image_url": fp.image.url if fp.image else "",
        }
        for fp in floor_plans
    ]

    return render(request, "core/portal/portal_dashboard.html", {
        "portal": portal,
        "project": project,
        "session": session,
        "active_touchups": active_touchups,
        "closed_touchups": closed_touchups,
        "floor_plans": floor_plans,
        "floor_plans_json": json.dumps(floor_plans_data),
    })


@require_POST
def portal_create_touchup(request, token):
    """Create a touch-up from the resident portal."""
    portal = _get_portal_or_404(token)
    session = _get_resident_session(request, portal)

    if not session:
        return redirect("portal_landing", token=token)

    project = portal.project
    title = request.POST.get("title", "").strip()

    if not title:
        return redirect("portal_dashboard", token=token)

    touchup = TouchUp.objects.create(
        project=project,
        title=title,
        description=request.POST.get("description", "").strip(),
        priority=request.POST.get("priority", "medium") or "medium",
        resident_name=session.name,
        resident_unit=session.unit,
        resident_email=session.email,
        resident_phone=session.phone,
        # No created_by (no Django User) — created_by stays None
    )

    # Floor plan pin
    floor_plan_id = request.POST.get("floor_plan_id")
    pin_x = request.POST.get("pin_x")
    pin_y = request.POST.get("pin_y")
    if floor_plan_id and pin_x and pin_y:
        try:
            fp = FloorPlan.objects.get(id=floor_plan_id, project=project)
            touchup.floor_plan = fp
            touchup.pin_x = Decimal(pin_x)
            touchup.pin_y = Decimal(pin_y)
            touchup.save(update_fields=["floor_plan", "pin_x", "pin_y"])
        except (FloorPlan.DoesNotExist, InvalidOperation, Exception):
            pass

    # Handle photos
    if portal.allow_photo_upload:
        photos = request.FILES.getlist("photos")
        for photo in photos:
            TouchUpPhoto.objects.create(
                touchup=touchup,
                image=photo,
                phase="before",
                # No uploaded_by — anonymous upload
            )

    # Notify staff
    _notify_staff_new_touchup(portal, touchup)

    return redirect("portal_dashboard", token=token)


def portal_touchup_detail(request, token, touchup_id):
    """View touch-up detail from portal."""
    portal = _get_portal_or_404(token)
    session = _get_resident_session(request, portal)

    if not session:
        return redirect("portal_landing", token=token)

    project = portal.project
    touchup = get_object_or_404(
        TouchUp.objects.select_related("floor_plan", "assigned_to")
        .prefetch_related("photos", "updates__author"),
        pk=touchup_id,
        project=project,
    )

    # Verify the resident owns this touch-up
    if touchup.resident_name != session.name or touchup.resident_unit != session.unit:
        return redirect("portal_dashboard", token=token)

    before_photos = touchup.photos.filter(phase="before")
    progress_photos = touchup.photos.filter(phase="progress")
    after_photos = touchup.photos.filter(phase="after")

    return render(request, "core/portal/portal_touchup_detail.html", {
        "portal": portal,
        "project": project,
        "session": session,
        "touchup": touchup,
        "before_photos": before_photos,
        "progress_photos": progress_photos,
        "after_photos": after_photos,
    })


def portal_logout(request, token):
    """Clear the session cookie and redirect to landing."""
    response = redirect("portal_landing", token=token)
    response.delete_cookie(f"portal_{token}")
    return response


# ─── STAFF MANAGEMENT VIEWS (login required) ────────────────────────────────

from django.contrib.auth.decorators import login_required


@login_required
def portal_manage(request, project_id):
    """
    PM view: create/edit the resident portal for a project.
    Also manage units and see sessions.
    """
    project = get_object_or_404(Project, pk=project_id)

    portal, _created = ResidentPortal.objects.get_or_create(
        project=project,
        defaults={"created_by": request.user},
    )

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update_settings":
            portal.welcome_message = request.POST.get("welcome_message", "").strip()
            portal.require_unit = request.POST.get("require_unit") == "on"
            portal.require_email = request.POST.get("require_email") == "on"
            portal.require_phone = request.POST.get("require_phone") == "on"
            portal.allow_photo_upload = request.POST.get("allow_photo_upload") == "on"
            portal.save()

        elif action == "toggle_active":
            portal.is_active = not portal.is_active
            portal.save(update_fields=["is_active"])

        elif action == "add_unit":
            identifier = request.POST.get("identifier", "").strip()
            if identifier:
                floor_raw = request.POST.get("floor", "").strip()
                try:
                    floor_val = int(floor_raw) if floor_raw else None
                except (ValueError, TypeError):
                    floor_val = None
                ProjectUnit.objects.get_or_create(
                    project=project,
                    identifier=identifier,
                    defaults={
                        "resident_name": request.POST.get("unit_resident_name", "").strip(),
                        "floor": floor_val,
                        "notes": request.POST.get("unit_notes", "").strip(),
                    },
                )

        elif action == "bulk_add_units":
            # One unit per line
            raw = request.POST.get("bulk_units", "")
            for line in raw.strip().splitlines():
                identifier = line.strip()
                if identifier:
                    ProjectUnit.objects.get_or_create(
                        project=project, identifier=identifier
                    )

        elif action == "delete_unit":
            unit_id = request.POST.get("unit_id")
            if unit_id:
                ProjectUnit.objects.filter(pk=unit_id, project=project).delete()

        return redirect("portal_manage", project_id=project.id)

    units = ProjectUnit.objects.filter(project=project).order_by("identifier")
    sessions = (
        ResidentSession.objects.filter(portal=portal)
        .order_by("-last_active")[:50]
    )

    # Build the full portal URL
    portal_url = request.build_absolute_uri(f"/portal/{portal.token}/")

    # Touch-ups submitted via the portal
    portal_touchups = (
        TouchUp.objects.filter(project=project)
        .exclude(resident_name="")
        .order_by("-created_at")[:50]
    )

    return render(request, "core/portal/portal_manage.html", {
        "project": project,
        "portal": portal,
        "portal_url": portal_url,
        "units": units,
        "sessions": sessions,
        "portal_touchups": portal_touchups,
    })
