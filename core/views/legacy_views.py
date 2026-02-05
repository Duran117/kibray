from collections import defaultdict
import contextlib
import csv
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps
import io
from io import BytesIO
import json
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives, send_mail
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Max, Q, Sum
from django.db.models.functions import Coalesce
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods, require_POST

try:
    from xhtml2pdf import pisa  # Optional HTML->PDF engine (requires system cairo libs)
except Exception:  # Build may omit system deps (Railway minimal image)
    pisa = None


# Fallback lightweight PDF generator (text only) using ReportLab
def _generate_basic_pdf_from_html(html: str) -> bytes:
    """Very small fallback: strip tags and render lines into a single-page PDF.
    Avoids hard dependency on xhtml2pdf when system cairo is missing.
    """
    try:
        from reportlab.lib.pagesizes import LETTER
        from reportlab.pdfgen import canvas
    except Exception:
        return b"PDF generation unavailable"
    text = re.sub(r"<[^>]+>", "", html)
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    y = 770
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if y < 50:
            c.showPage()
            y = 770
        c.drawString(40, y, line[:110])
        y -= 14
    c.showPage()
    c.save()
    return buf.getvalue()


from core import models  # noqa: E402
from core.forms import (  # noqa: E402
    ActivationWizardForm,
    ActivityTemplateForm,
    BudgetLineForm,
    BudgetLineScheduleForm,
    BudgetProgressEditForm,
    BudgetProgressForm,
    ChangeOrderForm,
    ClockInForm,
    ColorSampleForm,
    ColorSampleReviewForm,
    CostCodeForm,
    EstimateForm,
    EstimateLineFormSet,
    ExpenseForm,
    FloorPlanForm,
    IncomeForm,
    InventoryMovementForm,
    InvoiceForm,
    InvoiceLineFormSet,
    IssueForm,
    MaterialsRequestForm,
    PlanPinForm,
    ProposalEmailForm,
    RFIAnswerForm,
    RFIForm,
    RiskForm,
    SchedulePhaseForm,
    ScheduleForm,
    ScheduleItemForm,
    TimeEntryForm,
)
from core.models import (  # noqa: E402
    RFI,
    ActivityCompletion,
    ActivityTemplate,
    BudgetLine,
    BudgetProgress,
    ChangeOrder,
    ChangeOrderPhoto,
    ChatChannel,
    ChatMessage,
    ColorApproval,
    ColorSample,
    Comment,
    CostCode,
    DailyLog,
    DailyPlan,
    DamageReport,
    Employee,
    Estimate,
    Expense,
    FloorPlan,
    Income,
    InventoryLocation,
    Invoice,
    InvoiceLine,
    Issue,
    MaterialCatalog,
    MaterialRequest,
    MaterialRequestItem,
    PayrollPayment,
    PayrollPeriod,
    PayrollRecord,
    PlannedActivity,
    Profile,
    Project,
    ProjectInventory,
    ResourceAssignment,
    Risk,
    Schedule,
    SchedulePhaseV2,
    ScheduleItemV2,
    Task,
    TimeEntry,
)
from core.services.earned_value import compute_project_ev  # noqa: E402
from core.services.financial_service import FinancialAnalyticsService  # BI Module 21  # noqa: E402


# ===== SECURITY HELPER: Check project access =====
def _check_user_project_access(user, project):
    """
    SECURITY: Verify if a user has access to a specific project.
    
    Returns:
        tuple: (has_access: bool, redirect_url: str or None)
    
    Rules:
        - Staff/superusers can access all projects
        - Clients can only access projects where they are the contact
        - Users with explicit ClientProjectAccess can access
        - Assigned users (if field exists) can access
    """
    from core.models import ClientProjectAccess
    
    # Staff can access all projects
    if user.is_staff or user.is_superuser:
        return True, None
    
    # Check explicit granular access
    has_explicit_access = ClientProjectAccess.objects.filter(
        user=user, project=project
    ).exists()
    if has_explicit_access:
        return True, None
    
    # Check if user is the client contact for this project
    if project.client:
        # Check by email
        if project.client.email and project.client.email == user.email:
            return True, None
        # Check by linked user
        if hasattr(project.client, 'user') and project.client.user == user:
            return True, None
        if project.client.user_id == user.id:
            return True, None
    
    # Check if user is assigned to the project (for workers/PMs)
    if hasattr(project, 'assigned_to') and project.assigned_to.filter(id=user.id).exists():
        return True, None
    
    # No access
    profile = getattr(user, "profile", None)
    if profile and profile.role == "client":
        return False, "dashboard_client"
    return False, "dashboard"
# ===== END SECURITY HELPER =====


# --- CLIENT REQUESTS ---
@login_required
def client_request_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)
    
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description", "")
        if not title:
            messages.error(request, _("Título es requerido"))
        else:
            from core.models import ClientRequest

            ClientRequest.objects.create(
                project=project, title=title, description=description, created_by=request.user
            )
            messages.success(request, _("Solicitud creada"))
            return redirect("client_requests_list", project_id=project.id)
    return render(request, "core/client_request_form.html", {"project": project})


@login_required
def client_requests_list(request, project_id=None):
    from core.models import ClientRequest

    if project_id:
        project = get_object_or_404(Project, id=project_id)
        
        # SECURITY: Check project access
        has_access, redirect_url = _check_user_project_access(request.user, project)
        if not has_access:
            messages.error(request, _("You don't have access to this project."))
            return redirect(redirect_url)
        
        qs = ClientRequest.objects.filter(project=project).order_by("-created_at")
    else:
        # Without project_id, only staff can see all requests
        if not request.user.is_staff:
            messages.error(request, _("Access denied."))
            return redirect("dashboard_client")
        project = None
        qs = ClientRequest.objects.all().select_related("project").order_by("-created_at")
    return render(request, "core/client_requests_list.html", {"project": project, "requests": qs})


@login_required
def client_request_convert_to_co(request, request_id):
    from core.models import ClientRequest

    cr = get_object_or_404(ClientRequest, id=request_id)
    if cr.change_order:
        messages.info(
            request,
            _("Esta solicitud ya fue convertida al CO #%(co_id)s.") % {"co_id": cr.change_order.id},
        )
        return redirect("client_requests_list", project_id=cr.project.id)
    if request.method == "POST":
        description = request.POST.get("description") or cr.description or cr.title
        amount_str = request.POST.get("amount") or "0"
        try:
            amt = Decimal(amount_str)
        except Exception:
            amt = Decimal("0")
        co = ChangeOrder.objects.create(
            project=cr.project, description=description, amount=amt, status="pending"
        )
        cr.change_order = co
        cr.status = "converted"
        cr.save()
        messages.success(request, _("Solicitud convertida al CO #%(co_id)s.") % {"co_id": co.id})
        return redirect("changeorder_detail", changeorder_id=co.id)
    return render(request, "core/client_request_convert.html", {"req": cr})


PRESET_PRODUCTS = [
    # Pinturas
    {
        "category": "paint",
        "category_label": "Pintura",
        "brand": "sherwin_williams",
        "brand_label": "Sherwin‑Williams",
        "product_name": "Emerald Interior",
        "unit": "gal",
    },
    {
        "category": "primer",
        "category_label": "Primer",
        "brand": "sherwin_williams",
        "brand_label": "Sherwin‑Williams",
        "product_name": "Multi‑Purpose Primer",
        "unit": "gal",
    },
    {
        "category": "paint",
        "category_label": "Pintura",
        "brand": "benjamin_moore",
        "brand_label": "Benjamin Moore",
        "product_name": "Regal Select",
        "unit": "gal",
    },
    # Stain / Laca
    {
        "category": "stain",
        "category_label": "Stain",
        "brand": "milesi",
        "brand_label": "Milesi",
        "product_name": "Interior Wood Stain",
        "unit": "liter",
    },
    {
        "category": "lacquer",
        "category_label": "Laca/Clear",
        "brand": "chemcraft",
        "brand_label": "Chemcraft",
        "product_name": "Clear Lacquer",
        "unit": "liter",
    },
    # Enmascarado / protección
    {
        "category": "tape",
        "category_label": "Tape",
        "brand": "3m",
        "brand_label": "3M",
        "product_name": "2090 ScotchBlue",
        "unit": "roll",
    },
    {
        "category": "plastic",
        "category_label": "Plástico",
        "brand": "3m",
        "brand_label": "3M",
        "product_name": "Hand‑Masker Film 9ft",
        "unit": "roll",
    },
    {
        "category": "masking_paper",
        "category_label": "Papel enmascarar",
        "brand": "3m",
        "brand_label": "3M",
        "product_name": "Hand‑Masker Brown Paper 12in",
        "unit": "roll",
    },
    {
        "category": "floor_paper",
        "category_label": "Papel para piso",
        "brand": "other",
        "brand_label": "Otro",
        "product_name": "Ram Board",
        "unit": "roll",
    },
    # Herramientas
    {
        "category": "brush",
        "category_label": "Brocha",
        "brand": "purdy",
        "brand_label": "Purdy",
        "product_name": 'Pro‑Extra 2.5"',
        "unit": "unit",
    },
    {
        "category": "roller_cover",
        "category_label": "Rodillo (cover)",
        "brand": "wooster",
        "brand_label": "Wooster",
        "product_name": '9in Micro Plush 3/8"',
        "unit": "unit",
    },
    {
        "category": "tray_liner",
        "category_label": "Liner",
        "brand": "other",
        "brand_label": "Otro",
        "product_name": "Liner para charola 9in",
        "unit": "pack",
    },
    {
        "category": "sandpaper",
        "category_label": "Lija",
        "brand": "3m",
        "brand_label": "3M",
        "product_name": "P220 Hookit",
        "unit": "box",
    },
    {
        "category": "blades",
        "category_label": "Cuchillas",
        "brand": "other",
        "brand_label": "Otro",
        "product_name": "Cuchillas trapezoidales",
        "unit": "box",
    },
    # Selladores/PPE
    {
        "category": "caulk",
        "category_label": "Caulk/Sellador",
        "brand": "wurth",
        "brand_label": "Würth",
        "product_name": "Acrylic Latex Caulk (White)",
        "unit": "tube",
    },
    {
        "category": "respirator",
        "category_label": "Respirador",
        "brand": "3m",
        "brand_label": "3M",
        "product_name": "Half Facepiece 6200",
        "unit": "unit",
    },
    {
        "category": "mask",
        "category_label": "Mascarilla",
        "brand": "3m",
        "brand_label": "3M",
        "product_name": "N95",
        "unit": "box",
    },
    {
        "category": "coverall",
        "category_label": "Overol",
        "brand": "other",
        "brand_label": "Otro",
        "product_name": "Coverall desechable",
        "unit": "unit",
    },
    {
        "category": "gloves",
        "category_label": "Guantes",
        "brand": "other",
        "brand_label": "Otro",
        "product_name": "Nitrilo",
        "unit": "box",
    },
]


