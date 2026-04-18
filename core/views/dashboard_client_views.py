"""Client dashboard views — client portal main entry."""
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





# --- DASHBOARD CLIENTE (VISUAL Y ESTÉTICO) ---
@login_required
def dashboard_client(request):
    """Client visual dashboard with progress, photos, invoices"""
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != "client":
        messages.error(request, "Access restricted to clients only.")
        return redirect("dashboard")

    # Activate user's preferred language
    from django.utils import translation
    user_language = getattr(profile, 'language', None) or 'en'
    translation.activate(user_language)

    # Import unified schedule service for Gantt data
    from core.services.schedule_unified import get_project_progress

    # Client projects: via direct link (legacy) or granular assignment
    access_projects = Project.objects.filter(client_accesses__user=request.user)
    legacy_projects = Project.objects.filter(client=request.user.username)
    projects = access_projects.union(legacy_projects).order_by("-start_date")

    # For each project, calculate visual metrics
    project_data = []
    for project in projects:
        # Invoices
        invoices = project.invoices.all().order_by("-date_issued")[:5]
        total_invoiced = invoices.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")
        total_paid = invoices.aggregate(paid=Sum("amount_paid"))["paid"] or Decimal("0")

        # Progress - use Gantt V2/V1 system
        gantt_progress = get_project_progress(project)
        progress_pct = gantt_progress.get('progress_percent', 0)
        
        # Fallback if no items in Gantt
        if gantt_progress.get('total_items', 0) == 0:
            try:
                metrics = compute_project_ev(project)
                if metrics and metrics.get("PV") and metrics["PV"] > 0:
                    progress_pct = min(100, (metrics.get("EV", 0) / metrics["PV"]) * 100)
            except Exception:
                # Fallback: date-based progress
                if project.start_date and project.end_date:
                    total_days = (project.end_date - project.start_date).days
                    elapsed_days = (timezone.localdate() - project.start_date).days
                    progress_pct = min(100, (elapsed_days / total_days * 100)) if total_days > 0 else 0

        # Recent photos
        from core.models import SitePhoto

        recent_photos = SitePhoto.objects.filter(project=project).order_by("-created_at")[:6]

        # Next schedule - search in Gantt V2 first, then legacy Schedule
        from core.models import ScheduleItemV2
        
        next_schedule = None
        today = timezone.localdate()
        
        # Search in Gantt V2 items - priority:
        # 1. Next future item not completed
        # 2. Item in progress (any date)
        # 3. Next future item (even if completed)
        # 4. Last completed item (most recent)
        
        # 1. Next future item not completed
        next_gantt_item = ScheduleItemV2.objects.filter(
            project=project,
            start_date__gte=today,
            status__in=['planned', 'in_progress']
        ).order_by('start_date').first()
        
        # 2. Item in progress (any date)
        if not next_gantt_item:
            next_gantt_item = ScheduleItemV2.objects.filter(
                project=project,
                status='in_progress'
            ).order_by('-start_date').first()
        
        # 3. Next future item (even if completed)
        if not next_gantt_item:
            next_gantt_item = ScheduleItemV2.objects.filter(
                project=project,
                start_date__gte=today
            ).order_by('start_date').first()
        
        # 4. Last completed item (most recent) - to show latest achievement
        if not next_gantt_item:
            next_gantt_item = ScheduleItemV2.objects.filter(
                project=project,
                status='done'
            ).order_by('-end_date', '-start_date').first()
        
        if next_gantt_item:
            # Create template-compatible object
            class NextEventProxy:
                def __init__(self, item):
                    self.title = item.name
                    self.description = item.description or f"Status: {item.get_status_display()}"
                    # Convert date to datetime for template
                    self.start_datetime = timezone.make_aware(
                        datetime.combine(item.start_date, datetime.min.time())
                    ) if item.start_date else None
                    self.status = item.status
            next_schedule = NextEventProxy(next_gantt_item)
        else:
            # Fallback to legacy Schedule
            next_schedule = (
                Schedule.objects.filter(project=project, start_datetime__gte=timezone.now())
                .order_by("start_datetime")
                .first()
            )

        # Client requests
        from core.models import ClientRequest

        client_requests = ClientRequest.objects.filter(project=project).order_by("-created_at")[:5]

        # Change Orders pending client signature
        # Only show COs that are approved/sent and waiting for client signature
        from core.models import ChangeOrder
        from core.services.financial_service import ChangeOrderService
        
        pending_change_orders = ChangeOrder.objects.filter(
            project=project,
            status__in=['approved', 'sent'],  # Only approved or sent COs (not pending/draft)
            signed_at__isnull=True,  # Not yet signed
        ).filter(
            Q(signature_image__isnull=True) | Q(signature_image='')
        ).order_by('-date_created')[:10]  # Increased limit to 10
        
        # Calculate T&M totals for each pending CO
        for co in pending_change_orders:
            if co.pricing_type == 'T_AND_M':
                tm_data = ChangeOrderService.get_billable_amount(co)
                co.calculated_total = tm_data.get('grand_total', Decimal("0"))
            else:
                co.calculated_total = co.amount or Decimal("0")
        
        # Recently signed Change Orders
        signed_change_orders = ChangeOrder.objects.filter(
            project=project,
        ).exclude(
            Q(signature_image__isnull=True) | Q(signature_image='')
        ).order_by('-signed_at')[:3]
        
        # Color Samples pending approval
        from core.models import ColorSample
        pending_color_samples = ColorSample.objects.filter(
            project=project,
            status__in=['proposed', 'review']
        ).order_by('-created_at')[:5]
        
        # Recently signed/approved Color Samples
        signed_color_samples = ColorSample.objects.filter(
            project=project,
            status='approved'
        ).exclude(
            client_signature__isnull=True
        ).exclude(
            client_signature=''
        ).order_by('-client_signed_at')[:3]

        # Contracts pending signature
        from core.models import Contract
        pending_contracts = Contract.objects.filter(
            project=project,
            status='pending_signature'
        ).order_by('-created_at')[:5]
        
        # Recently signed contracts
        signed_contracts = Contract.objects.filter(
            project=project,
            status__in=['signed', 'active']
        ).exclude(
            client_signed_at__isnull=True
        ).order_by('-client_signed_at')[:3]

        # Recent Daily Logs (only published ones for clients)
        from core.models import DailyLog
        recent_daily_logs = DailyLog.objects.filter(
            project=project,
            is_published=True
        ).select_related('created_by').order_by('-date')[:3]

        project_data.append(
            {
                "project": project,
                "invoices": invoices,
                "total_invoiced": total_invoiced,
                "total_paid": total_paid,
                "balance": total_invoiced - total_paid,
                "progress_pct": int(progress_pct),
                "gantt_progress": gantt_progress,  # Full progress data from Gantt
                "recent_photos": recent_photos,
                "next_schedule": next_schedule,
                "client_requests": client_requests,
                "pending_change_orders": pending_change_orders,
                "signed_change_orders": signed_change_orders,
                "pending_color_samples": pending_color_samples,
                "signed_color_samples": signed_color_samples,
                "pending_contracts": pending_contracts,
                "signed_contracts": signed_contracts,
                "recent_daily_logs": recent_daily_logs,
            }
        )

    # === MORNING BRIEFING (Categorized alerts for client) ===
    morning_briefing = []

    # Category: Updates (new photos, comments)
    latest_photos = []
    for proj_data in project_data:
        latest_photos.extend(proj_data["recent_photos"][:2])

    if latest_photos:
        morning_briefing.append(
            {
                "text": _("There are %(count)s new photos from your project") % {"count": len(latest_photos)},
                "severity": "info",
                "action_url": "#",
                "action_label": _("View photos"),
                "category": "updates",
            }
        )

    # Category: Payments (pending invoices)
    overdue_invoices = []
    for proj_data in project_data:
        for inv in proj_data["invoices"]:
            if proj_data["balance"] > 0:
                overdue_invoices.append(inv)

    if overdue_invoices:
        total_due = sum(inv.total_amount - inv.amount_paid for inv in overdue_invoices)
        invoices_url = reverse("dashboard_client")
        morning_briefing.append(
            {
                "text": _("You have %(amount)s in pending invoices") % {"amount": f"${total_due:,.2f}"},
                "severity": "warning",
                "action_url": invoices_url,
                "action_label": _("View Invoices"),
                "category": "payments",
            }
        )

    # Category: Schedule (upcoming activities)
    upcoming_schedules = []
    for proj_data in project_data:
        if proj_data["next_schedule"]:
            upcoming_schedules.append(proj_data["next_schedule"])

    if upcoming_schedules:
        next_date = upcoming_schedules[0].start_datetime
        morning_briefing.append(
            {
                "text": _("Next activity scheduled for %(date)s") % {"date": next_date.strftime('%m/%d/%Y')},
                "severity": "info",
                "action_url": "#",
                "action_label": _("View schedule"),
                "category": "schedule",
            }
        )

    # Apply filter if requested
    active_filter = request.GET.get("filter", "all")
    if active_filter != "all":
        morning_briefing = [
            item for item in morning_briefing if item.get("category") == active_filter
        ]

    # Get display name (prefer profile display_name, then full name, then username)
    display_name = None
    try:
        prof = getattr(request.user, "profile", None)
        candidate = None
        if prof is not None:
            candidate = getattr(prof, "display_name", None) or getattr(prof, "full_name", None)
        display_name = (candidate or request.user.get_full_name() or request.user.username).strip()
    except Exception:
        display_name = request.user.username

    # Determine active project index from GET param or default to first
    active_project_index = 0
    active_project_id = request.GET.get("project_id")
    if active_project_id:
        for idx, data in enumerate(project_data):
            if str(data["project"].id) == active_project_id:
                active_project_index = idx
                break

    context = {
        "project_data": project_data,
        "today": timezone.localdate(),
        "display_name": display_name,
        "morning_briefing": morning_briefing,
        "active_filter": active_filter,
        "active_project_index": active_project_index,
    }

    # Use premium template (unified design)
    return render(request, "core/dashboard_client_premium.html", context)
