"""Client-facing project portal views (client_project_view, documents, financials)."""
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





# --- CLIENTE: Vista de proyecto y formularios ---
@login_required
def client_project_view(request, project_id):
    """
    Dashboard completo de UN proyecto individual para el cliente.
    El cliente ve: pending requests, minutas, fotos, schedule, tareas/touch-ups,
    pending contracts/COs for signature, color sample approvals, daily logs.
    """
    project = get_object_or_404(Project, id=project_id)

    # SECURITY: Reuse centralised access check
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)

    # === SOLICITUDES Y COMUNICACIÓN ===
    from core.models import ClientRequest, ProjectMinute

    # Pending client requests (cosas que el cliente solicitó)
    pending_requests = ClientRequest.objects.filter(project=project, status="pending").order_by(
        "-created_at"
    )

    # Minutas visibles para cliente (decisiones, cambios, milestones)
    project_minutes = ProjectMinute.objects.filter(
        project=project, visible_to_client=True
    ).order_by("-event_date")[:10]

    # === FOTOS DEL PROYECTO ===
    from core.models import SitePhoto

    recent_photos = SitePhoto.objects.filter(project=project).order_by("-created_at")[:12]

    # === MUESTRAS DE COLOR ===
    color_samples = project.color_samples.all().order_by("-created_at")[:8]

    # === SCHEDULE PRÓXIMO ===
    upcoming_schedules = Schedule.objects.filter(
        project=project, start_datetime__gte=timezone.now()
    ).order_by("start_datetime")[:5]

    # === TAREAS Y TOUCH-UPS ===
    # Tasks incluyen touch-ups que el cliente puede agregar
    tasks = Task.objects.filter(project=project).order_by("-created_at")
    pending_tasks = tasks.filter(status__in=["Pending", "In Progress"])
    completed_tasks = tasks.filter(status="Completed")[:10]

    # Touch-ups V2 (sistema principal)
    project_touchups_v2 = TouchUp.objects.filter(
        project=project
    ).select_related("assigned_to__user", "floor_plan").prefetch_related("photos").order_by("-created_at")
    active_touchups_v2 = project_touchups_v2.filter(status__in=["open", "in_progress", "review"])
    closed_touchups_v2 = project_touchups_v2.filter(status="closed")[:10]

    # === COMENTARIOS ===
    comments = Comment.objects.filter(project=project).order_by("-created_at")[:10]

    # === FACTURAS ===
    invoices = project.invoices.all().order_by("-date_issued")[:5]
    total_invoiced = invoices.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")
    total_paid = invoices.aggregate(paid=Sum("amount_paid"))["paid"] or Decimal("0")

    # === CONTRACT & CHANGE ORDERS ===
    from core.models import ChangeOrder, Estimate
    
    # Base contract (latest approved estimate)
    latest_estimate = Estimate.objects.filter(
        project=project, approved=True
    ).order_by('-version').first()
    
    base_contract_total = Decimal("0")
    if latest_estimate:
        # total_price is a property, so we need to sum manually
        base_contract_total = sum(
            line.total_price for line in latest_estimate.lines.all()
        ) or Decimal("0")
    
    # Change Orders - considering client signature status
    all_project_cos = ChangeOrder.objects.filter(project=project).order_by('-date_created')
    
    # Approved and SIGNED by client - these are truly approved
    approved_cos = all_project_cos.filter(
        status__in=['approved', 'sent', 'billed', 'paid']
    ).exclude(signed_at__isnull=True, status='approved')  # Exclude approved but not signed
    
    # Pending includes:
    # 1. status='pending' (waiting admin approval)
    # 2. status='approved' but signed_at=None (approved by admin, waiting client signature)
    pending_for_admin = all_project_cos.filter(status='pending')
    pending_for_client = all_project_cos.filter(status='approved', signed_at__isnull=True)
    pending_cos = pending_for_admin | pending_for_client
    
    # Calculate totals - for T&M COs, calculate dynamic total from time entries & expenses
    from core.services.financial_service import ChangeOrderService
    
    def get_co_total(co):
        """Get CO total - for T&M calculates from time entries & expenses"""
        if co.pricing_type == 'T_AND_M':
            billable = ChangeOrderService.get_billable_amount(co)
            return billable.get('grand_total', Decimal("0"))
        return co.amount or Decimal("0")
    
    # Annotate COs for template use
    for co in all_project_cos:
        co.calculated_total = get_co_total(co)
        co.pending_client_signature = (co.status == 'approved' and not co.signed_at)
    
    approved_cos_total = sum(get_co_total(co) for co in approved_cos)
    pending_cos_total = sum(get_co_total(co) for co in pending_cos)
    total_contract_value = base_contract_total + approved_cos_total

    # === PROGRESO DEL PROYECTO (usando Gantt V2/V1) ===
    from core.services.schedule_unified import get_project_progress
    gantt_progress = get_project_progress(project)
    progress_pct = gantt_progress.get('progress_percent', 0)
    
    # Fallback si no hay items en el Gantt
    if gantt_progress.get('total_items', 0) == 0:
        try:
            metrics = compute_project_ev(project)
            if metrics and metrics.get("PV") and metrics["PV"] > 0:
                progress_pct = min(100, (metrics.get("EV", 0) / metrics["PV"]) * 100)
        except Exception:
            # Fallback: progreso basado en fechas
            if project.start_date and project.end_date:
                total_days = (project.end_date - project.start_date).days
                elapsed_days = (timezone.localdate() - project.start_date).days
                progress_pct = min(100, (elapsed_days / total_days * 100)) if total_days > 0 else 0

    # === PROJECT MANAGER (from PM assignments) ===
    from core.models import ProjectManagerAssignment
    pm_assignment = ProjectManagerAssignment.objects.filter(
        project=project
    ).select_related("pm").first()
    project_manager = pm_assignment.pm if pm_assignment else None

    # === PUBLIC FILES ===
    from core.models import ProjectFile
    public_files = ProjectFile.objects.filter(
        project=project, is_public=True
    ).select_related("category").order_by("-uploaded_at")[:10]

    # === FLOOR PLANS (for touch-up location picker) ===
    from core.models import FloorPlan
    floor_plans = FloorPlan.objects.filter(
        project=project, is_current=True
    ).order_by("level", "name")

    # === CONTRACTS PENDING SIGNATURE ===
    from core.models import Contract
    pending_contracts = Contract.objects.filter(
        project=project,
        status="pending_signature",
    ).order_by("-created_at")[:5]

    # === CHANGE ORDERS PENDING CLIENT SIGNATURE ===
    from core.services.financial_service import ChangeOrderService as _COService
    pending_change_orders = ChangeOrder.objects.filter(
        project=project,
        status__in=["approved", "sent"],
        signed_at__isnull=True,
    ).filter(
        Q(signature_image__isnull=True) | Q(signature_image="")
    ).order_by("-date_created")[:10]
    for co in pending_change_orders:
        if co.pricing_type == "T_AND_M":
            co.calculated_total = _COService.get_billable_amount(co).get("grand_total", Decimal("0"))
        else:
            co.calculated_total = co.amount or Decimal("0")

    # === COLOR SAMPLES PENDING APPROVAL ===
    from core.models import ColorSample
    pending_color_samples = ColorSample.objects.filter(
        project=project,
        status__in=["proposed", "review"],
    ).order_by("-created_at")[:5]

    # === DAILY LOGS (published only — visible to client) ===
    from core.models import DailyLog
    recent_daily_logs = DailyLog.objects.filter(
        project=project,
        is_published=True,
    ).select_related("created_by").order_by("-date")[:5]

    # === UNREAD NOTIFICATIONS COUNT ===
    unread_notifications = Notification.objects.filter(
        user=request.user,
        project=project,
        is_read=False,
    ).count()

    context = {
        "project": project,
        "pending_requests": pending_requests,
        "project_minutes": project_minutes,
        "recent_photos": recent_photos,
        "upcoming_schedules": upcoming_schedules,
        "tasks": tasks,
        "pending_tasks": pending_tasks,
        "completed_tasks": completed_tasks,
        "active_touchups_v2": active_touchups_v2,
        "closed_touchups_v2": closed_touchups_v2,
        "comments": comments,
        "invoices": invoices,
        "total_invoiced": total_invoiced,
        "total_paid": total_paid,
        "balance": total_invoiced - total_paid,
        "progress_pct": int(progress_pct),
        "gantt_progress": gantt_progress,
        "color_samples": color_samples,
        "project_manager": project_manager,
        "public_files": public_files,
        "floor_plans": floor_plans,
        # Financial summary
        "latest_estimate": latest_estimate,
        "base_contract_total": base_contract_total,
        "approved_cos": approved_cos,
        "pending_cos": pending_cos,
        "approved_cos_total": approved_cos_total,
        "pending_cos_total": pending_cos_total,
        "total_contract_value": total_contract_value,
        # Actionable items for client
        "pending_contracts": pending_contracts,
        "pending_change_orders": pending_change_orders,
        "pending_color_samples": pending_color_samples,
        "recent_daily_logs": recent_daily_logs,
        "unread_notifications": unread_notifications,
    }
    return render(request, "core/client_project_view.html", context)