# --- DASHBOARD ADMIN (COMPLETO) ---
@login_required
def dashboard_admin(request):
    """Dashboard completo para Admin con todas las métricas, alertas y aprobaciones"""
    if not (request.user.is_superuser or request.user.is_staff):
        # Never render/redirect into a view that could show privileged data.
        # Return 403 immediately to avoid any transient exposure.
        return HttpResponseForbidden("Forbidden")

    # Respect session language hint for legacy rendering (used by i18n tests)
    session_lang = request.session.get("lang")
    if session_lang:
        translation.activate(session_lang)
        request.LANGUAGE_CODE = session_lang

    today = timezone.localdate()
    now = timezone.localtime()

    # Obtener empleado ligado al usuario (para Admin que también es empleado)
    employee = Employee.objects.filter(user=request.user).first()

    # TimeEntry abierto (si está trabajando) - Solo si hay empleado vinculado
    open_entry = None
    if employee:
        open_entry = (
            TimeEntry.objects.filter(employee=employee, end_time__isnull=True)
            .order_by("-date", "-start_time")
            .first()
        )

    # Manejo de Clock In/Out para Admins
    if request.method == "POST" and employee:
        action = request.POST.get("action")

        if action == "clock_in":
            if open_entry:
                messages.warning(request, _("You already have an open entry. Clock out first."))
                return redirect("dashboard_admin")
            form = ClockInForm(request.POST)
            if form.is_valid():
                TimeEntry.objects.create(
                    employee=employee,
                    project=form.cleaned_data["project"],
                    change_order=form.cleaned_data.get("change_order"),
                    budget_line=form.cleaned_data.get("budget_line"),  # Nueva línea
                    date=today,
                    start_time=now.time(),
                    end_time=None,
                    notes=form.cleaned_data.get("notes") or "",
                    cost_code=form.cleaned_data.get("cost_code"),
                )
                messages.success(
                    request,
                    _("✓ Clocked in at %(time)s.") % {"time": now.strftime("%H:%M")},
                )
                return redirect("dashboard_admin")

        elif action == "clock_out":
            if not open_entry:
                messages.warning(request, _("You don't have an open entry."))
                return redirect("dashboard_admin")
            open_entry.end_time = now.time()
            open_entry.save()
            messages.success(
                request,
                _("✓ Clocked out at %(time)s. Hours: %(hours)s") % {"time": now.strftime("%H:%M"), "hours": open_entry.hours_worked},
            )
            return redirect("dashboard_admin")

        elif action == "switch_context" and open_entry:
            # CORRECCIÓN: Cerrar entrada actual y crear nueva para registrar tiempo correctamente
            switch_type = request.POST.get("switch_type")
            current_time = now.time()
            
            # Guardar datos de la entrada actual
            old_project = open_entry.project
            old_co = open_entry.change_order
            
            if switch_type == "base":
                # Cerrar entrada actual y crear nueva sin CO
                open_entry.end_time = current_time
                open_entry.save()
                
                TimeEntry.objects.create(
                    employee=employee,
                    project=old_project,
                    change_order=None,
                    budget_line=open_entry.budget_line,
                    date=today,
                    start_time=current_time,
                    end_time=None,
                    notes=f"Switched from CO: {old_co.title if old_co else 'N/A'}",
                    cost_code=open_entry.cost_code,
                )
                messages.success(
                    request,
                    _("✓ Entry closed (%(hours)s hrs). Now on base work. Previously: %(co)s")
                    % {"hours": open_entry.hours_worked, "co": old_co.title if old_co else "N/A"},
                )
                
            elif switch_type == "co":
                target_id = request.POST.get("target_id") or request.POST.get("co_id")
                if target_id:
                    try:
                        new_co = ChangeOrder.objects.get(
                            id=target_id,
                            project=open_entry.project,
                            status__in=['draft', 'pending', 'approved', 'sent', 'billed']
                        )
                        open_entry.end_time = current_time
                        open_entry.save()
                        
                        TimeEntry.objects.create(
                            employee=employee,
                            project=old_project,
                            change_order=new_co,
                            budget_line=None,
                            date=today,
                            start_time=current_time,
                            end_time=None,
                            notes=f"Switched from: {old_co.title if old_co else 'Base work'}",
                            cost_code=open_entry.cost_code,
                        )
                        messages.success(
                            request,
                            _("✓ Entry closed (%(hours)s hrs). Now on %(co)s (%(type)s)")
                            % {"hours": open_entry.hours_worked, "co": new_co.title, "type": new_co.get_pricing_type_display()},
                        )
                    except ChangeOrder.DoesNotExist:
                        messages.error(request, _("Change Order not found or not available."))
                        
            elif switch_type == "project":
                target_id = request.POST.get("target_id") or request.POST.get("project_id")
                if target_id:
                    try:
                        new_project = Project.objects.get(id=target_id)
                        
                        open_entry.end_time = current_time
                        open_entry.save()
                        
                        TimeEntry.objects.create(
                            employee=employee,
                            project=new_project,
                            change_order=None,
                            budget_line=None,
                            date=today,
                            start_time=current_time,
                            end_time=None,
                            notes=f"Switched from project: {old_project.name}",
                            cost_code=None,
                        )
                        messages.success(
                            request,
                            _("✓ Entry closed (%(hours)s hrs on %(old)s). Now on %(proj)s")
                            % {"hours": open_entry.hours_worked, "old": old_project.name, "proj": new_project.name},
                        )
                    except Project.DoesNotExist:
                        messages.error(request, _("Project not found."))
            return redirect("dashboard_admin")

    # Form para clock in
    form = ClockInForm() if employee else None

    # === MÉTRICAS FINANCIERAS (refactored to service) ===
    fa = FinancialAnalyticsService()
    kpis = fa.get_company_health_kpis()
    net_profit = Decimal(
        str(kpis.get("net_profit", 0))
    )  # maintain existing variable for template compatibility
    # Provide legacy totals for templates/tests expecting these context keys
    total_income = Project.objects.aggregate(t=Sum("total_income"))["t"] or Decimal("0")
    total_expense = Project.objects.aggregate(t=Sum("total_expenses"))["t"] or Decimal("0")

    # === ALERTAS CRÍTICAS ===
    # 1. TimeEntries sin CO asignar
    unassigned_time_count = TimeEntry.objects.filter(change_order__isnull=True).count()
    unassigned_time_hours = TimeEntry.objects.filter(change_order__isnull=True).aggregate(
        total=Sum("hours_worked")
    )["total"] or Decimal("0")

    # 2. Solicitudes Cliente pendientes
    from core.models import ClientRequest

    pending_client_requests = ClientRequest.objects.filter(status="pending").count()

    # 3. Nómina pendiente (periodos aprobados pero no pagados completamente)
    pending_payroll = (
        PayrollPeriod.objects.filter(status="approved")
        .exclude(records__payments__isnull=False)
        .distinct()
        .count()
    )

    # 4. Facturas pendientes de pago
    pending_invoices = Invoice.objects.filter(
        status__in=["SENT", "VIEWED", "APPROVED", "PARTIAL"]
    ).count()
    pending_invoice_amount = Invoice.objects.filter(
        status__in=["SENT", "VIEWED", "APPROVED", "PARTIAL"]
    ).aggregate(total=Sum("total_amount"))["total"] or Decimal("0")

    # 5. COs pendientes de aprobación
    pending_cos = ChangeOrder.objects.filter(status="pending").count()

    # === PROYECTOS CON ALERTAS EV ===
    today = timezone.localdate()
    projects_with_alerts = []

    for project in Project.objects.filter(end_date__isnull=True).order_by("name"):
        try:
            metrics = compute_project_ev(project, as_of=today)
            alerts = []

            # SPI < 0.9: retraso en cronograma
            if metrics and metrics.get("SPI") and metrics["SPI"] < 0.9:
                alerts.append(("danger", f"Retraso crítico (SPI: {metrics['SPI']})"))
            elif metrics and metrics.get("SPI") and metrics["SPI"] < 1.0:
                alerts.append(("warning", f"Leve retraso (SPI: {metrics['SPI']})"))

            # CPI < 0.9: sobrecosto
            if metrics and metrics.get("CPI") and metrics["CPI"] < 0.9:
                alerts.append(("danger", f"Sobrecosto crítico (CPI: {metrics['CPI']})"))
            elif metrics and metrics.get("CPI") and metrics["CPI"] < 1.0:
                alerts.append(("warning", f"Leve sobrecosto (CPI: {metrics['CPI']})"))

            # Presupuesto casi agotado
            if project.budget_total > 0:
                remaining_pct = (project.budget_remaining / project.budget_total) * 100
                if remaining_pct < 10:
                    alerts.append(
                        ("danger", f"Presupuesto crítico ({remaining_pct:.1f}% restante)")
                    )
                elif remaining_pct < 20:
                    alerts.append(("warning", f"Presupuesto bajo ({remaining_pct:.1f}% restante)"))

            if alerts:
                projects_with_alerts.append(
                    {"project": project, "alerts": alerts, "metrics": metrics}
                )
        except Exception:
            pass

    # === APROBACIONES PENDIENTES ===
    # COs pendientes detallados
    pending_cos_list = ChangeOrder.objects.filter(status="pending").select_related("project")[:10]

    # Solicitudes cliente detalladas
    pending_requests_list = ClientRequest.objects.filter(status="pending").select_related(
        "project", "created_by"
    )[:10]

    # Materiales pendientes orden
    pending_materials = MaterialRequest.objects.filter(status="submitted").count()

    # === NÓMINA ===
    # Último periodo y balance
    latest_payroll_period = PayrollPeriod.objects.order_by("-week_start").first()
    payroll_balance = latest_payroll_period.balance_due() if latest_payroll_period else Decimal("0")

    # === RESUMEN PROYECTOS ===
    active_projects = Project.objects.filter(end_date__isnull=True).count()
    completed_projects = Project.objects.filter(end_date__isnull=False).count()

    # === MÉTRICAS TIEMPO ===
    today_entries = TimeEntry.objects.filter(date=today)
    today_hours = today_entries.aggregate(total=Sum("hours_worked"))["total"] or Decimal("0")
    today_labor_cost = sum(entry.labor_cost for entry in today_entries)

    week_start = today - timedelta(days=today.weekday())
    week_entries = TimeEntry.objects.filter(date__gte=week_start, date__lte=today)
    week_hours = week_entries.aggregate(total=Sum("hours_worked"))["total"] or Decimal("0")

    # Morning Briefing (executive summary)
    morning_briefing = []
    try:
        if unassigned_time_count > 0:
            morning_briefing.append(
                {
                    "text": _("%d time entries without Change Order require assignment")
                    % unassigned_time_count,
                    "severity": "danger" if unassigned_time_count >= 5 else "warning",
                    "action_url": reverse("unassigned_timeentries"),
                    "action_label": _("Assign"),
                    "category": "problems",
                }
            )
        if pending_client_requests > 0:
            morning_briefing.append(
                {
                    "text": _("%d client requests pending review") % pending_client_requests,
                    "severity": "info" if pending_client_requests < 5 else "warning",
                    "action_url": reverse("client_requests_list_all"),
                    "action_label": _("Review"),
                    "category": "approvals",
                }
            )
        if pending_cos > 0:
            morning_briefing.append(
                {
                    "text": _("%d change orders awaiting approval") % pending_cos,
                    "severity": "warning" if pending_cos < 3 else "danger",
                    "action_url": reverse("changeorder_board"),
                    "action_label": _("Approve"),
                    "category": "approvals",
                }
            )
        if pending_invoices > 0:
            morning_briefing.append(
                {
                    "text": _("%d invoices pending payment/processing") % pending_invoices,
                    "severity": "warning",
                    "action_url": reverse("invoice_payment_dashboard"),
                    "action_label": _("Payments"),
                    "category": "problems",
                }
            )
    except Exception:
        morning_briefing = []

    # Apply filter to morning briefing
    active_filter = request.GET.get("filter", "all")
    if active_filter == "problems":
        morning_briefing = [item for item in morning_briefing if item.get("category") == "problems"]
    elif active_filter == "approvals":
        morning_briefing = [
            item for item in morning_briefing if item.get("category") == "approvals"
        ]

    active_lang = (
        session_lang or getattr(request, "LANGUAGE_CODE", None) or translation.get_language()
    )
    english_mode = str(active_lang or "").lower().startswith("en")

    # === SWITCH OPTIONS (para cambiar proyecto/CO cuando hay entrada abierta) ===
    switch_options = {"other_projects": [], "current_project_cos": [], "can_switch_to_base": False}
    if open_entry:
        # Otros proyectos (Admin puede ver todos, excluir el actual)
        other_projects = Project.objects.filter(is_archived=False).exclude(id=open_entry.project_id)[:10]
        switch_options["other_projects"] = [
            {"id": p.id, "name": p.name}
            for p in other_projects
        ]
        
        # COs del proyecto actual (disponibles para trabajo)
        # Incluir draft, pending, approved, sent, billed (excluir solo 'paid' que ya está cerrado)
        current_project_cos = ChangeOrder.objects.filter(
            project=open_entry.project,
            status__in=['draft', 'pending', 'approved', 'sent', 'billed']
        ).exclude(id=open_entry.change_order_id if open_entry.change_order else None)
        switch_options["current_project_cos"] = [
            {"id": co.id, "title": co.title, "pricing_type": co.pricing_type}
            for co in current_project_cos
        ]
        
        # Puede volver a base si actualmente está en un CO
        switch_options["can_switch_to_base"] = open_entry.change_order is not None

    context = {
        # Financiero
        "total_income": total_income,
        "total_expense": total_expense,
        "net_profit": net_profit,
        # Alertas
        "unassigned_time_count": unassigned_time_count,
        "unassigned_time_hours": unassigned_time_hours,
        "pending_client_requests": pending_client_requests,
        "pending_payroll": pending_payroll,
        "pending_invoices": pending_invoices,
        "pending_invoice_amount": pending_invoice_amount,
        "pending_cos": pending_cos,
        "pending_materials": pending_materials,
        # Proyectos con alertas
        "projects_with_alerts": projects_with_alerts,
        # Aprobaciones
        "pending_cos_list": pending_cos_list,
        "pending_requests_list": pending_requests_list,
        # Nómina
        "latest_payroll_period": latest_payroll_period,
        "payroll_balance": payroll_balance,
        # Resumen proyectos
        "active_projects": active_projects,
        "completed_projects": completed_projects,
        # Tiempo
        "today_hours": today_hours,
        "today_labor_cost": today_labor_cost,
        "week_hours": week_hours,
        "today": today,
        "now": now,
        # Briefing
        "morning_briefing": morning_briefing,
        "active_filter": active_filter,
        # Clock in/out para Admin
        "employee": employee,
        "open_entry": open_entry,
        "form": form,
        "switch_options": switch_options,
        "active_lang": active_lang,
        "session_lang": session_lang,
        "english_mode": english_mode,
    }

    # Keep `?legacy=` reserved for the legacy_shell (sidebar suppression) behavior.
    # The admin dashboard no longer supports a separate legacy template.
    template = "core/dashboard_admin_clean.html"

    context.setdefault("badges", {"unread_notifications_count": 0})

    return render(request, template, context)


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
        from core.models import ChangeOrder
        from core.services.financial_service import ChangeOrderService
        
        pending_change_orders = ChangeOrder.objects.filter(
            project=project,
            status__in=['pending', 'sent', 'approved'],
        ).filter(
            Q(signature_image__isnull=True) | Q(signature_image='')
        ).order_by('-date_created')[:5]
        
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
                "text": f"There are {len(latest_photos)} new photos from your project",
                "severity": "info",
                "action_url": "#",
                "action_label": "View photos",
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
        morning_briefing.append(
            {
                "text": f"You have ${total_due:,.2f} in pending invoices",
                "severity": "warning",
                "action_url": reverse("client_invoices")
                if "client_invoices"
                in [
                    pattern.name
                    for pattern in __import__("django.urls", fromlist=["get_resolver"])
                    .get_resolver()
                    .url_patterns
                ]
                else "#",
                "action_label": "Pay now",
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
                "text": f"Next activity scheduled for {next_date.strftime('%m/%d/%Y')}",
                "severity": "info",
                "action_url": "#",
                "action_label": "View schedule",
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


# --- EXECUTIVE BI DASHBOARD (Module 21) ---
@login_required
def executive_bi_dashboard(request):
    """High-level consolidated business intelligence dashboard.

    Uses FinancialAnalyticsService to avoid duplicated financial logic across
    various views and ensures consistency of KPIs.

    Supports cache invalidation via ?refresh query parameter.
    """
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Acceso solo para Admin/Staff.")
        return redirect("dashboard")

    # Check if refresh is requested
    if request.GET.get("refresh"):
        from django.core.cache import cache

        # Clear all BI-related caches
        today = timezone.localdate()
        cache_keys = [
            f"fa:cashflow:{today.isoformat()}:30",
            "fa:project_margins",
            f"fa:kpis:{today.isoformat()}",
            "fa:inventory_risk",
        ]
        for key in cache_keys:
            cache.delete(key)

    service = FinancialAnalyticsService()
    cash_flow = service.get_cash_flow_projection(days=30)
    margins = service.get_project_margins()
    kpis = service.get_company_health_kpis()
    top_employees = service.get_top_performing_employees(limit=8)
    inventory_risk = service.get_inventory_risk_items()

    from django.conf import settings

    low_margin_threshold = getattr(settings, "BI_LOW_MARGIN_THRESHOLD", 15.0)

    low_margin_projects = [m for m in margins if m["margin_pct"] < low_margin_threshold]
    high_margin_projects = sorted(margins, key=lambda m: m["margin_pct"], reverse=True)[:5]

    context = {
        "today": timezone.localdate(),
        "kpis": kpis,
        "cash_flow_chart_data": cash_flow["chart"],
        "low_margin_projects": low_margin_projects,
        "high_margin_projects": high_margin_projects,
        "top_performing_employees": top_employees,
        "inventory_risk_items": inventory_risk,
    }
    return render(request, "core/dashboard_bi.html", context)


@login_required
def master_schedule_center(request):
    """Master Schedule Center: unified view for strategic project timeline and tactical event calendar.

    Requires admin/staff access. Data is loaded asynchronously via API.
    """
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Acceso solo para Admin/Staff.")
        return redirect("dashboard")

    context = {
        "title": "Master Schedule Center",
    }
    return render(request, "core/master_schedule.html", context)


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


# --- PROJECT PDF ---
@login_required
def project_pdf_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)
    
    incomes = Income.objects.filter(project=project)
    expenses = Expense.objects.filter(project=project)
    time_entries = TimeEntry.objects.filter(project=project)
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


# --- CRUD SCHEDULE, EXPENSE, INCOME, TIMEENTRY ---
@login_required
def schedule_create_view(request):
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"]:
        return redirect("dashboard")

    if request.method == "POST":
        form = ScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("dashboard")
    else:
        form = ScheduleForm()
    return render(request, "core/schedule_form.html", {"form": form})


@login_required
def expense_create_view(request):
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    # Allow Django superusers and staff automatically
    if not (
        request.user.is_superuser
        or request.user.is_staff
        or role in ["admin", "superuser", "project_manager"]
    ):
        return redirect("dashboard")

    if request.method == "POST":
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("dashboard")
    else:
        form = ExpenseForm()
    
    # Pass projects and change_orders for dynamic filtering
    projects = Project.objects.all().order_by('name')
    change_orders = ChangeOrder.objects.select_related('project').all().order_by('project__name', 'id')
    cost_codes = CostCode.objects.filter(active=True).order_by('code')
    
    return render(request, "core/expense_form.html", {
        "form": form,
        "projects": projects,
        "change_orders": change_orders,
        "cost_codes": cost_codes,
    })


@login_required
def income_create_view(request):
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    # Allow Django superusers and staff automatically
    if not (
        request.user.is_superuser
        or request.user.is_staff
        or role in ["admin", "superuser", "project_manager"]
    ):
        return redirect("dashboard")

    if request.method == "POST":
        form = IncomeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("dashboard")
    else:
        form = IncomeForm()
    return render(request, "core/income_form.html", {"form": form})


@login_required
def income_list(request):
    from core.models import Income

    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        return redirect("dashboard")
    qs = Income.objects.select_related("project").all().order_by("-date")
    project_id = request.GET.get("project")
    if project_id:
        qs = qs.filter(project_id=project_id)
    return render(request, "core/income_list.html", {"incomes": qs})


@login_required
def income_edit_view(request, income_id):
    from core.models import Income

    income = get_object_or_404(Income, id=income_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, "Acceso denegado.")
        return redirect("income_list")
    if request.method == "POST":
        form = IncomeForm(request.POST, request.FILES, instance=income)
        if form.is_valid():
            form.save()
            messages.success(request, "Ingreso actualizado.")
            return redirect("income_list")
    else:
        form = IncomeForm(instance=income)
    return render(request, "core/income_form.html", {"form": form, "income": income})


@login_required
def income_delete_view(request, income_id):
    from core.models import Income

    income = get_object_or_404(Income, id=income_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, "Acceso denegado.")
        return redirect("income_list")
    if request.method == "POST":
        income.delete()
        messages.success(request, "Ingreso eliminado.")
        return redirect("income_list")
    return render(request, "core/income_confirm_delete.html", {"income": income})


@login_required
def expense_list(request):
    from core.models import Expense

    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        return redirect("dashboard")
    qs = Expense.objects.select_related("project").all().order_by("-date")
    project_id = request.GET.get("project")
    if project_id:
        qs = qs.filter(project_id=project_id)
    return render(request, "core/expense_list.html", {"expenses": qs})


@login_required
def expense_edit_view(request, expense_id):
    from core.models import Expense

    expense = get_object_or_404(Expense, id=expense_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, "Acceso denegado.")
        return redirect("expense_list")
    if request.method == "POST":
        form = ExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, "Gasto actualizado.")
            return redirect("expense_list")
    else:
        form = ExpenseForm(instance=expense)
    return render(request, "core/expense_form.html", {"form": form, "expense": expense})


@login_required
def expense_delete_view(request, expense_id):
    from core.models import Expense

    expense = get_object_or_404(Expense, id=expense_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, "Acceso denegado.")
        return redirect("expense_list")
    if request.method == "POST":
        expense.delete()
        messages.success(request, "Gasto eliminado.")
        return redirect("expense_list")
    return render(request, "core/expense_confirm_delete.html", {"expense": expense})


@login_required
def timeentry_create_view(request):
    if request.method == "POST":
        form = TimeEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            # Support both legacy related name 'employee' and current 'employee_profile'
            from core.models import Employee

            emp = getattr(request.user, "employee_profile", None) or getattr(
                request.user, "employee", None
            )
            if emp is None:
                emp = Employee.objects.filter(user=request.user).first()
            entry.employee = emp
            entry.save()
            messages.success(request, "Horas registradas.")
            return redirect("dashboard")
    else:
        form = TimeEntryForm()
    return render(request, "core/timeentry_form.html", {"form": form})


@login_required
def timeentry_edit_view(request, entry_id: int):
    """Edit an existing TimeEntry. Allowed for staff/PM or the owning employee's user."""
    from core.models import TimeEntry

    entry = get_object_or_404(TimeEntry, id=entry_id)

    # Permissions: staff/pm or owner
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    is_staff_pm = role in ["admin", "superuser", "project_manager"] or request.user.is_staff
    is_owner = bool(getattr(entry.employee, "user_id", None) == request.user.id)
    if not (is_staff_pm or is_owner):
        messages.error(request, "Acceso denegado.")
        return redirect("dashboard")

    if request.method == "POST":
        form = TimeEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, "Registro de horas actualizado.")
            return redirect("dashboard")
    else:
        form = TimeEntryForm(instance=entry)
    return render(request, "core/timeentry_form.html", {"form": form, "timeentry": entry})


@login_required
def timeentry_delete_view(request, entry_id: int):
    """Delete a TimeEntry with confirmation. Same permissions as edit."""
    from core.models import TimeEntry

    entry = get_object_or_404(TimeEntry, id=entry_id)

    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    is_staff_pm = role in ["admin", "superuser", "project_manager"] or request.user.is_staff
    is_owner = bool(getattr(entry.employee, "user_id", None) == request.user.id)
    if not (is_staff_pm or is_owner):
        messages.error(request, "Acceso denegado.")
        return redirect("dashboard")

    if request.method == "POST":
        entry.delete()
        messages.success(request, "Registro de horas eliminado.")
        return redirect("dashboard")
    return render(request, "core/timeentry_confirm_delete.html", {"timeentry": entry})


