"""Project views — CRUD, overview, client portal, financials."""
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


# --- PROJECT PDF ---
@login_required
def project_pdf_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)
    
    incomes = Income.objects.filter(project=project).select_related("change_order")
    expenses = Expense.objects.filter(project=project).select_related("change_order", "cost_code")
    time_entries = TimeEntry.objects.filter(project=project).select_related("employee")
    schedules = Schedule.objects.filter(project=project).order_by("start_datetime")

    total_income = incomes.aggregate(total=Sum("amount"))["total"] or 0
    total_expense = expenses.aggregate(total=Sum("amount"))["total"] or 0
    profit = total_income - total_expense
    total_hours = sum([te.hours_worked for te in time_entries])
    labor_cost = sum([te.labor_cost for te in time_entries])

    context = {
        "project": project,
        "incomes": incomes,
        "expenses": expenses,
        "schedules": schedules,
        "total_income": total_income,
        "total_expense": total_expense,
        "profit": profit,
        "total_hours": total_hours,
        "labor_cost": labor_cost,
        "logo_url": request.build_absolute_uri("/static/Kibray.jpg"),
        "user": request.user,
        "now": timezone.now(),  # <-- reemplazo
    }

    template = get_template("core/project_pdf.html")
    html = template.render(context)
    # Prefer xhtml2pdf if available; otherwise fallback to basic PDF
    if pisa:
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        if not pdf.err:
            return HttpResponse(result.getvalue(), content_type="application/pdf")
    fallback_bytes = _generate_basic_pdf_from_html(html)
    return HttpResponse(fallback_bytes, content_type="application/pdf")



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



@login_required
def project_activation_view(request, project_id):
    """
    Project Activation Wizard - Automates transition from Sales to Production.

    Converts approved estimate into operational entities:
    - ScheduleItems for Gantt
    - BudgetLines for financial control
    - Tasks for daily operations
    - Invoice for deposit/advance
    """
    from core.services.activation_service import ProjectActivationService

    project = get_object_or_404(Project, pk=project_id)

    # Check permissions (PM, admin, superuser only)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"]:
        messages.error(request, "No tienes permisos para activar proyectos")
        return redirect("dashboard")

    # Get approved estimate
    estimate = project.estimates.filter(approved=True).order_by("-version").first()

    if not estimate:
        messages.error(request, "No hay estimado aprobado para este proyecto")
        return redirect("project_overview", project_id=project.id)

    # Check if already activated
    has_schedule = project.schedule_items.exists()
    has_budget = project.budget_lines.exists()

    if request.method == "POST":
        form = ActivationWizardForm(request.POST, estimate=estimate)

        if form.is_valid():
            try:
                # Initialize service
                service = ProjectActivationService(project=project, estimate=estimate)

                # Get form data
                start_date = form.cleaned_data["start_date"]
                create_schedule = form.cleaned_data["create_schedule"]
                create_budget = form.cleaned_data["create_budget"]
                create_tasks = form.cleaned_data["create_tasks"]
                deposit_percent = form.cleaned_data.get("deposit_percent", 0)
                items_to_schedule = form.cleaned_data.get("items_to_schedule")
                # Selected line IDs (spec wants passing IDs)
                selected_line_ids = (
                    [line.id for line in items_to_schedule]
                    if items_to_schedule and items_to_schedule.exists()
                    else None
                )

                # Get employee from user if exists (for task assignment)
                from core.models import Employee

                employee = Employee.objects.filter(user=request.user).first()

                # Activate project
                result = service.activate_project(
                    start_date=start_date,
                    create_schedule=create_schedule,
                    create_budget=create_budget,
                    create_tasks=create_tasks,
                    deposit_percent=deposit_percent,
                    items_to_schedule=None,  # keep backward compatibility not used now
                    selected_line_ids=selected_line_ids,
                    assigned_to=employee,
                )

                # Build success message
                summary = result["summary"]
                msg_parts = ["Proyecto activado exitosamente:"]

                if summary["schedule_items_count"] > 0:
                    msg_parts.append(
                        f"✓ {summary['schedule_items_count']} ítems de cronograma creados"
                    )

                if summary["budget_lines_count"] > 0:
                    msg_parts.append(
                        f"✓ {summary['budget_lines_count']} líneas de presupuesto creadas"
                    )

                if summary["tasks_count"] > 0:
                    msg_parts.append(f"✓ {summary['tasks_count']} tareas operativas creadas")

                if summary["invoice_created"]:
                    msg_parts.append(f"✓ Factura de anticipo creada (${summary['invoice_amount']})")

                messages.success(request, " | ".join(msg_parts))

                # Redirect to Gantt if schedule was created, otherwise to project detail
                if create_schedule:
                    return redirect("schedule_generator", project_id=project.id)
                else:
                    return redirect("project_overview", project_id=project.id)

            except ValueError as e:
                messages.error(request, _("Error de validación: %(error)s") % {"error": str(e)})
            except Exception as e:
                messages.error(
                    request, _("Error al activar proyecto: %(error)s") % {"error": str(e)}
                )
    else:
        form = ActivationWizardForm(estimate=estimate)

    # Calculate estimate summary
    estimate_lines = estimate.lines.all()
    direct_cost = sum(line.direct_cost() for line in estimate_lines)
    material_markup = (
        (direct_cost * (estimate.markup_material / 100)) if estimate.markup_material else 0
    )
    labor_markup = (direct_cost * (estimate.markup_labor / 100)) if estimate.markup_labor else 0
    overhead = (direct_cost * (estimate.overhead_pct / 100)) if estimate.overhead_pct else 0
    profit = (direct_cost * (estimate.target_profit_pct / 100)) if estimate.target_profit_pct else 0
    estimate_total = direct_cost + material_markup + labor_markup + overhead + profit

    context = {
        "project": project,
        "estimate": estimate,
        "estimate_lines": estimate_lines,
        "estimate_total": estimate_total,
        "form": form,
        "has_schedule": has_schedule,
        "has_budget": has_budget,
        "is_reactivation": has_schedule or has_budget,
    }

    return render(request, "core/project_activation.html", context)