@login_required
def client_documents_view(request, project_id):
    """
    Documents workspace view for clients.
    Uses the same workspace as PM but only shows PUBLIC files.
    SECURITY: Only shows files marked as is_public=True for the specific project.
    """
    from core.models import ClientProjectAccess, ProjectFile, FileCategory, DocumentTag
    from django.db.models import Q, Count
    
    project = get_object_or_404(Project, id=project_id)

    # === STRICT ACCESS CONTROL ===
    profile = getattr(request.user, "profile", None)
    has_explicit_access = ClientProjectAccess.objects.filter(
        user=request.user, project=project
    ).exists()
    
    is_project_client = False
    if project.client:
        client_text = project.client.strip().lower()
        is_project_client = client_text in (
            request.user.email.lower(),
            request.user.get_full_name().lower(),
            request.user.username.lower(),
        )
    
    if profile and profile.role == "client":
        if not (has_explicit_access or is_project_client):
            messages.error(request, _("You don't have access to this project."))
            return redirect("dashboard_client")
    elif not (request.user.is_staff or has_explicit_access):
        messages.error(request, _("Access denied."))
        return redirect("dashboard")

    # === GET CATEGORIES (only show those with public files) ===
    # Get categories that have at least one public file
    categories = FileCategory.objects.filter(
        project=project
    ).annotate(
        public_file_count=Count('files', filter=Q(files__is_public=True))
    ).filter(parent=None).order_by('order')
    
    # Get selected category
    selected_category_id = request.GET.get("category")
    selected_category = None
    if selected_category_id:
        selected_category = FileCategory.objects.filter(
            id=selected_category_id, 
            project=project
        ).first()

    # === BUILD FILE QUERYSET - ONLY PUBLIC FILES ===
    files = ProjectFile.objects.filter(
        project=project,
        is_public=True  # CRITICAL: Only public files for clients
    ).select_related("category", "uploaded_by").prefetch_related("document_tags")

    # Filter by category
    if selected_category_id:
        files = files.filter(category_id=selected_category_id)

    # Filter by favorites (client can have their own favorites)
    if request.GET.get("favorites"):
        files = files.filter(is_favorited=True)

    # Filter by tag
    tag_filter = request.GET.get("tag")
    if tag_filter:
        files = files.filter(document_tags__id=tag_filter)

    # Search filter
    search_query = request.GET.get("q")
    if search_query:
        files = files.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(tags__icontains=search_query)
        )

    files = files.order_by("-uploaded_at")

    # Get all tags that have public files
    all_tags = DocumentTag.objects.filter(
        project=project,
        files__is_public=True
    ).distinct()
    
    # Stats (only public files)
    total_files = ProjectFile.objects.filter(project=project, is_public=True).count()
    favorites_count = ProjectFile.objects.filter(
        project=project, is_public=True, is_favorited=True
    ).count()

    return render(
        request,
        "core/documents_workspace.html",  # Same workspace template, with is_client_view flag
        {
            "project": project,
            "categories": categories,
            "files": files,
            "selected_category": selected_category,
            "selected_category_id": selected_category_id,
            "search_query": search_query or "",
            "all_tags": all_tags,
            "total_files": total_files,
            "favorites_count": favorites_count,
            "public_count": total_files,  # All visible files are public for client
            "is_client_view": True,  # Flag to hide upload/edit features
        },
    )