@login_required
def payroll_weekly_review(request):
    """
    Vista para revisar y aprobar la nómina semanal.
    Muestra todos los empleados con sus horas trabajadas en la semana,
    permite editar horas de entrada/salida por día, y registrar pagos.
    
    SOLO ACCESIBLE POR ADMIN/SUPERUSER
    """
    # Solo admin/superuser puede acceder
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
        messages.error(request, "No tienes permiso para acceder a esta función.")
        return redirect("dashboard")

    from datetime import datetime, timedelta
    from decimal import Decimal, InvalidOperation
    from core.models import EmployeeSavings

    # Obtener parámetros de fecha (por defecto: semana actual)
    week_start_str = request.GET.get("week_start")
    if week_start_str:
        try:
            week_start = datetime.strptime(week_start_str, "%Y-%m-%d").date()
        except ValueError:
            week_start = datetime.now().date() - timedelta(days=datetime.now().date().weekday())
    else:
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())  # Lunes de esta semana

    week_end = week_start + timedelta(days=6)  # Domingo
    prev_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)

    # Crear lista de días de la semana
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    days = []
    for i in range(7):
        day_date = week_start + timedelta(days=i)
        days.append({
            'name': day_names[i],
            'date': day_date,
            'index': i
        })

    # Buscar o crear PayrollPeriod
    period, created = PayrollPeriod.objects.get_or_create(
        week_start=week_start, week_end=week_end, defaults={"created_by": request.user}
    )

    # Obtener todos los empleados activos
    employees = Employee.objects.filter(is_active=True).order_by("last_name", "first_name")

    # POST: Actualizar registros
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update_records":
            time_format = "%H:%M"
            
            for emp in employees:
                emp_id = str(emp.id)
                
                # Procesar horas de entrada/salida por cada día
                for i in range(7):
                    day = week_start + timedelta(days=i)
                    start_val = request.POST.get(f"start_{emp_id}_{i}")
                    end_val = request.POST.get(f"end_{emp_id}_{i}")
                    
                    # Buscar entrada existente para este día
                    existing_entry = TimeEntry.objects.filter(
                        employee=emp, date=day, change_order__isnull=True
                    ).first()
                    
                    if start_val and end_val:
                        try:
                            start_time = datetime.strptime(start_val, time_format).time()
                            end_time = datetime.strptime(end_val, time_format).time()
                        except ValueError:
                            continue
                        
                        if existing_entry:
                            existing_entry.start_time = start_time
                            existing_entry.end_time = end_time
                            existing_entry.save()
                        else:
                            TimeEntry.objects.create(
                                employee=emp,
                                date=day,
                                start_time=start_time,
                                end_time=end_time,
                            )
                    elif existing_entry and not start_val and not end_val:
                        # Si se borraron ambos campos, eliminar la entrada
                        existing_entry.delete()
                
                # Actualizar PayrollRecord
                record, _ = PayrollRecord.objects.get_or_create(
                    period=period,
                    employee=emp,
                    week_start=week_start,
                    week_end=week_end,
                    defaults={
                        "hourly_rate": emp.hourly_rate,
                        "total_hours": Decimal("0.00"),
                        "total_pay": Decimal("0.00"),
                    },
                )
                
                # IMPORTANTE: Guardar total_pay ANTES de recalcular (para pagos)
                original_total_pay = record.total_pay
                
                # Recalcular horas totales
                time_entries = TimeEntry.objects.filter(
                    employee=emp, date__range=(week_start, week_end)
                )
                total_hours = sum(
                    Decimal(str(entry.hours_worked)) if entry.hours_worked else Decimal("0.00")
                    for entry in time_entries
                )
                
                # Actualizar rate si cambió
                rate = request.POST.get(f"rate_{emp_id}")
                if rate:
                    try:
                        record.adjusted_rate = Decimal(rate)
                    except:
                        pass
                
                record.total_hours = total_hours
                record.split_hours_regular_overtime()
                record.calculate_total_pay()
                record.reviewed = True
                record.save()
                
                # Procesar pago si se proporcionó cantidad pagada y fecha
                paid_amount_str = request.POST.get(f"paid_{emp_id}")
                check_number = request.POST.get(f"check_{emp_id}", "").strip()
                pay_date = request.POST.get(f"pay_date_{emp_id}")
                
                # Solo procesar si hay monto pagado y fecha
                if paid_amount_str and paid_amount_str.strip():
                    try:
                        paid_amount = Decimal(paid_amount_str.strip())
                        
                        # Solo procesar si el monto es > 0 y hay fecha
                        if paid_amount > 0:
                            if not pay_date:
                                messages.warning(
                                    request, 
                                    f"{emp.first_name} {emp.last_name}: Falta la fecha de pago"
                                )
                                continue
                            
                            # Usar el total_pay original (antes de recalcular) para calcular savings
                            # Esto permite registrar pagos parciales incluso si no hay TimeEntries
                            total_to_pay = original_total_pay if original_total_pay > 0 else paid_amount
                            
                            # Calcular savings: diferencia entre total y lo pagado
                            # Si paid_amount >= total_to_pay, no hay savings
                            if paid_amount >= total_to_pay:
                                savings_amount = Decimal("0")
                            else:
                                savings_amount = total_to_pay - paid_amount
                            
                            # Verificar si ya existe un pago para esta semana y empleado
                            existing_payment = PayrollPayment.objects.filter(
                                payroll_record=record,
                                payment_date=pay_date,
                            ).first()
                            
                            # Si hay check_number, también verificar por ese
                            if check_number and not existing_payment:
                                existing_payment = PayrollPayment.objects.filter(
                                    payroll_record=record,
                                    check_number=check_number
                                ).first()
                            
                            if existing_payment:
                                # Ya existe un pago, actualizarlo si los montos son diferentes
                                if existing_payment.amount_taken != paid_amount:
                                    existing_payment.amount = paid_amount + savings_amount
                                    existing_payment.amount_taken = paid_amount
                                    existing_payment.amount_saved = savings_amount
                                    existing_payment.check_number = check_number
                                    existing_payment.save()
                                    messages.info(
                                        request,
                                        f"{emp.first_name}: Pago actualizado - ${paid_amount}" + 
                                        (f", Ahorro ${savings_amount}" if savings_amount > 0 else "")
                                    )
                            else:
                                # Crear nuevo pago
                                PayrollPayment.objects.create(
                                    payroll_record=record,
                                    amount=paid_amount + savings_amount,  # Total amount (paid + saved)
                                    amount_taken=paid_amount,  # What employee takes
                                    amount_saved=savings_amount,  # What goes to savings
                                    payment_date=pay_date,
                                    payment_method="check" if check_number else "cash",
                                    check_number=check_number,
                                    notes=f"Savings: ${savings_amount}" if savings_amount > 0 else "",
                                    recorded_by=request.user,
                                )
                                
                                if savings_amount > 0:
                                    messages.info(
                                        request,
                                        f"{emp.first_name} {emp.last_name}: Pagado ${paid_amount}, Ahorro ${savings_amount}"
                                    )
                                else:
                                    messages.success(
                                        request,
                                        f"{emp.first_name} {emp.last_name}: Pagado ${paid_amount}"
                                    )
                    except (ValueError, InvalidOperation) as e:
                        messages.warning(request, f"Error procesando pago para {emp.first_name}: {str(e)}")

            messages.success(request, "Nómina actualizada correctamente.")
            return redirect(f"{request.path}?week_start={week_start.isoformat()}")

    # Preparar datos de cada empleado
    employee_data = []
    for emp in employees:
        # Buscar o crear PayrollRecord
        record, rec_created = PayrollRecord.objects.get_or_create(
            period=period,
            employee=emp,
            week_start=week_start,
            week_end=week_end,
            defaults={
                "hourly_rate": emp.hourly_rate,
                "total_hours": Decimal("0.00"),
                "total_pay": Decimal("0.00"),
            },
        )

        # Obtener TODAS las entradas de tiempo para cada día (incluyendo CO)
        day_entries = []
        calculated_hours = Decimal("0.00")
        base_hours = Decimal("0.00")
        co_hours = Decimal("0.00")
        
        for i in range(7):
            day = week_start + timedelta(days=i)
            # Obtener TODAS las entradas del día (base + CO)
            entries = TimeEntry.objects.filter(
                employee=emp, date=day
            ).select_related('change_order', 'project').order_by('start_time')
            
            day_total_hours = Decimal("0.00")
            day_base_hours = Decimal("0.00")
            day_co_hours = Decimal("0.00")
            first_start = None
            last_end = None
            entry_details = []
            
            for entry in entries:
                hours = Decimal(str(entry.hours_worked)) if entry.hours_worked else Decimal("0")
                day_total_hours += hours
                
                if entry.change_order:
                    day_co_hours += hours
                    entry_details.append({
                        'type': 'CO',
                        'co_id': entry.change_order.id,
                        'co_title': entry.change_order.title,
                        'hours': float(hours),
                    })
                else:
                    day_base_hours += hours
                    entry_details.append({
                        'type': 'BASE',
                        'project': entry.project.name if entry.project else '',
                        'hours': float(hours),
                    })
                
                # Track first start and last end for display
                if entry.start_time:
                    if first_start is None or entry.start_time < first_start:
                        first_start = entry.start_time
                if entry.end_time:
                    if last_end is None or entry.end_time > last_end:
                        last_end = entry.end_time
            
            calculated_hours += day_total_hours
            base_hours += day_base_hours
            co_hours += day_co_hours
            
            day_entries.append({
                'start': first_start.strftime("%H:%M") if first_start else "",
                'end': last_end.strftime("%H:%M") if last_end else "",
                'hours': day_total_hours if day_total_hours > 0 else None,
                'base_hours': day_base_hours,
                'co_hours': day_co_hours,
                'details': entry_details,
                'entry_count': len(entries),
            })
        
        # Actualizar record con horas calculadas si es diferente
        if record.total_hours != calculated_hours:
            record.total_hours = calculated_hours
            record.split_hours_regular_overtime()
            record.calculate_total_pay()
            record.save()
        
        # Obtener último pago
        last_payment = record.payments.order_by('-payment_date').first()
        
        # Obtener balance de ahorros del empleado
        savings_balance = EmployeeSavings.get_employee_balance(emp)

        employee_data.append({
            "employee": emp,
            "record": record,
            "calculated_hours": calculated_hours,
            "base_hours": base_hours,
            "co_hours": co_hours,
            "day_entries": day_entries,
            "last_payment": last_payment,
            "savings_balance": savings_balance,
        })

    # Calcular totales
    total_hours = sum(data["calculated_hours"] for data in employee_data)
    total_payroll = sum(data["record"].total_pay or Decimal("0") for data in employee_data)
    total_paid = sum(data["record"].amount_paid() for data in employee_data)
    balance_due = total_payroll - total_paid

    context = {
        "period": period,
        "week_start": week_start,
        "week_end": week_end,
        "prev_week": prev_week,
        "next_week": next_week,
        "days": days,
        "employee_data": employee_data,
        "total_hours": total_hours,
        "total_payroll": total_payroll,
        "total_paid": total_paid,
        "balance_due": balance_due,
    }

    return render(request, "core/payroll_weekly_review.html", context)


@login_required
def payroll_record_payment(request, record_id):
    """
    Registrar un pago (parcial o completo) para un PayrollRecord.
    Soporta pagos con ahorro - el empleado puede llevarse menos y dejar el resto.
    SOLO ACCESIBLE POR ADMIN/SUPERUSER
    """
    # Solo admin/superuser puede acceder
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
        messages.error(request, "No tienes permiso para acceder a esta función.")
        return redirect("dashboard")

    record = get_object_or_404(PayrollRecord, id=record_id)

    if request.method == "POST":
        amount = request.POST.get("amount")
        amount_taken = request.POST.get("amount_taken")
        amount_saved = request.POST.get("amount_saved", "0")
        payment_date = request.POST.get("payment_date")
        payment_method = request.POST.get("payment_method", "check")
        check_number = request.POST.get("check_number", "")
        reference = request.POST.get("reference", "")
        notes = request.POST.get("notes", "")

        if amount and payment_date:
            try:
                total_amount = Decimal(amount)
                taken = Decimal(amount_taken) if amount_taken else total_amount
                saved = Decimal(amount_saved) if amount_saved else Decimal("0")
                
                # Validate: amount_taken + amount_saved should equal total amount
                if taken + saved != total_amount:
                    messages.error(
                        request,
                        _("Amount taken ($%(taken)s) + Amount saved ($%(saved)s) must equal Total ($%(total)s)")
                        % {"taken": taken, "saved": saved, "total": total_amount}
                    )
                    return redirect(request.path)
                
                PayrollPayment.objects.create(
                    payroll_record=record,
                    amount=total_amount,
                    amount_taken=taken,
                    amount_saved=saved,
                    payment_date=payment_date,
                    payment_method=payment_method,
                    check_number=check_number,
                    reference=reference,
                    notes=notes,
                    recorded_by=request.user,
                )

                if saved > 0:
                    messages.success(
                        request,
                        _("Payment recorded: $%(taken)s paid to %(employee)s, $%(saved)s saved.")
                        % {"taken": taken, "employee": record.employee, "saved": saved},
                    )
                else:
                    messages.success(
                        request,
                        _("Payment of $%(amount)s recorded for %(employee)s.")
                        % {"amount": total_amount, "employee": record.employee},
                    )
            except Exception as e:
                messages.error(request, f"Error processing payment: {str(e)}")
                return redirect(request.path)

            # Redirigir de vuelta a la revisión semanal
            return redirect("payroll_weekly_review")
        else:
            messages.error(request, "Monto y fecha de pago son requeridos.")

    return render(
        request,
        "core/payroll_payment_form.html",
        {
            "record": record,
        },
    )


@login_required
def payroll_payment_history(request, employee_id=None):
    """
    Historial de pagos de nómina. Si se especifica employee_id, muestra solo ese empleado.
    SOLO ACCESIBLE POR ADMIN/SUPERUSER
    """
    # Solo admin/superuser puede acceder
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
        messages.error(request, "No tienes permiso para acceder a esta función.")
        return redirect("dashboard")

    if employee_id:
        employee = get_object_or_404(Employee, id=employee_id)
        records = PayrollRecord.objects.filter(employee=employee).order_by("-week_start")
    else:
        employee = None
        records = PayrollRecord.objects.all().order_by("-week_start", "employee__last_name")

    # Agregar datos de pagos a cada registro
    records_data = []
    for record in records:
        payments = record.payments.all()
        records_data.append(
            {
                "record": record,
                "payments": payments,
                "amount_paid": record.amount_paid(),
                "balance_due": record.balance_due(),
            }
        )

    context = {
        "employee": employee,
        "records_data": records_data,
    }

    return render(request, "core/payroll_payment_history.html", context)


@login_required
def employee_savings_ledger(request, employee_id=None):
    """
    Vista del ledger de ahorros de empleados.
    Muestra el balance actual y historial de transacciones para cada empleado.
    Permite registrar retiros.
    SOLO ACCESIBLE POR ADMIN/SUPERUSER
    """
    from core.models import EmployeeSavings
    from decimal import Decimal
    
    # Solo admin/superuser puede acceder
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
        messages.error(request, "No tienes permiso para acceder a esta función.")
        return redirect("dashboard")
    
    # Si se especifica employee_id, mostrar solo ese empleado
    if employee_id:
        employee = get_object_or_404(Employee, id=employee_id)
        employees_data = [{
            'employee': employee,
            'balance': EmployeeSavings.get_employee_balance(employee),
            'ledger': EmployeeSavings.get_employee_ledger(employee),
        }]
    else:
        # Mostrar todos los empleados activos con ahorros
        employees = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
        employees_data = []
        
        for emp in employees:
            balance = EmployeeSavings.get_employee_balance(emp)
            # Solo mostrar empleados con historial de ahorros
            has_savings = EmployeeSavings.objects.filter(employee=emp).exists()
            if has_savings or balance > 0:
                employees_data.append({
                    'employee': emp,
                    'balance': balance,
                    'ledger': EmployeeSavings.get_employee_ledger(emp),
                })
    
    # Calcular totales
    total_balance = sum(data['balance'] for data in employees_data)
    total_employees_with_savings = len([d for d in employees_data if d['balance'] > 0])
    
    # Handle POST: registrar retiro
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "withdrawal":
            emp_id = request.POST.get("employee_id")
            amount = request.POST.get("amount")
            notes = request.POST.get("notes", "")
            withdrawal_date = request.POST.get("date")
            
            if emp_id and amount and withdrawal_date:
                try:
                    emp = Employee.objects.get(id=emp_id)
                    withdrawal_amount = Decimal(amount)
                    current_balance = EmployeeSavings.get_employee_balance(emp)
                    
                    if withdrawal_amount > current_balance:
                        messages.error(
                            request,
                            _("Cannot withdraw $%(amount)s. Employee only has $%(balance)s saved.")
                            % {"amount": withdrawal_amount, "balance": current_balance}
                        )
                    else:
                        EmployeeSavings.objects.create(
                            employee=emp,
                            amount=withdrawal_amount,
                            transaction_type='withdrawal',
                            date=withdrawal_date,
                            notes=notes or "Cash withdrawal",
                            recorded_by=request.user,
                        )
                        messages.success(
                            request,
                            _("Withdrawal of $%(amount)s recorded for %(employee)s.")
                            % {"amount": withdrawal_amount, "employee": f"{emp.first_name} {emp.last_name}"}
                        )
                except Employee.DoesNotExist:
                    messages.error(request, "Employee not found.")
                except Exception as e:
                    messages.error(request, f"Error: {str(e)}")
                
                return redirect("employee_savings_ledger")
        
        elif action == "adjustment":
            emp_id = request.POST.get("employee_id")
            amount = request.POST.get("amount")
            notes = request.POST.get("notes", "")
            adjustment_date = request.POST.get("date")
            
            if emp_id and amount and adjustment_date:
                try:
                    emp = Employee.objects.get(id=emp_id)
                    EmployeeSavings.objects.create(
                        employee=emp,
                        amount=Decimal(amount),  # Can be positive or negative
                        transaction_type='adjustment',
                        date=adjustment_date,
                        notes=notes or "Manual adjustment",
                        recorded_by=request.user,
                    )
                    messages.success(
                        request,
                        _("Adjustment recorded for %(employee)s.")
                        % {"employee": f"{emp.first_name} {emp.last_name}"}
                    )
                except Exception as e:
                    messages.error(request, f"Error: {str(e)}")
                
                return redirect("employee_savings_ledger")
    
    # Get all active employees for dropdown
    all_employees = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
    
    # Determine selected employee for context
    selected_employee = None
    if employee_id:
        selected_employee = get_object_or_404(Employee, id=employee_id)
    
    context = {
        "employees_data": employees_data,
        "total_balance": total_balance,
        "total_employees_with_savings": total_employees_with_savings,
        "all_employees": all_employees,
        "selected_employee": selected_employee,
    }
    
    return render(request, "core/employee_savings_ledger.html", context)


@login_required
def manual_timeentry_create(request):
    """
    Admin view to manually create TimeEntry for any employee.
    Used when employee forgot to check in/out.
    SOLO ACCESIBLE POR ADMIN/SUPERUSER
    """
    from core.models import Employee, Project, ChangeOrder, TimeEntry
    from decimal import Decimal
    from datetime import datetime
    
    # Solo admin/superuser puede acceder
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
        messages.error(request, "No tienes permiso para acceder a esta función.")
        return redirect("dashboard")
    
    employees = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
    projects = Project.objects.filter(is_archived=False).order_by('name')
    change_orders = ChangeOrder.objects.filter(status='approved').order_by('-created_at')[:100]
    
    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        project_id = request.POST.get("project_id")
        change_order_id = request.POST.get("change_order_id")
        entry_date = request.POST.get("date")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")
        notes = request.POST.get("notes", "")
        
        if employee_id and entry_date and start_time and end_time:
            try:
                emp = Employee.objects.get(id=employee_id)
                
                # Parse times
                start_t = datetime.strptime(start_time, "%H:%M").time()
                end_t = datetime.strptime(end_time, "%H:%M").time()
                
                # Calculate hours
                start_mins = start_t.hour * 60 + start_t.minute
                end_mins = end_t.hour * 60 + end_t.minute
                if end_mins < start_mins:  # Overnight shift
                    end_mins += 24 * 60
                hours_worked = Decimal(str((end_mins - start_mins) / 60.0))
                
                # Create entry
                entry = TimeEntry(
                    employee=emp,
                    date=entry_date,
                    start_time=start_t,
                    end_time=end_t,
                    hours_worked=hours_worked,
                    notes=f"[Manual entry by {request.user.username}] {notes}".strip(),
                )
                
                # Assign project if provided
                if project_id:
                    entry.project = Project.objects.get(id=project_id)
                
                # Assign CO if provided
                if change_order_id:
                    entry.change_order = ChangeOrder.objects.get(id=change_order_id)
                
                entry.save()
                
                messages.success(
                    request,
                    _("Time entry created: %(employee)s - %(hours)s hours on %(date)s")
                    % {
                        "employee": f"{emp.first_name} {emp.last_name}",
                        "hours": hours_worked,
                        "date": entry_date,
                    }
                )
                
                # Redirect back with week_start to stay on same week
                # Calculate week start from entry date
                from datetime import timedelta
                entry_date_obj = datetime.strptime(entry_date, "%Y-%m-%d").date()
                week_start = entry_date_obj - timedelta(days=entry_date_obj.weekday())
                
                return redirect(f"/payroll/week/?week_start={week_start.isoformat()}")
                
            except Employee.DoesNotExist:
                messages.error(request, "Employee not found.")
            except Project.DoesNotExist:
                messages.error(request, "Project not found.")
            except ChangeOrder.DoesNotExist:
                messages.error(request, "Change Order not found.")
            except Exception as e:
                messages.error(request, f"Error creating time entry: {str(e)}")
        else:
            messages.error(request, _("Employee, date, start time, and end time are required."))
    
    # Get default date from query param or today
    default_date = request.GET.get("date", datetime.now().strftime("%Y-%m-%d"))
    default_employee = request.GET.get("employee_id", "")
    
    context = {
        "employees": employees,
        "projects": projects,
        "change_orders": change_orders,
        "default_date": default_date,
        "default_employee": default_employee,
    }
    
    return render(request, "core/manual_timeentry_form.html", context)