@login_required
def project_list(request):
    """List projects filtered by user role.
    
    - Clients: Only see projects they have access to
    - Employees: Only see projects they are assigned to
    - Staff/Admin/PM: See all projects
    """
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", None) if profile else None
    
    # If user is a client, only show their projects
    if role == "client":
        # Get projects via ClientProjectAccess
        access_projects = Project.objects.filter(client_accesses__user=request.user)
        # Get projects via legacy client field
        legacy_projects = Project.objects.filter(client=request.user.username)
        # Combine both querysets
        projects = access_projects.union(legacy_projects).order_by("-start_date")
    elif role == "employee":
        # SECURITY: Employees can only see projects they have time entries for
        # or projects they are scheduled to work on (via daily plan activities)
        emp = getattr(request.user, "employee", None)
        if emp:
            from core.models import TimeEntry
            time_entry_projects = Project.objects.filter(
                timeentry__employee=emp
            ).distinct()
            # Also check daily plan assignments
            activity_projects = Project.objects.filter(
                daily_plans__activities__assigned_employees=emp
            ).distinct()
            projects = (time_entry_projects | activity_projects).distinct().order_by("-start_date")
        else:
            projects = Project.objects.none()
    else:
        # Staff, admin, PM - show all projects
        projects = Project.objects.all().order_by("id")
    
    return render(request, "core/project_list.html", {"projects": projects})



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
        },
    )



def pickup_view(request, project_id: int):
    project = get_object_or_404(Project, pk=project_id)
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("Access denied."))
        return redirect(redirect_url or "dashboard")
    return render(request, "core/pickup_view.html", {"project": project})



@login_required
@staff_member_required
def project_create(request):
    """Crear nuevo proyecto"""
    from core.forms import ProjectCreateForm

    if request.method == "POST":
        form = ProjectCreateForm(request.POST)
        if form.is_valid():
            project = form.save()
            messages.success(request, f'Proyecto "{project.name}" creado exitosamente.')
            return redirect("project_overview", project_id=project.id)
    else:
        form = ProjectCreateForm()

    return render(request, "core/project_form.html", {"form": form, "is_create": True})



