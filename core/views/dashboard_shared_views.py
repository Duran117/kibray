"""Shared dashboard helpers — focus wizard, dispatch, superintendent stub."""
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





@login_required
def focus_wizard(request):
    """Executive Focus Wizard: 4-Step Daily Planning (Pareto + Eat That Frog).

    Step 1: Brain Dump (capture all tasks)
    Step 2: 80/20 Filter (identify high impact tasks)
    Step 3: The Frog (select #1 most important task)
    Step 4: Battle Plan (break down frog + time blocking)
    """
    context = {
        "title": "Executive Focus Wizard",
        "today": timezone.localdate(),
        "user_token": request.user.id,  # For calendar feed URL
    }
    return render(request, "core/focus_wizard.html", context)




# --- DASHBOARD (Redirect to role-based dashboards) ---
@login_required
def dashboard_view(request):
    """
    Smart redirect to appropriate dashboard based on user role.
    This replaces the old generic dashboard.
    """
    user = request.user

    # Apply preferred language from profile if available
    try:
        prof = getattr(user, "profile", None)
        preferred = getattr(prof, "language", None)
        if preferred and request.session.get("lang") != preferred:
            request.session["lang"] = preferred
            translation.activate(preferred)
    except Exception:
        pass

    # Get user profile to determine role
    profile = getattr(user, "profile", None)
    role = getattr(profile, "role", None)

    # Check if user has an Employee record (priority for employee redirect)
    from core.models import Employee

    has_employee = Employee.objects.filter(user=user).exists()

    # Redirect based on role
    if user.is_superuser or (profile and role == "admin"):
        return redirect("dashboard_admin")
    elif profile and role in ["client", "superintendent"]:
        # Unificación: superintendente utiliza vista cliente/builder
        return redirect("dashboard_client")
    elif profile and role == "project_manager":
        return redirect("dashboard_pm")
    elif profile and role == "employee":
        return redirect("dashboard_employee")
    elif profile and role == "designer":
        return redirect("dashboard_designer")
    # Rol superintendente ya cubierto arriba por cliente/builder unificado
    # PRIORITY FIX: If user has Employee record, always go to employee dashboard
    elif has_employee:
        return redirect("dashboard_employee")
    else:
        # Default: check if user is staff -> PM dashboard, otherwise employee
        if user.is_staff:
            return redirect("dashboard_pm")
        else:
            return redirect("dashboard_employee")




@login_required
def dashboard_superintendent(request):
    """Dashboard for superintendents - manage damage reports, touch-ups, task assignments."""
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != "superintendent":
        return HttpResponseForbidden("Acceso restringido a superintendentes")

    employee = Employee.objects.filter(user=request.user).first()

    # Projects assigned to this superintendent (via damage reports or tasks)
    project_ids = set()

    # Via damage reports
    damage_projects = DamageReport.objects.values_list("project_id", flat=True).distinct()
    project_ids.update(damage_projects)

    # Via assigned touch-ups
    if employee:
        touchup_projects = (
            Task.objects.filter(assigned_to=employee, is_touchup=True)
            .values_list("project_id", flat=True)
            .distinct()
        )
        project_ids.update(touchup_projects)

    projects = Project.objects.filter(id__in=project_ids).order_by("-created_at")[:10]

    # Open damage reports
    damages = (
        DamageReport.objects.filter(project__in=projects, status__in=["reported", "in_repair"])
        .select_related("project", "reported_by")
        .order_by("-created_at")[:15]
    )

    # Assigned touch-ups
    touchups = (
        (
            Task.objects.filter(
                assigned_to=employee, is_touchup=True, status__in=["Pending", "In Progress"]
            )
            .select_related("project")
            .order_by("-created_at")[:15]
        )
        if employee
        else Task.objects.none()
    )

    # Unassigned touch-ups (for assignment)
    unassigned_touchups = (
        Task.objects.filter(
            project__in=projects, is_touchup=True, assigned_to__isnull=True, status="Pending"
        )
        .select_related("project")
        .order_by("-created_at")[:10]
    )

    # === MORNING BRIEFING (On-site Management) ===
    morning_briefing = []

    # Category: issues (Damage reports)
    if damages:
        count = len(damages)
        morning_briefing.append(
            {
                "text": f"Hay {count} {'reporte de daño' if count == 1 else 'reportes de daño'} en progreso",
                "severity": "danger" if count > 3 else "warning",
                "action_url": "#",
                "action_label": "Ver reportes",
                "category": "issues",
            }
        )

    # Category: tasks (Touch-ups to assign)
    if unassigned_touchups:
        count = len(unassigned_touchups)
        morning_briefing.append(
            {
                "text": f"Hay {count} {'reparación' if count == 1 else 'reparaciones'} sin asignar",
                "severity": "warning",
                "action_url": "#",
                "action_label": "Asignar",
                "category": "tasks",
            }
        )

    # Category: progress (My touch-ups)
    if touchups:
        count = len(touchups)
        morning_briefing.append(
            {
                "text": f"Tú tienes {count} {'reparación' if count == 1 else 'reparaciones'} asignada{'s' if count > 1 else ''}",
                "severity": "info",
                "action_url": "#",
                "action_label": "Ver mis reparaciones",
                "category": "progress",
            }
        )

    # Apply filter if requested
    active_filter = request.GET.get("filter", "all")
    if active_filter != "all":
        morning_briefing = [
            item for item in morning_briefing if item.get("category") == active_filter
        ]

    return render(
        request,
        "core/dashboard_superintendent.html",
        {
            "projects": projects,
            "damages": damages,
            "touchups": touchups,
            "unassigned_touchups": unassigned_touchups,
            "morning_briefing": morning_briefing,
            "active_filter": active_filter,
        },
    )