# --- CLIENTE: Vista de proyecto y formularios ---
@login_required
def client_project_view(request, project_id):
    """
    Dashboard completo de UN proyecto individual para el cliente.
    El cliente ve: pending requests, minutas, fotos, schedule, tareas/touch-ups.
    """
    project = get_object_or_404(Project, id=project_id)

    # Verificar acceso: el usuario debe ser el cliente de este proyecto
    # o tener perfil de cliente con acceso (en caso de múltiples PMs de una compañía)
    profile = getattr(request.user, "profile", None)
    from core.models import ClientProjectAccess

    has_explicit_access = ClientProjectAccess.objects.filter(
        user=request.user, project=project
    ).exists()
    if profile and profile.role == "client":
        # Permitir si está asignado por acceso granular o si coincide el nombre de cliente (legacy)
        if not (has_explicit_access or project.client == request.user.username):
            messages.error(request, "You don't have access to this project.")
            return redirect("dashboard_client")
    else:
        # Permitir staff; si es PM externo (no staff), permitir solo si tiene acceso granular
        if request.user.is_staff or has_explicit_access:
            pass
        else:
            messages.error(request, "Access denied.")
            return redirect("dashboard")

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

    context = {
        "project": project,
        "pending_requests": pending_requests,
        "project_minutes": project_minutes,
        "recent_photos": recent_photos,
        "upcoming_schedules": upcoming_schedules,
        "tasks": tasks,
        "pending_tasks": pending_tasks,
        "completed_tasks": completed_tasks,
        "comments": comments,
        "invoices": invoices,
        "total_invoiced": total_invoiced,
        "total_paid": total_paid,
        "balance": total_invoiced - total_paid,
        "progress_pct": int(progress_pct),
        "gantt_progress": gantt_progress,
        "color_samples": color_samples,
        # Financial summary for mini panel
        "latest_estimate": latest_estimate,
        "base_contract_total": base_contract_total,
        "approved_cos": approved_cos,
        "pending_cos": pending_cos,
        "approved_cos_total": approved_cos_total,
        "pending_cos_total": pending_cos_total,
        "total_contract_value": total_contract_value,
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
    if project.client and hasattr(project.client, 'user'):
        is_project_client = project.client.user == request.user
    
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
    
    context = {
        "project": project,
        "latest_estimate": latest_estimate,
        "estimate_lines": estimate_lines,
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
        "payments": payments,
        "contract_breakdown_chart": contract_breakdown_chart,
        "payment_status_chart": payment_status_chart,
    }
    return render(request, "core/client_financials.html", context)


# --- COLOR SAMPLES ---
@login_required
def color_sample_list(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)
    
    samples = project.color_samples.select_related("created_by").all().order_by("-created_at")

    # Calculate status counts before filtering
    all_samples = project.color_samples.all()
    proposed_count = all_samples.filter(status="proposed").count()
    review_count = all_samples.filter(status="review").count()
    approved_count = all_samples.filter(status="approved").count()
    rejected_count = all_samples.filter(status="rejected").count()

    # Filters
    brand = request.GET.get("brand")
    if brand:
        samples = samples.filter(brand__icontains=brand)

    status = request.GET.get("status")
    if status:
        samples = samples.filter(status=status)

    return render(
        request,
        "core/color_sample_list.html",
        {
            "project": project,
            "samples": samples,
            "filter_brand": brand,
            "filter_status": status,
            "proposed_count": proposed_count,
            "review_count": review_count,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
        },
    )


@login_required
def color_sample_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)

    if request.method == "POST":
        form = ColorSampleForm(request.POST, request.FILES)
        if form.is_valid():
            inst = form.save(commit=False)
            inst.project = project
            inst.created_by = request.user
            inst.save()
            messages.success(request, "Color sample created.")
            return redirect("color_sample_list", project_id=project_id)
    else:
        form = ColorSampleForm(initial={"project": project})
    return render(
        request,
        "core/color_sample_form.html",
        {
            "form": form,
            "project": project,
        },
    )


@login_required
def color_sample_detail(request, sample_id):
    from core.models import ColorSample, ClientProjectAccess

    sample = get_object_or_404(ColorSample, id=sample_id)
    project = sample.project
    
    # Check access for clients
    profile = getattr(request.user, "profile", None)
    if profile and profile.role == "client":
        has_access = ClientProjectAccess.objects.filter(
            user=request.user, project=project
        ).exists() or project.client == request.user.username
        if not has_access:
            messages.error(request, "You don't have access to this project.")
            return redirect("dashboard_client")
    
    return render(
        request,
        "core/color_sample_detail.html",
        {
            "sample": sample,
            "project": project,
        },
    )


@login_required
def color_sample_review(request, sample_id):
    from core.models import ColorSample

    sample = get_object_or_404(ColorSample, id=sample_id)
    project = sample.project
    profile = getattr(request.user, "profile", None)
    # Permissions: clients, PM and designers can leave notes and move to 'review'; only staff can approve/reject
    if not (
        request.user.is_staff
        or (profile and profile.role in ["client", "project_manager", "designer"])
    ):
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    if request.method == "POST":
        form = ColorSampleReviewForm(request.POST, instance=sample)
        if form.is_valid():
            old_status = sample.status
            inst = form.save(commit=False)
            # Validate status transition
            requested_status = inst.status
            if requested_status in ["approved", "rejected"] and not request.user.is_staff:
                messages.error(request, "Only staff can approve or reject colors.")
            else:
                if requested_status == "approved" and not inst.approved_by:
                    inst.approved_by = request.user
                inst.save()
                # Notify changes
                from core.notifications import notify_color_approved, notify_color_review

                if requested_status == "approved":
                    notify_color_approved(inst, request.user)
                elif old_status != requested_status:
                    notify_color_review(inst, request.user)
                messages.success(
                    request,
                    f"Status updated to {inst.get_status_display()}"
                )
            return redirect("color_sample_detail", sample_id=sample.id)
    else:
        form = ColorSampleReviewForm(instance=sample)
    return render(
        request,
        "core/color_sample_review.html",
        {
            "form": form,
            "sample": sample,
            "project": project,
        },
    )


@login_required
def color_sample_quick_action(request, sample_id):
    """Quick approve/reject color sample (staff only, AJAX)."""
    if not request.user.is_staff:
        return JsonResponse({"error": "Permission denied"}, status=403)

    sample = get_object_or_404(ColorSample, id=sample_id)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "approve":
            # Use model method to ensure signature and audit
            sample.approve(request.user, request.META.get("REMOTE_ADDR"))
            from core.notifications import notify_color_approved

            notify_color_approved(sample, request.user)
            return JsonResponse(
                {
                    "success": True,
                    "status": "approved",
                    "display": "Approved",
                    "sample_number": sample.sample_number,
                    "signature": sample.approval_signature,
                }
            )
        elif action == "reject":
            reason = request.POST.get("reason", "").strip()
            if not reason:
                return JsonResponse({"error": "Rejection reason required"}, status=400)
            sample.reject(request.user, reason)
            return JsonResponse(
                {
                    "success": True,
                    "status": "rejected",
                    "display": "Rejected",
                    "reason": sample.rejection_reason,
                }
            )

    return JsonResponse({"error": "Invalid action"}, status=400)


@login_required
def color_sample_client_feedback(request, sample_id):
    """Handle client feedback on color samples (request changes or add comment)."""
    from core.models import ColorSample
    from core.notifications import notify_color_review
    
    sample = get_object_or_404(ColorSample, id=sample_id)
    project = sample.project
    
    # Check access - client must have access to this project
    profile = getattr(request.user, "profile", None)
    if not profile:
        messages.error(request, "Access denied.")
        return redirect("dashboard")
    
    # Allow clients, PMs, and staff
    if profile.role == "client":
        from core.models import ClientProjectAccess
        has_access = ClientProjectAccess.objects.filter(
            user=request.user, project=project
        ).exists() or project.client == request.user.username
        if not has_access:
            messages.error(request, "You don't have access to this project.")
            return redirect("dashboard_client")
    elif profile.role not in ["project_manager", "designer"] and not request.user.is_staff:
        messages.error(request, "Access denied.")
        return redirect("dashboard")
    
    if request.method == "POST":
        action = request.POST.get("action")
        feedback = request.POST.get("feedback", "").strip()
        
        if not feedback:
            messages.error(request, _("Please enter your feedback."))
            return redirect("color_sample_detail", sample_id=sample_id)
        
        if action == "request_changes":
            # Add feedback to client_notes and move to 'review' status
            existing_notes = sample.client_notes or ""
            timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
            new_note = f"[{timestamp}] Change requested by {request.user.get_full_name() or request.user.username}:\n{feedback}"
            sample.client_notes = f"{new_note}\n\n{existing_notes}".strip() if existing_notes else new_note
            sample.status = "review"
            sample.save()
            
            # Notify PM
            notify_color_review(sample, request.user)
            
            messages.success(request, _("Your feedback has been sent. The team will review your request."))
        
        elif action == "comment":
            # Just add comment to client_notes
            existing_notes = sample.client_notes or ""
            timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
            new_note = f"[{timestamp}] Comment from {request.user.get_full_name() or request.user.username}:\n{feedback}"
            sample.client_notes = f"{new_note}\n\n{existing_notes}".strip() if existing_notes else new_note
            sample.save()
            
            # Notify PM
            notify_color_review(sample, request.user)
            
            messages.success(request, _("Your comment has been added."))
        
        return redirect("color_sample_detail", sample_id=sample_id)
    
    return redirect("color_sample_detail", sample_id=sample_id)


@login_required
def color_sample_edit(request, sample_id):
    """Edit existing color sample"""
    sample = get_object_or_404(ColorSample, id=sample_id)
    project = sample.project
    profile = getattr(request.user, "profile", None)

    if not (request.user.is_staff or (profile and profile.role in ["client", "project_manager"])):
        messages.error(request, "Access denied.")
        return redirect("color_sample_detail", sample_id=sample_id)

    if request.method == "POST":
        form = ColorSampleForm(request.POST, request.FILES, instance=sample)
        if form.is_valid():
            form.save()
            messages.success(request, "Color sample updated.")
            return redirect("color_sample_detail", sample_id=sample_id)
    else:
        form = ColorSampleForm(instance=sample)

    return render(
        request,
        "core/color_sample_form.html",
        {
            "form": form,
            "project": project,
            "sample": sample,
            "is_edit": True,
        },
    )


@login_required
def color_sample_delete(request, sample_id):
    """Delete color sample"""
    sample = get_object_or_404(ColorSample, id=sample_id)
    project = sample.project
    profile = getattr(request.user, "profile", None)

    if not (request.user.is_staff or (profile and profile.role == "project_manager")):
        messages.error(request, "Access denied.")
        return redirect("color_sample_detail", sample_id=sample_id)

    if request.method == "POST":
        project_id = sample.project.id
        sample.delete()
        messages.success(request, "Color sample deleted.")
        return redirect("color_sample_list", project_id=project_id)

    return render(
        request,
        "core/color_sample_confirm_delete.html",
        {
            "sample": sample,
            "project": project,
        },
    )


# --- FLOOR PLANS ---
@login_required
def floor_plan_list(request, project_id):
    """List all floor plans for a project, grouped by level"""

    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)
    
    plans = project.floor_plans.all().order_by("level", "name")

    # Group plans by level
    plans_by_level = defaultdict(list)
    for plan in plans:
        plans_by_level[plan.level].append(plan)

    # Sort levels
    sorted_levels = sorted(plans_by_level.keys(), reverse=True)  # Top to bottom

    # Check if user can edit pins (PM, Admin, Client, Designer, Owner)
    profile = getattr(request.user, "profile", None)
    can_edit_pins = request.user.is_staff or (
        profile
        and profile.role in ["project_manager", "admin", "superuser", "client", "designer", "owner"]
    )

    return render(
        request,
        "core/floor_plan_list.html",
        {
            "project": project,
            "plans": plans,
            "plans_by_level": dict(plans_by_level),
            "sorted_levels": sorted_levels,
            "can_edit_pins": can_edit_pins,
        },
    )


@login_required
def floor_plan_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)
    
    if request.method == "POST":
        form = FloorPlanForm(request.POST, request.FILES)
        if form.is_valid():
            inst = form.save(commit=False)
            inst.project = project
            inst.created_by = request.user
            inst.save()
            messages.success(request, "Plano subido.")
            return redirect("floor_plan_list", project_id=project_id)
    else:
        form = FloorPlanForm(initial={"project": project})
    return render(
        request,
        "core/floor_plan_form.html",
        {
            "form": form,
            "project": project,
        },
    )


@login_required
def floor_plan_detail(request, plan_id):
    import json

    from core.models import FloorPlan

    plan = get_object_or_404(FloorPlan, id=plan_id)
    pins = plan.pins.select_related("color_sample", "linked_task").all()
    color_samples = plan.project.color_samples.filter(status__in=["approved", "review"]).order_by(
        "-created_at"
    )[:50]

    # Check if user can edit pins (PM, Admin, Client, Designer, Owner)
    profile = getattr(request.user, "profile", None)
    can_edit_pins = request.user.is_staff or (
        profile
        and profile.role in ["project_manager", "admin", "superuser", "client", "designer", "owner"]
    )

    # Check if user can delete pins/plan (only PM, Admin, Owner - NOT Designer)
    can_delete = request.user.is_staff or (
        profile and profile.role in ["project_manager", "admin", "superuser", "owner"]
    )

    # Serialize pins data for JavaScript
    pins_data = []
    for pin in pins:
        pins_data.append(
            {
                "id": pin.id,
                "x": float(pin.x),
                "y": float(pin.y),
                "title": pin.title,
                "description": pin.description or "",
                "pin_type": pin.pin_type,
                "pin_color": pin.pin_color,
                "path_points": pin.path_points or [],
            }
        )
    pins_json = json.dumps(pins_data)

    # Provide PlanPinForm so the page can render the pin editor fields
    from core.forms import PlanPinForm

    pin_form = PlanPinForm()

    return render(
        request,
        "core/floor_plan_detail.html",
        {
            "plan": plan,
            "pins": pins,
            "pins_json": pins_json,
            "color_samples": color_samples,
            "project": plan.project,
            "can_edit_pins": can_edit_pins,
            "can_delete": can_delete,
            "form": pin_form,
        },
    )


@login_required
def floor_plan_touchup_view(request, plan_id):
    """Display floor plan with touch-up and task pins (work items view)"""
    import json

    from core.models import FloorPlan

    plan = get_object_or_404(FloorPlan, id=plan_id)

    # Filter pins that are work items: touchup OR have a linked_task
    from django.db.models import Q
    all_work_pins = plan.pins.filter(
        Q(pin_type="touchup") | Q(linked_task__isnull=False)
    ).select_related("color_sample", "linked_task", "created_by").distinct()

    color_samples = plan.project.color_samples.filter(status__in=["approved", "review"]).order_by(
        "-created_at"
    )[:50]

    # Check if user can edit pins (PM, Admin, Client, Designer, Owner)
    profile = getattr(request.user, "profile", None)
    can_edit_pins = request.user.is_staff or (
        profile
        and profile.role in ["project_manager", "admin", "superuser", "client", "designer", "owner"]
    )

    # Check if user can delete pins/plan (only PM, Admin, Owner - NOT Designer)
    can_delete = request.user.is_staff or (
        profile and profile.role in ["project_manager", "admin", "superuser", "owner"]
    )

    # Serialize pins data for JavaScript
    pins_data = []
    for pin in all_work_pins:
        pins_data.append(
            {
                "id": pin.id,
                "x": float(pin.x),
                "y": float(pin.y),
                "title": pin.title,
                "description": pin.description or "",
                "pin_type": pin.pin_type,
                "pin_color": pin.pin_color,
                "path_points": pin.path_points or [],
            }
        )
    pins_json = json.dumps(pins_data)

    # Provide PlanPinForm so the page can render the pin editor fields
    from core.forms import PlanPinForm

    pin_form = PlanPinForm()

    # Get employees for task assignment
    from core.models import UserProfile
    employees = UserProfile.objects.filter(
        role__in=["project_manager", "admin", "designer", "field_worker"]
    ).select_related("user").order_by("user__first_name", "user__last_name")

    # Get existing tasks for linking (unlinked tasks without a pin)
    from core.models import Task
    unlinked_tasks = Task.objects.filter(
        project=plan.project,
        plan_pin__isnull=True  # Only tasks without a pin location
    ).order_by("-created_at")[:50]

    # Separate touchup pins and task pins for the template
    touchup_pins = [p for p in all_work_pins if p.pin_type == "touchup"]
    task_pins = [p for p in all_work_pins if p.pin_type != "touchup" and p.linked_task]

    return render(
        request,
        "core/floor_plan_touchup_view.html",
        {
            "plan": plan,
            "pins": all_work_pins,
            "pins_json": pins_json,
            "touchup_pins": touchup_pins,
            "task_pins": task_pins,
            "color_samples": color_samples,
            "project": plan.project,
            "can_edit_pins": can_edit_pins,
            "can_delete": can_delete,
            "form": pin_form,
            "employees": employees,
            "unlinked_tasks": unlinked_tasks,
        },
    )


@login_required
def floor_plan_edit(request, plan_id):
    """Edit an existing floor plan (name, level, image)"""
    plan = get_object_or_404(FloorPlan, id=plan_id)
    project = plan.project
    profile = getattr(request.user, "profile", None)
    if not (request.user.is_staff or (profile and profile.role in ["project_manager"])):
        messages.error(request, "Acceso denegado.")
        return redirect("floor_plan_detail", plan_id=plan.id)
    if request.method == "POST":
        form = FloorPlanForm(request.POST, request.FILES, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, "Plano actualizado.")
            return redirect("floor_plan_detail", plan_id=plan.id)
    else:
        form = FloorPlanForm(instance=plan)
    return render(
        request,
        "core/floor_plan_form.html",
        {
            "form": form,
            "project": project,
            "plan": plan,
            "is_edit": True,
        },
    )


@login_required
def floor_plan_delete(request, plan_id):
    """Delete a floor plan and its pins"""
    plan = get_object_or_404(FloorPlan, id=plan_id)
    project = plan.project
    profile = getattr(request.user, "profile", None)
    if not (request.user.is_staff or (profile and profile.role in ["project_manager"])):
        messages.error(request, "Acceso denegado.")
        return redirect("floor_plan_detail", plan_id=plan.id)
    if request.method == "POST":
        project_id = project.id
        plan.delete()
        messages.success(request, "Plano eliminado.")
        return redirect("floor_plan_list", project_id=project_id)
    return render(
        request,
        "core/floor_plan_confirm_delete.html",
        {
            "project": project,
            "plan": plan,
        },
    )


@login_required
def pin_detail_ajax(request, pin_id):
    """Return JSON details for a pin to show in a popover."""
    from core.models import PlanPin

    pin = get_object_or_404(
        PlanPin.objects.select_related("linked_task", "color_sample"), id=pin_id
    )
    data = {
        "id": pin.id,
        "title": getattr(pin, "title", f"Pin #{pin.id}"),
        "description": getattr(pin, "description", ""),
        "type": getattr(pin, "pin_type", ""),
        "color": getattr(pin, "pin_color", ""),
        "task": None,
        "color_sample": None,
        "links": {},
    }
    try:
        if pin.linked_task_id:
            data["task"] = {
                "id": pin.linked_task_id,
                "title": getattr(pin.linked_task, "title", ""),
                "status": getattr(pin.linked_task, "status", ""),
            }
            data["links"]["task"] = reverse("task_detail", args=[pin.linked_task_id])
        if pin.color_sample_id:
            data["color_sample"] = {
                "id": pin.color_sample_id,
                "name": getattr(pin.color_sample, "name", ""),
                "brand": getattr(pin.color_sample, "brand", ""),
                "status": getattr(pin.color_sample, "status", ""),
            }
            data["links"]["color_sample"] = reverse(
                "color_sample_detail", args=[pin.color_sample_id]
            )
    except Exception:
        pass
    return JsonResponse(data)