@login_required
@staff_member_required
def project_edit(request, project_id):
    """Editar proyecto existente"""
    from core.forms import ProjectEditForm

    project = get_object_or_404(Project, id=project_id)

    if request.method == "POST":
        form = ProjectEditForm(request.POST, instance=project)
        if form.is_valid():
            project = form.save()
            messages.success(request, f'Proyecto "{project.name}" actualizado exitosamente.')
            return redirect("project_overview", project_id=project.id)
    else:
        form = ProjectEditForm(instance=project)

    return render(
        request, "core/project_form.html", {"form": form, "project": project, "is_create": False}
    )



@login_required
@staff_member_required
def project_delete(request, project_id):
    """Eliminar proyecto (con confirmación y validación de dependencias)"""
    project = get_object_or_404(Project, id=project_id)

    if request.method == "POST":
        # SECURITY: Logging de auditoría

        audit_logger = logging.getLogger("django")
        audit_logger.warning(
            f"PROJECT_DELETE_ATTEMPT | Actor: {request.user.username} (ID:{request.user.id}) | "
            f"Project: {project.name} (ID:{project.id}) | "
            f"IP: {request.META.get('REMOTE_ADDR')}"
        )

        # SECURITY: Verificar dependencias críticas ANTES de permitir eliminación
        has_expenses = Expense.objects.filter(project=project).exists()
        has_incomes = Income.objects.filter(project=project).exists()
        has_timeentries = TimeEntry.objects.filter(project=project).exists()
        has_changeorders = ChangeOrder.objects.filter(project=project).exists()
        has_dailylogs = DailyLog.objects.filter(project=project).exists()
        has_schedules = ScheduleItemV2.objects.filter(project=project).exists()
        has_invoices = Invoice.objects.filter(project=project).exists()

        if any(
            [
                has_expenses,
                has_incomes,
                has_timeentries,
                has_changeorders,
                has_dailylogs,
                has_schedules,
                has_invoices,
            ]
        ):
            messages.error(
                request,
                "❌ No se puede eliminar este proyecto porque tiene datos financieros o operacionales asociados. "
                "Considera marcarlo como completado en lugar de eliminarlo para preservar la integridad de los datos.",
            )
            return redirect("project_overview", project_id=project.id)

        project_name = project.name
        project.delete()
        messages.success(request, f'Proyecto "{project_name}" eliminado permanentemente.')
        return redirect("project_list")

    # GET: Calcular estadísticas detalladas para confirmación

    expense_count = Expense.objects.filter(project=project).count()
    income_count = Income.objects.filter(project=project).count()
    timeentry_count = TimeEntry.objects.filter(project=project).count()
    co_count = ChangeOrder.objects.filter(project=project).count()
    task_count = Task.objects.filter(project=project).count()
    dailylog_count = DailyLog.objects.filter(project=project).count()
    schedule_count = ScheduleItemV2.objects.filter(project=project).count()
    invoice_count = Invoice.objects.filter(project=project).count()

    context = {
        "project": project,
        "expense_count": expense_count,
        "income_count": income_count,
        "timeentry_count": timeentry_count,
        "co_count": co_count,
        "task_count": task_count,
        "dailylog_count": dailylog_count,
        "schedule_count": schedule_count,
        "invoice_count": invoice_count,
        "has_critical_data": any(
            [
                expense_count,
                income_count,
                timeentry_count,
                co_count,
                dailylog_count,
                schedule_count,
                invoice_count,
            ]
        ),
    }

    return render(request, "core/project_delete_confirm.html", context)



@login_required
@staff_member_required
def project_status_toggle(request, project_id):
    """Cambiar estado del proyecto (activo/completado)"""
    project = get_object_or_404(Project, id=project_id)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "complete":
            if not project.end_date:
                project.end_date = timezone.localdate()
                project.save()
                messages.success(request, f'Proyecto "{project.name}" marcado como completado.')
        elif action == "reopen":
            project.end_date = None
            project.save()
            messages.success(request, f'Proyecto "{project.name}" reabierto.')

        return redirect("project_overview", project_id=project.id)

    return redirect("project_overview", project_id=project.id)



