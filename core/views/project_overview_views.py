"""Project overview — main detail page combining all data."""
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
def project_overview(request, project_id: int):
    if not request.user.is_staff:
        messages.error(request, "Acceso solo para PM/Staff.")
        return redirect("dashboard_employee")

    project = get_object_or_404(Project, pk=project_id)

    # Get Gantt progress first (used for progress bar)
    from core.services.schedule_unified import get_project_progress
    gantt_progress = get_project_progress(project)

    # Imports opcionales por si no existen algunos modelos
    # Nota: algunos modelos están importados a nivel de módulo (Task/Schedule/Issue/DailyLog);
    # aquí sólo necesitamos opcionalmente ProjectFile.
    try:
        from core.models import ProjectFile as ProjectFileModel
    except Exception:
        project_file_model = None
    else:
        project_file_model = ProjectFileModel

    try:
        from core.models import Color as ColorModel
    except Exception:
        color_model = None
    else:
        color_model = ColorModel

    try:
        from core.models import LeftoverItem as LeftoverItemModel  # “sobras” de material
    except Exception:
        leftover_item_model = None
    else:
        leftover_item_model = LeftoverItemModel

    # Info básica segura
    project_info = {
        "address": getattr(project, "address", None),
        "city": getattr(project, "city", None),
        "state": getattr(project, "state", None),
        "zip": getattr(project, "zip", None),
        "client": getattr(project, "client", None),
    }

    colors = []
    if color_model:
        colors = list(color_model.objects.filter(project=project).order_by("name"))

    # Fallback: If no Color model records found, parse from Project text fields
    if not colors:

        class SimpleColor:
            def __init__(self, name, code=None, brand=None):
                self.name = name
                self.code = code
                self.brand = brand

        # 1. Paint Colors
        if getattr(project, "paint_colors", None):
            # Split by comma or newline
            import re

            items = re.split(r"[,\n]+", project.paint_colors)
            for item in items:
                clean_item = item.strip()
                if clean_item:
                    colors.append(SimpleColor(name=clean_item, brand="Paint"))

        # 2. Paint Codes
        if getattr(project, "paint_codes", None):
            items = re.split(r"[,\n]+", project.paint_codes)
            for item in items:
                clean_item = item.strip()
                if clean_item:
                    colors.append(SimpleColor(name=clean_item, brand="Code"))

        # 3. Stains/Finishes
        if getattr(project, "stains_or_finishes", None):
            items = re.split(r"[,\n]+", project.stains_or_finishes)
            for item in items:
                clean_item = item.strip()
                if clean_item:
                    colors.append(SimpleColor(name=clean_item, brand="Finish"))

    upcoming_schedules = (
        Schedule.objects.filter(project=project).order_by("start_datetime")[:10] if Schedule else []
    )
    recent_tasks = Task.objects.filter(project=project).order_by("-id")[:10] if Task else []
    recent_issues = (
        Issue.objects.filter(project=project).order_by("-created_at")[:10] if Issue else []
    )
    recent_logs = (
        DailyLog.objects.filter(project=project).order_by("-date")[:10] if DailyLog else []
    )
    files = (
        project_file_model.objects.filter(project=project).order_by("-uploaded_at")[:10]
        if project_file_model
        else []
    )

    # Load Gantt V2 items for upcoming tasks display
    upcoming_gantt_items = []
    try:
        from core.models import ScheduleItemV2, SchedulePhaseV2
        from datetime import date, timedelta
        
        today = date.today()
        # Get items from today onwards, sorted by start_date
        gantt_items = (
            ScheduleItemV2.objects
            .filter(project=project, start_date__gte=today)
            .select_related('phase', 'assigned_to')
            .order_by('start_date', 'order')[:10]
        )
        
        # If no future items, get recent/current items
        if not gantt_items.exists():
            gantt_items = (
                ScheduleItemV2.objects
                .filter(project=project)
                .select_related('phase', 'assigned_to')
                .order_by('-start_date', 'order')[:10]
            )
        
        for item in gantt_items:
            upcoming_gantt_items.append({
                'id': item.id,
                'title': item.name,
                'start_date': item.start_date,
                'end_date': item.end_date,
                'status': item.status,
                'progress': item.progress,
                'is_milestone': item.is_milestone,
                'phase_name': item.phase.name if item.phase else None,
                'phase_color': item.phase.color if item.phase else '#6366f1',
                'assigned_to': item.assigned_to.get_full_name() if item.assigned_to else None,
            })
    except Exception as e:
        # If ScheduleItemV2 doesn't exist or any error, keep empty list
        pass

    # Floor Plans data
    try:
        from core.models import FloorPlan, PlanPin

        floor_plans = FloorPlan.objects.filter(project=project).order_by("level")[:5]
        total_floor_plans = FloorPlan.objects.filter(project=project).count()
        total_pins = PlanPin.objects.filter(floor_plan__project=project).count()
    except Exception:
        floor_plans = []
        total_floor_plans = 0
        total_pins = 0

    # Touch-ups data
    try:
        from core.models import TouchUpPin

        touchups_pending = TouchUpPin.objects.filter(
            floor_plan__project=project, status="pending"
        ).count()
        touchups_in_progress = TouchUpPin.objects.filter(
            floor_plan__project=project, status="in_progress"
        ).count()
        touchups_completed = TouchUpPin.objects.filter(
            floor_plan__project=project, status="completed"
        ).count()
        total_touchups = touchups_pending + touchups_in_progress + touchups_completed
        recent_touchups = (
            TouchUpPin.objects.filter(floor_plan__project=project)
            .select_related("floor_plan", "assigned_to")
            .order_by("-created_at")[:5]
        )
    except Exception:
        touchups_pending = 0
        touchups_in_progress = 0
        touchups_completed = 0
        total_touchups = 0
        recent_touchups = []

    # Change Orders data
    try:
        from core.models import ChangeOrder

        cos_draft = ChangeOrder.objects.filter(project=project, status="draft").count()
        cos_review = ChangeOrder.objects.filter(project=project, status="review").count()
        cos_approved = ChangeOrder.objects.filter(project=project, status="approved").count()
        cos_in_progress = ChangeOrder.objects.filter(project=project, status="in_progress").count()
        cos_completed = ChangeOrder.objects.filter(project=project, status="completed").count()
        total_cos = ChangeOrder.objects.filter(project=project).count()
    except Exception:
        cos_draft = 0
        cos_review = 0
        cos_approved = 0
        cos_in_progress = 0
        cos_completed = 0
        total_cos = 0

    leftovers = []
    if leftover_item_model:
        q = leftover_item_model.objects.filter(project=project)
        # si hay campo category, filtra pintura/stain/lacquer
        try:
            leftovers = q.filter(category__in=["paint", "stain", "lacquer"]).order_by(
                "category", "name"
            )
        except Exception:
            leftovers = q.order_by("id")

    # Resident Portal data
    portal_active = False
    portal_touchup_count = 0
    portal_session_count = 0
    portal_unit_count = 0
    try:
        from core.models import ResidentPortal, TouchUp as TouchUpModel

        portal_obj = ResidentPortal.objects.filter(project=project).first()
        if portal_obj:
            portal_active = portal_obj.is_active
            portal_touchup_count = (
                TouchUpModel.objects.filter(project=project)
                .exclude(resident_name="")
                .exclude(resident_name__isnull=True)
                .count()
            )
            portal_session_count = portal_obj.sessions.count()
            portal_unit_count = project.units.count()
    except Exception:
        pass

    # Phase D follow-up — Earned Value + Critical Path widgets.
    # Both helpers are exception-safe and return None on missing data so
    # the template can render a friendly placeholder.
    from core.services.dashboard_widgets import (
        get_critical_path_widget,
        get_ev_sparkline,
        get_ev_widget,
    )

    ev_widget = get_ev_widget(project)
    ev_sparkline = get_ev_sparkline(project)
    critical_path_widget = get_critical_path_widget(project)

    return render(
        request,
        "core/project_overview.html",
        {
            "project": project,
            "project_info": project_info,
            "show_sidebar": False,  # Hide global sidebar, use project-specific Asana-style sidebar
            "colors": colors,
            "upcoming_schedules": upcoming_schedules,
            "upcoming_gantt_items": upcoming_gantt_items,
            "recent_tasks": recent_tasks,
            "recent_issues": recent_issues,
            "recent_logs": recent_logs,
            "files": files,
            "leftovers": leftovers,
            # Gantt Progress
            "gantt_progress": gantt_progress,
            # Floor Plans
            "floor_plans": floor_plans,
            "total_floor_plans": total_floor_plans,
            "total_pins": total_pins,
            # Touch-ups
            "touchups_pending": touchups_pending,
            "touchups_in_progress": touchups_in_progress,
            "touchups_completed": touchups_completed,
            "total_touchups": total_touchups,
            "recent_touchups": recent_touchups,
            # Change Orders
            "cos_draft": cos_draft,
            "cos_review": cos_review,
            "cos_approved": cos_approved,
            "cos_in_progress": cos_in_progress,
            "cos_completed": cos_completed,
            "total_cos": total_cos,
            # Resident Portal
            "portal_active": portal_active,
            "portal_touchup_count": portal_touchup_count,
            "portal_session_count": portal_session_count,
            "portal_unit_count": portal_unit_count,
            # Phase D follow-up widgets
            "ev_widget": ev_widget,
            "ev_sparkline": ev_sparkline,
            "critical_path_widget": critical_path_widget,
        },
    )