@login_required
def floor_plan_add_pin(request, plan_id):
    from core.models import DamageReport, FloorPlan, Task

    plan = get_object_or_404(FloorPlan, id=plan_id)
    if request.method == "POST":
        form = PlanPinForm(request.POST)
        try:
            x = Decimal(request.POST.get("x"))
            y = Decimal(request.POST.get("y"))
        except Exception:
            messages.error(request, "Coordenadas inválidas.")
            return redirect("floor_plan_detail", plan_id=plan.id)

        # Capturar datos de trayectoria multipunto si existen
        is_multipoint = request.POST.get("is_multipoint") == "true"
        path_points_json = request.POST.get("path_points", "[]")
        try:
            path_points = json.loads(path_points_json) if is_multipoint else []
        except Exception:
            path_points = []

        if form.is_valid():
            pin = form.save(commit=False)
            pin.plan = plan
            pin.x = x
            pin.y = y
            pin.is_multipoint = is_multipoint
            pin.path_points = path_points
            pin.created_by = request.user
            pin.save()
            # Crear entidades asociadas según tipo
            if form.cleaned_data.get("create_task") and pin.pin_type in ["touchup", "color"]:
                task = Task.objects.create(
                    project=plan.project,
                    title=pin.title or "Touch-up plano",
                    description=pin.description,
                    status="Pending",
                    created_by=request.user,
                    is_touchup=True,
                )
                pin.linked_task = task
                pin.save(update_fields=["linked_task"])
            elif pin.pin_type == "damage":
                # Crear reporte de daño básico y asociarlo al pin
                dr = DamageReport.objects.create(
                    project=plan.project,
                    plan=plan,
                    pin=pin,
                    title=pin.title or "Damage reported",
                    description=pin.description,
                    severity="medium",
                    status="open",
                    reported_by=request.user,
                )
                # Notificar PM
                from core.notifications import notify_damage_reported

                notify_damage_reported(dr, request.user)
            messages.success(request, "Pin agregado.")
            return redirect("floor_plan_detail", plan_id=plan.id)
    else:
        form = PlanPinForm()
    return render(
        request,
        "core/floor_plan_add_pin.html",
        {
            "form": form,
            "plan": plan,
            "project": plan.project,
        },
    )


@login_required
def agregar_tarea(request, project_id):
    """
    Permite a clientes agregar tareas (principalmente touch-ups).
    Cliente puede adjuntar fotos y agregar descripción.
    PM recibirá notificación y asignará a empleado.
    """
    project = get_object_or_404(Project, id=project_id)

    # Verificar que el usuario es el cliente de este proyecto o staff
    profile = getattr(request.user, "profile", None)
    from core.models import ClientProjectAccess

    has_access = ClientProjectAccess.objects.filter(user=request.user, project=project).exists()
    if profile and profile.role == "client":
        if not (has_access or project.client == request.user.username):
            messages.error(request, "No tienes acceso a este proyecto.")
            return redirect("dashboard_client")
    elif not request.user.is_staff and not has_access:
        messages.error(request, "Acceso denegado.")
        return redirect("dashboard")

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        image = request.FILES.get("image")

        if not title:
            messages.error(request, "Title is required.")
            return redirect("client_project_view", project_id=project_id)

        # Create task with Pending status and photo if exists
        task = Task.objects.create(
            project=project,
            title=title,
            description=description,
            status="Pending",
            created_by=request.user,
            image=image,
            is_touchup=True,
        )

        # Notificar a PMs
        from core.notifications import notify_task_created

        notify_task_created(task, request.user)

        messages.success(
            request,
            _("Tarea '%(title)s' creada exitosamente. El PM será notificado.") % {"title": title},
        )
        return redirect("client_project_view", project_id=project_id)


@login_required
def touchup_board(request, project_id):
    """Vista dedicada para gestionar touch-ups del proyecto (Q11.2 con mejoras)."""
    from django.core.paginator import Paginator

    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)
    
    qs = (
        project.tasks.filter(is_touchup=True)
        .select_related("assigned_to", "created_by")
        .order_by("-created_at")
    )

    # Filters
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)

    # ACTIVITY 1: Priority filter (Q11.6)
    priority = request.GET.get("priority")
    if priority:
        qs = qs.filter(priority=priority)

    assigned = request.GET.get("assigned")
    if assigned == "unassigned":
        qs = qs.filter(assigned_to__isnull=True)
    elif assigned:
        qs = qs.filter(assigned_to__id=assigned)

    date_from = request.GET.get("date_from")
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)

    date_to = request.GET.get("date_to")
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    # ACTIVITY 1: Filter by due date (Q11.1 - overdue tasks)
    show_overdue = request.GET.get("overdue")
    if show_overdue:
        from django.utils import timezone

        qs = qs.filter(due_date__lt=timezone.now().date(), status__in=["pending", "in_progress"])

    # Sorting (updated with new fields)
    sort_by = request.GET.get("sort", "-created_at")
    valid_sorts = [
        "created_at",
        "-created_at",
        "status",
        "-status",
        "assigned_to",
        "-assigned_to",
        "priority",
        "-priority",  # Q11.6
        "due_date",
        "-due_date",  # Q11.1
    ]
    if sort_by in valid_sorts:
        qs = qs.order_by(sort_by)

    # Pagination
    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get available employees for filter dropdown
    employees = User.objects.filter(profile__role__in=["employee", "superintendent"]).order_by(
        "username"
    )

    # ACTIVITY 1: Priority choices for filter dropdown
    from core.models import Task

    priority_choices = Task.PRIORITY_CHOICES

    # Usamos plantilla limpia para evitar errores de bloques duplicados
    return render(
        request,
        "core/touchup_board_clean.html",
        {
            "project": project,
            "page_obj": page_obj,
            "filter_status": status,
            "filter_priority": priority,
            "filter_assigned": assigned,
            "filter_date_from": date_from,
            "filter_date_to": date_to,
            "show_overdue": show_overdue,
            "sort_by": sort_by,
            "employees": employees,
            "priority_choices": priority_choices,
        },
    )


@login_required
def touchup_quick_update(request, task_id):
    """AJAX endpoint for quick status/assignment updates on touch-up board."""
    if request.method != "POST":
        return JsonResponse({"error": gettext("POST required")}, status=405)

    task = get_object_or_404(Task, id=task_id, is_touchup=True)

    # Check permission
    if not (request.user.is_staff or task.project.client == request.user.username):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

    action = request.POST.get("action")

    if action == "status":
        new_status = request.POST.get("status")
        if new_status in dict(Task.STATUS_CHOICES):
            task.status = new_status
            if new_status == "Completed":
                task.completed_at = timezone.now()
            task.save()
            return JsonResponse({"success": True, "status": task.get_status_display()})

    elif action == "assign":
        employee_id = request.POST.get("employee_id")
        if employee_id:
            employee = get_object_or_404(User, id=employee_id)
            task.assigned_to = employee
            task.save()
            return JsonResponse({"success": True, "assigned_to": employee.username})
        else:
            task.assigned_to = None
            task.save()
            return JsonResponse({"success": True, "assigned_to": "Sin asignar"})

    return JsonResponse({"error": gettext("Acción inválida")}, status=400)


@login_required
def damage_report_list(request, project_id):
    """Lista y creación de reportes de daños del proyecto."""
    from core.forms import DamageReportForm
    from core.models import DamagePhoto

    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)

    # Handle creation
    if request.method == "POST":
        form = DamageReportForm(project, request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.project = project
            report.reported_by = request.user
            report.save()

            # Handle multiple photo uploads
            photos = request.FILES.getlist("photos")
            for photo_file in photos:
                DamagePhoto.objects.create(
                    report=report, image=photo_file, notes=request.POST.get("photo_notes", "")
                )

            messages.success(
                request, _("Reporte creado con %(count)s foto(s)") % {"count": len(photos)}
            )
            return redirect("damage_report_detail", report_id=report.id)
    else:
        form = DamageReportForm(project)

    # List reports
    reports = project.damage_reports.select_related("plan", "pin", "reported_by").all()
    severity = request.GET.get("severity")
    if severity:
        reports = reports.filter(severity=severity)
    status = request.GET.get("status")
    if status:
        reports = reports.filter(status=status)

    return render(
        request,
        "core/damage_report_list.html",
        {
            "project": project,
            "reports": reports,
            "form": form,
            "filter_severity": severity,
            "filter_status": status,
        },
    )


@login_required
def damage_report_detail(request, report_id):
    from core.models import DamageReport

    report = get_object_or_404(DamageReport, id=report_id)
    return render(
        request,
        "core/damage_report_detail.html",
        {
            "report": report,
            "project": report.project,
        },
    )


@login_required
def damage_report_edit(request, report_id):
    """Edit an existing damage report."""
    from core.forms import DamageReportForm
    from core.models import DamageReport

    report = get_object_or_404(DamageReport, id=report_id)
    project = report.project
    profile = getattr(request.user, "profile", None)
    can_edit = (
        request.user.is_staff
        or (profile and profile.role in ["superintendent", "project_manager"])
        or (request.user == report.reported_by)
    )
    if not can_edit:
        messages.error(request, "Acceso denegado.")
        return redirect("damage_report_detail", report_id=report.id)
    if request.method == "POST":
        form = DamageReportForm(project, request.POST, request.FILES, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, "Reporte actualizado.")
            return redirect("damage_report_detail", report_id=report.id)
    else:
        form = DamageReportForm(project, instance=report)
    return render(
        request,
        "core/damage_report_form.html",
        {
            "form": form,
            "project": project,
            "report": report,
            "is_edit": True,
        },
    )


@login_required
def damage_report_delete(request, report_id):
    """Delete a damage report with confirmation."""
    from core.models import DamageReport

    report = get_object_or_404(DamageReport, id=report_id)
    project = report.project
    profile = getattr(request.user, "profile", None)
    can_delete = (
        request.user.is_staff
        or (profile and profile.role in ["superintendent", "project_manager"])
        or (request.user == report.reported_by)
    )
    if not can_delete:
        messages.error(request, "Acceso denegado.")
        return redirect("damage_report_detail", report_id=report.id)
    if request.method == "POST":
        project_id = project.id
        report.delete()
        messages.success(request, "Reporte de daño eliminado.")
        return redirect("damage_report_list", project_id=project_id)
    return render(
        request,
        "core/damage_report_confirm_delete.html",
        {
            "project": project,
            "report": report,
        },
    )


@login_required
def damage_report_add_photos(request, report_id):
    """Add multiple photos to existing damage report."""
    from core.models import DamagePhoto, DamageReport

    report = get_object_or_404(DamageReport, id=report_id)

    # Check permission
    if not (request.user.is_staff or request.user == report.reported_by):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

    if request.method == "POST":
        photos = request.FILES.getlist("photos")
        if not photos:
            return JsonResponse({"error": gettext("No se enviaron fotos")}, status=400)

        # Create DamagePhoto for each uploaded image
        created_count = 0
        for photo_file in photos:
            notes = request.POST.get("notes", "")
            DamagePhoto.objects.create(report=report, image=photo_file, notes=notes)
            created_count += 1

        return JsonResponse(
            {
                "success": True,
                "count": created_count,
                "message": f"{created_count} foto(s) agregada(s) correctamente",
            }
        )

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)


@login_required
def damage_report_update_status(request, report_id):
    """Update damage report status and severity."""
    report = get_object_or_404(DamageReport, id=report_id)

    # Check permission (staff or superintendent)
    profile = getattr(request.user, "profile", None)
    if not (request.user.is_staff or (profile and profile.role == "superintendent")):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

    if request.method == "POST":
        new_status = request.POST.get("status")
        new_severity = request.POST.get("severity")

        if new_status and new_status in dict(DamageReport.STATUS_CHOICES):
            report.status = new_status
            report.save()

        if new_severity and new_severity in dict(DamageReport.SEVERITY_CHOICES):
            report.severity = new_severity
            report.save()

        return JsonResponse(
            {
                "success": True,
                "status": report.get_status_display(),
                "severity": report.get_severity_display(),
            }
        )

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)


# =============================
# Project Chat (Premium)
# =============================


def _ensure_default_channels(project, user):
    group, _ = ChatChannel.objects.get_or_create(
        project=project,
        name="Group",
        defaults={"channel_type": "group", "is_default": True, "created_by": user},
    )
    direct, _ = ChatChannel.objects.get_or_create(
        project=project,
        name="Direct",
        defaults={"channel_type": "direct", "is_default": True, "created_by": user},
    )
    # Ensure participants
    if user and not group.participants.filter(id=user.id).exists():
        group.participants.add(user)
    if user and not direct.participants.filter(id=user.id).exists():
        direct.participants.add(user)
    # Include client user if matches username
    from django.contrib.auth.models import User as DjangoUser

    if project.client:
        try:
            cu = DjangoUser.objects.get(username=project.client)
            group.participants.add(cu)
            direct.participants.add(cu)
        except DjangoUser.DoesNotExist:
            pass
    return group, direct


@login_required
def chat_redirect_to_premium(request, project_id, channel_id=None):
    """Redirect legacy chat URLs to premium chat."""
    if channel_id:
        return redirect("project_chat_premium_channel", project_id=project_id, channel_id=channel_id)
    return redirect("project_chat_premium", project_id=project_id)


@login_required
def project_chat_premium(request, project_id, channel_id=None):
    """
    Premium chat view with WebSocket support.
    """
    project = get_object_or_404(Project, id=project_id)
    
    # ===== SECURITY: Verify user has access to this project =====
    if not request.user.is_staff:
        # Check if user is the client contact for this project
        is_client_contact = False
        if project.client:
            is_client_contact = (
                project.client.email == request.user.email or 
                project.client.user == request.user
            )
        
        # Check if user is assigned to the project
        is_assigned = project.assigned_to.filter(id=request.user.id).exists() if hasattr(project, 'assigned_to') else False
        
        if not is_client_contact and not is_assigned:
            messages.error(request, _("You don't have access to this project."))
            return redirect("dashboard_client")
    # ===== END SECURITY CHECK =====
    
    # Ensure default channels exist
    group, direct = _ensure_default_channels(project, request.user)
    
    # Get all channels for this project that user can access
    if request.user.is_staff:
        channels = project.chat_channels.all().order_by("name")
    else:
        channels = project.chat_channels.filter(
            participants=request.user
        ).order_by("name")
    
    # Select active channel
    if channel_id:
        channel = get_object_or_404(ChatChannel, id=channel_id, project=project)
        # Access control
        if not (request.user.is_staff or channel.participants.filter(id=request.user.id).exists()):
            messages.error(request, "No tienes acceso a este canal.")
            return redirect("project_chat_premium", project_id=project.id)
    else:
        # Default to group channel
        channel = group
    
    # Handle channel creation
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "send":
            # Send message via HTTP (fallback when WebSocket not available)
            text = (request.POST.get("message") or "").strip()
            link_url = (request.POST.get("link_url") or "").strip() or ""
            image = request.FILES.get("image")
            if text or image or link_url:
                ChatMessage.objects.create(
                    channel=channel,
                    user=request.user,
                    message=text,
                    link_url=link_url,
                    image=image if image else None
                )
            return redirect("project_chat_premium_channel", project_id=project.id, channel_id=channel.id)
        
        elif action == "create_channel":
            channel_name = (request.POST.get("channel_name") or "").strip()
            channel_type = request.POST.get("channel_type", "group")
            if channel_name:
                new_channel = ChatChannel.objects.create(
                    project=project,
                    name=channel_name,
                    channel_type=channel_type
                )
                new_channel.participants.add(request.user)
                messages.success(request, f"Canal '{channel_name}' creado.")
                return redirect("project_chat_premium_channel", project_id=project.id, channel_id=new_channel.id)
            else:
                messages.error(request, "El nombre del canal es requerido.")
        
        elif action == "invite":
            username = (request.POST.get("username") or "").strip()
            from django.contrib.auth.models import User as DjangoUser
            try:
                u = DjangoUser.objects.get(username=username)
                channel.participants.add(u)
                messages.success(request, _("%(username)s invitado al canal.") % {"username": username})
            except DjangoUser.DoesNotExist:
                messages.error(request, "Usuario no encontrado.")
            return redirect("project_chat_premium_channel", project_id=project.id, channel_id=channel.id)
        
        elif action == "delete_channel":
            if channel.is_default:
                messages.error(request, "No puedes eliminar el canal por defecto.")
            else:
                channel_name = channel.name
                channel.delete()
                messages.success(request, f"Canal '{channel_name}' eliminado.")
            return redirect("project_chat_premium", project_id=project.id)
    
    # Get messages for the active channel (for initial load)
    messages_list = channel.messages.select_related("user").order_by("-created_at")[:50]
    messages_list = list(reversed(messages_list))  # Show oldest first
    
    # Get team members for invite functionality
    team_members = []
    if request.user.is_staff:
        from django.contrib.auth.models import User as DjangoUser
        team_members = DjangoUser.objects.filter(is_active=True).exclude(
            id__in=channel.participants.values_list('id', flat=True)
        )
    
    # Prepare channel data for JavaScript
    channels_data = []
    for ch in channels:
        unread_count = ch.messages.exclude(read_by=request.user).count()
        last_msg = ch.messages.order_by("-created_at").first()
        channels_data.append({
            'id': ch.id,
            'name': ch.name,
            'type': ch.channel_type,
            'is_default': ch.is_default,
            'unread': unread_count,
            'last_message': last_msg.message[:50] if last_msg else '',
            'last_time': last_msg.created_at.isoformat() if last_msg else '',
        })
    
    import json
    return render(
        request,
        "core/project_chat_premium.html",
        {
            "project": project,
            "channel": channel,
            "channels": channels,
            "channels_json": json.dumps(channels_data),
            "messages": messages_list,
            "team_members": team_members,
            "current_user_id": request.user.id,
        },
    )


@login_required
def agregar_comentario(request, project_id):
    """
    Permite a clientes y staff agregar comentarios con imágenes.
    Útil para comunicación continua y documentación visual.
    """
    project = get_object_or_404(Project, id=project_id)

    # Verificar acceso
    profile = getattr(request.user, "profile", None)
    from core.models import ClientProjectAccess

    has_access = ClientProjectAccess.objects.filter(user=request.user, project=project).exists()
    if profile and profile.role == "client":
        if not (has_access or project.client == request.user.username):
            messages.error(request, "No tienes acceso a este proyecto.")
            return redirect("dashboard_client")
    elif not request.user.is_staff and not has_access:
        messages.error(request, "Acceso denegado.")
        return redirect("dashboard")

    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        image = request.FILES.get("image")

        if not text and not image:
            messages.error(request, "Debes agregar texto o imagen.")
            return redirect("client_project_view", project_id=project_id)

        Comment.objects.create(
            project=project, user=request.user, text=text or "Imagen adjunta", image=image
        )

        messages.success(request, "Comentario agregado exitosamente.")
        return redirect("client_project_view", project_id=project_id)

    return render(request, "core/agregar_comentario.html", {"project": project})


# --- CHANGE ORDER ---
@login_required
def changeorder_detail_view(request, changeorder_id):
    changeorder = get_object_or_404(ChangeOrder, id=changeorder_id)

    # Compute T&M preview if applicable
    tm_preview = None
    if changeorder.pricing_type == "T_AND_M":
        from core.services.financial_service import ChangeOrderService

        tm_preview = ChangeOrderService.get_billable_amount(changeorder)

    return render(
        request,
        "core/changeorder_detail_standalone.html",
        {"changeorder": changeorder, "tm_preview": tm_preview},
    )