@login_required
def project_financials_hub(request, project_id):
    """
    Hub financiero principal del proyecto.
    Muestra resumen de budget, spent, remaining y breakdown por cost code.
    
    Para PM (no admin): muestra Working Budget (-30%) 
    Para Admin/Superuser: muestra Budget real completo
    """
    if not _is_staffish(request.user):
        return redirect("dashboard")
    project = get_object_or_404(Project, pk=project_id)
    
    # Determinar si es PM (no admin)
    profile = getattr(request.user, 'profile', None)
    is_pm = profile and profile.role == 'pm' if profile else False
    
    # Calcular totales
    budget_lines = project.budget_lines.select_related('cost_code').all()
    
    # Total budget = suma de revised_amount de todas las líneas
    total_budget = sum(line.revised_amount or line.baseline_amount for line in budget_lines)
    
    # Working budget para PM = total - 30%
    working_budget = total_budget * Decimal('0.70') if total_budget else Decimal('0')
    
    # Calculate actual spent from expenses linked to project
    from django.db.models import Sum as DJSum
    total_spent = project.expenses.aggregate(total=DJSum('amount'))['total'] or Decimal('0')
    
    # Also include labor cost from time entries
    time_labor_cost = Decimal('0')
    for te in TimeEntry.objects.filter(project=project).select_related('employee'):
        rate = te.employee.hourly_rate if te.employee and te.employee.hourly_rate else Decimal('0')
        time_labor_cost += (te.hours_worked or Decimal('0')) * rate
    total_spent += time_labor_cost
    
    # Remaining
    if is_pm and not request.user.is_superuser:
        remaining = working_budget - total_spent
        display_budget = working_budget
    else:
        remaining = total_budget - total_spent
        display_budget = total_budget
    
    # Porcentajes
    spent_percentage = int((total_spent / display_budget * 100) if display_budget else 0)
    margin_percentage = 30 if is_pm else (int((remaining / total_budget * 100)) if total_budget else 0)
    
    # Preparar datos de líneas para display
    # Pre-compute expense totals per cost_code for per-line breakdown
    from core.models import Expense
    expense_by_costcode = {}
    for exp in Expense.objects.filter(project=project).values('cost_code_id').annotate(total=DJSum('amount')):
        if exp['cost_code_id']:
            expense_by_costcode[exp['cost_code_id']] = exp['total'] or Decimal('0')
    
    lines_data = []
    for line in budget_lines:
        line_budget = line.revised_amount or line.baseline_amount
        # Para PM mostrar budget reducido
        if is_pm and not request.user.is_superuser:
            line_display_budget = line_budget * Decimal('0.70')
        else:
            line_display_budget = line_budget
        
        line_spent = expense_by_costcode.get(line.cost_code_id, Decimal('0'))
        line_remaining = line_display_budget - line_spent
        line_spent_pct = (line_spent / line_display_budget * 100) if line_display_budget else 0
        line_remaining_pct = 100 - float(line_spent_pct)
        
        lines_data.append({
            'cost_code': line.cost_code,
            'description': line.description,
            'display_budget': line_display_budget,
            'spent': line_spent,
            'remaining': line_remaining,
            'spent_pct': line_spent_pct,
            'remaining_pct': line_remaining_pct,
        })
    
    context = {
        'project': project,
        'is_pm': is_pm,
        'total_budget': total_budget,
        'working_budget': working_budget,
        'total_spent': total_spent,
        'remaining': remaining,
        'spent_percentage': spent_percentage,
        'margin_percentage': margin_percentage,
        'budget_lines': lines_data,
        'active_tab': 'overview',
    }
    
    return render(request, 'core/project_financials_hub.html', context)



