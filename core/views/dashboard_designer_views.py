"""Designer dashboard views."""
from core.views._helpers import *  # noqa: F401, F403
from core.views._helpers import (
    _generate_basic_pdf_from_html,
    _check_user_project_access,
    _is_admin_user,
    _is_pm_or_admin,
    _is_staffish,
    _require_admin_or_redirect,
    _require_roles,
    _parse_date,
    _ensure_inventory_item,
    staff_required,
    logger,
    pisa,
    ROLES_ADMIN,
    ROLES_PM,
    ROLES_STAFF,
    ROLES_FIELD,
    ROLES_ALL_INTERNAL,
    ROLES_CLIENT_SIDE,
    ROLES_PROJECT_ACCESS,
)
from django.utils.translation import gettext_lazy as _  # noqa: F811





# --- DESIGNER & SUPERINTENDENT DASHBOARDS ---
@login_required
def dashboard_designer(request):
    """Dashboard for designers - read-only access to projects, plans, color samples, chat."""
    from django.db import models as db_models

    profile = getattr(request.user, "profile", None)
    is_designer = profile and profile.role == "designer"
    if not is_designer and not request.user.is_superuser:
        return HttpResponseForbidden("Acceso restringido a diseñadores")

    # Projects the designer is involved with (via ColorSample, FloorPlan, or chat)
    projects = (
        Project.objects.filter(
            db_models.Q(color_samples__isnull=False)
            | db_models.Q(floor_plans__isnull=False)
            | db_models.Q(chat_channels__participants=request.user)
        )
        .distinct()
        .order_by("-created_at")[:10]
    )

    # Recent color samples
    color_samples = (
        ColorSample.objects.filter(project__in=projects)
        .select_related("project")
        .order_by("-created_at")[:15]
    )

    # Floor plans
    plans = (
        FloorPlan.objects.filter(project__in=projects)
        .select_related("project")
        .order_by("-created_at")[:10]
    )

    # Recent schedules
    schedules = (
        Schedule.objects.filter(project__in=projects)
        .select_related("project")
        .order_by("-start_datetime")[:10]
    )

    # === MORNING BRIEFING (Design Tasks) ===
    morning_briefing = []

    # Category: designs (New color samples)
    if color_samples:
        count = len(color_samples)
        morning_briefing.append(
            {
                "text": f"Hay {count} nueva{'s' if count > 1 else ''} muestra{'s' if count > 1 else ''} de color",
                "severity": "info",
                "action_url": "#",
                "action_label": "Ver muestras",
                "category": "designs",
            }
        )

    # Category: documents (Plans uploaded)
    if plans:
        count = len(plans)
        morning_briefing.append(
            {
                "text": f"{count} plano{'s' if count > 1 else ''} disponible{'s' if count > 1 else ''} para revisar",
                "severity": "info",
                "action_url": "#",
                "action_label": "Ver planos",
                "category": "documents",
            }
        )

    # Category: schedule (Upcoming meetings)
    if schedules:
        morning_briefing.append(
            {
                "text": f"Tienes {len(schedules)} reunión{'es' if len(schedules) > 1 else ''} programada{'s' if len(schedules) > 1 else ''}",
                "severity": "info",
                "action_url": "#",
                "action_label": "Ver calendario",
                "category": "schedule",
            }
        )

    # Apply filter if requested
    active_filter = request.GET.get("filter", "all")
    if active_filter != "all":
        morning_briefing = [
            item for item in morning_briefing if item.get("category") == active_filter
        ]

    context = {
        "projects": projects,
        "color_samples": color_samples,
        "plans": plans,
        "schedules": schedules,
        "morning_briefing": morning_briefing,
        "active_filter": active_filter,
    }

    return render(request, "core/dashboard_designer.html", context)