@login_required
def changeorder_billing_history_view(request, changeorder_id):
    """
    Billing history report for a Change Order.
    Shows all InvoiceLines with breakdown of labor vs materials.
    Admin/PM only.
    """
    changeorder = get_object_or_404(ChangeOrder, id=changeorder_id)

    # Get all invoice lines related to this CO through TimeEntry or Expense
    from django.db.models import Q

    from core.models import InvoiceLine

    invoice_lines = (
        InvoiceLine.objects.filter(
            Q(time_entry__change_order=changeorder) | Q(expense__change_order=changeorder)
        )
        .select_related("invoice")
        .distinct()
        .order_by("-invoice__date_issued", "id")
    )

    # Separate labor and material lines
    labor_lines = []
    material_lines = []

    for line in invoice_lines:
        # Get related time entries and expenses
        time_entries = []
        expenses = []

        if line.time_entry and line.time_entry.change_order == changeorder:
            time_entries = [line.time_entry]

        if line.expense and line.expense.change_order == changeorder:
            expenses = [line.expense]

        line_data = {
            "invoice_line": line,
            "time_entries": time_entries,
            "expenses": expenses,
        }

        # Check if it's labor or materials based on description or related entries
        if (
            time_entries
            or "labor" in line.description.lower()
            or "mano de obra" in line.description.lower()
        ):
            labor_lines.append(line_data)
        else:
            material_lines.append(line_data)

    # Calculate totals
    total_labor = sum(line_item["invoice_line"].amount for line_item in labor_lines)
    total_materials = sum(line_item["invoice_line"].amount for line_item in material_lines)
    grand_total = total_labor + total_materials

    context = {
        "changeorder": changeorder,
        "labor_lines": labor_lines,
        "material_lines": material_lines,
        "total_labor": total_labor,
        "total_materials": total_materials,
        "grand_total": grand_total,
    }

    return render(request, "core/changeorder_billing_history.html", context)


@login_required
def changeorder_cost_breakdown_view(request, changeorder_id):
    """
    Vista estilo factura para mostrar el desglose de costos de un Change Order.
    Separa Materiales vs Mano de Obra para fácil envío al cliente.
    """
    from decimal import Decimal

    from django.db.models import Sum

    changeorder = get_object_or_404(ChangeOrder, id=changeorder_id)

    # Get all expenses associated with this CO, separated by category
    material_expenses = changeorder.expenses.filter(
        category__in=["MATERIALES", "ALMACÉN"]
    ).order_by("date")
    other_expenses = changeorder.expenses.exclude(
        category__in=["MATERIALES", "ALMACÉN", "MANO_OBRA"]
    ).order_by("date")

    # Get all time entries for labor costs
    time_entries = changeorder.time_entries.select_related("employee").order_by("date")

    # Calculate totals
    total_materials = material_expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    total_other_expenses = other_expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    # Labor cost from TimeEntries
    labor_cost = sum(entry.labor_cost for entry in time_entries)
    total_hours = sum((entry.hours_worked or Decimal("0")) for entry in time_entries)

    # Apply markup if CO has T&M pricing
    material_markup_pct = Decimal("0")
    billing_rate = Decimal("50.00")  # Default rate

    if hasattr(changeorder, "pricing_type") and changeorder.pricing_type == "T_AND_M":
        material_markup_pct = changeorder.material_markup_percent or Decimal("0")
        billing_rate = changeorder.get_effective_billing_rate() if hasattr(changeorder, "get_effective_billing_rate") else Decimal("50.00")

    # Calculate billable amounts with markup
    material_with_markup = total_materials * (1 + material_markup_pct / Decimal("100"))
    labor_billable = total_hours * billing_rate

    # Grand totals
    subtotal_cost = total_materials + labor_cost + total_other_expenses
    subtotal_billable = material_with_markup + labor_billable + total_other_expenses
    profit_margin = subtotal_billable - subtotal_cost if subtotal_billable > 0 else Decimal("0.00")

    context = {
        "changeorder": changeorder,
        "material_expenses": material_expenses,
        "other_expenses": other_expenses,
        "time_entries": time_entries,
        "total_materials": total_materials,
        "total_other_expenses": total_other_expenses,
        "labor_cost": labor_cost,
        "total_hours": total_hours,
        "material_markup_pct": material_markup_pct,
        "billing_rate": billing_rate,
        "material_with_markup": material_with_markup,
        "labor_billable": labor_billable,
        "subtotal_cost": subtotal_cost,
        "subtotal_billable": subtotal_billable,
        "profit_margin": profit_margin,
    }

    return render(request, "core/changeorder_cost_breakdown.html", context)


def changeorder_customer_signature_view(request, changeorder_id, token=None):
    """Vista pública para capturar firma de cliente en Change Orders.
    Mejoras:
    - Validación de token firmado (HMAC) con expiración.
    - Acceso opcional sin token (compatibilidad con flujo interno).
    - Manejo explícito de errores de token (expirado / manipulado).
    """
    changeorder = get_object_or_404(ChangeOrder, id=changeorder_id)

    # --- Calculate T&M total if applicable ---
    tm_breakdown = None
    if changeorder.pricing_type == 'T_AND_M':
        from core.services.financial_service import ChangeOrderService
        tm_breakdown = ChangeOrderService.get_billable_amount(changeorder)

    # --- Token validation (solo si se proporciona en la URL) ---
    if token is not None:
        try:
            payload = signing.loads(token, max_age=60 * 60 * 24 * 7)  # 7 días
            if payload.get("co") != changeorder.id:
                return HttpResponseForbidden("Token no coincide con este Change Order.")
        except signing.SignatureExpired:
            return HttpResponseForbidden("El enlace de firma ha expirado. Solicite uno nuevo.")
        except signing.BadSignature:
            return HttpResponseForbidden("Token inválido o manipulado.")

    # Si ya está firmado mostrar pantalla correspondiente
    if changeorder.signature_image:
        return render(
            request, "core/changeorder_signature_already_signed.html", {
                "changeorder": changeorder,
                "tm_breakdown": tm_breakdown,
            }
        )

    if request.method == "POST":
        import base64
        import uuid

        from django.core.files.base import ContentFile
        from django.utils import timezone

        signature_data = request.POST.get("signature_data")
        signer_name = request.POST.get("signer_name", "").strip()

        if not signature_data:
            return render(
                request,
                "core/changeorder_signature_form.html",
                {
                    "changeorder": changeorder,
                    "tm_breakdown": tm_breakdown,
                    "error": "Por favor, dibuje su firma antes de continuar.",
                },
            )
        if not signer_name:
            return render(
                request,
                "core/changeorder_signature_form.html",
                {
                    "changeorder": changeorder,
                    "tm_breakdown": tm_breakdown,
                    "error": "Por favor, ingrese su nombre completo.",
                },
            )

        try:
            format_str, imgstr = signature_data.split(";base64,")
            ext = format_str.split("/")[-1]
            signature_file = ContentFile(
                base64.b64decode(imgstr),
                name=f"signature_co_{changeorder.id}_{uuid.uuid4().hex[:8]}.{ext}",
            )

            changeorder.signature_image = signature_file
            changeorder.signed_by = signer_name
            changeorder.signed_at = timezone.now()
            changeorder.status = "approved"
            # Audit trail capture (Paso 4)
            forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
            ip = (
                forwarded_for.split(",")[0].strip()
                if forwarded_for
                else request.META.get("REMOTE_ADDR")
            )
            changeorder.signed_ip = ip
            changeorder.signed_user_agent = request.META.get("HTTP_USER_AGENT", "")[:512]
            changeorder.save(
                update_fields=[
                    "signature_image",
                    "signed_by",
                    "signed_at",
                    "status",
                    "signed_ip",
                    "signed_user_agent",
                ]
            )

            # --- Email notifications (Paso 2) ---
            from django.conf import settings
            from django.core.mail import send_mail

            customer_email = request.POST.get("customer_email", "").strip()
            internal_recipients = list(
                User.objects.filter(is_staff=True, is_active=True).values_list("email", flat=True)
            )
            # Filtrar emails vacíos
            internal_recipients = [e for e in internal_recipients if e]

            subject = f"CO #{changeorder.id} signed by client"
            body_lines = [
                f"Change Order #{changeorder.id} has been signed.",
                f"Project: {changeorder.project.name if changeorder.project else '-'}",
                f"Description: {changeorder.description[:180]}"
                + ("..." if len(changeorder.description) > 180 else ""),
                f"Pricing Type: {changeorder.pricing_type}",
                f"Signed by: {signer_name}",
                f"Date/Time: {timezone.localtime(changeorder.signed_at).strftime('%Y-%m-%d %H:%M:%S')}",
            ]

            if changeorder.pricing_type == "T_AND_M":
                body_lines.append(
                    f"Labor Rate: ${changeorder.get_effective_billing_rate():.2f} | Material Markup: {changeorder.material_markup_pct}%"
                )
            else:
                body_lines.append(f"Approved Fixed Amount: ${changeorder.amount:.2f}")

            body_lines.append("---")
            body_lines.append("This is an automated email. Do not reply.")
            message_body = "\n".join(body_lines)

            # Send to internal staff
            if internal_recipients:
                with contextlib.suppress(Exception):
                    send_mail(
                        subject,
                        message_body,
                        getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@kibray.com"),
                        internal_recipients,
                        fail_silently=True,
                    )

            # Send confirmation to client if they provided email
            if customer_email:
                with contextlib.suppress(Exception):
                    send_mail(
                        f"Signature Confirmation CO #{changeorder.id}",
                        "Thank you for signing the Change Order. We have recorded your approval.",
                        getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@kibray.com"),
                        [customer_email],
                        fail_silently=True,
                    )

            # --- PDF Generation (Paso 3) - Using ReportLab ---
            try:
                from core.services.pdf_service import generate_signed_changeorder_pdf
                from django.core.files.base import ContentFile
                
                pdf_bytes = generate_signed_changeorder_pdf(changeorder)
                if pdf_bytes:
                    changeorder.signed_pdf = ContentFile(
                        pdf_bytes, name=f"co_{changeorder.id}_signed.pdf"
                    )
                    changeorder.save(update_fields=["signed_pdf"])
            except Exception as pdf_error:
                # Log but don't block flow
                import logging
                logging.getLogger(__name__).warning(f"CO PDF generation failed: {pdf_error}")

            # --- Auto-save PDF to Project Files (Paso 4) ---
            try:
                from core.services.document_storage_service import auto_save_changeorder_pdf
                auto_save_changeorder_pdf(changeorder, user=None, overwrite=True)
            except Exception as e:
                # Log but don't block flow
                import logging
                logging.getLogger(__name__).warning(f"Failed to auto-save CO PDF: {e}")

            # --- Generate download token for client ---
            from django.core import signing
            download_token = signing.dumps({"changeorder_id": changeorder.id})

            return render(
                request, "core/changeorder_signature_success.html", {
                    "changeorder": changeorder,
                    "tm_breakdown": tm_breakdown,
                    "download_token": download_token,
                }
            )
        except Exception as e:
            return render(
                request,
                "core/changeorder_signature_form.html",
                {
                    "changeorder": changeorder,
                    "tm_breakdown": tm_breakdown,
                    "error": f"Error al procesar la firma: {e}",
                },
            )

    return render(request, "core/changeorder_signature_form.html", {
        "changeorder": changeorder,
        "tm_breakdown": tm_breakdown,
    })


@login_required
def changeorder_create_view(request):
    if request.method == "POST":
        form = ChangeOrderForm(request.POST, request.FILES)
        if form.is_valid():
            co = form.save()
            # Handle photo uploads
            photos = request.FILES.getlist("photos")
            for idx, photo_file in enumerate(photos):
                description = request.POST.get(f"photo_description_{idx}", "")
                ChangeOrderPhoto.objects.create(
                    change_order=co, image=photo_file, description=description, order=idx
                )
            return redirect("changeorder_board")
    else:
        form = ChangeOrderForm()

    # Get approved colors from the project if project is selected
    approved_colors = []
    project_id = request.GET.get("project")
    if project_id:
        with contextlib.suppress(Exception):
            approved_colors = ColorSample.objects.filter(
                project_id=project_id, status="approved"
            ).order_by("code")

    return render(request, "core/changeorder_form_clean.html", {"form": form, "approved_colors": approved_colors})


@login_required
def changeorder_edit_view(request, co_id):
    """Editar un Change Order existente"""
    changeorder = get_object_or_404(ChangeOrder, id=co_id)
    if request.method == "POST":
        form = ChangeOrderForm(request.POST, request.FILES, instance=changeorder)
        if form.is_valid():
            co = form.save()
            # Handle new photo uploads
            photos = request.FILES.getlist("photos")
            for idx, photo_file in enumerate(photos):
                description = request.POST.get(f"photo_description_{idx}", "")
                ChangeOrderPhoto.objects.create(
                    change_order=co,
                    image=photo_file,
                    description=description,
                    order=co.photos.count() + idx,
                )
            return redirect("changeorder_board")
    else:
        form = ChangeOrderForm(instance=changeorder)

    # Get approved colors from the project
    approved_colors = ColorSample.objects.filter(
        project=changeorder.project, status="approved"
    ).order_by("code")

    return render(
        request,
        "core/changeorder_form_clean.html",
        {
            "form": form,
            "changeorder": changeorder,
            "is_edit": True,
            "approved_colors": approved_colors,
        },
    )


@login_required
def changeorder_delete_view(request, co_id):
    """Eliminar un Change Order"""
    changeorder = get_object_or_404(ChangeOrder, id=co_id)
    if request.method == "POST":
        changeorder.delete()
        return redirect("changeorder_board")
    return render(request, "core/changeorder_confirm_delete.html", {"changeorder": changeorder})


@login_required
def photo_editor_standalone_view(request):
    """Standalone photo editor that opens in new tab/window"""
    return render(request, "core/photo_editor_standalone.html")


@login_required
def get_approved_colors(request, project_id):
    """API endpoint to get approved colors for a project"""
    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        return JsonResponse({"error": "Access denied"}, status=403)
    
    colors = (
        ColorSample.objects.filter(project_id=project_id, status="approved")
        .values("id", "code", "name", "brand", "finish")
        .order_by("code")
    )

    return JsonResponse({"colors": list(colors)})

    # (Legacy annotation and delete endpoints removed; use DRF versions under /api/v1/changeorder-photo/)


def color_sample_client_signature_view(request, sample_id, token=None):
    """Public view to capture client signature on color samples.

    Token validation (HMAC) with 7-day expiration.
    Captures base64 signature, client name, and generates PDF.
    """
    color_sample = get_object_or_404(ColorSample, id=sample_id)

    # --- Token validation (only if provided in URL) ---
    if token is not None:
        try:
            payload = signing.loads(token, max_age=60 * 60 * 24 * 7)  # 7 days
            if payload.get("sample_id") != color_sample.id:
                return HttpResponseForbidden("Token does not match this color sample.")
        except signing.SignatureExpired:
            return HttpResponseForbidden("The signature link has expired. Please request a new one.")
        except signing.BadSignature:
            return HttpResponseForbidden("Invalid or tampered token.")

    # If already signed, show corresponding screen
    if color_sample.client_signature:
        return render(
            request,
            "core/color_sample_signature_already_signed.html",
            {"color_sample": color_sample},
        )

    if request.method == "POST":
        import base64
        import uuid

        from django.core.files.base import ContentFile
        from django.utils import timezone

        signature_data = request.POST.get("signature_data")
        signed_name = request.POST.get("signed_name", "").strip()

        if not signature_data:
            return render(
                request,
                "core/color_sample_signature_form.html",
                {
                    "color_sample": color_sample,
                    "error": "Please draw your signature before continuing.",
                },
            )
        if not signed_name:
            return render(
                request,
                "core/color_sample_signature_form.html",
                {"color_sample": color_sample, "error": "Please enter your full name."},
            )

        try:
            # --- Process base64 signature ---
            format_str, imgstr = signature_data.split(";base64,")
            ext = format_str.split("/")[-1]
            if ext not in ["png", "jpeg", "jpg"]:
                ext = "png"

            # Decode base64
            decoded_image = base64.b64decode(imgstr)

            # Create unique filename
            file_name = f"color_sample_{color_sample.id}_signature_{uuid.uuid4().hex}.{ext}"
            signature_file = ContentFile(decoded_image, name=file_name)

            # Get client IP
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            client_ip = (
                x_forwarded_for.split(",")[0]
                if x_forwarded_for
                else request.META.get("REMOTE_ADDR", "")
            )

            # --- Save signature using the new model fields ---
            color_sample.sign_by_client(signature_file, signed_name, client_ip)

            # --- Notify project PM ---
            try:
                project = color_sample.project
                if project:
                    pm_profile = Profile.objects.filter(
                        project=project, role="project_manager"
                    ).first()
                    if pm_profile and pm_profile.user.email:
                        subject = f"Color Sample #{color_sample.id} signed by client"
                        message_body = (
                            f"Color sample '{color_sample.name}' (Code: {color_sample.code}) "
                            f"has been signed by:\n\n"
                            f"Name: {signed_name}\n"
                            f"Date: {color_sample.client_signed_at.strftime('%m/%d/%Y %H:%M')}\n"
                            f"IP: {client_ip}\n\n"
                            f"Project: {project.name}\n"
                            f"Location: {color_sample.room_location or 'N/A'}\n\n"
                            f"This is an automated message. Do not reply."
                        )
                        with contextlib.suppress(Exception):
                            send_mail(
                                subject,
                                message_body,
                                getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@kibray.com"),
                                [pm_profile.user.email],
                                fail_silently=True,
                            )
            except Exception:
                pass

            # --- Generate PDF using ReportLab ---
            # Note: PDF is auto-saved to Project Files below, no need for inline generation here

            # --- Auto-save PDF to Project Files ---
            try:
                from core.services.document_storage_service import auto_save_colorsample_pdf
                auto_save_colorsample_pdf(color_sample, user=None, overwrite=True)
            except Exception as e:
                # Log but don't block flow
                import logging
                logging.getLogger(__name__).warning(f"Failed to auto-save ColorSample PDF: {e}")

            # --- Generate download token for client ---
            from django.core import signing
            download_token = signing.dumps({"sample_id": color_sample.id})

            return render(
                request,
                "core/color_sample_signature_success.html",
                {"color_sample": color_sample, "download_token": download_token},
            )
        except Exception as e:
            return render(
                request,
                "core/color_sample_signature_form.html",
                {"color_sample": color_sample, "error": f"Error processing the signature: {e}"},
            )

    return render(request, "core/color_sample_signature_form.html", {"color_sample": color_sample})


@login_required
def changeorder_board_view(request):
    qs = ChangeOrder.objects.select_related("project").order_by("-date_created")
    status = request.GET.get("status")
    project_id = request.GET.get("project")
    if status:
        qs = qs.filter(status=status)
    if project_id:
        with contextlib.suppress(TypeError, ValueError):
            qs = qs.filter(project_id=int(project_id))
    total_amount = qs.aggregate(total=Sum("amount"))["total"] or 0
    projects = Project.objects.order_by("name")
    return render(
        request,
        "core/changeorder_board.html",
        {
            "changeorders": qs,
            "filter_status": status or "",
            "filter_project": str(project_id) if project_id else "",
            "total_amount": total_amount,
            "projects": projects,
        },
    )