@login_required
def project_budget_detail(request, project_id):
    """
    Vista de detalle del budget con capacidad de agregar/editar/eliminar líneas.
    Solo staff/admin puede editar.
    """
    if not _is_staffish(request.user):
        return redirect("dashboard")
    project = get_object_or_404(Project, pk=project_id)
    
    # Verificar permisos de edición
    can_edit = request.user.is_staff or request.user.is_superuser
    
    if request.method == 'POST' and can_edit:
        action = request.POST.get('action', 'add')
        
        # DELETE action
        if action == 'delete':
            line_id = request.POST.get('line_id')
            if line_id:
                try:
                    line = BudgetLine.objects.get(pk=line_id, project=project)
                    line.delete()
                    messages.success(request, _('Budget line deleted successfully.'))
                except BudgetLine.DoesNotExist:
                    messages.error(request, _('Budget line not found.'))
            return redirect('project_budget_detail', project_id=project.id)
        
        # EDIT action
        elif action == 'edit':
            line_id = request.POST.get('line_id')
            if line_id:
                try:
                    line = BudgetLine.objects.get(pk=line_id, project=project)
                    line.description = request.POST.get('description', line.description)
                    line.qty = Decimal(str(request.POST.get('qty', line.qty) or 0))
                    line.unit = request.POST.get('unit', line.unit)
                    line.unit_cost = Decimal(str(request.POST.get('unit_cost', line.unit_cost) or 0))
                    # Allow editing revised_amount directly
                    revised = request.POST.get('revised_amount')
                    if revised:
                        line.revised_amount = Decimal(str(revised))
                    line.save()
                    messages.success(request, _('Budget line updated successfully.'))
                except (BudgetLine.DoesNotExist, InvalidOperation) as e:
                    messages.error(request, _('Error updating budget line.'))
            return redirect('project_budget_detail', project_id=project.id)
        
        # ADD action (default)
        else:
            cost_code_id = request.POST.get('cost_code')
            description = request.POST.get('description', '')
            qty = request.POST.get('qty', 0)
            unit = request.POST.get('unit', '')
            unit_cost = request.POST.get('unit_cost', 0)
            
            if cost_code_id:
                try:
                    cost_code = CostCode.objects.get(pk=cost_code_id)
                    BudgetLine.objects.create(
                        project=project,
                        cost_code=cost_code,
                        description=description,
                        qty=Decimal(str(qty)) if qty else Decimal('0'),
                        unit=unit,
                        unit_cost=Decimal(str(unit_cost)) if unit_cost else Decimal('0'),
                    )
                    messages.success(request, _('Budget line added successfully.'))
                except (CostCode.DoesNotExist, InvalidOperation) as e:
                    messages.error(request, _('Error adding budget line.'))
            
            return redirect('project_budget_detail', project_id=project.id)
    
    budget_lines = project.budget_lines.select_related('cost_code').order_by('cost_code__code')
    cost_codes = CostCode.objects.filter(active=True).order_by('code')
    
    # Calcular totales
    total_baseline = sum(line.baseline_amount for line in budget_lines)
    total_revised = sum(line.revised_amount for line in budget_lines)
    variance = total_revised - total_baseline
    
    context = {
        'project': project,
        'budget_lines': budget_lines,
        'cost_codes': cost_codes,
        'can_edit': can_edit,
        'total_baseline': total_baseline,
        'total_revised': total_revised,
        'variance': variance,
        'active_tab': 'budget',
    }
    
    return render(request, 'core/project_budget_detail.html', context)