# ---------------------------------------------------------------------------
# Critical Path drill-down (Phase D follow-up)
# ---------------------------------------------------------------------------


@login_required
def project_critical_path(request, project_id: int):
    """Full-page Critical Path drill-down for a single project.

    Renders the complete CPM table (ES/EF/LS/LF/slack + critical badge) plus
    a simple horizontal Gantt-style bar visualisation. Defensive against
    cycles in the dependency graph: returns a 200 with a friendly error
    instead of crashing the page.

    Query params
    ------------
    ``critical_only=1`` — filter the rendered table to critical tasks only.
    """
    if not request.user.is_staff:
        messages.error(request, "Acceso solo para PM/Staff.")
        return redirect("dashboard_employee")

    project = get_object_or_404(Project, pk=project_id)

    from core.services.critical_path import (
        compute_critical_path,
        CriticalPathCycleError,
    )

    cpm_error = None
    try:
        cpm = compute_critical_path(project.id)
    except CriticalPathCycleError as exc:
        cpm_error = str(exc) or "cycle_detected"
        cpm = {
            "tasks": [],
            "edges": [],
            "critical_path_ids": [],
            "project_duration_minutes": 0,
        }
    except Exception:  # pragma: no cover — extra safety net
        logger.exception("Unexpected error computing critical path for project %s", project.id)
        cpm = {
            "tasks": [],
            "edges": [],
            "critical_path_ids": [],
            "project_duration_minutes": 0,
        }

    show_critical_only = request.GET.get("critical_only") == "1"
    visible_tasks = (
        [t for t in cpm["tasks"] if t.get("is_critical")]
        if show_critical_only
        else cpm["tasks"]
    )

    project_duration_minutes = int(cpm.get("project_duration_minutes") or 0)
    project_duration_hours = round(project_duration_minutes / 60, 1)
    critical_count = sum(1 for t in cpm["tasks"] if t.get("is_critical"))

    # Pre-compute bar offsets/widths (% of project_duration_minutes) for the
    # template — keeps the template free of math and lets us assert deterministic
    # output in tests.
    bars = []
    if project_duration_minutes > 0:
        for t in visible_tasks:
            es = int(t.get("es") or 0)
            dur = int(t.get("duration_minutes") or 0)
            offset_pct = round(100 * es / project_duration_minutes, 2)
            width_pct = round(100 * max(dur, 1) / project_duration_minutes, 2)
            # Clamp so widths don't push past 100% due to rounding.
            if offset_pct + width_pct > 100:
                width_pct = round(100 - offset_pct, 2)
            bars.append(
                {
                    "task_id": t["task_id"],
                    "title": t.get("title") or f"Task #{t['task_id']}",
                    "is_critical": t.get("is_critical", False),
                    "offset_pct": offset_pct,
                    "width_pct": max(width_pct, 0.5),
                    "duration_minutes": dur,
                    "slack_minutes": int(t.get("slack_minutes") or 0),
                }
            )

    return render(
        request,
        "core/project_critical_path.html",
        {
            "project": project,
            "show_sidebar": False,
            "cpm": cpm,
            "cpm_error": cpm_error,
            "visible_tasks": visible_tasks,
            "show_critical_only": show_critical_only,
            "project_duration_minutes": project_duration_minutes,
            "project_duration_hours": project_duration_hours,
            "task_count": len(cpm["tasks"]),
            "critical_count": critical_count,
            "bars": bars,
        },
    )