@login_required
def unassigned_timeentries_view(request):
    """Lista de TimeEntries sin change_order para asignación masiva por PM/admin."""
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"]:
        return redirect("dashboard")

    # Filtros
    project_id = request.GET.get("project")
    employee_id = request.GET.get("employee")
    date_from = request.GET.get("from")
    date_to = request.GET.get("to")

    qs = (
        TimeEntry.objects.filter(change_order__isnull=True)
        .select_related("employee", "project")
        .order_by("-date")
    )
    if project_id:
        qs = qs.filter(project_id=project_id)
    if employee_id:
        qs = qs.filter(employee_id=employee_id)
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)

    # Bulk assign
    if request.method == "POST":
        action = request.POST.get("action")
        selected_ids = request.POST.getlist("selected")
        co_id = request.POST.get("change_order_id")
        if action == "assign" and selected_ids and co_id:
            co = get_object_or_404(ChangeOrder, id=co_id)
            # Validar que todas las filas seleccionadas pertenezcan al proyecto del CO
            diff = (
                TimeEntry.objects.filter(id__in=selected_ids).exclude(project=co.project).exists()
            )
            if diff:
                messages.error(
                    request, "Selecciona registros del mismo proyecto que el CO elegido."
                )
                return redirect(request.get_full_path())
            updated = TimeEntry.objects.filter(
                id__in=selected_ids, change_order__isnull=True
            ).update(change_order=co)
            messages.success(
                request,
                _("%(count)s registros asignados al CO #%(co_id)s.")
                % {"count": updated, "co_id": co.id},
            )
            return redirect(request.get_full_path())
        elif action == "create_and_assign" and selected_ids:
            # Crear un nuevo CO rápido
            project_for_new = None
            # Intentar tomar el proyecto de la primera time entry válida
            first_te = (
                TimeEntry.objects.filter(id__in=selected_ids).select_related("project").first()
            )
            if first_te and first_te.project:
                project_for_new = first_te.project
            if not project_for_new:
                messages.error(
                    request,
                    "No se puede crear CO sin proyecto asociado en los registros seleccionados.",
                )
            else:
                # validar que todos pertenecen al mismo proyecto
                mixed = (
                    TimeEntry.objects.filter(id__in=selected_ids)
                    .exclude(project=project_for_new)
                    .exists()
                )
                if mixed:
                    messages.error(request, "Para crear CO, selecciona filas de un solo proyecto.")
                    return redirect(request.get_full_path())
                description = request.POST.get("new_co_description", "Trabajo adicional")
                amount = request.POST.get("new_co_amount") or "0"
                try:
                    amt = Decimal(amount)
                except Exception:
                    amt = Decimal("0")
                co = ChangeOrder.objects.create(
                    project=project_for_new, description=description, amount=amt, status="pending"
                )
                updated = TimeEntry.objects.filter(
                    id__in=selected_ids, change_order__isnull=True
                ).update(change_order=co)
                messages.success(
                    request,
                    _("CO #%(co_id)s creado y %(count)s registros asignados.")
                    % {"co_id": co.id, "count": updated},
                )
            return redirect(request.get_full_path())

    # Paginación ligera (tolerante a valores inválidos)
    try:
        page_size = int(request.GET.get("ps", 50))
    except (TypeError, ValueError):
        page_size = 50
    if page_size <= 0:
        page_size = 50
    if page_size > 500:
        page_size = 500
    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(request.GET.get("page"))

    projects = Project.objects.all().order_by("name")
    employees = Employee.objects.filter(is_active=True).order_by("last_name")
    change_orders = ChangeOrder.objects.filter(status__in=["pending", "approved", "sent"]).order_by(
        "-date_created"
    )
    if project_id:
        change_orders = change_orders.filter(project_id=project_id)
    change_orders = change_orders[:200]

    return render(
        request,
        "core/unassigned_timeentries.html",
        {
            "page_obj": page_obj,
            "projects": projects,
            "employees": employees,
            "change_orders": change_orders,
            "filters": {
                "project_id": project_id,
                "employee_id": employee_id,
                "date_from": date_from,
                "date_to": date_to,
                "page_size": page_size,
            },
            "page_sizes": [25, 50, 100],
        },
    )


@login_required
def payroll_summary_view(request):
    """Legacy view - redirects to new payroll_weekly_review"""
    return redirect("payroll_weekly_review")


# --- INVOICES ---


@login_required
@staff_member_required
def invoice_builder_view(request, project_id):
    """
    SMART INVOICE CREATION
    - Pre-load approved Estimate items
    - Show unbilled ChangeOrders (approved/sent status, not yet billed)
    - Show unbilled TimeEntries (T&M work)
    - Generate InvoiceLines automatically
    """
    project = get_object_or_404(Project, pk=project_id)

    # Get latest approved estimate
    latest_estimate = project.estimates.filter(approved=True).order_by("-version").first()

    # Progressive billing: compute already billed percentage per estimate line
    estimate_lines_data = []
    if latest_estimate:
        from django.db.models import Sum as DJSum

        from core.models import InvoiceLineEstimate

        # Prefetch sums for efficiency
        billed_map = (
            InvoiceLineEstimate.objects.filter(estimate_line__estimate=latest_estimate)
            .values("estimate_line_id")
            .annotate(total_pct=DJSum("percentage_billed"))
        )
        billed_lookup = {row["estimate_line_id"]: (row["total_pct"] or 0) for row in billed_map}
        for line in latest_estimate.lines.select_related("cost_code").all():
            already = billed_lookup.get(line.id, 0)
            remaining = max(0, 100 - (already or 0))
            estimate_lines_data.append(
                {
                    "id": line.id,
                    "code": line.cost_code.code,
                    "description": line.description,
                    "direct_cost": line.direct_cost(),
                    "already_pct": float(already or 0),
                    "remaining_pct": float(remaining),
                }
            )

    # Unbilled ChangeOrders (ANY status except already billed/paid)
    # Shows ALL COs that haven't been invoiced yet, regardless of approval status
    unbilled_cos = (
        project.change_orders.exclude(status__in=["billed", "paid"])
        .exclude(invoices__isnull=False)
        .distinct()
    )

    # Unbilled TimeEntries (not yet linked to any invoice)
    unbilled_time = (
        TimeEntry.objects.filter(project=project, invoiceline__isnull=True)
        .select_related("employee", "change_order")
        .order_by("date")
    )

    # Group unbilled time by change_order (if any)
    time_by_co = {}
    time_general = []
    tm_hourly_rate = Decimal("50.00")  # Your rate: $50/hour

    for te in unbilled_time:
        if te.change_order:
            if te.change_order.id not in time_by_co:
                time_by_co[te.change_order.id] = {
                    "co": te.change_order,
                    "entries": [],
                    "total_hours": Decimal("0"),
                    "total_cost": Decimal("0"),
                    "billable_amount": Decimal("0"),
                }
            time_by_co[te.change_order.id]["entries"].append(te)
            time_by_co[te.change_order.id]["total_hours"] += te.hours_worked or 0
            time_by_co[te.change_order.id]["total_cost"] += te.labor_cost
        else:
            time_general.append(te)

    # Calculate billable amounts for time by CO
    for co_data in time_by_co.values():
        co_data["billable_amount"] = co_data["total_hours"] * tm_hourly_rate

    # Calculate totals for general T&M
    general_hours = sum((te.hours_worked or 0) for te in time_general)
    general_cost = sum(te.labor_cost for te in time_general)

    if request.method == "POST":
        # User selects what to include
        include_estimate = request.POST.get("include_estimate") == "on"
        selected_co_ids = request.POST.getlist("change_orders")
        include_time_general = request.POST.get("include_time_general") == "on"
        selected_time_co_ids = request.POST.getlist("time_cos")

        # Get due date
        due_date_str = request.POST.get("due_date")
        due_date = timezone.now().date() + timedelta(days=30)  # Default Net 30
        if due_date_str:
            with contextlib.suppress(Exception):
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()

        # Create Invoice
        invoice = Invoice.objects.create(
            project=project,
            date_issued=timezone.now().date(),
            due_date=due_date,
            status="DRAFT",
        )

        lines_created = 0

        # Add Estimate base contract (full) or progressive portions
        if include_estimate and latest_estimate:
            # Calculate total from EstimateLines with markup
            direct_cost = sum(line.direct_cost() for line in latest_estimate.lines.all())
            material_markup = (
                direct_cost * (latest_estimate.markup_material / 100)
                if latest_estimate.markup_material
                else 0
            )
            labor_markup = (
                direct_cost * (latest_estimate.markup_labor / 100)
                if latest_estimate.markup_labor
                else 0
            )
            overhead = (
                direct_cost * (latest_estimate.overhead_pct / 100)
                if latest_estimate.overhead_pct
                else 0
            )
            profit = (
                direct_cost * (latest_estimate.target_profit_pct / 100)
                if latest_estimate.target_profit_pct
                else 0
            )
            total = direct_cost + material_markup + labor_markup + overhead + profit

            # Check if user provided progressive percentages per estimate line
            progressive_used = False
            from core.models import InvoiceLineEstimate

            for eline in latest_estimate.lines.all():
                field_name = f"prog_pct_{eline.id}"
                raw = request.POST.get(field_name)
                if not raw:
                    continue
                try:
                    pct = Decimal(raw)
                except Exception:
                    pct = Decimal("0")
                if pct <= 0:
                    continue
                # Respect remaining percentage
                # Compute already billed
                already_pct = InvoiceLineEstimate.objects.filter(estimate_line=eline).aggregate(
                    total=DJSum("percentage_billed")
                )["total"] or Decimal("0")
                remaining_pct = max(Decimal("0"), Decimal("100") - already_pct)
                if pct > remaining_pct:
                    pct = remaining_pct
                if pct <= 0:
                    continue
                progressive_used = True
                # Compute amount using direct cost proportionally (note: markups are handled in base total; here we bill direct portion)
                amount = (eline.direct_cost() or Decimal("0")) * (pct / Decimal("100"))
                il = InvoiceLine.objects.create(
                    invoice=invoice,
                    description=f"Progreso Estimado: {eline.cost_code.code} - {eline.description[:60]} ({pct}%)",
                    amount=amount,
                )
                InvoiceLineEstimate.objects.create(
                    invoice_line=il,
                    estimate_line=eline,
                    percentage_billed=pct,
                    amount=amount,
                )
                lines_created += 1

            # If no progressive input was supplied, add full base contract one-line
            if not progressive_used:
                InvoiceLine.objects.create(
                    invoice=invoice,
                    description=f"Contrato Base - Estimado v{latest_estimate.version}",
                    amount=total,
                )
                lines_created += 1

        # Add ChangeOrders
        # Change Orders (Fixed or T&M)
        from core.services.financial_service import ChangeOrderService

        for co_id in selected_co_ids:
            try:
                co = ChangeOrder.objects.get(pk=int(co_id))
                if co.pricing_type == "FIXED":
                    InvoiceLine.objects.create(
                        invoice=invoice,
                        description=f"CO #{co.id} (Fijo): {co.description[:90]}",
                        amount=co.amount,
                    )
                    lines_created += 1
                else:
                    # T&M breakdown
                    breakdown = ChangeOrderService.get_billable_amount(co)
                    # Labor line
                    labor_line = InvoiceLine.objects.create(
                        invoice=invoice,
                        description=(
                            f"Mano de Obra CO #{co.id}: {breakdown['labor_hours']} hrs @ ${breakdown['billing_rate']}/hr"
                        ),
                        amount=breakdown["labor_total"],
                    )
                    lines_created += 1
                    # Materials line (only if there is material cost)
                    if breakdown["material_total"] > 0:
                        material_line = InvoiceLine.objects.create(
                            invoice=invoice,
                            description=(
                                f"Materiales CO #{co.id}: costo ${breakdown['raw_material_cost']} + {breakdown['material_markup_pct']}%"
                            ),
                            amount=breakdown["material_total"],
                        )
                        lines_created += 1
                    else:
                        material_line = None
                    # Mark involved entries/expenses as billed
                    for te in breakdown["time_entries"]:
                        te.invoice_line = labor_line
                        te.save(update_fields=["invoice_line"])
                    for ex in breakdown["expenses"]:
                        if material_line:
                            ex.invoice_line = material_line
                            ex.save(update_fields=["invoice_line"])
                # Mark CO billed
                co.status = "billed"
                co.save(update_fields=["status"])
                invoice.change_orders.add(co)
            except (ChangeOrder.DoesNotExist, ValueError):
                continue

        # Add Time & Materials (general - not linked to COs)
        if include_time_general and time_general:
            total_billed = general_hours * tm_hourly_rate
            InvoiceLine.objects.create(
                invoice=invoice,
                description=f"Tiempo & Materiales - {general_hours} horas @ ${tm_hourly_rate}/hr",
                amount=total_billed,
            )
            # Link time entries to this line (optional - for tracking)
            # We'll just mark them as billed for now
            lines_created += 1

        # Add Time linked to specific COs
        for co_id_str in selected_time_co_ids:
            try:
                co_id = int(co_id_str)
                if co_id in time_by_co:
                    co_data = time_by_co[co_id]
                    co = co_data["co"]
                    hours = co_data["total_hours"]
                    total_billed = hours * tm_hourly_rate

                    InvoiceLine.objects.create(
                        invoice=invoice,
                        description=f"T&M para CO #{co.id}: {co.description[:80]} - {hours} hrs @ ${tm_hourly_rate}/hr",
                        amount=total_billed,
                    )
                    lines_created += 1
            except (ValueError, KeyError):
                pass

        # Calculate total
        invoice.total_amount = sum(line.amount for line in invoice.lines.all())
        invoice.save()

        messages.success(
            request,
            f"✅ Factura {invoice.invoice_number} creada con {lines_created} líneas. Total: ${invoice.total_amount:,.2f}",
        )
        return redirect("invoice_detail", pk=invoice.id)

    # Calculate preview totals
    estimate_total = Decimal("0")
    if latest_estimate:
        direct = sum(line.direct_cost() for line in latest_estimate.lines.all())
        estimate_total = direct * (
            1
            + (
                latest_estimate.markup_material
                + latest_estimate.markup_labor
                + latest_estimate.overhead_pct
                + latest_estimate.target_profit_pct
            )
            / 100
        )

    co_total = sum(co.amount for co in unbilled_cos)
    time_general_total = general_hours * tm_hourly_rate
    time_co_total = sum(data["total_hours"] * tm_hourly_rate for data in time_by_co.values())

    context = {
        "project": project,
        "estimate": latest_estimate,
        "estimate_lines_data": estimate_lines_data,
        "estimate_total": estimate_total,
        "unbilled_cos": unbilled_cos,
        "co_total": co_total,
        "time_general": time_general,
        "general_hours": general_hours,
        "general_cost": general_cost,
        "time_general_total": time_general_total,
        "time_by_co": time_by_co.values(),
        "time_co_total": time_co_total,
        "tm_rate": tm_hourly_rate,
        "grand_total": estimate_total + co_total + time_general_total + time_co_total,
    }
    return render(request, "core/invoice_builder.html", context)


@login_required
def invoice_list(request):
    """
    Invoice list view with filtering by status and project.
    """
    invoices = (
        Invoice.objects.select_related("project")
        .prefetch_related("lines", "payments")
        .order_by("-date_issued", "-id")
    )
    
    # Apply filters
    status_filter = request.GET.get("status", "")
    project_filter = request.GET.get("project", "")
    
    if status_filter:
        if status_filter == "pending":
            # Pending = not PAID and not CANCELLED
            invoices = invoices.exclude(status__in=["PAID", "CANCELLED"])
        elif status_filter == "paid":
            invoices = invoices.filter(status="PAID")
        elif status_filter == "overdue":
            from datetime import date
            invoices = invoices.filter(
                due_date__lt=date.today()
            ).exclude(status__in=["PAID", "CANCELLED"])
        else:
            invoices = invoices.filter(status=status_filter)
    
    if project_filter:
        invoices = invoices.filter(project_id=project_filter)
    
    # Get summary stats
    from django.db.models import Sum, Count
    stats = {
        "total_count": Invoice.objects.count(),
        "draft_count": Invoice.objects.filter(status="DRAFT").count(),
        "pending_count": Invoice.objects.exclude(status__in=["PAID", "CANCELLED", "DRAFT"]).count(),
        "paid_count": Invoice.objects.filter(status="PAID").count(),
        "total_pending_amount": Invoice.objects.exclude(
            status__in=["PAID", "CANCELLED"]
        ).aggregate(total=Sum("total_amount"))["total"] or 0,
        "total_paid_amount": Invoice.objects.filter(status="PAID").aggregate(
            total=Sum("total_amount")
        )["total"] or 0,
    }
    
    projects = Project.objects.filter(is_archived=False).order_by("name")
    
    # Status choices for filter dropdown
    status_choices = Invoice.STATUS_CHOICES
    
    return render(request, "core/invoice_list.html", {
        "invoices": invoices,
        "projects": projects,
        "status_filter": status_filter,
        "project_filter": project_filter,
        "status_choices": status_choices,
        "stats": stats,
    })


@login_required
def invoice_detail(request, pk):
    """
    Modern Invoice Detail View with full financial integration.
    Shows invoice details, payment history, related COs, and actions.
    """
    invoice = get_object_or_404(
        Invoice.objects.select_related("project")
        .prefetch_related("lines", "payments", "change_orders"),
        pk=pk
    )
    
    # Company Info (Kibray Paint & Stain LLC)
    company = {
        "name": "Kibray Paint & Stain LLC",
        "address": "P.O. Box 25881",
        "city_state_zip": "Silverthorne, CO 80497",
        "phone": "(970) 333-4872",
        "email": "jduran@kibraypainting.net",
        "website": "kibraypainting.net",
        "logo_path": "images/kibray-logo.png",
    }
    
    # Payment history
    payments = invoice.payments.all().order_by("-payment_date")
    
    # Related Change Orders
    change_orders = invoice.change_orders.all()
    
    # Calculate days until due / overdue
    days_until_due = None
    is_overdue = False
    if invoice.due_date:
        from datetime import date
        today = date.today()
        days_until_due = (invoice.due_date - today).days
        is_overdue = days_until_due < 0
    
    # Status color mapping for badges
    status_colors = {
        "DRAFT": "secondary",
        "SENT": "primary",
        "VIEWED": "info",
        "APPROVED": "success",
        "PARTIAL": "warning",
        "PAID": "success",
        "OVERDUE": "danger",
        "CANCELLED": "dark",
    }
    status_color = status_colors.get(invoice.status, "secondary")
    
    context = {
        "invoice": invoice,
        "company": company,
        "payments": payments,
        "change_orders": change_orders,
        "days_until_due": days_until_due,
        "is_overdue": is_overdue,
        "status_color": status_color,
    }
    return render(request, "core/invoice_detail.html", context)


@login_required
def invoice_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    template = get_template("core/invoice_pdf.html")
    context = {
        "invoice": invoice,
        "user": request.user,
        "now": timezone.now(),  # <-- reemplazo
        "logo_url": request.build_absolute_uri("/static/kibray-logo.png"),
    }
    html = template.render(context)
    if pisa:
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        if not pdf.err:
            return HttpResponse(result.getvalue(), content_type="application/pdf")
    fallback_bytes = _generate_basic_pdf_from_html(html)
    return HttpResponse(fallback_bytes, content_type="application/pdf")


@login_required
def changeorders_ajax(request):
    project_id = request.GET.get("project_id")
    status_filter = request.GET.get("status", "all")
    
    qs = ChangeOrder.objects.filter(project_id=project_id)
    
    # Filter by status if requested
    # "active" = COs where work can be tracked (excludes only 'paid')
    if status_filter == "active":
        qs = qs.filter(status__in=["draft", "pending", "approved", "sent", "billed"])
    elif status_filter != "all":
        qs = qs.filter(status=status_filter)
    
    qs = qs.order_by("-date_created")
    
    data = []
    for co in qs:
        pricing_label = "T&M" if co.pricing_type == "T_AND_M" else f"${co.amount}"
        data.append({
            "id": co.id,
            "title": co.title or f"CO #{co.id}",
            "description": co.description or "",
            "amount": float(co.amount),
            "pricing_type": co.pricing_type,
            "pricing_label": pricing_label,
            "status": co.status,
        })
    
    return JsonResponse({"change_orders": data})