@login_required  
def project_cost_codes(request, project_id):
    """
    Gestión de Cost Codes - códigos para categorizar costos.
    Solo admin puede crear/editar.
    """
    if not _is_staffish(request.user):
        return redirect("dashboard")
    project = get_object_or_404(Project, pk=project_id)
    
    can_edit = request.user.is_staff or request.user.is_superuser
    
    if request.method == 'POST' and can_edit:
        action = request.POST.get('action', 'create')
        
        if action == 'create':
            code = request.POST.get('code', '').strip().upper()
            name = request.POST.get('name', '').strip()
            category = request.POST.get('category', '').strip()
            
            if code and name:
                try:
                    CostCode.objects.create(
                        code=code,
                        name=name,
                        category=category,
                        active=True,
                    )
                    messages.success(request, _('Cost code created successfully.'))
                except IntegrityError:
                    messages.error(request, _('A cost code with that code already exists.'))
            else:
                messages.error(request, _('Code and name are required.'))
        
        elif action == 'update':
            costcode_id = request.POST.get('costcode_id')
            if costcode_id:
                try:
                    costcode = CostCode.objects.get(pk=costcode_id)
                    costcode.code = request.POST.get('code', '').strip().upper()
                    costcode.name = request.POST.get('name', '').strip()
                    costcode.category = request.POST.get('category', '').strip()
                    costcode.active = request.POST.get('active') == 'on'
                    costcode.save()
                    messages.success(request, _('Cost code updated successfully.'))
                except CostCode.DoesNotExist:
                    messages.error(request, _('Cost code not found.'))
        
        elif action == 'delete':
            costcode_id = request.POST.get('costcode_id')
            if costcode_id:
                try:
                    costcode = CostCode.objects.get(pk=costcode_id)
                    costcode.delete()
                    messages.success(request, _('Cost code deleted.'))
                except CostCode.DoesNotExist:
                    messages.error(request, _('Cost code not found.'))
        
        return redirect('project_cost_codes', project_id=project.id)
    
    cost_codes = CostCode.objects.all().order_by('category', 'code')
    
    # Default categories for construction
    default_categories = [
        'Appliances',
        'Cabinets',
        'Cleanup',
        'Concrete',
        'Countertops',
        'Demolition',
        'Drywall',
        'Electrical',
        'Equipment',
        'Exterior',
        'Exterior Painting',
        'Flooring',
        'Framing',
        'HVAC',
        'Interior',
        'Interior Painting',
        'Labor',
        'Landscaping',
        'Material',
        'Plumbing',
        'Roofing',
        'Subcontractor',
        'Windows & Doors',
        'Other',
    ]
    
    # Get existing categories, normalize to title case
    existing_raw = CostCode.objects.exclude(category__isnull=True).exclude(category='').values_list('category', flat=True).distinct()
    existing_normalized = set()
    for cat in existing_raw:
        # Normalize: "interior painting" -> "Interior Painting"
        normalized = cat.strip().title()
        existing_normalized.add(normalized)
    
    # Merge and deduplicate
    all_categories = sorted(set(default_categories) | existing_normalized)
    
    # Agrupar por categoría (normalizado)
    codes_by_category = defaultdict(list)
    for cc in cost_codes:
        cat = (cc.category or '').strip().title() or _('Uncategorized')
        codes_by_category[cat].append(cc)
    
    context = {
        'project': project,
        'cost_codes': cost_codes,
        'codes_by_category': dict(codes_by_category),
        'can_edit': can_edit,
        'active_tab': 'costcodes',
        'categories': all_categories,
    }
    
    return render(request, 'core/project_cost_codes.html', context)



@login_required
def project_estimates(request, project_id):
    """
    Lista de estimados del proyecto.
    Solo visible para staff/admin.
    """
    # SECURITY: Only staff/superusers can view estimates (financial data)
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden(_('Access denied'))
    
    project = get_object_or_404(Project, pk=project_id)
    
    estimates = project.estimates.all().order_by('-version')
    
    # Calcular totales para cada estimado
    estimates_data = []
    for est in estimates:
        lines = est.lines.select_related('cost_code')
        direct_cost = sum(line.direct_cost() for line in lines)
        
        # Calcular precio propuesto con markups
        material_markup = direct_cost * (est.markup_material / 100)
        labor_markup = direct_cost * (est.markup_labor / 100)
        overhead = direct_cost * (est.overhead_pct / 100)
        profit = direct_cost * (est.target_profit_pct / 100)
        proposed_price = direct_cost + material_markup + labor_markup + overhead + profit
        
        estimates_data.append({
            'estimate': est,
            'direct_cost': direct_cost,
            'proposed_price': proposed_price,
            'lines_count': lines.count(),
        })
    
    context = {
        'project': project,
        'estimates': estimates_data,
        'can_create': request.user.is_staff or request.user.is_superuser,
        'active_tab': 'estimates',
    }
    
    return render(request, 'core/project_estimates_list.html', context)



@login_required
def project_invoices(request, project_id):
    """
    Lista de facturas del proyecto.
    Solo visible para staff/admin.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden(_('Access denied'))
    
    project = get_object_or_404(Project, pk=project_id)
    
    invoices = project.invoices.all().order_by('-created_at')
    
    context = {
        'project': project,
        'invoices': invoices,
        'active_tab': 'invoices',
    }
    
    return render(request, 'core/project_invoices_list.html', context)