@login_required
def client_financials_view(request, project_id):
    """
    Dedicated financial analytics page for clients.
    Shows: Contract breakdown, Change Orders, Invoices, Payments with charts.
    """
    project = get_object_or_404(Project, id=project_id)

    # Access control (same as client_project_view)
    profile = getattr(request.user, "profile", None)
    from core.models import ClientProjectAccess
    has_explicit_access = ClientProjectAccess.objects.filter(
        user=request.user, project=project
    ).exists()
    
    if profile and profile.role == "client":
        if not (has_explicit_access or project.client == request.user.username):
            messages.error(request, "You don't have access to this project.")
            return redirect("dashboard_client")
    else:
        if not (request.user.is_staff or has_explicit_access):
            messages.error(request, "Access denied.")
            return redirect("dashboard")

    # === CONTRACT DATA ===
    from core.models import ChangeOrder, Estimate, Invoice, InvoicePayment
    
    # Base contract (latest approved estimate)
    latest_estimate = Estimate.objects.filter(
        project=project, approved=True
    ).order_by('-version').first()
    
    base_contract_total = Decimal("0")
    estimate_lines = []
    if latest_estimate:
        estimate_lines = latest_estimate.lines.select_related('budget_line').all()
        base_contract_total = sum(line.total_price or Decimal("0") for line in estimate_lines)
    
    # Change Orders by status
    all_change_orders = ChangeOrder.objects.filter(project=project).order_by('-date_created')
    
    # Approved and SIGNED by client - these are truly approved
    approved_cos = all_change_orders.filter(
        status__in=['approved', 'sent', 'billed', 'paid']
    ).exclude(signed_at__isnull=True, status='approved')  # Exclude approved but not signed
    
    # Pending includes: 
    # 1. status='pending' (waiting admin approval)
    # 2. status='approved' but signed_at=None (approved by admin, waiting client signature)
    pending_for_admin = all_change_orders.filter(status='pending')
    pending_for_client = all_change_orders.filter(status='approved', signed_at__isnull=True)
    pending_cos = pending_for_admin | pending_for_client  # Union of both querysets
    
    billed_cos = all_change_orders.filter(status__in=['billed', 'paid'])
    
    # Calculate totals - for T&M COs, calculate dynamic total from time entries & expenses
    from core.services.financial_service import ChangeOrderService
    
    def get_co_total(co):
        """Get CO total - for T&M calculates from time entries & expenses"""
        if co.pricing_type == 'T_AND_M':
            billable = ChangeOrderService.get_billable_amount(co)
            return billable.get('grand_total', Decimal("0"))
        return co.amount or Decimal("0")
    
    # Annotate each CO with its calculated total for template use
    for co in all_change_orders:
        co.calculated_total = get_co_total(co)
        # Mark if pending client signature
        co.pending_client_signature = (co.status == 'approved' and not co.signed_at)
    
    approved_cos_total = sum(get_co_total(co) for co in approved_cos)
    pending_cos_total = sum(get_co_total(co) for co in pending_cos)
    billed_cos_total = sum(get_co_total(co) for co in billed_cos)
    total_contract_value = base_contract_total + approved_cos_total
    
    # === INVOICES DATA ===
    invoices = Invoice.objects.filter(project=project).order_by('-date_issued')
    total_invoiced = sum(inv.total_amount or Decimal("0") for inv in invoices)
    total_paid = sum(inv.amount_paid or Decimal("0") for inv in invoices)
    balance = total_invoiced - total_paid
    
    # === PAYMENT HISTORY ===
    payments = InvoicePayment.objects.filter(
        invoice__project=project
    ).select_related('invoice').order_by('-payment_date')[:20]
    
    # === PROGRESSIVE BILLING DATA ===
    # Calculate % billed per estimate line (for progressive billing visualization)
    from core.models import InvoiceLineEstimate
    lines_billing_data = []
    for line in estimate_lines:
        invoiced_for_line = InvoiceLineEstimate.objects.filter(
            estimate_line=line
        ).aggregate(total=Sum('amount'))['total'] or Decimal("0")
        pct_billed = (invoiced_for_line / line.total_price * 100) if line.total_price else 0
        lines_billing_data.append({
            'line': line,
            'invoiced': invoiced_for_line,
            'remaining': line.total_price - invoiced_for_line,
            'pct_billed': min(100, float(pct_billed)),
        })
    
    # === CHART DATA (for Chart.js) ===
    import json
    contract_breakdown_chart = {
        'labels': json.dumps(['Base Contract', 'Approved COs', 'Pending COs']),
        'data': json.dumps([float(base_contract_total), float(approved_cos_total), float(pending_cos_total)]),
        'colors': json.dumps(['#667eea', '#28a745', '#ffc107']),
    }
    payment_status_chart = {
        'labels': json.dumps(['Contract Value', 'Invoiced', 'Paid']),
        'data': json.dumps([float(total_contract_value), float(total_invoiced), float(total_paid)]),
        'colors': json.dumps(['#667eea', '#17a2b8', '#28a745']),
    }
    
    # Total for all COs
    all_cos_total = approved_cos_total + pending_cos_total

    # Percentages for template
    invoiced_pct = float(total_invoiced / total_contract_value * 100) if total_contract_value else 0
    paid_pct = float(total_paid / total_contract_value * 100) if total_contract_value else 0

    # Recent payments (for template section)
    recent_payments = payments[:10]

    # Estimate lines data for progressive billing table
    estimate_lines_data = []
    for lbd in lines_billing_data:
        line = lbd['line']
        estimate_lines_data.append({
            'code': getattr(line, 'code', '') or getattr(line.budget_line, 'code', '') if hasattr(line, 'budget_line') and line.budget_line else '',
            'description': line.description or '',
            'direct_cost': line.total_price or Decimal("0"),
            'already_pct': lbd['pct_billed'],
        })

    context = {
        "project": project,
        "latest_estimate": latest_estimate,
        "estimate_lines": estimate_lines,
        "estimate_lines_data": estimate_lines_data,
        "lines_billing_data": lines_billing_data,
        "base_contract_total": base_contract_total,
        "change_orders": all_change_orders,  # Alias for template compatibility
        "all_change_orders": all_change_orders,
        "approved_cos": approved_cos,
        "pending_cos": pending_cos,
        "billed_cos": billed_cos,
        "approved_cos_total": approved_cos_total,
        "pending_cos_total": pending_cos_total,
        "billed_cos_total": billed_cos_total,
        "all_cos_total": all_cos_total,
        "total_contract_value": total_contract_value,
        "invoices": invoices,
        "total_invoiced": total_invoiced,
        "total_paid": total_paid,
        "balance": balance,
        "invoiced_pct": invoiced_pct,
        "paid_pct": paid_pct,
        "payments": payments,
        "recent_payments": recent_payments,
        "contract_breakdown_chart": contract_breakdown_chart,
        "payment_status_chart": payment_status_chart,
    }
    return render(request, "core/client_financials.html", context)