@login_required
def changeorder_lines_ajax(request):
    ids = request.GET.getlist("ids[]")
    qs = ChangeOrder.objects.filter(id__in=ids)
    lines = [{"description": co.description, "amount": float(co.amount)} for co in qs]
    return JsonResponse({"lines": lines})


@login_required
def invoice_payment_dashboard(request):
    """
    Dashboard showing SENT invoices awaiting payment.
    Allows quick payment recording with check/transfer details.
    """
    # Show invoices that are SENT, VIEWED, APPROVED, PARTIAL, or OVERDUE (not DRAFT, PAID, CANCELLED)
    pending_invoices = (
        Invoice.objects.filter(status__in=["SENT", "VIEWED", "APPROVED", "PARTIAL", "OVERDUE"])
        .select_related("project")
        .prefetch_related("lines", "payments")
        .order_by("-date_issued")
    )

    recently_paid = (
        Invoice.objects.filter(status="PAID").select_related("project").order_by("-paid_date")[:10]
    )

    # Calculate stats for the dashboard
    overdue_count = pending_invoices.filter(status="OVERDUE").count()
    partial_count = pending_invoices.filter(status="PARTIAL").count()

    context = {
        "pending_invoices": pending_invoices,
        "recently_paid": recently_paid,
        "overdue_count": overdue_count,
        "partial_count": partial_count,
    }
    return render(request, "core/invoice_payment_dashboard.html", context)


@login_required
@transaction.atomic
def record_invoice_payment(request, invoice_id):
    """
    Quick payment recording form.
    Creates InvoicePayment, updates Invoice.amount_paid, triggers status update.
    """
    invoice = get_object_or_404(Invoice, pk=invoice_id)

    if request.method == "POST":
        amount = request.POST.get("amount")
        payment_date = request.POST.get("payment_date")
        payment_method = request.POST.get("payment_method", "CHECK")
        reference = request.POST.get("reference", "")
        notes = request.POST.get("notes", "")

        try:
            amount_decimal = Decimal(amount)

            # Create payment record (this auto-updates invoice via model save)
            from core.models import InvoicePayment

            InvoicePayment.objects.create(
                invoice=invoice,
                amount=amount_decimal,
                payment_date=payment_date,
                payment_method=payment_method,
                reference=reference,
                notes=notes,
                recorded_by=request.user,
            )

            messages.success(
                request,
                f"✅ Pago de ${amount_decimal:,.2f} registrado. Status: {invoice.get_status_display()}",
            )
            return redirect("invoice_payment_dashboard")

        except (ValueError, ValidationError) as e:
            messages.error(request, _("Error: %(error)s") % {"error": e})
            return redirect("invoice_detail", pk=invoice.id)

    # GET: show form
    context = {
        "invoice": invoice,
    }
    return render(request, "core/record_payment_form.html", context)


@login_required
@transaction.atomic
def invoice_mark_sent(request, invoice_id):
    """Mark invoice as SENT and record sent_date and sent_by."""
    invoice = get_object_or_404(Invoice, pk=invoice_id)

    if invoice.status == "DRAFT":
        invoice.status = "SENT"
        invoice.sent_date = timezone.now()
        invoice.sent_by = request.user
        invoice.save()
        
        # --- Auto-save PDF to Project Files ---
        try:
            from core.services.document_storage_service import auto_save_invoice_pdf
            auto_save_invoice_pdf(invoice, user=request.user, overwrite=True)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to auto-save Invoice PDF: {e}")
        
        messages.success(
            request,
            _("✅ Factura %(invoice_number)s marcada como ENVIADA.")
            % {"invoice_number": invoice.invoice_number},
        )
    else:
        messages.warning(
            request,
            _("La factura ya tiene status: %(status)s") % {"status": invoice.get_status_display()},
        )

    return redirect("invoice_detail", pk=invoice.id)


@login_required
@transaction.atomic
def invoice_mark_approved(request, invoice_id):
    """Mark invoice as APPROVED by client."""
    invoice = get_object_or_404(Invoice, pk=invoice_id)

    if invoice.status in ["DRAFT", "SENT", "VIEWED"]:
        invoice.status = "APPROVED"
        invoice.approved_date = timezone.now()
        invoice.save()
        messages.success(
            request,
            _("✅ Factura %(invoice_number)s marcada como APROBADA.")
            % {"invoice_number": invoice.invoice_number},
        )
    else:
        messages.warning(
            request,
            _("La factura ya tiene status: %(status)s") % {"status": invoice.get_status_display()},
        )

    return redirect("invoice_detail", pk=invoice.id)


@login_required
@require_POST
@transaction.atomic
def invoice_delete(request, invoice_id):
    """
    Delete an invoice. Only allowed for DRAFT or CANCELLED invoices.
    """
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    
    # Only allow deletion of DRAFT or CANCELLED invoices
    if invoice.status not in ["DRAFT", "CANCELLED"]:
        messages.error(
            request,
            _("⚠️ Solo se pueden eliminar facturas en estado BORRADOR o CANCELADA. "
              "Estado actual: %(status)s") % {"status": invoice.get_status_display()},
        )
        return redirect("invoice_list")
    
    # Check if there are payments
    if invoice.payments.exists():
        messages.error(
            request,
            _("⚠️ No se puede eliminar la factura porque tiene pagos registrados."),
        )
        return redirect("invoice_detail", pk=invoice.id)
    
    invoice_number = invoice.invoice_number
    project_name = invoice.project.name
    
    # Delete related lines first
    invoice.lines.all().delete()
    
    # Delete the invoice
    invoice.delete()
    
    messages.success(
        request,
        _("✅ Factura %(invoice_number)s del proyecto %(project)s eliminada correctamente.")
        % {"invoice_number": invoice_number, "project": project_name},
    )
    
    return redirect("invoice_list")


@login_required
@require_POST
@transaction.atomic
def invoice_cancel(request, invoice_id):
    """
    Cancel an invoice. Changes status to CANCELLED.
    """
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    
    if invoice.status == "PAID":
        messages.error(
            request,
            _("⚠️ No se puede cancelar una factura que ya está PAGADA."),
        )
        return redirect("invoice_detail", pk=invoice.id)
    
    if invoice.status == "CANCELLED":
        messages.warning(
            request,
            _("La factura ya está cancelada."),
        )
        return redirect("invoice_detail", pk=invoice.id)
    
    invoice.status = "CANCELLED"
    invoice.save()
    
    messages.success(
        request,
        _("✅ Factura %(invoice_number)s cancelada correctamente.")
        % {"invoice_number": invoice.invoice_number},
    )
    
    return redirect("invoice_detail", pk=invoice.id)


@login_required
@staff_member_required
def project_profit_dashboard(request, project_id):
    """
    Project Profit Dashboard: Real-time visibility of margins and financial health.
    Shows: Budgeted Revenue, Actual Costs, Billed Amount, Collected, Profit Margin.
    """
    project = get_object_or_404(Project, pk=project_id)

    # 1. BASE BUDGET FROM BUDGET LINES
    # Sum all baseline_amount from BudgetLine (the actual project budget)
    budget_lines_total = project.budget_lines.aggregate(
        total=Sum("baseline_amount")
    )["total"] or Decimal("0")

    # 2. ESTIMATE REVENUE (if using Estimates with markup - alternative method)
    estimate_revenue = Decimal("0")
    latest_estimate = project.estimates.filter(approved=True).order_by("-version").first()
    if latest_estimate:
        # Calculate with markup
        direct = sum(line.direct_cost() for line in latest_estimate.lines.all())
        markup_total = (
            latest_estimate.markup_material
            + latest_estimate.markup_labor
            + latest_estimate.overhead_pct
            + latest_estimate.target_profit_pct
        ) / 100
        estimate_revenue = direct * (1 + markup_total)

    # 3. CHANGE ORDERS (approved/sent, not cancelled)
    cos_revenue = project.change_orders.exclude(status__in=["cancelled", "pending"]).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0")

    # 4. TOTAL BUDGETED REVENUE
    # Use the HIGHER of: budget_lines_total or estimate_revenue, PLUS change orders
    base_budget = max(budget_lines_total, estimate_revenue)
    budgeted_revenue = base_budget + cos_revenue

    # 5. ACTUAL COSTS (Labor + Materials/Expenses)
    # Labor cost from TimeEntries (calculated in Python since labor_cost is a property)
    time_entries = TimeEntry.objects.filter(project=project)
    labor_cost = sum(entry.labor_cost for entry in time_entries)

    # Material/Expense costs
    material_cost = Expense.objects.filter(project=project).aggregate(total=Sum("amount"))[
        "total"
    ] or Decimal("0")

    total_actual_cost = labor_cost + material_cost

    # 6. BILLED AMOUNT (Sum of all invoices)
    billed_amount = Invoice.objects.filter(project=project).exclude(status="CANCELLED").aggregate(
        total=Sum("total_amount")
    )["total"] or Decimal("0")

    # 7. COLLECTED AMOUNT (Sum of invoice payments)
    collected_amount = Invoice.objects.filter(project=project).exclude(
        status="CANCELLED"
    ).aggregate(total=Sum("amount_paid"))["total"] or Decimal("0")

    # 8. CALCULATIONS
    # Net Profit = Budgeted Revenue - Actual Costs (projected profit based on budget)
    # This shows how much profit you EXPECT to make once project is complete
    net_profit = budgeted_revenue - total_actual_cost

    # Profit Margin % = (Net Profit / Budgeted Revenue) * 100
    # Shows expected margin based on budget vs costs incurred
    margin_pct = (net_profit / budgeted_revenue * 100) if budgeted_revenue > 0 else Decimal("0")

    # Outstanding = Billed - Collected (for cash flow tracking)
    outstanding = billed_amount - collected_amount

    # Budget consumed % (how much of budget has been spent)
    budget_consumed_pct = (total_actual_cost / budgeted_revenue * 100) if budgeted_revenue > 0 else Decimal("0")
    
    # Remaining budget
    remaining_budget = budgeted_revenue - total_actual_cost

    # 9. CALCULATE PERCENTAGES FOR DISPLAY (avoid template math)
    labor_pct = (labor_cost / total_actual_cost * 100) if total_actual_cost > 0 else Decimal("0")
    material_pct = (material_cost / total_actual_cost * 100) if total_actual_cost > 0 else Decimal("0")
    collected_pct = (collected_amount / billed_amount * 100) if billed_amount > 0 else Decimal("0")
    outstanding_pct = (outstanding / billed_amount * 100) if billed_amount > 0 else Decimal("0")

    # Alert flags
    alerts = []
    if margin_pct < 10:
        alerts.append(
            {"type": "danger", "message": f"Margen crítico: {margin_pct:.1f}% (meta: >25%)"}
        )
    elif margin_pct < 25:
        alerts.append(
            {"type": "warning", "message": f"Margen bajo: {margin_pct:.1f}% (meta: >25%)"}
        )
    if outstanding > budgeted_revenue * Decimal("0.3") and outstanding > 0:
        alerts.append(
            {"type": "warning", "message": f"Alto saldo pendiente: ${outstanding:,.2f}"}
        )
    if total_actual_cost > budgeted_revenue and budgeted_revenue > 0:
        alerts.append(
            {
                "type": "danger",
                "message": f"Costos exceden presupuesto: ${total_actual_cost:,.2f} > ${budgeted_revenue:,.2f}",
            }
        )

    context = {
        "project": project,
        "budgeted_revenue": budgeted_revenue,
        "base_budget": base_budget,  # Budget Lines total or Estimate (whichever is higher)
        "budget_lines_total": budget_lines_total,  # Sum of all BudgetLine.baseline_amount
        "estimate_revenue": estimate_revenue,  # From approved Estimate with markup
        "cos_revenue": cos_revenue,
        "labor_cost": labor_cost,
        "material_cost": material_cost,
        "total_actual_cost": total_actual_cost,
        "billed_amount": billed_amount,
        "collected_amount": collected_amount,
        "outstanding": outstanding,
        "net_profit": net_profit,  # Budgeted - Costs
        "margin_pct": margin_pct,
        "budget_consumed_pct": budget_consumed_pct,
        "remaining_budget": remaining_budget,
        "labor_pct": labor_pct,
        "material_pct": material_pct,
        "collected_pct": collected_pct,
        "outstanding_pct": outstanding_pct,
        "alerts": alerts,
    }
    return render(request, "core/project_profit_dashboard.html", context)


@login_required
def costcode_list_view(request):
    """Cost Code management view with full CRUD operations."""
    codes = CostCode.objects.all().order_by("category", "code")
    
    # Default categories for construction
    default_categories = [
        'Appliances', 'Cabinets', 'Cleanup', 'Concrete', 'Countertops',
        'Demolition', 'Drywall', 'Electrical', 'Equipment', 'Exterior',
        'Exterior Painting', 'Flooring', 'Framing', 'HVAC', 'Interior',
        'Interior Painting', 'Labor', 'Landscaping', 'Material', 'Plumbing',
        'Roofing', 'Subcontractor', 'Windows & Doors', 'Other',
    ]
    
    # Get existing categories normalized
    existing_raw = CostCode.objects.exclude(category__isnull=True).exclude(category='').values_list('category', flat=True).distinct()
    existing_normalized = {cat.strip().title() for cat in existing_raw}
    categories = sorted(set(default_categories) | existing_normalized)
    
    if request.method == "POST":
        action = request.POST.get('action', 'create')
        
        if action == 'create':
            category = request.POST.get('category', '').strip()
            code = request.POST.get('code', '').strip().upper()
            name = request.POST.get('name', '').strip()
            active = request.POST.get('active') == 'on'
            
            if code and name:
                CostCode.objects.create(
                    code=code,
                    name=name,
                    category=category,
                    active=active
                )
                messages.success(request, _("Cost code created successfully."))
            return redirect("costcode_list")
            
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
                    messages.success(request, _("Cost code updated successfully."))
                except CostCode.DoesNotExist:
                    messages.error(request, _("Cost code not found."))
            return redirect("costcode_list")
            
        elif action == 'delete':
            costcode_id = request.POST.get('costcode_id')
            if costcode_id:
                try:
                    costcode = CostCode.objects.get(pk=costcode_id)
                    costcode.delete()
                    messages.success(request, _("Cost code deleted."))
                except CostCode.DoesNotExist:
                    messages.error(request, _("Cost code not found."))
            return redirect("costcode_list")
    
    return render(request, "core/costcode_list.html", {
        "codes": codes,
        "categories": categories,
    })


@login_required
@staff_member_required
def budget_lines_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = BudgetLineForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        bl = form.save(commit=False)
        bl.project = project
        bl.save()
        return redirect("budget_lines", project_id=project.id)
    lines = project.budget_lines.select_related("cost_code")
    return render(
        request, "core/budget_lines.html", {"project": project, "lines": lines, "form": form}
    )


@login_required
@staff_member_required
def estimate_create_view(request, project_id):
    import logging
    logger = logging.getLogger(__name__)
    
    project = get_object_or_404(Project, pk=project_id)
    version = (project.estimates.aggregate(m=Max("version"))["m"] or 0) + 1
    cost_codes = CostCode.objects.all().order_by("code")
    
    if request.method == "POST":
        form = EstimateForm(request.POST)
        formset = EstimateLineFormSet(request.POST, prefix='lines')
        
        logger.info(f"Estimate form POST received for project {project_id}")
        logger.info(f"Form valid: {form.is_valid()}")
        logger.info(f"Formset valid: {formset.is_valid()}")
        
        if not form.is_valid():
            logger.warning(f"Form errors: {form.errors}")
            messages.error(request, _("Please correct the errors in the form."))
            
        if not formset.is_valid():
            logger.warning(f"Formset errors: {formset.errors}")
            # Count non-empty lines that have errors
            line_errors = [e for e in formset.errors if e]
            if line_errors:
                messages.error(request, _("Please correct the errors in the line items."))
        
        if form.is_valid() and formset.is_valid():
            est = form.save(commit=False)
            est.project = project
            est.version = version
            est.save()
            formset.instance = est
            
            # Save lines and filter out empty ones
            saved_lines = []
            for line_form in formset:
                if line_form.cleaned_data and not line_form.cleaned_data.get('DELETE', False):
                    if line_form.cleaned_data.get('cost_code'):
                        line = line_form.save(commit=False)
                        line.estimate = est
                        line.save()
                        saved_lines.append(line)
            
            logger.info(f"Created Estimate {est.code} with {len(saved_lines)} lines")
            messages.success(request, _("Estimate created successfully! You can now send it to the client for approval."))
            return redirect("estimate_detail", estimate_id=est.id)
    else:
        form = EstimateForm()
        formset = EstimateLineFormSet(prefix='lines')
    
    return render(
        request,
        "core/estimate_form.html",
        {
            "project": project,
            "form": form,
            "formset": formset,
            "version": version,
            "cost_codes": cost_codes,
        },
    )


@login_required
def estimate_edit_view(request, estimate_id):
    """Edit an existing estimate."""
    import logging
    logger = logging.getLogger(__name__)
    
    estimate = get_object_or_404(Estimate, pk=estimate_id)
    project = estimate.project
    cost_codes = CostCode.objects.all().order_by("code")
    
    # Prevent editing approved estimates
    if estimate.approved:
        messages.warning(request, _("This estimate has been approved and cannot be edited."))
        return redirect("estimate_detail", estimate_id=estimate.id)
    
    if request.method == "POST":
        form = EstimateForm(request.POST, instance=estimate)
        formset = EstimateLineFormSet(request.POST, instance=estimate, prefix='lines')
        
        logger.info(f"Estimate edit POST received for estimate {estimate_id}")
        logger.info(f"Form valid: {form.is_valid()}")
        logger.info(f"Formset valid: {formset.is_valid()}")
        
        if not form.is_valid():
            logger.warning(f"Form errors: {form.errors}")
            messages.error(request, _("Please correct the errors in the form."))
            
        if not formset.is_valid():
            logger.warning(f"Formset errors: {formset.errors}")
            line_errors = [e for e in formset.errors if e]
            if line_errors:
                messages.error(request, _("Please correct the errors in the line items."))
        
        if form.is_valid() and formset.is_valid():
            est = form.save()
            
            # Save lines
            saved_lines = []
            for line_form in formset:
                if line_form.cleaned_data:
                    if line_form.cleaned_data.get('DELETE', False):
                        if line_form.instance.pk:
                            line_form.instance.delete()
                    elif line_form.cleaned_data.get('cost_code'):
                        line = line_form.save(commit=False)
                        line.estimate = est
                        line.save()
                        saved_lines.append(line)
            
            logger.info(f"Updated Estimate {est.code} with {len(saved_lines)} lines")
            messages.success(request, _("Estimate updated successfully!"))
            return redirect("estimate_detail", estimate_id=est.id)
    else:
        form = EstimateForm(instance=estimate)
        formset = EstimateLineFormSet(instance=estimate, prefix='lines')
    
    return render(
        request,
        "core/estimate_form.html",
        {
            "project": project,
            "form": form,
            "formset": formset,
            "estimate": estimate,
            "version": estimate.version,
            "cost_codes": cost_codes,
            "is_edit": True,
        },
    )


@login_required
def estimate_detail_view(request, estimate_id):
    import logging
    logger = logging.getLogger(__name__)
    
    est = get_object_or_404(Estimate, pk=estimate_id)
    
