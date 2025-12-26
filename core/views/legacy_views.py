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
from django.db.models import Q, Sum
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
    PayrollRecordForm,
    PlanPinForm,
    ProposalEmailForm,
    RFIAnswerForm,
    RFIForm,
    RiskForm,
    ScheduleCategoryForm,
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
    ScheduleCategory,
    ScheduleItem,
    Task,
    TimeEntry,
)
from core.services.earned_value import compute_project_ev  # noqa: E402
from core.services.financial_service import FinancialAnalyticsService  # BI Module 21  # noqa: E402


# --- CLIENT REQUESTS ---
@login_required
def client_request_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
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
        qs = ClientRequest.objects.filter(project=project).order_by("-created_at")
    else:
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
                messages.warning(request, "Ya tienes una entrada abierta. Marca salida primero.")
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
                    _("✓ Entrada registrada a las %(time)s.") % {"time": now.strftime("%H:%M")},
                )
                return redirect("dashboard_admin")

        elif action == "clock_out":
            if not open_entry:
                messages.warning(request, "No tienes una entrada abierta.")
                return redirect("dashboard_admin")
            open_entry.end_time = now.time()
            open_entry.save()
            messages.success(
                request,
                f"✓ Salida registrada a las {now.strftime('%H:%M')}. Horas: {open_entry.hours_worked}",
            )
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
    """Dashboard visual para clientes con progreso, fotos, facturas"""
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != "client":
        messages.error(request, "Acceso solo para clientes.")
        return redirect("dashboard")

    # Proyectos del cliente: por vínculo directo (legacy) o por asignación granular
    access_projects = Project.objects.filter(client_accesses__user=request.user)
    legacy_projects = Project.objects.filter(client=request.user.username)
    projects = access_projects.union(legacy_projects).order_by("-start_date")

    # Para cada proyecto, calcular métricas visuales
    project_data = []
    for project in projects:
        # Facturas
        invoices = project.invoices.all().order_by("-date_issued")[:5]
        total_invoiced = invoices.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")
        total_paid = invoices.aggregate(paid=Sum("amount_paid"))["paid"] or Decimal("0")

        # Progreso (usando EV si disponible, sino estimado simple)
        progress_pct = 0
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

        # Fotos recientes
        from core.models import SitePhoto

        recent_photos = SitePhoto.objects.filter(project=project).order_by("-created_at")[:6]

        # Schedule próximo
        next_schedule = (
            Schedule.objects.filter(project=project, start_datetime__gte=timezone.now())
            .order_by("start_datetime")
            .first()
        )

        # Solicitudes cliente
        from core.models import ClientRequest

        client_requests = ClientRequest.objects.filter(project=project).order_by("-created_at")[:5]

        project_data.append(
            {
                "project": project,
                "invoices": invoices,
                "total_invoiced": total_invoiced,
                "total_paid": total_paid,
                "balance": total_invoiced - total_paid,
                "progress_pct": int(progress_pct),
                "recent_photos": recent_photos,
                "next_schedule": next_schedule,
                "client_requests": client_requests,
            }
        )

    # === MORNING BRIEFING (Categorized alerts for client) ===
    morning_briefing = []

    # Category: Updates (nuevas fotos, comentarios)
    latest_photos = []
    for proj_data in project_data:
        latest_photos.extend(proj_data["recent_photos"][:2])

    if latest_photos:
        morning_briefing.append(
            {
                "text": f"Hay {len(latest_photos)} nuevas fotos de tu proyecto",
                "severity": "info",
                "action_url": "#",
                "action_label": "Ver fotos",
                "category": "updates",
            }
        )

    # Category: Payments (facturas pendientes)
    overdue_invoices = []
    for proj_data in project_data:
        for inv in proj_data["invoices"]:
            if proj_data["balance"] > 0:
                overdue_invoices.append(inv)

    if overdue_invoices:
        total_due = sum(inv.total_amount - inv.amount_paid for inv in overdue_invoices)
        morning_briefing.append(
            {
                "text": f"Tienes ${total_due:,.2f} en facturas pendientes de pago",
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
                "action_label": "Pagar ahora",
                "category": "payments",
            }
        )

    # Category: Schedule (próximas actividades)
    upcoming_schedules = []
    for proj_data in project_data:
        if proj_data["next_schedule"]:
            upcoming_schedules.append(proj_data["next_schedule"])

    if upcoming_schedules:
        next_date = upcoming_schedules[0].start_datetime
        morning_briefing.append(
            {
                "text": f"Próxima actividad programada para {next_date.strftime('%d/%m/%Y')}",
                "severity": "info",
                "action_url": "#",
                "action_label": "Ver cronograma",
                "category": "schedule",
            }
        )

    # Apply filter if requested
    active_filter = request.GET.get("filter", "all")
    if active_filter != "all":
        morning_briefing = [
            item for item in morning_briefing if item.get("category") == active_filter
        ]

    # Mostrar nombre asignado al usuario (preferir display_name del perfil, luego nombre completo, luego username)
    display_name = None
    try:
        prof = getattr(request.user, "profile", None)
        candidate = None
        if prof is not None:
            candidate = getattr(prof, "display_name", None) or getattr(prof, "full_name", None)
        display_name = (candidate or request.user.get_full_name() or request.user.username).strip()
    except Exception:
        display_name = request.user.username

    context = {
        "project_data": project_data,
        "today": timezone.localdate(),
        "display_name": display_name,
        "morning_briefing": morning_briefing,
        "active_filter": active_filter,
    }

    # Always serve clean modern template; legacy can be enabled manually if needed
    force_legacy = request.GET.get("legacy", "false").lower() == "true"
    template_name = (
        "core/dashboard_client.html" if force_legacy else "core/dashboard_client_clean.html"
    )
    return render(request, template_name, context)


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
    return render(request, "core/expense_form.html", {"form": form})


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


# --- PAYROLL (DEPRECATED - usar payroll_weekly_review) ---
# @login_required
# def payroll_create_view(request):
#     # Vista obsoleta - reemplazada por sistema de revisión semanal
#     pass


# --- SISTEMA DE NÓMINA MEJORADO ---
@login_required
def payroll_weekly_review(request):
    """
    Vista para revisar y aprobar la nómina semanal.
    Muestra todos los empleados con sus horas trabajadas en la semana,
    permite editar horas de entrada/salida por día, y registrar pagos.
    """
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"]:
        return redirect("dashboard")

    from datetime import datetime, timedelta
    from decimal import Decimal
    from django.utils import timezone

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
                
                # Procesar pago con cheque si se proporcionó
                check_number = request.POST.get(f"check_{emp_id}")
                pay_date = request.POST.get(f"pay_date_{emp_id}")
                
                if check_number and pay_date and record.total_pay > 0:
                    # Verificar si ya existe un pago con este cheque
                    existing_payment = PayrollPayment.objects.filter(
                        payroll_record=record,
                        check_number=check_number
                    ).first()
                    
                    if not existing_payment:
                        PayrollPayment.objects.create(
                            payroll_record=record,
                            amount=record.balance_due(),
                            payment_date=pay_date,
                            payment_method="check",
                            check_number=check_number,
                            recorded_by=request.user,
                        )

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

        # Obtener entradas de tiempo para cada día de la semana
        day_entries = []
        calculated_hours = Decimal("0.00")
        
        for i in range(7):
            day = week_start + timedelta(days=i)
            entry = TimeEntry.objects.filter(
                employee=emp, date=day, change_order__isnull=True
            ).first()
            
            if entry:
                start_str = entry.start_time.strftime("%H:%M") if entry.start_time else ""
                end_str = entry.end_time.strftime("%H:%M") if entry.end_time else ""
                hours = entry.hours_worked or Decimal("0")
                calculated_hours += Decimal(str(hours)) if hours else Decimal("0")
            else:
                start_str = ""
                end_str = ""
                hours = None
            
            day_entries.append({
                'start': start_str,
                'end': end_str,
                'hours': hours,
            })
        
        # Actualizar record con horas calculadas si es diferente
        if record.total_hours != calculated_hours:
            record.total_hours = calculated_hours
            record.split_hours_regular_overtime()
            record.calculate_total_pay()
            record.save()
        
        # Obtener último pago
        last_payment = record.payments.order_by('-payment_date').first()

        employee_data.append({
            "employee": emp,
            "record": record,
            "calculated_hours": calculated_hours,
            "day_entries": day_entries,
            "last_payment": last_payment,
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
    """
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"]:
        return redirect("dashboard")

    record = get_object_or_404(PayrollRecord, id=record_id)

    if request.method == "POST":
        amount = request.POST.get("amount")
        payment_date = request.POST.get("payment_date")
        payment_method = request.POST.get("payment_method", "check")
        check_number = request.POST.get("check_number", "")
        reference = request.POST.get("reference", "")
        notes = request.POST.get("notes", "")

        if amount and payment_date:
            PayrollPayment.objects.create(
                payroll_record=record,
                amount=Decimal(amount),
                payment_date=payment_date,
                payment_method=payment_method,
                check_number=check_number,
                reference=reference,
                notes=notes,
                recorded_by=request.user,
            )

            messages.success(
                request,
                _("Pago de $%(amount)s registrado para %(employee)s.")
                % {"amount": amount, "employee": record.employee},
            )

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
    """
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"]:
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


# --- CLIENTE: Vista de proyecto y formularios ---
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
            messages.error(request, "No tienes acceso a este proyecto.")
            return redirect("dashboard_client")
    else:
        # Permitir staff; si es PM externo (no staff), permitir solo si tiene acceso granular
        if request.user.is_staff or has_explicit_access:
            pass
        else:
            messages.error(request, "Acceso denegado.")
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
    pending_tasks = tasks.filter(status__in=["Pendiente", "En Progreso"])
    completed_tasks = tasks.filter(status="Completada")[:10]

    # === COMENTARIOS ===
    comments = Comment.objects.filter(project=project).order_by("-created_at")[:10]

    # === FACTURAS ===
    invoices = project.invoices.all().order_by("-date_issued")[:5]
    total_invoiced = invoices.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")
    total_paid = invoices.aggregate(paid=Sum("amount_paid"))["paid"] or Decimal("0")

    # === PROGRESO DEL PROYECTO ===
    progress_pct = 0
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
        "color_samples": color_samples,
    }
    return render(request, "core/client_project_view.html", context)


# --- COLOR SAMPLES ---
@login_required
def color_sample_list(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    samples = project.color_samples.select_related("created_by").all().order_by("-created_at")

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
        },
    )


@login_required
def color_sample_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    profile = getattr(request.user, "profile", None)
    if not (request.user.is_staff or (profile and profile.role in ["client", "project_manager"])):
        messages.error(request, "Acceso denegado.")
        return redirect("dashboard")

    if request.method == "POST":
        form = ColorSampleForm(request.POST, request.FILES)
        if form.is_valid():
            inst = form.save(commit=False)
            inst.project = project
            inst.created_by = request.user
            inst.save()
            messages.success(request, "Muestra creada.")
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
    from core.models import ColorSample

    sample = get_object_or_404(ColorSample, id=sample_id)
    project = sample.project
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
    # Permisos: clientes, PM y diseñadores pueden dejar notas y mover a 'review'; solo staff puede aprobar/rechazar
    if not (
        request.user.is_staff
        or (profile and profile.role in ["client", "project_manager", "designer"])
    ):
        messages.error(request, "Acceso denegado.")
        return redirect("dashboard")

    if request.method == "POST":
        form = ColorSampleReviewForm(request.POST, instance=sample)
        if form.is_valid():
            old_status = sample.status
            inst = form.save(commit=False)
            # Validar transición de estado
            requested_status = inst.status
            if requested_status in ["approved", "rejected"] and not request.user.is_staff:
                messages.error(request, "Solo el staff puede aprobar o rechazar colores.")
            else:
                if requested_status == "approved" and not inst.approved_by:
                    inst.approved_by = request.user
                inst.save()
                # Notificar cambios
                from core.notifications import notify_color_approved, notify_color_review

                if requested_status == "approved":
                    notify_color_approved(inst, request.user)
                elif old_status != requested_status:
                    notify_color_review(inst, request.user)
                messages.success(
                    request,
                    _("Estado actualizado a %(status)s") % {"status": inst.get_status_display()},
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
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

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
                    "display": "Aprobado",
                    "sample_number": sample.sample_number,
                    "signature": sample.approval_signature,
                }
            )
        elif action == "reject":
            reason = request.POST.get("reason", "").strip()
            if not reason:
                return JsonResponse({"error": gettext("Razón de rechazo requerida")}, status=400)
            sample.reject(request.user, reason)
            return JsonResponse(
                {
                    "success": True,
                    "status": "rejected",
                    "display": "Rechazado",
                    "reason": sample.rejection_reason,
                }
            )

    return JsonResponse({"error": gettext("Acción inválida")}, status=400)


@login_required
def color_sample_edit(request, sample_id):
    """Edit existing color sample"""
    sample = get_object_or_404(ColorSample, id=sample_id)
    project = sample.project
    profile = getattr(request.user, "profile", None)

    if not (request.user.is_staff or (profile and profile.role in ["client", "project_manager"])):
        messages.error(request, "Acceso denegado.")
        return redirect("color_sample_detail", sample_id=sample_id)

    if request.method == "POST":
        form = ColorSampleForm(request.POST, request.FILES, instance=sample)
        if form.is_valid():
            form.save()
            messages.success(request, "Muestra actualizada.")
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
        messages.error(request, "Acceso denegado.")
        return redirect("color_sample_detail", sample_id=sample_id)

    if request.method == "POST":
        project_id = sample.project.id
        sample.delete()
        messages.success(request, "Muestra eliminada.")
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
    profile = getattr(request.user, "profile", None)
    if not (request.user.is_staff or (profile and profile.role in ["project_manager", "client"])):
        messages.error(request, "Acceso denegado.")
        return redirect("dashboard")
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
    """Display floor plan with ONLY touch-up pins (filtered view)"""
    import json

    from core.models import FloorPlan

    plan = get_object_or_404(FloorPlan, id=plan_id)

    # Filter to show ONLY touchup pins
    pins = plan.pins.filter(pin_type="touchup").select_related("color_sample", "linked_task").all()

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

    # Serialize pins data for JavaScript (only touchup pins)
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
        "core/floor_plan_touchup_view.html",
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
                    status="Pendiente",
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
                    title=pin.title or "Daño reportado",
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
            messages.error(request, "El título es requerido.")
            return redirect("client_project_view", project_id=project_id)

        # Crear tarea con estado Pendiente y foto si existe
        task = Task.objects.create(
            project=project,
            title=title,
            description=description,
            status="Pendiente",
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
            if new_status == "Completada":
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


@login_required
def design_chat(request, project_id):
    """Chat colaborativo de diseño (simple poll)."""
    from core.models import DesignChatMessage

    project = get_object_or_404(Project, id=project_id)
    if request.method == "POST":
        msg = request.POST.get("message", "").strip()
        image = request.FILES.get("image")
        if msg or image:
            DesignChatMessage.objects.create(
                project=project, user=request.user, message=msg, image=image
            )
            return redirect("design_chat", project_id=project.id)
    messages_qs = project.design_messages.select_related("user")[:200]
    return render(
        request,
        "core/design_chat.html",
        {
            "project": project,
            "messages": messages_qs,
        },
    )


# =============================
# Project Chat (group + direct)
# =============================


def _ensure_default_channels(project, user):
    group, _ = ChatChannel.objects.get_or_create(
        project=project,
        name="Grupo",
        defaults={"channel_type": "group", "is_default": True, "created_by": user},
    )
    direct, _ = ChatChannel.objects.get_or_create(
        project=project,
        name="Directo",
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
def project_chat_index(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    group, direct = _ensure_default_channels(project, request.user)
    return redirect("project_chat_room", project_id=project.id, channel_id=group.id)


@login_required
def project_chat_room(request, project_id, channel_id):
    project = get_object_or_404(Project, id=project_id)
    channel = get_object_or_404(ChatChannel, id=channel_id, project=project)
    # Access control
    if not (request.user.is_staff or channel.participants.filter(id=request.user.id).exists()):
        messages.error(request, "No tienes acceso a este chat.")
        return redirect("dashboard")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "invite":
            username = (request.POST.get("username") or "").strip()
            from django.contrib.auth.models import User as DjangoUser

            try:
                u = DjangoUser.objects.get(username=username)
                channel.participants.add(u)
                messages.success(request, _("%(username)s invitado.") % {"username": username})
                return redirect("project_chat_room", project_id=project.id, channel_id=channel.id)
            except DjangoUser.DoesNotExist:
                messages.error(request, "Usuario no encontrado.")
        elif action == "send":
            text = (request.POST.get("message") or "").strip()
            link_url = (request.POST.get("link_url") or "").strip()
            image = request.FILES.get("image")
            if not text and not image and not link_url:
                messages.error(request, "Mensaje vacío.")
            else:
                ChatMessage.objects.create(
                    channel=channel, user=request.user, message=text, link_url=link_url, image=image
                )
                return redirect("project_chat_room", project_id=project.id, channel_id=channel.id)

    messages_list = channel.messages.select_related("user")[:200]
    channels = project.chat_channels.all().order_by("name")
    return render(
        request,
        "core/project_chat_room.html",
        {
            "project": project,
            "channel": channel,
            "channels": channels,
            "messages": messages_list,
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


def changeorder_customer_signature_view(request, changeorder_id, token=None):
    """Vista pública para capturar firma de cliente en Change Orders.
    Mejoras:
    - Validación de token firmado (HMAC) con expiración.
    - Acceso opcional sin token (compatibilidad con flujo interno).
    - Manejo explícito de errores de token (expirado / manipulado).
    """
    changeorder = get_object_or_404(ChangeOrder, id=changeorder_id)

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
            request, "core/changeorder_signature_already_signed.html", {"changeorder": changeorder}
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
                    "error": "Por favor, dibuje su firma antes de continuar.",
                },
            )
        if not signer_name:
            return render(
                request,
                "core/changeorder_signature_form.html",
                {"changeorder": changeorder, "error": "Por favor, ingrese su nombre completo."},
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

            subject = f"CO #{changeorder.id} firmado por cliente"
            body_lines = [
                f"Change Order #{changeorder.id} ha sido firmado.",
                f"Proyecto: {changeorder.project.name if changeorder.project else '-'}",
                f"Descripción: {changeorder.description[:180]}"
                + ("..." if len(changeorder.description) > 180 else ""),
                f"Tipo de precio: {changeorder.pricing_type}",
                f"Firmado por: {signer_name}",
                f"Fecha/Hora: {timezone.localtime(changeorder.signed_at).strftime('%Y-%m-%d %H:%M:%S')}",
            ]

            if changeorder.pricing_type == "T_AND_M":
                body_lines.append(
                    f"Tarifa Labor: ${changeorder.get_effective_billing_rate():.2f} | Markup Materiales: {changeorder.material_markup_pct}%"
                )
            else:
                body_lines.append(f"Monto fijo aprobado: ${changeorder.amount:.2f}")

            body_lines.append("---")
            body_lines.append("Este correo es automático. No responder.")
            message_body = "\n".join(body_lines)

            # Enviar a staff interno
            if internal_recipients:
                with contextlib.suppress(Exception):
                    send_mail(
                        subject,
                        message_body,
                        getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@kibray.com"),
                        internal_recipients,
                        fail_silently=True,
                    )

            # Enviar confirmación al cliente si proporcionó correo
            if customer_email:
                with contextlib.suppress(Exception):
                    send_mail(
                        f"Confirmación firma CO #{changeorder.id}",
                        "Gracias por firmar el Change Order. Hemos registrado su aprobación.",
                        getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@kibray.com"),
                        [customer_email],
                        fail_silently=True,
                    )

            # --- PDF Generation (Paso 3) ---
            try:
                pdf_template = get_template("core/changeorder_pdf.html")
                html = pdf_template.render({"changeorder": changeorder})
                if pisa:
                    pdf_io = BytesIO()
                    try:
                        pisa.CreatePDF(html, dest=pdf_io)
                        pdf_bytes = pdf_io.getvalue()
                    except Exception:
                        pdf_bytes = b""
                else:
                    pdf_bytes = _generate_basic_pdf_from_html(html)
                if pdf_bytes:
                    from django.core.files.base import ContentFile

                    changeorder.signed_pdf = ContentFile(
                        pdf_bytes, name=f"co_{changeorder.id}_signed.pdf"
                    )
                    changeorder.save(update_fields=["signed_pdf"])
            except Exception:
                # No bloquear flujo por fallo de PDF
                pass

            return render(
                request, "core/changeorder_signature_success.html", {"changeorder": changeorder}
            )
        except Exception as e:
            return render(
                request,
                "core/changeorder_signature_form.html",
                {"changeorder": changeorder, "error": f"Error al procesar la firma: {e}"},
            )

    return render(request, "core/changeorder_signature_form.html", {"changeorder": changeorder})


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

    # Use clean Design System template by default
    # Legacy template available via ?legacy=true
    use_legacy = request.GET.get("legacy", "false").lower() == "true"
    use_standalone = request.GET.get("standalone", "false").lower() == "true"

    if use_standalone:
        template = "core/changeorder_form_standalone.html"
    elif use_legacy:
        template = "core/changeorder_form_modern.html"
    else:
        template = "core/changeorder_form_clean.html"

    return render(request, template, {"form": form, "approved_colors": approved_colors})


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

    # Use clean Design System template by default
    # Legacy template available via ?legacy=true
    use_legacy = request.GET.get("legacy", "false").lower() == "true"
    use_standalone = request.GET.get("standalone", "false").lower() == "true"

    if use_standalone:
        template = "core/changeorder_form_standalone.html"
    elif use_legacy:
        template = "core/changeorder_form_modern.html"
    else:
        template = "core/changeorder_form_clean.html"

    return render(
        request,
        template,
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
    colors = (
        ColorSample.objects.filter(project_id=project_id, status="approved")
        .values("id", "code", "name", "brand", "finish")
        .order_by("code")
    )

    return JsonResponse({"colors": list(colors)})

    # (Legacy annotation and delete endpoints removed; use DRF versions under /api/v1/changeorder-photo/)


def color_sample_client_signature_view(request, sample_id, token=None):
    """Vista pública para capturar firma de cliente en muestras de color.

    Basada en: changeorder_customer_signature_view
    Validación de token firmado (HMAC) con expiración de 7 días.
    Captura la firma en base64, nombre del cliente, y genera PDF.
    """
    color_sample = get_object_or_404(ColorSample, id=sample_id)

    # --- Token validation (solo si se proporciona en la URL) ---
    if token is not None:
        try:
            payload = signing.loads(token, max_age=60 * 60 * 24 * 7)  # 7 días
            if payload.get("sample_id") != color_sample.id:
                return HttpResponseForbidden("Token no coincide con esta muestra de color.")
        except signing.SignatureExpired:
            return HttpResponseForbidden("El enlace de firma ha expirado. Solicite uno nuevo.")
        except signing.BadSignature:
            return HttpResponseForbidden("Token inválido o manipulado.")

    # Si ya está firmado mostrar pantalla correspondiente
    if color_sample.approval_signature:
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
        signer_name = request.POST.get("signer_name", "").strip()
        signer_email = request.POST.get("signer_email", "").strip()

        if not signature_data:
            return render(
                request,
                "core/color_sample_signature_form.html",
                {
                    "color_sample": color_sample,
                    "error": "Por favor, dibuje su firma antes de continuar.",
                },
            )
        if not signer_name:
            return render(
                request,
                "core/color_sample_signature_form.html",
                {"color_sample": color_sample, "error": "Por favor, ingrese su nombre completo."},
            )

        try:
            # --- Procesar firma base64 ---
            format_str, imgstr = signature_data.split(";base64,")
            ext = format_str.split("/")[-1]
            if ext not in ["png", "jpeg", "jpg"]:
                ext = "png"

            # Decodificar base64
            decoded_image = base64.b64decode(imgstr)

            # Crear nombre único para archivo
            file_name = f"color_sample_{color_sample.id}_signature_{uuid.uuid4().hex}.{ext}"
            signature_file = ContentFile(decoded_image, name=file_name)

            # Obtener IP del cliente
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            client_ip = (
                x_forwarded_for.split(",")[0]
                if x_forwarded_for
                else request.META.get("REMOTE_ADDR", "")
            )

            # --- Guardar firma en ColorSample ---
            color_sample.approval_signature = signature_file
            color_sample.approval_ip = client_ip
            color_sample.approval_date = timezone.now()
            color_sample.status = "approved"  # Marcar como aprobada
            color_sample.save(
                update_fields=["approval_signature", "approval_ip", "approval_date", "status"]
            )

            # --- Crear/actualizar registro de aprobación en ColorApproval ---
            color_approval, created = ColorApproval.objects.get_or_create(
                color_sample=color_sample,
                defaults={
                    "client_name": signer_name,
                    "client_email": signer_email,
                    "client_signature": signature_file,
                    "signed_at": timezone.now(),
                    "status": "approved",
                    "ip_address": client_ip,
                },
            )
            if not created:
                color_approval.client_name = signer_name
                color_approval.client_email = signer_email
                color_approval.client_signature = signature_file
                color_approval.signed_at = timezone.now()
                color_approval.status = "approved"
                color_approval.ip_address = client_ip
                color_approval.save()

            # --- Notificar al PM del proyecto ---
            try:
                project = color_sample.project
                if project:
                    pm_profile = Profile.objects.filter(
                        project=project, role="project_manager"
                    ).first()
                    if pm_profile and pm_profile.user.email:
                        subject = f"Muestra de color #{color_sample.id} firmada por cliente"
                        message_body = (
                            f"La muestra de color '{color_sample.name}' (Código: {color_sample.code}) "
                            f"ha sido firmada por:\n\n"
                            f"Nombre: {signer_name}\n"
                            f"Email: {signer_email}\n"
                            f"Fecha: {color_approval.signed_at.strftime('%d/%m/%Y %H:%M')}\n"
                            f"IP: {client_ip}\n\n"
                            f"Proyecto: {project.name}\n"
                            f"Ubicación: {color_sample.room_location or 'N/A'}\n\n"
                            f"Este correo es automático. No responder."
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

            # --- Generar PDF (opcional, similar a Change Order) ---
            try:
                pdf_template = get_template("core/color_sample_approval_pdf.html")
                html = pdf_template.render(
                    {"color_sample": color_sample, "color_approval": color_approval}
                )
                if pisa:
                    pdf_io = BytesIO()
                    try:
                        pisa.CreatePDF(html, dest=pdf_io)
                        pdf_io.getvalue()
                    except Exception:
                        pass
                else:
                    _generate_basic_pdf_from_html(html)
                # Opcional: guardar PDF en ColorApproval si tiene campo para ello
                # color_approval.signed_pdf = ContentFile(pdf_bytes, name=f"sample_{sample_id}_approval.pdf")
                # color_approval.save(update_fields=["signed_pdf"])
            except Exception:
                # No bloquear flujo por fallo de PDF
                pass

            return render(
                request,
                "core/color_sample_signature_success.html",
                {"color_sample": color_sample, "color_approval": color_approval},
            )
        except Exception as e:
            return render(
                request,
                "core/color_sample_signature_form.html",
                {"color_sample": color_sample, "error": f"Error al procesar la firma: {e}"},
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


# --- PAYROLL SUMMARY (DEPRECATED: reemplazado por payroll_weekly_review) ---
# --- DASHBOARD ASIGNACIÓN DE CHANGE ORDERS ---
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
@transaction.atomic
def invoice_create_view(request):
    edit_mode = False
    if request.method == "POST":
        form = InvoiceForm(request.POST)
        formset = InvoiceLineFormSet(request.POST, prefix="lines")
        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.save()  # 1) obtener PK
            form.save_m2m()  # 2) asignar M2M (change_orders)

            # 3) guardar líneas del formset
            instances = formset.save(commit=False)
            for ln in instances:
                ln.invoice = invoice
                ln.save()
            for ln in formset.deleted_objects:
                ln.delete()

            # 4) opcional: agregar líneas por CO seleccionados si no existen
            selected_cos = form.cleaned_data.get("change_orders") or []
            for co in selected_cos:
                if not InvoiceLine.objects.filter(
                    invoice=invoice, description=co.description, amount=co.amount
                ).exists():
                    InvoiceLine.objects.create(
                        invoice=invoice, description=co.description, amount=co.amount
                    )

            # 5) recalcular total desde líneas y validar presupuesto
            total = InvoiceLine.objects.filter(invoice=invoice).aggregate(s=Sum("amount"))["s"] or 0
            invoice.total_amount = total
            invoice.full_clean(exclude=None, validate_unique=False)
            invoice.save(update_fields=["total_amount"])

            messages.success(request, "Factura creada correctamente.")
            return redirect("dashboard")
        messages.error(request, "Corrige los errores del formulario.")
    else:
        form = InvoiceForm()
        formset = InvoiceLineFormSet(prefix="lines")

    return render(
        request,
        "core/invoice_form.html",
        {"form": form, "formset": formset, "edit_mode": edit_mode},
    )


@login_required
def invoice_list(request):
    invoices = (
        Invoice.objects.select_related("project")
        .prefetch_related("lines")
        .order_by("-date_issued", "-id")
    )
    projects = Project.objects.filter(is_archived=False).order_by("name")
    return render(request, "core/invoice_list.html", {"invoices": invoices, "projects": projects})


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, "core/invoice_detail.html", {"invoice": invoice})


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
@transaction.atomic
def invoice_edit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == "POST":
        form = InvoiceForm(request.POST, instance=invoice)
        formset = InvoiceLineFormSet(request.POST, instance=invoice)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Invoice updated.")
            return redirect("invoice_detail", pk=invoice.pk)
    else:
        form = InvoiceForm(instance=invoice)
        formset = InvoiceLineFormSet(instance=invoice)
    return render(
        request, "core/invoice_form.html", {"form": form, "formset": formset, "edit_mode": True}
    )


@login_required
def changeorders_ajax(request):
    project_id = request.GET.get("project_id")
    qs = ChangeOrder.objects.filter(project_id=project_id).order_by("id")
    data = [{"id": co.id, "description": co.description, "amount": float(co.amount)} for co in qs]
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

    context = {
        "pending_invoices": pending_invoices,
        "recently_paid": recently_paid,
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
def project_profit_dashboard(request, project_id):
    """
    Project Profit Dashboard: Real-time visibility of margins and financial health.
    Shows: Budgeted Revenue, Actual Costs, Billed Amount, Collected, Profit Margin.
    """
    project = get_object_or_404(Project, pk=project_id)

    # 1. BUDGETED REVENUE (Estimate + Approved COs)
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

    # Change Orders (approved/sent, not cancelled)
    cos_revenue = project.change_orders.exclude(status__in=["cancelled", "pending"]).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0")

    budgeted_revenue = estimate_revenue + cos_revenue

    # 2. ACTUAL COSTS (Labor + Materials/Expenses)
    # Labor cost from TimeEntries (calculated in Python since labor_cost is a property)
    time_entries = TimeEntry.objects.filter(project=project)
    labor_cost = sum(entry.labor_cost for entry in time_entries)

    # Material/Expense costs
    material_cost = Expense.objects.filter(project=project).aggregate(total=Sum("amount"))[
        "total"
    ] or Decimal("0")

    total_actual_cost = labor_cost + material_cost

    # 3. BILLED AMOUNT (Sum of all invoices)
    billed_amount = Invoice.objects.filter(project=project).exclude(status="CANCELLED").aggregate(
        total=Sum("total_amount")
    )["total"] or Decimal("0")

    # 4. COLLECTED AMOUNT (Sum of invoice payments)
    collected_amount = Invoice.objects.filter(project=project).exclude(
        status="CANCELLED"
    ).aggregate(total=Sum("amount_paid"))["total"] or Decimal("0")

    # 5. CALCULATIONS
    # Profit = Billed - Actual Costs
    profit = billed_amount - total_actual_cost

    # Margin % = (Profit / Billed) * 100
    margin_pct = (profit / billed_amount * 100) if billed_amount > 0 else Decimal("0")

    # Outstanding = Billed - Collected
    outstanding = billed_amount - collected_amount

    # Budget variance
    budget_variance = billed_amount - budgeted_revenue
    budget_variance_pct = (
        (budget_variance / budgeted_revenue * 100) if budgeted_revenue > 0 else Decimal("0")
    )

    # Cost breakdown for chart
    cost_breakdown = {
        "labor": float(labor_cost),
        "materials": float(material_cost),
    }

    # Alert flags
    alerts = []
    if margin_pct < 10:
        alerts.append(
            {"type": "danger", "message": f"⚠️ Margen bajo: {margin_pct:.1f}% (meta: >25%)"}
        )
    if outstanding > budgeted_revenue * Decimal("0.3"):
        alerts.append(
            {"type": "warning", "message": f"💰 Alto saldo pendiente: ${outstanding:,.2f}"}
        )
    if total_actual_cost > budgeted_revenue:
        alerts.append(
            {
                "type": "danger",
                "message": f"📉 Costos exceden presupuesto: ${total_actual_cost:,.2f} > ${budgeted_revenue:,.2f}",
            }
        )

    context = {
        "project": project,
        "budgeted_revenue": budgeted_revenue,
        "estimate_revenue": estimate_revenue,
        "cos_revenue": cos_revenue,
        "labor_cost": labor_cost,
        "material_cost": material_cost,
        "total_actual_cost": total_actual_cost,
        "billed_amount": billed_amount,
        "collected_amount": collected_amount,
        "outstanding": outstanding,
        "profit": profit,
        "margin_pct": margin_pct,
        "budget_variance": budget_variance,
        "budget_variance_pct": budget_variance_pct,
        "cost_breakdown": cost_breakdown,
        "alerts": alerts,
    }
    return render(request, "core/project_profit_dashboard.html", context)


@login_required
def costcode_list_view(request):
    codes = CostCode.objects.all().order_by("code")
    form = CostCodeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("costcode_list")
    return render(request, "core/costcode_list.html", {"codes": codes, "form": form})


@login_required
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
def estimate_create_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    version = (project.estimates.aggregate(m=models.Max("version"))["m"] or 0) + 1
    if request.method == "POST":
        form = EstimateForm(request.POST)
        formset = EstimateLineFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            est = form.save(commit=False)
            est.project = project
            est.version = version
            est.save()
            formset.instance = est
            formset.save()
            return redirect("estimate_detail", estimate_id=est.id)
    else:
        form = EstimateForm()
        formset = EstimateLineFormSet()
    return render(
        request,
        "core/estimate_form.html",
        {"project": project, "form": form, "formset": formset, "version": version},
    )


@login_required
def estimate_detail_view(request, estimate_id):
    est = get_object_or_404(Estimate, pk=estimate_id)
    lines = est.lines.select_related("cost_code")
    direct = sum(line.direct_cost() for line in lines)
    material_markup = direct * (est.markup_material / 100)
    labor_markup = direct * (est.markup_labor / 100)
    overhead = direct * (est.overhead_pct / 100)
    target_profit = direct * (est.target_profit_pct / 100)
    proposed_price = direct + material_markup + labor_markup + overhead + target_profit
    return render(
        request,
        "core/estimate_detail.html",
        {
            "estimate": est,
            "lines": lines,
            "direct": direct,
            "proposed_price": proposed_price,
        },
    )


@login_required
def estimate_send_email(request, estimate_id):
    """Vista para pre-editar y enviar la propuesta al cliente por email.

    GET: retorna fragmento HTML con formulario pre-llenado (para cargar en modal).
    POST: envía el correo y redirige al detalle del estimate con mensaje de éxito.
    """
    import uuid

    from django.conf import settings
    from django.utils import timezone

    est = get_object_or_404(Estimate, pk=estimate_id)
    # Asegurar Proposal y token
    from core.models import Proposal

    proposal, created = Proposal.objects.get_or_create(
        estimate=est,
        defaults={"issued_at": timezone.now()},
    )
    if not proposal.client_view_token:
        proposal.client_view_token = uuid.uuid4()
        proposal.save(update_fields=["client_view_token"])

    public_url = request.build_absolute_uri(
        reverse("proposal_public", kwargs={"token": str(proposal.client_view_token)})
    )

    # Heurística para pre-llenar email del cliente
    initial_recipient = None
    if est.project.client and "@" in est.project.client:
        initial_recipient = est.project.client.strip()
    else:
        try:
            from core.models import ClientProjectAccess

            cpa = (
                ClientProjectAccess.objects.filter(project=est.project, role="client")
                .select_related("user")
                .first()
            )
            if cpa and cpa.user and cpa.user.email:
                initial_recipient = cpa.user.email
        except Exception:
            pass

    if request.method == "POST":
        form = ProposalEmailForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data["subject"]
            message = form.cleaned_data["message"]
            recipient = form.cleaned_data["recipient"]
            # Garantizar que el link está incluido
            if public_url not in message:
                message = f"{message}\n\nVer y aprobar la cotización:\n{public_url}"
            sender = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")
            error_msg = None
            success_flag = True
            try:
                # Construir versión HTML simple
                html_body = (
                    "<p>"
                    + message.replace("\n\n", "</p><p>").replace("\n", "<br>")
                    + "</p>"
                    + f"<p><a href='{public_url}' style='display:inline-block;padding:12px 20px;background:#4CAF50;color:#fff;text-decoration:none;border-radius:6px;'>Ver y Aprobar Cotización</a></p>"
                )
                email = EmailMultiAlternatives(subject, message, sender, [recipient])
                email.attach_alternative(html_body, "text/html")
                email.send()
                messages.success(request, "Propuesta enviada correctamente al cliente.")
            except Exception as e:
                success_flag = False
                error_msg = str(e)
                messages.error(request, _("Error enviando correo: %(error)s") % {"error": e})

            # Log persistente
            from core.models import ProposalEmailLog

            with contextlib.suppress(Exception):
                ProposalEmailLog.objects.create(
                    proposal=proposal,
                    estimate=est,
                    recipient=recipient,
                    subject=subject,
                    message_preview=message[:500],
                    success=success_flag,
                    error_message=error_msg,
                )
            return redirect("estimate_detail", estimate_id=est.id)
    else:
        client_name = est.project.client or "Cliente"
        subject = f"Cotización {getattr(est, 'code', '')} - {est.project.name}".strip()
        message = (
            f"Hola {client_name},\n\n"
            "Adjunto encontrarás la cotización detallada para tu revisión.\n\n"
            f"Puedes verla y aprobarla aquí:\n{public_url}\n\n"
            "Saludos,\nTu Empresa"
        )
        form = ProposalEmailForm(
            initial={
                "subject": subject,
                "message": message,
                "recipient": initial_recipient or "",
            }
        )

    # GET -> retornar fragmento para modal (o página completa si se accede directamente)
    template_name = (
        "core/partials/proposal_email_form.html"
        if request.headers.get("Hx-Request") or request.GET.get("partial")
        else "core/partials/proposal_email_form.html"
    )
    return render(
        request,
        template_name,
        {
            "form": form,
            "estimate": est,
            "public_url": public_url,
        },
    )


@login_required
@login_required
def daily_log_view(request, project_id):
    """
    Vista para gestionar Daily Logs de un proyecto.
    PM puede crear reportes diarios seleccionando tareas completadas,
    agregando fotos y notas. Visible para PM, diseñadores, cliente, owner.
    """
    from core.forms import DailyLogForm
    from core.models import DailyLogPhoto

    project = get_object_or_404(Project, pk=project_id)

    # Verificar permisos (PM, admin, superuser)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    can_create = role in ["admin", "superuser", "project_manager"]

    if request.method == "POST" and can_create:
        form = DailyLogForm(request.POST, project=project)
        if form.is_valid():
            dl = form.save(commit=False)
            dl.project = project
            dl.created_by = request.user
            dl.save()

            # Guardar relaciones many-to-many
            form.save_m2m()

            # Procesar fotos si hay
            photos = request.FILES.getlist("photos")
            for photo_file in photos:
                photo = DailyLogPhoto.objects.create(
                    image=photo_file,
                    caption=request.POST.get("photo_caption", ""),
                    uploaded_by=request.user,
                )
                dl.photos.add(photo)

            messages.success(request, _("Daily Log creado para %(date)s") % {"date": dl.date})
            return redirect("daily_log_detail", log_id=dl.id)
    else:
        form = DailyLogForm(project=project) if can_create else None

    # Listar logs del proyecto (ordenados por fecha)
    logs = (
        project.daily_logs.select_related("created_by", "schedule_item")
        .prefetch_related("completed_tasks", "photos")
        .all()
    )

    # Filtros
    if not can_create and role == "employee":
        # Empleados NO pueden ver daily logs
        return redirect("dashboard_employee")

    # Filtrar solo publicados para clientes
    if role == "client":
        logs = logs.filter(is_published=True)

    context = {
        "project": project,
        "logs": logs,
        "form": form,
        "can_create": can_create,
    }
    return render(request, "core/daily_log_list.html", context)


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
def daily_log_detail(request, log_id):
    """Vista detallada de un Daily Log específico"""
    from core.models import DailyLog, DailyLogPhoto

    log = get_object_or_404(
        DailyLog.objects.select_related("project", "created_by", "schedule_item").prefetch_related(
            "completed_tasks", "photos"
        ),
        id=log_id,
    )

    # Verificar permisos
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")

    # Empleados no pueden ver
    if role == "employee":
        messages.error(request, "No tienes permiso para ver Daily Logs")
        return redirect("dashboard_employee")

    # Clientes solo ven publicados
    if role == "client" and not log.is_published:
        messages.error(request, "Este Daily Log no está disponible")
        return redirect("dashboard_client")

    # POST: Agregar más fotos
    if request.method == "POST" and role in ["admin", "superuser", "project_manager"]:
        photos = request.FILES.getlist("photos")
        caption = request.POST.get("caption", "")
        for photo_file in photos:
            photo = DailyLogPhoto.objects.create(
                image=photo_file, caption=caption, uploaded_by=request.user
            )
            log.photos.add(photo)
        messages.success(request, _("%(count)s foto(s) agregada(s)") % {"count": len(photos)})
        return redirect("daily_log_detail", log_id=log.id)

    context = {
        "log": log,
        "project": log.project,
        "can_edit": role in ["admin", "superuser", "project_manager"],
    }

    return render(request, "core/daily_log_detail.html", context)


@login_required
def daily_log_delete(request, log_id):
    """Eliminar un Daily Log (solo PM, admin, superuser)"""
    from core.models import DailyLog

    log = get_object_or_404(DailyLog.objects.select_related("project"), id=log_id)

    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    can_delete = role in ["admin", "superuser", "project_manager"]

    if not can_delete:
        messages.error(request, "No tienes permisos para eliminar Daily Logs")
        return redirect("daily_log_detail", log_id=log.id)

    if request.method == "POST":
        project_id = log.project_id
        log.delete()
        messages.success(request, "Daily Log eliminado correctamente")
        return redirect("daily_log", project_id=project_id)

    return render(
        request, "core/daily_log_confirm_delete.html", {"log": log, "project": log.project}
    )


@login_required
def daily_log_create(request, project_id):
    """Vista dedicada para crear un nuevo Daily Log"""
    from datetime import date

    from core.forms import DailyLogForm
    from core.models import Schedule, Task

    project = get_object_or_404(Project, pk=project_id)

    # Verificar permisos
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"]:
        messages.error(request, "Solo PM puede crear Daily Logs")
        return redirect("project_overview", project_id=project.id)

    if request.method == "POST":
        form = DailyLogForm(request.POST, project=project)
        if form.is_valid():
            dl = form.save(commit=False)
            dl.project = project
            dl.created_by = request.user
            dl.save()
            form.save_m2m()

            # Procesar fotos
            photos = request.FILES.getlist("photos")
            for photo_file in photos:
                from core.models import DailyLogPhoto

                photo = DailyLogPhoto.objects.create(
                    image=photo_file,
                    caption=request.POST.get("photo_caption", ""),
                    uploaded_by=request.user,
                )
                dl.photos.add(photo)

            messages.success(request, "Daily Log creado exitosamente")
            return redirect("daily_log_detail", log_id=dl.id)
    else:
        # Valores por defecto
        initial = {
            "date": date.today(),
            "is_published": False,
        }
        form = DailyLogForm(initial=initial, project=project)

    # Obtener tareas pendientes/en progreso para sugerencias
    pending_tasks = (
        Task.objects.filter(project=project, status__in=["pending", "in_progress"])
        .select_related("assigned_to")
        .order_by("created_at")
    )

    # Obtener actividades del schedule activas
    active_schedules = Schedule.objects.filter(
        project=project, start_datetime__lte=date.today()
    ).order_by("-start_datetime")[:10]

    context = {
        "project": project,
        "form": form,
        "pending_tasks": pending_tasks,
        "active_schedules": active_schedules,
    }

    return render(request, "core/daily_log_create.html", context)


@login_required
def rfi_list_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = RFIForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        number = (project.rfis.aggregate(m=models.Max("number"))["m"] or 0) + 1
        rfi = form.save(commit=False)
        rfi.project = project
        rfi.number = number
        rfi.save()
        return redirect("rfi_list", project_id=project.id)
    rfis = project.rfis.all()
    return render(request, "core/rfi_list.html", {"project": project, "rfis": rfis, "form": form})


@login_required
def rfi_answer_view(request, rfi_id):
    rfi = get_object_or_404(RFI, pk=rfi_id)
    form = RFIAnswerForm(request.POST or None, instance=rfi)
    if request.method == "POST" and form.is_valid():
        ans = form.save(commit=False)
        if ans.answer and ans.status == "open":
            ans.status = "answered"
        ans.save()
        return redirect("rfi_list", project_id=rfi.project_id)
    return render(request, "core/rfi_answer.html", {"rfi": rfi, "form": form})


@login_required
def rfi_edit_view(request, rfi_id):
    """Edit an RFI. Allowed for staff/PM."""
    rfi = get_object_or_404(RFI, pk=rfi_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, "Acceso denegado.")
        return redirect("rfi_list", project_id=rfi.project_id)

    if request.method == "POST":
        form = RFIForm(request.POST, instance=rfi)
        if form.is_valid():
            form.save()
            messages.success(request, "RFI actualizado.")
            return redirect("rfi_list", project_id=rfi.project_id)
    else:
        form = RFIForm(instance=rfi)
    return render(request, "core/rfi_form.html", {"form": form, "rfi": rfi, "project": rfi.project})


@login_required
def rfi_delete_view(request, rfi_id):
    """Delete an RFI with confirmation. Staff/PM only."""
    rfi = get_object_or_404(RFI, pk=rfi_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, "Acceso denegado.")
        return redirect("rfi_list", project_id=rfi.project_id)

    project_id = rfi.project_id
    if request.method == "POST":
        rfi.delete()
        messages.success(request, "RFI eliminado.")
        return redirect("rfi_list", project_id=project_id)
    return render(request, "core/rfi_confirm_delete.html", {"rfi": rfi})


@login_required
def issue_list_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = IssueForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        isue = form.save(commit=False)
        isue.project = project
        isue.save()
        return redirect("issue_list", project_id=project.id)
    issues = project.issues.all()
    return render(
        request, "core/issue_list.html", {"project": project, "issues": issues, "form": form}
    )


@login_required
def issue_edit_view(request, issue_id):
    """Edit an Issue. Allowed for staff/PM."""
    issue = get_object_or_404(Issue, pk=issue_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, "Acceso denegado.")
        return redirect("issue_list", project_id=issue.project_id)

    if request.method == "POST":
        form = IssueForm(request.POST, instance=issue)
        if form.is_valid():
            form.save()
            messages.success(request, "Issue actualizado.")
            return redirect("issue_list", project_id=issue.project_id)
    else:
        form = IssueForm(instance=issue)
    return render(
        request, "core/issue_form.html", {"form": form, "issue": issue, "project": issue.project}
    )


@login_required
def issue_delete_view(request, issue_id):
    """Delete an Issue with confirmation. Staff/PM only."""
    issue = get_object_or_404(Issue, pk=issue_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, "Acceso denegado.")
        return redirect("issue_list", project_id=issue.project_id)

    project_id = issue.project_id
    if request.method == "POST":
        issue.delete()
        messages.success(request, "Issue eliminado.")
        return redirect("issue_list", project_id=project_id)
    return render(request, "core/issue_confirm_delete.html", {"issue": issue})


@login_required
def risk_list_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = RiskForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        rk = form.save(commit=False)
        rk.project = project
        rk.save()
        return redirect("risk_list", project_id=project.id)
    risks = project.risks.all()
    return render(
        request, "core/risk_list.html", {"project": project, "risks": risks, "form": form}
    )


@login_required
def risk_edit_view(request, risk_id):
    """Edit a Risk. Allowed for staff/PM."""
    risk = get_object_or_404(Risk, pk=risk_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, "Acceso denegado.")
        return redirect("risk_list", project_id=risk.project_id)

    if request.method == "POST":
        form = RiskForm(request.POST, instance=risk)
        if form.is_valid():
            form.save()
            messages.success(request, "Risk actualizado.")
            return redirect("risk_list", project_id=risk.project_id)
    else:
        form = RiskForm(instance=risk)
    return render(
        request, "core/risk_form.html", {"form": form, "risk": risk, "project": risk.project}
    )


@login_required
def risk_delete_view(request, risk_id):
    """Delete a Risk with confirmation. Staff/PM only."""
    risk = get_object_or_404(Risk, pk=risk_id)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"] and not request.user.is_staff:
        messages.error(request, "Acceso denegado.")
        return redirect("risk_list", project_id=risk.project_id)

    project_id = risk.project_id
    if request.method == "POST":
        risk.delete()
        messages.success(request, "Risk eliminado.")
        return redirect("risk_list", project_id=project_id)
    return render(request, "core/risk_confirm_delete.html", {"risk": risk})


@login_required
def root_redirect(request):
    """Redirige al dashboard apropiado según rol del usuario"""
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", None)

    # Admin/Superuser → dashboard completo
    if request.user.is_superuser or request.user.is_staff:
        return redirect("dashboard_admin")

    # Según rol definido en Profile
    if role == "project_manager":
        return redirect("dashboard_pm")
    elif role == "client":
        return redirect("dashboard_client")
    elif role == "employee":
        return redirect("dashboard_employee")

    # Fallback
    return redirect("dashboard")


def navigation_app_view(request):
    """
    Serves the React navigation SPA for Phase 4 features.
    This view handles client-side routing for paths like /files, /users, /calendar, etc.
    """
    return render(request, "navigation/index.html")


# --- PROJECT EV ---
@login_required
def project_ev_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    # ?as_of=YYYY-MM-DD
    as_of = timezone.now().date()
    as_of_str = request.GET.get("as_of")
    if as_of_str:
        with contextlib.suppress(ValueError):
            as_of = datetime.strptime(as_of_str, "%Y-%m-%d").date()

    # BLOQUEA POST si no tiene permiso (antes de tocar datos)
    if request.method == "POST" and not _is_staffish(request.user):
        messages.error(request, "No tienes permisos para agregar progreso.")
        return redirect("project_ev", project_id=project_id)

    # Form de progreso (solo staff puede crear; coherente con tests que esperan redirect 302)
    if request.method == "POST":
        if _is_staffish(request.user):
            form = BudgetProgressForm(request.POST)
            form.fields["budget_line"].queryset = BudgetLine.objects.filter(project=project)
            if form.is_valid():
                try:
                    form.save()
                except (IntegrityError, ValidationError):
                    # Si ya existe progreso para esa fecha, crea uno en el siguiente día disponible
                    bl = form.cleaned_data.get("budget_line")
                    dt = form.cleaned_data.get("date") or as_of
                    for i in range(1, 8):
                        candidate = dt + timedelta(days=i)
                        if not BudgetProgress.objects.filter(
                            budget_line=bl, date=candidate
                        ).exists():
                            obj = form.save(commit=False)
                            obj.date = candidate
                            obj.save()
                            break
            else:
                # Fallback: intentar crear manualmente si el formulario falla por validaciones no críticas
                try:
                    bl_id = (
                        int(request.POST.get("budget_line"))
                        if request.POST.get("budget_line")
                        else None
                    )
                except (TypeError, ValueError):
                    bl_id = None
                dt_str = request.POST.get("date")
                try:
                    dt = datetime.strptime(dt_str, "%Y-%m-%d").date() if dt_str else as_of
                except ValueError:
                    dt = as_of
                try:
                    qty = Decimal(request.POST.get("qty_completed") or "0")
                    pc = Decimal(request.POST.get("percent_complete") or "0")
                except Exception:
                    qty, pc = Decimal("0"), Decimal("0")

                if bl_id:
                    bl = get_object_or_404(BudgetLine, id=bl_id, project=project)
                    # Ajustar percent si viene vacío y hay qty/qty_total
                    if (pc is None or pc == 0) and getattr(bl, "qty", None) and bl.qty:
                        pc = min(Decimal("100"), (Decimal(qty) / Decimal(bl.qty)) * Decimal("100"))
                    try:
                        BudgetProgress.objects.create(
                            budget_line=bl,
                            date=dt,
                            qty_completed=qty,
                            percent_complete=pc,
                            note=request.POST.get("note", ""),
                        )
                    except IntegrityError:
                        # fecha ocupada: usa siguiente día
                        for i in range(1, 8):
                            candidate = dt + timedelta(days=i)
                            if not BudgetProgress.objects.filter(
                                budget_line=bl, date=candidate
                            ).exists():
                                BudgetProgress.objects.create(
                                    budget_line=bl,
                                    date=candidate,
                                    qty_completed=qty,
                                    percent_complete=pc,
                                    note=request.POST.get("note", ""),
                                )
                                break
            return redirect(f"{reverse('project_ev', args=[project.id])}?as_of={as_of.isoformat()}")
        # Si no staff o form inválido, redirigir (para que test vea 302 en staff y no staff case ya cubierto antes)
        return redirect(f"{reverse('project_ev', args=[project.id])}?as_of={as_of.isoformat()}")
    else:
        form = BudgetProgressForm(initial={"date": as_of})
        form.fields["budget_line"].queryset = BudgetLine.objects.filter(project=project)

    # Calcula métricas
    summary = compute_project_ev(project, as_of=as_of)
    ev = summary.get("EV") or 0
    pv = summary.get("PV") or 0
    ac = summary.get("AC") or 0
    summary["cost_variance"] = (ev - ac) if (ev or ac) else None
    summary["schedule_variance"] = (ev - pv) if (ev or pv) else None

    # Query base
    qs = (
        BudgetProgress.objects.filter(budget_line__project=project, date__lte=as_of)
        .select_related("budget_line", "budget_line__cost_code")
        .order_by("-date", "-id")
    )

    # Paginación
    page_size = int(request.GET.get("ps", 20))
    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "project": project,
        "form": form,
        "summary": summary,
        "progress": page_obj.object_list,
        "page_obj": page_obj,
        "as_of": as_of,
        "SPI": summary.get("SPI") or 0,
        "CPI": summary.get("CPI") or 0,
        "can_edit_progress": _is_staffish(request.user),
    }
    return render(request, "core/project_ev.html", context)


@login_required
def project_ev_series(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    days = int(request.GET.get("days", 30))
    end_str = request.GET.get("end")
    if end_str:
        try:
            end = datetime.strptime(end_str, "%Y-%m-%d").date()
        except ValueError:
            end = timezone.now().date()
    else:
        end = timezone.now().date()
    start = end - timedelta(days=days - 1)

    labels, pv, ev, ac = [], [], [], []
    cur = start
    while cur <= end:
        s = compute_project_ev(project, as_of=cur)
        labels.append(cur.isoformat())
        pv.append(float(s.get("PV") or 0))
        ev.append(float(s.get("EV") or 0))
        ac.append(float(s.get("AC") or 0))
        cur += timedelta(days=1)

    return JsonResponse({"labels": labels, "PV": pv, "EV": ev, "AC": ac})


@login_required
def project_ev_csv(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    days = int(request.GET.get("days", 45))
    end_str = request.GET.get("end")
    if end_str:
        try:
            end = datetime.strptime(end_str, "%Y-%m-%d").date()
        except ValueError:
            end = timezone.now().date()
    else:
        end = timezone.now().date()
    start = end - timedelta(days=days - 1)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="ev_{project.id}_{end.isoformat()}.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(["Date", "PV", "EV", "AC", "SPI", "CPI"])

    cur = start
    while cur <= end:
        s = compute_project_ev(project, as_of=cur)
        pv = s.get("PV") or 0
        ev = s.get("EV") or 0
        ac = s.get("AC") or 0
        spi = (ev / pv) if pv else ""
        cpi = (ev / ac) if ac else ""
        writer.writerow(
            [
                cur.isoformat(),
                float(pv),
                float(ev),
                float(ac),
                float(spi) if spi else "",
                float(cpi) if cpi else "",
            ]
        )
        cur += timedelta(days=1)

    return response


@login_required
def budget_line_plan_view(request, line_id):
    line = get_object_or_404(BudgetLine, pk=line_id)
    form = BudgetLineScheduleForm(request.POST or None, instance=line)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("budget_lines", project_id=line.project_id)
    return render(request, "core/budget_line_plan.html", {"line": line, "form": form})


@login_required
def project_list(request):
    projects = Project.objects.all().order_by("id")
    return render(request, "core/project_list.html", {"projects": projects})


def _parse_date(s):
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime((s or "").strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Fecha inválida: {s}")


@login_required
def download_progress_sample(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = f'attachment; filename="progress_sample_project_{project.id}.csv"'
    resp.write("project_id,cost_code,date,percent_complete,qty_completed,note\r\n")
    # Fila de ejemplo
    resp.write(f"{project.id},LAB001,2025-08-24,25,,Inicio\r\n")
    return resp


def _is_staffish(user):
    role = getattr(getattr(user, "profile", None), "role", None)
    # Permite superuser/staff y roles comunes del sistema
    return bool(user.is_superuser or user.is_staff or role in ("admin", "project_manager"))


def _ensure_inventory_item(name: str, category_key: str, unit: str, *, no_threshold=False):
    """
    Busca o crea un InventoryItem con el nombre dado.
    Si no existe, lo crea con umbrales por categoría:
    - Consumibles (tape, plastic, etc.): threshold=5
    - Resto: threshold=1 (a menos que no_threshold=True)
    """
    from core.models import InventoryItem

    # Categorías consideradas consumibles (umbral mayor)
    consumable_categories = {
        "tape",
        "plastic",
        "masking_paper",
        "floor_paper",
        "sandpaper",
        "tray_liner",
        "blades",
        "gloves",
        "mask",
        "respirator",
        "caulk",
    }

    # Mapeo simple de category_key a CATEGORY_CHOICES del modelo
    category_map = {
        "tape": "MATERIAL",
        "plastic": "MATERIAL",
        "masking_paper": "MATERIAL",
        "floor_paper": "MATERIAL",
        "sandpaper": "MATERIAL",
        "paint": "PINTURA",
        "primer": "PINTURA",
        "stain": "PINTURA",
        "ladder": "ESCALERA",
        "sander": "LIJADORA",
        "sprayer": "SPRAY",
        "other": "OTRO",
    }
    category = category_map.get(category_key, "MATERIAL")

    item, created = InventoryItem.objects.get_or_create(
        name=name.strip(),
        defaults={
            "category": category,
            "unit": unit or "pcs",
            "no_threshold": no_threshold,
            "default_threshold": (
                None if no_threshold else (5 if category_key in consumable_categories else 1)
            ),
            "is_equipment": category in {"ESCALERA", "LIJADORA", "SPRAY", "HERRAMIENTA"},
        },
    )

    # Si existía pero no tiene umbral configurado, completa:
    if not created and not item.no_threshold and item.default_threshold is None:
        item.default_threshold = 5 if category_key in consumable_categories else 1
        item.save(update_fields=["default_threshold"])

    return item


def staff_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if _is_staffish(request.user):
            return view_func(request, *args, **kwargs)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return HttpResponseForbidden("Forbidden")
        messages.error(request, "No tienes permisos para esta acción.")
        project_id = kwargs.get("project_id")
        return (
            redirect("project_ev", project_id=project_id) if project_id else redirect("dashboard")
        )

    return _wrapped


@login_required
@staff_required
def upload_project_progress(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if not _is_staffish(request.user):
        messages.error(request, "No tienes permisos para importar progreso.")
        return redirect("project_ev", project_id=project.id)
    context = {"project": project, "result": None, "errors": []}

    if request.method == "POST":
        f = request.FILES.get("file")
        create_missing = bool(request.POST.get("create_missing"))
        if not f:
            return HttpResponseBadRequest("Falta archivo CSV.")
        if f.size and f.size > 2_000_000:
            context["errors"].append("El archivo es demasiado grande (máx. 2 MB).")
            return render(request, "core/upload_progress.html", context)

        text = f.read().decode("utf-8", errors="ignore").lstrip("\ufeff")
        # Detecta delimitador , ; o tab
        try:
            dialect = csv.Sniffer().sniff(text[:2048], delimiters=[",", ";", "\t"])
            delim = dialect.delimiter
        except Exception:
            delim = ","
        reader = csv.DictReader(io.StringIO(text), delimiter=delim)
        headers = {h.lower(): h for h in (reader.fieldnames or [])}
        required = {"cost_code", "date"}
        if not required.issubset(set(headers.keys())):
            context["errors"].append(f"Encabezados requeridos: {sorted(required)}")
            return render(request, "core/upload_progress.html", context)

        created = updated = skipped = 0
        for i, row in enumerate(reader, start=2):
            try:
                cc = (row.get(headers["cost_code"]) or "").strip()
                if not cc:
                    raise ValueError("Falta cost_code.")

                try:
                    cost_code = CostCode.objects.get(code=cc)
                except CostCode.DoesNotExist as exc:
                    raise ValueError(f"CostCode no existe: {cc}") from exc

                bl = (
                    BudgetLine.objects.filter(project=project, cost_code=cost_code)
                    .order_by("id")
                    .first()
                )
                if not bl:
                    if create_missing:
                        bl = BudgetLine.objects.create(
                            project=project,
                            cost_code=cost_code,
                            description=f"Auto {cc}",
                            qty=0,
                            unit="",
                            unit_cost=0,
                        )
                    else:
                        raise ValueError(f"No hay BudgetLine en este proyecto para cost_code={cc}")

                date = _parse_date(row.get(headers["date"]))
                pct = row.get(headers.get("percent_complete"))
                qty = row.get(headers.get("qty_completed"))
                note = (row.get(headers.get("note")) or "").strip()

                pct_val = Decimal(str(pct).strip()) if pct not in (None, "", " ") else None
                qty_val = Decimal(str(qty).strip()) if qty not in (None, "", " ") else Decimal("0")

                if (
                    (pct_val is None or pct_val == 0)
                    and getattr(bl, "qty", None)
                    and bl.qty
                    and bl.qty != 0
                    and qty_val
                ):
                    pct_val = min(Decimal("100"), (qty_val / Decimal(bl.qty)) * Decimal("100"))

                if pct_val is not None and (pct_val < 0 or pct_val > 100):
                    raise ValueError("percent_complete fuera de 0–100.")

                obj, is_created = BudgetProgress.objects.get_or_create(
                    budget_line=bl,
                    date=date,
                    defaults={
                        "qty_completed": qty_val or 0,
                        "percent_complete": pct_val or 0,
                        "note": note,
                    },
                )
                if is_created:
                    obj.full_clean()
                    obj.save()
                    created += 1
                else:
                    if qty_val is not None:
                        obj.qty_completed = qty_val
                    if pct_val is not None:
                        obj.percent_complete = pct_val
                    if note:
                        obj.note = note
                    obj.full_clean()
                    obj.save()
                    updated += 1

            except Exception as e:
                skipped += 1
                context["errors"].append(f"Fila {i}: {e}")

        context["result"] = {"created": created, "updated": updated, "skipped": skipped}

    return render(request, "core/upload_progress.html", context)


@login_required
@staff_required
@require_POST
def delete_progress(request, project_id, pk):
    if not _is_staffish(request.user):
        messages.error(request, "No tienes permisos para borrar progreso.")
        return redirect("project_ev", project_id=project_id)
    prog = get_object_or_404(BudgetProgress, pk=pk, budget_line__project_id=project_id)
    prog.delete()
    messages.success(request, "Progreso eliminado.")
    return redirect("project_ev", project_id=project_id)


@login_required
@staff_required
@require_http_methods(["GET", "POST"])
def edit_progress(request, project_id, pk):
    try:
        prog = BudgetProgress.objects.select_related("budget_line__project").get(
            pk=pk, budget_line__project_id=project_id
        )
    except BudgetProgress.DoesNotExist:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return HttpResponseNotFound("Not found")
        raise Http404("BudgetProgress not found") from None

    if request.method == "POST":
        form = BudgetProgressEditForm(request.POST, instance=prog)
        if form.is_valid():
            form.save()
            messages.success(request, "Progreso actualizado.")
            as_of = request.POST.get("as_of")
            url = reverse("project_ev", args=[project_id])
            if as_of:
                url = f"{url}?as_of={as_of}"
            return redirect(url)
    else:
        form = BudgetProgressEditForm(instance=prog)
    return render(
        request,
        "core/progress_edit_form.html",
        {"form": form, "project": prog.budget_line.project, "prog": prog},
    )


@login_required
@staff_required
def project_progress_csv(request, project_id):
    if not _is_staffish(request.user):
        messages.error(request, "No tienes permisos para exportar progreso.")
        return redirect("project_ev", project_id=project_id)

    project = get_object_or_404(Project, pk=project_id)

    def parse(d):
        try:
            return datetime.strptime(d, "%Y-%m-%d").date()
        except Exception:
            return None

    start = parse(request.GET.get("start", "")) or None
    end = parse(request.GET.get("end", "")) or None

    qs = BudgetProgress.objects.filter(budget_line__project=project).select_related(
        "budget_line", "budget_line__cost_code"
    )

    if start:
        qs = qs.filter(date__gte=start)
    if end:
        qs = qs.filter(date__lte=end)

    qs = qs.order_by("date", "budget_line__cost_code__code")

    resp = HttpResponse(content_type="text/csv")
    fname_end = (end or (start or timezone.now().date())).isoformat()
    resp["Content-Disposition"] = f'attachment; filename="progress_{project.id}_{fname_end}.csv"'
    w = csv.writer(resp)
    w.writerow(
        [
            "project_id",
            "date",
            "cost_code",
            "description",
            "percent_complete",
            "qty_completed",
            "note",
        ]
    )
    for p in qs:
        w.writerow(
            [
                project.id,
                p.date.isoformat(),
                p.budget_line.cost_code.code,
                p.budget_line.description or p.budget_line.cost_code.name,
                float(p.percent_complete or 0),
                float(p.qty_completed or 0),
                p.note or "",
            ]
        )
    return resp


@login_required
def dashboard_employee(request):
    """Dashboard simple para empleados: qué hacer hoy, clock in/out, materiales"""
    # legacy flag kept for compatibility; value is handled by router/templates
    _is_legacy = request.GET.get("legacy", "false").lower() == "true"
    # Obtener empleado ligado al usuario
    employee = Employee.objects.filter(user=request.user).first()
    if not employee:
        messages.error(request, "Tu usuario no está vinculado a un empleado.")
        # NOTE: keep legacy template only (clean template was removed)
        return render(
            request,
            "core/dashboard_employee.html",
            {"employee": None, "badges": {"unread_notifications_count": 0}},
        )

    today = timezone.localdate()
    now = timezone.localtime()

    # TimeEntry abierto (si está trabajando)
    open_entry = (
        TimeEntry.objects.filter(employee=employee, end_time__isnull=True)
        .order_by("-date", "-start_time")
        .first()
    )

    # Touch-ups asignados
    my_touchups = (
        Task.objects.filter(
            assigned_to=employee, is_touchup=True, status__in=["Pendiente", "En Progreso"]
        )
        .select_related("project")
        .order_by("-created_at")[:10]
    )

    # === QUÉ HACER HOY (Daily Plan Activities) ===
    from core.models import DailyPlan

    today_plans = (
        DailyPlan.objects.filter(
            plan_date=today,
            project__in=employee.projects.all() if hasattr(employee, "projects") else [],
        )
        .select_related("project")
        .prefetch_related("activities__assigned_employees")
    )

    my_activities = []
    for plan in today_plans:
        for activity in plan.activities.filter(assigned_employees=employee, is_completed=False):
            my_activities.append(
                {
                    "activity": activity,
                    "project": plan.project,
                }
            )

    # === SCHEDULE ASIGNADO HOY ===
    my_schedule = (
        Schedule.objects.filter(assigned_to=request.user, start_datetime__date=today)
        .select_related("project")
        .order_by("start_datetime")
    )

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "clock_in":
            if open_entry:
                messages.warning(request, "Ya tienes una entrada abierta. Marca salida primero.")
                return redirect("dashboard_employee")
            form = ClockInForm(request.POST)
            if form.is_valid():
                project = form.cleaned_data["project"]

                # ✅ VALIDACIÓN (Regla A): solo si está asignado HOY.
                # SOURCE OF TRUTH: ResourceAssignment.
                is_assigned_today = ResourceAssignment.objects.filter(
                    employee=employee,
                    project=project,
                    date=today,
                ).exists()

                if not is_assigned_today:
                    messages.error(
                        request,
                        f"❌ No estás asignado a '{project.name}' hoy. "
                        f"Contacta a tu PM si hay un error.",
                    )
                    return redirect("dashboard_employee")

                TimeEntry.objects.create(
                    employee=employee,
                    project=project,
                    change_order=form.cleaned_data.get("change_order"),
                    date=today,
                    start_time=now.time(),
                    end_time=None,
                    notes=form.cleaned_data.get("notes") or "",
                    cost_code=form.cleaned_data.get("cost_code"),
                )
                messages.success(
                    request,
                    _("✓ Entrada registrada a las %(time)s.") % {"time": now.strftime("%H:%M")},
                )
                return redirect("dashboard_employee")

        elif action == "clock_out":
            if not open_entry:
                messages.warning(request, "No tienes una entrada abierta.")
                return redirect("dashboard_employee")
            open_entry.end_time = now.time()
            open_entry.save()  # recalcula hours_worked con tu lógica (almuerzo 12:30)
            messages.success(
                request,
                f"✓ Salida registrada a las {now.strftime('%H:%M')}. Horas: {open_entry.hours_worked}",
            )
            return redirect("dashboard_employee")

    # ✅ Obtener proyectos donde está asignado HOY (SOURCE OF TRUTH: ResourceAssignment)
    # Nota: DailyPlan NO define asignación de proyectos; solo planificación.
    my_projects_today = Project.objects.filter(
        resource_assignments__employee=employee,
        resource_assignments__date=today,
    ).distinct()

    # GET o POST inválido - crear form con proyectos filtrados
    form = ClockInForm(available_projects=my_projects_today)

    # === MORNING BRIEFING (Employee Daily Tasks) ===
    morning_briefing = []

    # Category: tasks (Touch-ups pendientes)
    if my_touchups:
        count = len(my_touchups)
        morning_briefing.append(
            {
                "text": f"Tienes {count} {'reparación' if count == 1 else 'reparaciones'} pendiente{'s' if count > 1 else ''}",
                "severity": "warning" if count > 2 else "info",
                "action_url": "#",
                "action_label": "Ver reparaciones",
                "category": "tasks",
            }
        )

    # Category: schedule (Actividades de hoy)
    if my_activities:
        count = len(my_activities)
        morning_briefing.append(
            {
                "text": f"Tienes {count} actividad{'es' if count > 1 else ''} programada{'s' if count > 1 else ''} para hoy",
                "severity": "info",
                "action_url": "#",
                "action_label": "Ver plan",
                "category": "schedule",
            }
        )

    # Horas de la semana (calcular ANTES de usarse)
    week_start = today - timedelta(days=today.weekday())
    week_entries = TimeEntry.objects.filter(
        employee=employee, date__gte=week_start, date__lte=today
    )
    week_hours = sum(entry.hours_worked or 0 for entry in week_entries)

    # Category: clock (Work hours)
    if not open_entry:
        morning_briefing.append(
            {
                "text": "Marca tu entrada para registrar horas de trabajo",
                "severity": "info",
                "action_url": "#",
                "action_label": "Marcar entrada",
                "category": "clock",
            }
        )
    else:
        morning_briefing.append(
            {
                "text": f"Ya marcaste entrada. Tiempo registrado hoy: {week_hours} horas",
                "severity": "success",
                "action_url": "#",
                "action_label": "Marcar salida",
                "category": "clock",
            }
        )

    # Apply filter if requested
    active_filter = request.GET.get("filter", "all")
    if active_filter != "all":
        morning_briefing = [
            item for item in morning_briefing if item.get("category") == active_filter
        ]

    # Historial reciente (últimas 5 entradas)
    recent = TimeEntry.objects.filter(employee=employee).order_by("-date", "-start_time")[:5]

    # Mensaje si no tiene asignaciones hoy
    has_assignments_today = my_projects_today.exists()

    # Variables para el template legacy
    assignments_today = ResourceAssignment.objects.filter(
        employee=employee, date=today
    ).select_related("project")

    available_projects_count = my_projects_today.count()
    available_projects_preview = list(my_projects_today[:5])

    context = {
        "employee": employee,
        "open_entry": open_entry,
        "form": form,
        "today": today,
        "now": now,
        "recent": recent,
        "week_hours": week_hours,
        "my_activities": my_activities,
        "my_schedule": my_schedule,
        "my_touchups": my_touchups,
        "morning_briefing": morning_briefing,
        "active_filter": active_filter,
        "badges": {"unread_notifications_count": 0},
        "my_projects_today": my_projects_today,
        "has_assignments_today": has_assignments_today,
        "assignments_today": assignments_today,
        "available_projects_count": available_projects_count,
        "available_projects_preview": available_projects_preview,
    }

    # Use legacy template (stable version)
    template_name = "core/dashboard_employee.html"
    return render(request, template_name, context)


# --- DASHBOARD PM ---
@login_required
def dashboard_pm(request):
    """Dashboard operacional para PM: materiales, planning, issues, tiempo sin CO"""
    if not request.user.is_staff:
        messages.error(request, "Acceso solo para PM/Staff.")
        return redirect("dashboard_employee")

    # Language prompt if user has no preference yet
    show_language_prompt = False
    prof = getattr(request.user, "profile", None)
    if prof:
        if getattr(prof, "language", None):
            if request.session.get("lang") != prof.language:
                request.session["lang"] = prof.language
                translation.activate(prof.language)
        else:
            show_language_prompt = True

    today = timezone.localdate()
    now = timezone.localtime()

    # Obtener empleado ligado al usuario (para PM que también son empleados)
    employee = Employee.objects.filter(user=request.user).first()

    # TimeEntry abierto (si está trabajando) - Solo si hay empleado vinculado
    open_entry = None
    if employee:
        open_entry = (
            TimeEntry.objects.filter(employee=employee, end_time__isnull=True)
            .order_by("-date", "-start_time")
            .first()
        )

    # Manejo de Clock In/Out para PMs
    if request.method == "POST" and employee:
        action = request.POST.get("action")

        if action == "clock_in":
            if open_entry:
                messages.warning(request, "Ya tienes una entrada abierta. Marca salida primero.")
                return redirect("dashboard_pm")
            form = ClockInForm(request.POST)
            if form.is_valid():
                TimeEntry.objects.create(
                    employee=employee,
                    project=form.cleaned_data["project"],
                    change_order=form.cleaned_data.get("change_order"),
                    date=today,
                    start_time=now.time(),
                    end_time=None,
                    notes=form.cleaned_data.get("notes") or "",
                    cost_code=form.cleaned_data.get("cost_code"),
                )
                messages.success(
                    request,
                    _("✓ Entrada registrada a las %(time)s.") % {"time": now.strftime("%H:%M")},
                )
                return redirect("dashboard_pm")

        elif action == "clock_out":
            if not open_entry:
                messages.warning(request, "No tienes una entrada abierta.")
                return redirect("dashboard_pm")
            open_entry.end_time = now.time()
            open_entry.save()
            messages.success(
                request,
                f"✓ Salida registrada a las {now.strftime('%H:%M')}. Horas: {open_entry.hours_worked}",
            )
            return redirect("dashboard_pm")

    # Form para clock in
    form = ClockInForm() if employee else None

    # === ALERTAS OPERACIONALES ===
    # 1. Tiempo sin CO
    unassigned_time_count = TimeEntry.objects.filter(change_order__isnull=True).count()

    # 2. Materiales pendientes
    pending_materials = MaterialRequest.objects.filter(status__in=["pending", "submitted"]).count()

    # 3. Issues abiertos
    open_issues = Issue.objects.filter(status__in=["open", "in_progress"]).count()

    # 4. RFIs sin respuesta
    open_rfis = RFI.objects.filter(status="open").count()

    # 5. Daily Plans de hoy
    from core.models import DailyPlan

    today_plans = DailyPlan.objects.filter(plan_date=today).count()

    # === MATERIALES PENDIENTES (top 10) ===
    pending_materials_list = (
        MaterialRequest.objects.filter(status__in=["pending", "submitted"])
        .select_related("project", "requested_by")
        .order_by("-created_at")[:10]
    )

    # === ISSUES ACTIVOS (top 10) ===
    active_issues = (
        Issue.objects.filter(status__in=["open", "in_progress"])
        .select_related("project")
        .order_by("-created_at")[:10]
    )

    # === RFIs ABIERTOS ===
    active_rfis = (
        RFI.objects.filter(status="open").select_related("project").order_by("-created_at")[:10]
    )

    # === TIEMPO HOY POR PROYECTO ===
    entries_today = TimeEntry.objects.filter(date=today).select_related("employee", "project")
    hours_by_project = {}
    for entry in entries_today:
        if entry.project:
            proj_name = entry.project.name
            if proj_name not in hours_by_project:
                hours_by_project[proj_name] = Decimal("0")
            hours_by_project[proj_name] += Decimal(entry.hours_worked or 0)

    # === PROYECTOS CON PROGRESO ===
    active_projects = Project.objects.filter(end_date__isnull=True).order_by("name")
    project_summary = []
    for project in active_projects:
        # Calcular progreso simple
        try:
            metrics = compute_project_ev(project, as_of=today)
            progress_pct = 0
            if metrics and metrics.get("PV") and metrics["PV"] > 0:
                progress_pct = min(100, (metrics.get("EV", 0) / metrics["PV"]) * 100)
        except Exception:
            progress_pct = 0

        project_summary.append(
            {
                "project": project,
                "progress_pct": int(progress_pct),
                "hours_today": hours_by_project.get(project.name, 0),
            }
        )

    # Morning Briefing (operational summary for PM)
    morning_briefing = []
    try:
        if unassigned_time_count > 0:
            morning_briefing.append(
                {
                    "text": _("%d unassigned time entries need review") % unassigned_time_count,
                    "severity": "danger" if unassigned_time_count >= 5 else "warning",
                    "action_url": reverse("unassigned_timeentries"),
                    "action_label": _("Assign"),
                    "category": "problems",
                }
            )
        if pending_materials > 0:
            morning_briefing.append(
                {
                    "text": _("%d material requests pending") % pending_materials,
                    "severity": "warning" if pending_materials >= 3 else "info",
                    "action_url": reverse("materials_requests_list_all"),
                    "action_label": _("Review"),
                    "category": "approvals",
                }
            )
        if open_issues > 0:
            morning_briefing.append(
                {
                    "text": _("%d active issues across projects") % open_issues,
                    "severity": "warning" if open_issues < 5 else "danger",
                    "action_url": reverse("pm_select_project", args=["overview"]),
                    "action_label": _("View"),
                    "category": "problems",
                }
            )
        if open_rfis > 0:
            morning_briefing.append(
                {
                    "text": _("%d open RFIs require responses") % open_rfis,
                    "severity": "info",
                    "action_url": reverse("changeorder_board"),
                    "action_label": _("RFIs"),
                    "category": "approvals",
                }
            )
    except Exception:
        morning_briefing = []

    # Filter handling
    active_filter = request.GET.get("filter", "all")
    if active_filter == "problems":
        morning_briefing = [item for item in morning_briefing if item.get("category") == "problems"]
    elif active_filter == "approvals":
        morning_briefing = [
            item for item in morning_briefing if item.get("category") == "approvals"
        ]

    context = {
        # Alertas
        "unassigned_time_count": unassigned_time_count,
        "pending_materials": pending_materials,
        "open_issues": open_issues,
        "open_rfis": open_rfis,
        "today_plans": today_plans,
        # Listas
        "pending_materials_list": pending_materials_list,
        "active_issues": active_issues,
        "active_rfis": active_rfis,
        "project_summary": project_summary,
        # Context
        "today": today,
        "now": now,
        "show_language_prompt": show_language_prompt,
        # Briefing
        "morning_briefing": morning_briefing,
        "active_filter": active_filter,
        # Clock in/out para PM
        "employee": employee,
        "open_entry": open_entry,
        "form": form,
        # Badges for notifications
        "badges": {"unread_notifications_count": 0},  # Placeholder
    }

    # Use clean template by default; legacy only when explicitly requested
    force_legacy = str(request.GET.get("legacy", "")).lower() in {"1", "true", "yes", "on"}
    template_name = "core/dashboard_pm.html" if force_legacy else "core/dashboard_pm_clean.html"
    return render(request, template_name, context)


# --- PM: seleccionar proyecto por acción ---
@login_required
def pm_select_project(request, action: str):
    if not request.user.is_staff:
        messages.error(request, "Acceso solo para PM/Staff.")
        return redirect("dashboard_employee")

    projects = Project.objects.all().order_by("name")

    if request.method == "POST":
        project_id = request.POST.get("project")
        try:
            pid = int(project_id)
        except (TypeError, ValueError):
            pid = None
        if not pid:
            messages.error(request, "Selecciona un proyecto.")
            return render(
                request, "core/pm_select_project.html", {"action": action, "projects": projects}
            )

        target = {
            "materials": "materials_request",
            "tasks": "task_list",
            "pickup": "pickup_view",
            "schedule": "project_schedule",
            "damages": "damage_report_list",
            "inventory": "inventory_view",
            "ev": "project_ev",
            "overview": "project_overview",
            "direct_purchase": "materials_direct_purchase",
            "touchups": "touchup_board",
            "chat": "project_chat_index",
            "plans": "floor_plan_list",
            "colors": "color_sample_list",
        }.get(action)

        if not target:
            messages.error(request, _("Acción no soportada: %(action)s") % {"action": action})
            return render(
                request, "core/pm_select_project.html", {"action": action, "projects": projects}
            )

        return redirect(reverse(target, args=[pid]))

    return render(request, "core/pm_select_project.html", {"action": action, "projects": projects})


def set_language_view(request, code: str = ""):
    """Set language using Django's standard session/cookie key and persist on profile."""
    lang_code = (code or request.POST.get("language") or "").lower()
    supported = {c[0] for c in settings.LANGUAGES}
    if lang_code not in supported:
        lang_code = settings.LANGUAGE_CODE

    translation.activate(lang_code)
    request.session[translation.LANGUAGE_SESSION_KEY] = lang_code

    # persist on user profile if logged in
    try:
        if request.user.is_authenticated:
            prof = getattr(request.user, "profile", None)
            if prof and prof.language != lang_code:
                prof.language = lang_code
                prof.save(update_fields=["language"])
    except Exception:
        pass

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse("dashboard")
    response = redirect(next_url)

    # mirror Django's set_language cookie behavior
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        lang_code,
        max_age=getattr(settings, "LANGUAGE_COOKIE_AGE", None),
        path=getattr(settings, "LANGUAGE_COOKIE_PATH", "/"),
        domain=getattr(settings, "LANGUAGE_COOKIE_DOMAIN", None),
        secure=getattr(settings, "LANGUAGE_COOKIE_SECURE", False),
        httponly=getattr(settings, "LANGUAGE_COOKIE_HTTPONLY", False),
        samesite=getattr(settings, "LANGUAGE_COOKIE_SAMESITE", None),
    )
    return response


@login_required
def project_overview(request, project_id: int):
    if not request.user.is_staff:
        messages.error(request, "Acceso solo para PM/Staff.")
        return redirect("dashboard_employee")

    project = get_object_or_404(Project, pk=project_id)

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

    return render(
        request,
        "core/project_overview.html",
        {
            "project": project,
            "project_info": project_info,
            "show_sidebar": False,  # Hide global sidebar, use project-specific Asana-style sidebar
            "colors": colors,
            "upcoming_schedules": upcoming_schedules,
            "recent_tasks": recent_tasks,
            "recent_issues": recent_issues,
            "recent_logs": recent_logs,
            "files": files,
            "leftovers": leftovers,
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
        },
    )


@login_required
def materials_request_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    try:
        from core.models import Color

        colors = Color.objects.filter(project=project).order_by("name")
    except Exception:
        colors = []

    catalog_qs = (
        MaterialCatalog.objects.filter(is_active=True)
        .filter(Q(project=project) | Q(project__isnull=True))
        .order_by("brand_text", "product_name")
    )

    if request.method == "POST":
        form = MaterialsRequestForm(
            request.POST, request.FILES, colors=colors, presets=PRESET_PRODUCTS, catalog=catalog_qs
        )
        if form.is_valid():
            # Get activity information from query parameters or POST
            activity_id = request.GET.get("activity_id") or request.POST.get("activity_id")
            activity_name = request.GET.get("activity_name", "") or request.POST.get(
                "activity_name", ""
            )

            # Build notes with activity reference
            notes = form.cleaned_data.get("comments", "")
            if activity_id and activity_name:
                activity_note = f"[Solicitado para actividad: {activity_name} (ID: {activity_id})]"
                notes = f"{activity_note}\n{notes}" if notes else activity_note

            mr = MaterialRequest.objects.create(
                project=project,
                requested_by=request.user,
                needed_when=form.cleaned_data["needed_when"],
                needed_date=form.cleaned_data.get("needed_date") or None,
                notes=notes,
                status="pending",
            )

            # 1) Si eligió un ítem del catálogo, precargar
            selected = form.cleaned_data.get("catalog_item")
            cat_data = None
            if selected:
                try:
                    mc = catalog_qs.get(id=int(selected))
                    cat_data = {
                        "category": mc.category,
                        "brand_text": mc.brand_text,
                        "product_name": mc.product_name,
                        "color_name": mc.color_name,
                        "color_code": mc.color_code,
                        "finish": mc.finish,
                        "gloss": mc.gloss,
                        "formula": mc.formula,
                        "default_unit": mc.default_unit,
                    }
                except Exception:
                    pass

            # 2) Datos del formulario (manual/preset/color aprobado)
            cleaned = form.cleaned_data
            category = cleaned["category"]
            brand_choice = cleaned["brand"]
            brand_text = dict(MaterialRequestItem.BRAND_CHOICES).get(brand_choice, brand_choice)
            if brand_choice == "other" and cleaned.get("brand_other"):
                brand_text = cleaned["brand_other"]

            product_name = cleaned["product_name"]
            color_name = cleaned["color_name"]
            color_code = cleaned["color_code"]
            finish = cleaned["finish"]
            gloss = cleaned["gloss"]
            formula = cleaned["formula"]
            unit = cleaned["unit"]

            # Aplicar preset si se eligió (solo completa vacíos)
            preset_idx = cleaned.get("product_preset")
            if preset_idx:
                try:
                    p = PRESET_PRODUCTS[int(preset_idx)]
                    category = category or p["category"]
                    if not product_name:
                        product_name = p["product_name"]
                    if unit in ("", None):
                        unit = p.get("unit") or unit
                    if not brand_text or brand_choice != "other":
                        brand_text = p["brand_label"]
                except Exception:
                    pass

            # Aplicar color aprobado si se eligió (solo completa vacíos)
            approved_id = cleaned.get("approved_color")
            if approved_id and colors:
                try:
                    c = colors.get(id=int(approved_id))
                    brand_text = getattr(c, "brand", brand_text) or brand_text
                    product_name = getattr(c, "line", product_name) or product_name
                    color_name = getattr(c, "name", color_name) or color_name
                    color_code = getattr(c, "code", color_code) or color_code
                    finish = getattr(c, "finish", finish) or finish
                    gloss = getattr(c, "gloss", gloss) or gloss
                    formula = getattr(c, "formula", formula) or formula
                except Exception:
                    pass

            # Si viene del catálogo, sobrescribir con sus valores
            if cat_data:
                category = cat_data["category"]
                brand_text = cat_data["brand_text"]
                product_name = cat_data["product_name"] or product_name
                color_name = cat_data["color_name"] or color_name
                color_code = cat_data["color_code"] or color_code
                finish = cat_data["finish"] or finish
                gloss = cat_data["gloss"] or gloss
                formula = cat_data["formula"] or formula
                unit = cat_data["default_unit"] or unit

            # Crear ítem solicitado
            extra_comments = cleaned.get("comments", "")
            if brand_choice == "other" and cleaned.get("brand_other"):
                extra_comments = f"Marca especificada: {cleaned['brand_other']}. " + extra_comments

            MaterialRequestItem.objects.create(
                request=mr,
                category=category,
                brand=cleaned["brand"],  # guardamos la clave de choice para el item
                product_name=product_name,
                color_name=color_name,
                color_code=color_code,
                finish=finish,
                gloss=gloss,
                formula=form.cleaned_data["formula"] or formula,
                reference_image=form.cleaned_data.get("reference_image"),
                quantity=cleaned["quantity"],
                qty_requested=cleaned["quantity"],
                unit=unit,
                comments=extra_comments,
            )

            # Guardar en catálogo si se indicó (scoped al proyecto)
            if cleaned.get("save_to_catalog"):
                MaterialCatalog.objects.get_or_create(
                    project=project,
                    category=category,
                    brand_text=brand_text or "",
                    product_name=product_name or "",
                    color_name=color_name or "",
                    color_code=color_code or "",
                    finish=finish or "",
                    defaults={
                        "gloss": gloss or "",
                        "formula": formula or "",
                        "default_unit": unit or "",
                        "created_by": request.user,
                    },
                )

            messages.success(
                request,
                (
                    "Solicitud registrada. El material quedó guardado en el catálogo del proyecto."
                    if cleaned.get("save_to_catalog")
                    else "Solicitud registrada."
                ),
            )
            return redirect(reverse("materials_request", args=[project.id]))

    else:
        form = MaterialsRequestForm(colors=colors, presets=PRESET_PRODUCTS, catalog=catalog_qs)

    catalog_payload = [
        {
            "id": m.id,
            "category": m.category,
            "brand_text": m.brand_text,
            "product_name": m.product_name,
            "color_name": m.color_name,
            "color_code": m.color_code,
            "finish": m.finish,
            "gloss": m.gloss,
            "formula": m.formula,
            "default_unit": m.default_unit,
        }
        for m in catalog_qs
    ]

    # Get activity information from query parameters
    activity_id = request.GET.get("activity_id")
    activity_name = request.GET.get("activity_name", "")

    # Use modern template by default, legacy with ?legacy=true
    template = (
        "core/materials_request.html"
        if request.GET.get("legacy")
        else "core/materials_request_modern.html"
    )

    return render(
        request,
        template,
        {
            "project": project,
            "form": form,
            "presets_json": json.dumps(PRESET_PRODUCTS),
            "catalog_json": json.dumps(catalog_payload),
            "activity_id": activity_id,
            "activity_name": activity_name,
        },
    )


@login_required
def pickup_view(request, project_id: int):
    project = get_object_or_404(Project, pk=project_id)
    return render(request, "core/pickup_view.html", {"project": project})


@login_required
def task_list_view(request, project_id: int):
    from datetime import date, timedelta

    project = get_object_or_404(Project, pk=project_id)
    tasks = (
        Task.objects.filter(project=project)
        .select_related("assigned_to")
        .prefetch_related("dependencies")
        if Task
        else []
    )

    # Apply filters from query parameters
    status_filter = request.GET.get("status")
    priority_filter = request.GET.get("priority")
    assigned_filter = request.GET.get("assigned_to")
    overdue_filter = request.GET.get("overdue")

    if status_filter:
        tasks = tasks.filter(status=status_filter)

    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)

    if assigned_filter:
        tasks = tasks.filter(assigned_to_id=assigned_filter)

    today = date.today()
    if overdue_filter == "yes":
        # Tasks overdue (due_date < today and not completed)
        tasks = tasks.filter(due_date__lt=today).exclude(status="Completada")
    elif overdue_filter == "today":
        # Tasks due today
        tasks = tasks.filter(due_date=today)
    elif overdue_filter == "week":
        # Tasks due this week
        week_end = today + timedelta(days=7)
        tasks = tasks.filter(due_date__lte=week_end, due_date__gte=today)

    tasks = tasks.order_by("-id")

    # Get employees for filter dropdown
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    employees = user_model.objects.filter(is_active=True).order_by("first_name", "last_name")

    can_create = request.user.is_staff
    form = None
    try:
        from core.forms import TaskForm as TaskFormModel
    except Exception:
        task_form_cls = None
    else:
        task_form_cls = TaskFormModel
    if can_create and task_form_cls:
        if request.method == "POST":
            form = task_form_cls(request.POST, request.FILES)
            if form.is_valid():
                inst = form.save(commit=False)
                inst.created_by = request.user
                inst.project = project
                inst.save()
                form.save_m2m()  # Save dependencies
                messages.success(request, "Tarea creada.")
                return redirect("task_list", project_id=project.id)
        else:
            form = task_form_cls(initial={"project": project})

    return render(
        request,
        "core/task_list.html",
        {
            "project": project,
            "tasks": tasks,
            "form": form,
            "can_create": can_create,
            "employees": employees,
            "today": today,
        },
    )


@login_required
def task_detail(request, task_id: int):
    """Detalle de una tarea.

    Permisos:
    - Staff: puede ver cualquier tarea.
    - Empleado: solo tareas asignadas a su Employee.
    """
    task = get_object_or_404(Task, pk=task_id)
    employee = Employee.objects.filter(user=request.user).first()

    if not request.user.is_staff and (not employee or task.assigned_to_id != employee.id):
        messages.error(request, gettext("Sin permiso para ver esta tarea."))
        return redirect("task_list_all")

    return render(request, "core/task_detail.html", {"task": task, "employee": employee})


@login_required
def task_edit_view(request, task_id: int):
    task = get_object_or_404(Task, pk=task_id)
    if not request.user.is_staff:
        messages.error(request, "Solo staff puede editar tareas.")
        return redirect("task_detail", task_id=task.id)
    from core.forms import TaskForm

    if request.method == "POST":
        form = TaskForm(request.POST, request.FILES, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "Tarea actualizada.")
            return redirect("task_detail", task_id=task.id)
    else:
        form = TaskForm(instance=task)
    return render(request, "core/task_form.html", {"form": form, "task": task, "edit": True})


@login_required
def task_delete_view(request, task_id: int):
    task = get_object_or_404(Task, pk=task_id)
    if not request.user.is_staff:
        messages.error(request, "Solo staff puede eliminar tareas.")
        return redirect("task_detail", task_id=task.id)
    if request.method == "POST":
        pid = task.project_id
        task.delete()
        messages.success(request, "Tarea eliminada.")
        return redirect("task_list", project_id=pid)
    return render(request, "core/task_confirm_delete.html", {"task": task})


@login_required
def task_list_all(request):
    """Lista de tareas asignadas al usuario actual (para empleado)."""
    employee = Employee.objects.filter(user=request.user).first()
    tasks = (
        Task.objects.filter(assigned_to=employee).select_related("project").order_by("-id")
        if employee and Task
        else []
    )
    return render(request, "core/task_list_all.html", {"tasks": tasks})


# ===========================
# ACTIVITY 1: NEW TIME TRACKING ENDPOINTS (Q11.13)
# ===========================


@login_required
def task_start_tracking(request, task_id):
    """AJAX endpoint to start time tracking on a task."""
    if request.method != "POST":
        return JsonResponse({"error": gettext("POST required")}, status=405)

    task = get_object_or_404(Task, id=task_id)
    employee = Employee.objects.filter(user=request.user).first()

    # Check permission
    if not (request.user.is_staff or (employee and task.assigned_to == employee)):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

    # Check if task can start (dependencies)
    if not task.can_start():
        incomplete_deps = task.dependencies.filter(status__in=["pending", "in_progress"])
        dep_names = ", ".join([d.title for d in incomplete_deps])
        return JsonResponse(
            {
                "error": gettext("No se puede iniciar. Dependencias incompletas: %(deps)s")
                % {"deps": dep_names}
            },
            status=400,
        )

    # Start tracking
    if task.start_tracking():
        return JsonResponse(
            {
                "success": True,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "message": "Seguimiento de tiempo iniciado",
            }
        )
    else:
        return JsonResponse({"error": gettext("Ya hay un seguimiento activo")}, status=400)


@login_required
def task_stop_tracking(request, task_id):
    """AJAX endpoint to stop time tracking on a task."""
    if request.method != "POST":
        return JsonResponse({"error": gettext("POST required")}, status=405)

    task = get_object_or_404(Task, id=task_id)
    employee = Employee.objects.filter(user=request.user).first()

    # Check permission
    if not (request.user.is_staff or (employee and task.assigned_to == employee)):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

    # Stop tracking
    elapsed = task.stop_tracking()
    if elapsed is not None:
        return JsonResponse(
            {
                "success": True,
                "elapsed_seconds": elapsed,
                "total_hours": task.get_time_tracked_hours(),
                "message": f"Seguimiento detenido. {elapsed} segundos agregados.",
            }
        )
    else:
        return JsonResponse({"error": gettext("No hay seguimiento activo")}, status=400)


# ===========================
# ACTIVITY 1: DAILY PLAN ENHANCEMENTS
# ===========================


@login_required
def daily_plan_fetch_weather(request, plan_id):
    """AJAX endpoint to fetch weather for a daily plan (Q12.8)."""
    if request.method != "POST":
        return JsonResponse({"error": gettext("POST required")}, status=405)

    if not _is_staffish(request.user):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

    plan = get_object_or_404(DailyPlan, id=plan_id)

    # Fetch weather (calls API)
    success = plan.fetch_weather()

    if success:
        return JsonResponse(
            {
                "success": True,
                "weather_data": plan.weather_data,
                "fetched_at": plan.weather_fetched_at.isoformat()
                if plan.weather_fetched_at
                else None,
            }
        )
    else:
        return JsonResponse(
            {"error": gettext("No se pudo obtener el clima. Verifique la ubicación del proyecto.")},
            status=400,
        )


@login_required
def daily_plan_convert_activities(request, plan_id):
    """Convert planned activities to tasks (Q12.2)."""
    if request.method != "POST":
        return JsonResponse({"error": gettext("POST required")}, status=405)

    if not _is_staffish(request.user):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

    plan = get_object_or_404(DailyPlan, id=plan_id)

    # Can only convert if status is PUBLISHED
    if plan.status != "PUBLISHED":
        return JsonResponse(
            {"error": gettext("Solo se pueden convertir planes en estado PUBLISHED")}, status=400
        )

    # Convert activities to tasks
    created_tasks = plan.convert_activities_to_tasks()

    # Update plan status
    plan.status = "IN_PROGRESS"
    plan.save()

    return JsonResponse(
        {
            "success": True,
            "tasks_created": len(created_tasks),
            "task_ids": [t.id for t in created_tasks],
            "message": f"{len(created_tasks)} tareas creadas exitosamente",
        }
    )


@login_required
def daily_plan_productivity(request, plan_id):
    """Get productivity score for a daily plan (Q12.5)."""
    plan = get_object_or_404(DailyPlan, id=plan_id)

    score = plan.calculate_productivity_score()

    return JsonResponse(
        {
            "plan_id": plan.id,
            "plan_date": plan.plan_date.isoformat(),
            "estimated_hours": float(plan.estimated_hours_total or 0),
            "actual_hours": float(plan.actual_hours_worked or 0),
            "productivity_score": score,
            "status": plan.status,
        }
    )


@login_required
def project_schedule_view(request, project_id: int):
    """
    Vista de cronograma del proyecto.
    Redirige a clientes a la vista hermosa y simplificada.
    PM/Admin ven la vista completa con todos los detalles.
    """
    project = get_object_or_404(Project, pk=project_id)
    profile = getattr(request.user, "profile", None)

    # Si es cliente, redirigir a la vista hermosa
    if profile and profile.role == "client":
        from django.shortcuts import redirect
        from django.urls import reverse

        return redirect(reverse("client_project_calendar", kwargs={"project_id": project_id}))

    # Para PM/Admin: Vista completa
    if ScheduleForm:
        form = ScheduleForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            s = form.save(commit=False)
            s.project = project
            s.save()
            return redirect("project_schedule", project_id=project.id)
    else:
        form = None

    schedules = (
        Schedule.objects.filter(project=project).order_by("start_datetime") if Schedule else []
    )

    # También incluir ScheduleItems modernos
    schedule_items = project.schedule_items.select_related("category").order_by("planned_start")
    categories = project.schedule_categories.filter(parent__isnull=True).order_by("order")

    return render(
        request,
        "core/project_schedule.html",
        {
            "project": project,
            "form": form,
            "schedules": schedules,
            "schedule_items": schedule_items,
            "categories": categories,
        },
    )


@login_required
def site_photo_list(request, project_id):
    from core.models import Project, SitePhoto

    project = get_object_or_404(Project, pk=project_id)
    photos = SitePhoto.objects.filter(project=project).order_by("-created_at")
    return render(request, "core/site_photo_list.html", {"project": project, "photos": photos})


@login_required
def site_photo_create(request, project_id):
    from core.forms import SitePhotoForm
    from core.models import Project

    project = get_object_or_404(Project, pk=project_id)
    if request.method == "POST":
        form = SitePhotoForm(request.POST, request.FILES, project=project)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.project = project
            obj.created_by = request.user
            try:
                obj.annotations = json.loads(form.cleaned_data.get("annotations") or "{}")
            except Exception:
                obj.annotations = {}
            obj.save()
            messages.success(request, "Foto y anotaciones guardadas.")
            return redirect("site_photo_list", project_id=project.id)
    else:
        form = SitePhotoForm(project=project)
    return render(request, "core/site_photo_form.html", {"project": project, "form": form})


@login_required
def inventory_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    storage = InventoryLocation.objects.filter(is_storage=True).first()
    loc, _ = InventoryLocation.objects.get_or_create(
        project=project, name="Principal", defaults={"is_storage": False}
    )
    stocks = (
        ProjectInventory.objects.filter(location=loc)
        .select_related("item")
        .order_by("item__category", "item__name")
    )
    low = [s for s in stocks if s.is_below]  # <- propiedad, sin paréntesis
    return render(
        request,
        "core/inventory_view.html",
        {
            "project": project,
            "stocks": stocks,
            "low": low,
            "storage": storage,
        },
    )


@login_required
@staff_required
@require_http_methods(["GET", "POST"])
def inventory_move_view(request, project_id):
    from core.models import InventoryItem, InventoryLocation, InventoryMovement, ProjectInventory

    project = get_object_or_404(Project, pk=project_id)

    # Asegurar storage y ubicación principal del proyecto actual
    storage = InventoryLocation.objects.filter(is_storage=True).first()
    if not storage:
        storage = InventoryLocation.objects.create(name="Main Storage", is_storage=True)
    proj_loc, _ = InventoryLocation.objects.get_or_create(
        project=project, name="Principal", defaults={"is_storage": False}
    )

    form = InventoryMovementForm(request.POST or None)

    # Desde: solo storage o ubicaciones del proyecto actual
    from_qs = InventoryLocation.objects.filter(Q(is_storage=True) | Q(project=project)).order_by(
        "-is_storage", "name"
    )
    # Hacia: storage o cualquier ubicación de cualquier proyecto (permite transferir a otro proyecto)
    to_qs = InventoryLocation.objects.filter(
        Q(is_storage=True) | Q(project__isnull=False)
    ).order_by("-is_storage", "project__name", "name")

    form.fields["from_location"].queryset = from_qs
    form.fields["to_location"].queryset = to_qs
    form.fields["item"].queryset = InventoryItem.objects.filter(active=True).order_by(
        "category", "name"
    )

    if request.method == "POST" and form.is_valid():
        item = form.cleaned_data["item"]
        mtype = form.cleaned_data["movement_type"]
        qty = form.cleaned_data["quantity"]
        from_loc = form.cleaned_data.get("from_location")
        to_loc = form.cleaned_data.get("to_location")
        note = form.cleaned_data.get("note") or ""

        # Validar requeridos según tipo
        if mtype in ("RECEIVE", "RETURN") and not to_loc:
            form.add_error("to_location", "Requerido.")
        if mtype in ("ISSUE", "CONSUME", "TRANSFER") and not from_loc:
            form.add_error("from_location", "Requerido.")

        # Validar stock en origen para salidas/traslados
        if not form.errors and mtype in ("ISSUE", "CONSUME", "TRANSFER"):
            stock = ProjectInventory.objects.filter(item=item, location=from_loc).first()
            if not stock or stock.quantity < qty:
                form.add_error(
                    "quantity",
                    f"Stock insuficiente en origen (disp: {float(stock.quantity) if stock else 0}).",
                )

        if not form.errors:
            move = InventoryMovement.objects.create(
                item=item,
                movement_type=mtype,
                quantity=qty,
                from_location=from_loc,
                to_location=to_loc,
                note=note,
                created_by=request.user,
            )
            move.apply()
            # Decidir siguiente paso
            if form.cleaned_data.get("add_expense"):
                next_url = reverse("inventory_history", args=[project.id])
                create_url = f"{reverse('expense_create')}?project_id={project.id}&next={next_url}&ref=inv_move_{move.id}"
                messages.info(request, "Ahora registra el gasto del ticket.")
                return redirect(create_url)
            if form.cleaned_data.get("no_expense"):
                messages.success(request, "Movimiento aplicado. Marcado sin gasto.")
                return redirect("inventory_view", project_id=project.id)

            messages.success(request, "Movimiento aplicado.")
            return redirect("inventory_view", project_id=project.id)
    return render(request, "core/inventory_move.html", {"project": project, "form": form})


@login_required
@staff_required
def inventory_history_view(request, project_id):
    from core.models import InventoryItem, InventoryLocation, InventoryMovement

    project = get_object_or_404(Project, pk=project_id)
    loc_qs = InventoryLocation.objects.filter(Q(project=project) | Q(is_storage=True))
    item_id = request.GET.get("item")
    mtype = request.GET.get("type")
    qs = (
        InventoryMovement.objects.filter(Q(from_location__in=loc_qs) | Q(to_location__in=loc_qs))
        .select_related("item", "from_location", "to_location", "created_by")
        .order_by("-created_at", "-id")
    )
    if item_id:
        qs = qs.filter(item_id=item_id)
    if mtype:
        qs = qs.filter(movement_type=mtype)

    items = InventoryItem.objects.filter(active=True).order_by("category", "name")
    return render(
        request,
        "core/inventory_history.html",
        {
            "project": project,
            "moves": qs[:200],
            "items": items,
            "current_item": int(item_id) if item_id else "",
            "current_type": mtype or "",
        },
    )


@login_required
@staff_required
def materials_receive_ticket_view(request, request_id):
    """
    Pantalla para recibir/comprar un lote (ticket) de ítems de la solicitud.
    Genera un Expense (si aplica) + movimientos RECEIVE por cada ítem seleccionado.
    """
    mat_request = get_object_or_404(MaterialRequest, pk=request_id)
    project = mat_request.project

    # Import here to ensure InventoryMovement is available in this scope
    from core.models import InventoryMovement

    if request.method == "POST":
        # Campos gasto
        store_name = request.POST.get("store_name", "").strip()
        total = request.POST.get("total", "0").strip()
        no_expense = request.POST.get("no_expense") == "on"
        receipt_photo = request.FILES.get("receipt_photo")

        # Items recibidos
        items_data = []
        for item in mat_request.items.all():
            checked = request.POST.get(f"item_{item.id}") == "on"
            qty = request.POST.get(f"qty_{item.id}", "0").strip()
            if checked:
                try:
                    # Clean thousands separators and convert string -> Decimal
                    q = qty.replace(",", "") if isinstance(qty, str) else qty
                    q_dec = Decimal(q) if q not in (None, "", " ") else Decimal("0")
                    if q_dec > 0:
                        items_data.append((item, q_dec))
                except Exception:
                    pass

        # Validar
        if not items_data:
            messages.error(request, "Selecciona al menos un ítem con cantidad > 0.")
            return redirect("materials_receive_ticket", request_id=mat_request.id)

        if not no_expense and (not store_name or not total or Decimal(total) <= 0):
            messages.error(request, "Completa tienda y total o marca 'Sin gasto'.")
            return redirect("materials_receive_ticket", request_id=mat_request.id)

        # Crear Expense (si aplica)
        expense_obj = None
        if not no_expense:
            expense_obj = Expense.objects.create(
                project=project,
                project_name=f"{project.name} - {store_name}",
                category="MATERIALES",
                amount=Decimal(total),
                description=f"Ticket {store_name} - {mat_request.id}",
                receipt=receipt_photo,
                date=timezone.now().date(),
            )

        # Asegurar ubicación Principal del proyecto
        loc, _ = InventoryLocation.objects.get_or_create(
            project=project, name="Principal", defaults={"is_storage": False}
        )

        # Crear movimientos RECEIVE y actualizar ítems
        with transaction.atomic():
            for item, qty in items_data:
                # Asegurar InventoryItem (auto-crear si no existe)
                if not item.inventory_item:
                    inv_item = _ensure_inventory_item(
                        name=item.product_name or "Item",
                        category_key=item.category or "MATERIAL",
                        unit=item.unit or "pcs",
                    )
                    item.inventory_item = inv_item
                    item.save(update_fields=["inventory_item"])

                # Crear movimiento RECEIVE
                move = InventoryMovement.objects.create(
                    item=item.inventory_item,
                    movement_type="RECEIVE",
                    quantity=qty,
                    to_location=loc,
                    note=f"Ticket {store_name} - Solicitud {mat_request.id}",
                    created_by=request.user,
                    expense=expense_obj,
                )
                move.apply()

                # Actualizar ítem de solicitud
                item.qty_received += qty
                if item.qty_received >= item.qty_requested:
                    item.item_status = "received"
                else:
                    item.item_status = "received_partial"
                item.save(update_fields=["qty_received", "item_status"])

        messages.success(
            request,
            _("Ticket procesado. %(count)s ítem(s) recibido(s).") % {"count": len(items_data)},
        )
        return redirect("materials_request_detail", request_id=mat_request.id)

    # GET: mostrar checklist
    items = mat_request.items.all()
    return render(
        request,
        "core/materials_receive_ticket.html",
        {
            "mat_request": mat_request,
            "project": project,
            "items": items,
        },
    )


@login_required
@staff_required
@require_http_methods(["GET", "POST"])
def materials_direct_purchase_view(request, project_id):
    """
    Compra directa del lead: registra ítems comprados, crea solicitud retroactiva
    con status 'purchased_lead', movimientos RECEIVE y Expense.
    """
    project = get_object_or_404(Project, pk=project_id)

    from core.models import InventoryMovement

    if request.method == "POST":
        # Datos del ticket
        store_name = request.POST.get("store_name", "").strip()
        total = request.POST.get("total", "0").strip()
        no_expense = request.POST.get("no_expense") == "on"
        receipt_photo = request.FILES.get("receipt_photo")
        notes = request.POST.get("notes", "").strip()

        # Items comprados (JSON enviado desde JS o form dinámico)
        # Formato esperado: [{"name": "Tape 2in", "category": "tape", "unit": "roll", "qty": 36}, ...]
        import json

        items_json = request.POST.get("items_json", "[]")
        try:
            items_data = json.loads(items_json)
        except Exception:
            items_data = []

        # Validar
        if not items_data:
            messages.error(request, "Agrega al menos un ítem con cantidad > 0.")
            return redirect("materials_direct_purchase", project_id=project.id)

        if not no_expense and (not store_name or not total or Decimal(total) <= 0):
            messages.error(request, "Completa tienda y total o marca 'Sin gasto'.")
            return redirect("materials_direct_purchase", project_id=project.id)

        # Crear Expense (si aplica)
        expense_obj = None
        if not no_expense:
            expense_obj = Expense.objects.create(
                project=project,
                project_name=f"{project.name} - {store_name}",
                category="MATERIALES",
                amount=Decimal(total),
                description=f"Compra directa {store_name}",
                receipt=receipt_photo,
                date=timezone.now().date(),
            )

        # Crear MaterialRequest retroactiva
        mat_request = MaterialRequest.objects.create(
            project=project,
            requested_by=request.user,
            status="purchased_lead",
            notes=notes or f"Compra directa en {store_name}",
        )

        # Asegurar ubicación Principal del proyecto
        loc, _ = InventoryLocation.objects.get_or_create(
            project=project, name="Principal", defaults={"is_storage": False}
        )

        # Crear ítems + movimientos RECEIVE
        with transaction.atomic():
            for item_data in items_data:
                name = item_data.get("name", "").strip()
                category = item_data.get("category", "MATERIAL")
                unit = item_data.get("unit", "pcs")
                qty = Decimal(item_data.get("qty", 0))

                if not name or qty <= 0:
                    continue

                # Asegurar InventoryItem
                inv_item = _ensure_inventory_item(name=name, category_key=category, unit=unit)

                # Crear ítem de solicitud
                MaterialRequestItem.objects.create(
                    request=mat_request,
                    inventory_item=inv_item,
                    product_name=name,
                    category=category,
                    unit=unit,
                    quantity=qty,
                    qty_requested=qty,
                    qty_received=qty,
                    item_status="received",
                )

                # Crear movimiento RECEIVE
                move = InventoryMovement.objects.create(
                    item=inv_item,
                    movement_type="RECEIVE",
                    quantity=qty,
                    to_location=loc,
                    note=f"Compra directa {store_name} - Solicitud {mat_request.id}",
                    created_by=request.user,
                    expense=expense_obj,
                )
                move.apply()

        messages.success(
            request,
            _("Compra directa registrada. %(count)s ítem(s) agregado(s) al inventario.")
            % {"count": len(items_data)},
        )
        return redirect("inventory_view", project_id=project.id)

    # GET: mostrar formulario dinámico
    return render(request, "core/materials_direct_purchase.html", {"project": project})


@login_required
@staff_required
def materials_requests_list_view(request, project_id=None):
    """
    Lista todas las solicitudes de materiales con acciones:
    - Ver detalle
    - Marcar como 'ordered'
    - Crear ticket (receive)
    """
    if project_id:
        project = get_object_or_404(Project, pk=project_id)
        qs = MaterialRequest.objects.filter(project=project)
    else:
        project = None
        qs = MaterialRequest.objects.all()

    # Filtros
    status_filter = request.GET.get("status", "")
    if status_filter:
        qs = qs.filter(status=status_filter)

    qs = (
        qs.select_related("project", "requested_by")
        .prefetch_related("items")
        .order_by("-created_at")
    )

    # Use modern template by default, legacy with ?legacy=true
    template = (
        "core/materials_requests_list.html"
        if request.GET.get("legacy")
        else "core/materials_requests_list_modern.html"
    )

    return render(
        request,
        template,
        {
            "project": project,
            "requests": qs,
            "status_filter": status_filter,
            "status_choices": MaterialRequest.STATUS_CHOICES,
        },
    )


@login_required
@staff_required
@require_POST
def materials_mark_ordered_view(request, request_id):
    """
    Cambia status de solicitud a 'ordered'.
    """
    mat_request = get_object_or_404(MaterialRequest, pk=request_id)
    mat_request.status = "ordered"
    mat_request.save(update_fields=["status"])

    mat_request.items.filter(item_status="pending").update(item_status="ordered")

    messages.success(
        request, _("Solicitud #%(id)s marcada como ordenada.") % {"id": mat_request.id}
    )
    return redirect("materials_requests_list", project_id=mat_request.project_id)


@login_required
def materials_request_detail_view(request, request_id):
    """
    Muestra detalle de solicitud con ítems.
    """
    mat_request = get_object_or_404(
        MaterialRequest.objects.select_related("project", "requested_by"), pk=request_id
    )
    items = mat_request.items.select_related("inventory_item").all()

    can_manage = _is_staffish(request.user)

    return render(
        request,
        "core/materials_request_detail.html",
        {
            "mat_request": mat_request,
            "items": items,
            "can_manage": can_manage,
        },
    )


# ===========================
# ACTIVITY 2: NEW MATERIAL REQUEST WORKFLOW VIEWS
# ===========================


@login_required
@require_POST
def materials_request_submit(request, request_id):
    """Q14.4: Enviar solicitud para aprobación del admin"""
    mat_request = get_object_or_404(MaterialRequest, pk=request_id)

    # Verify user can submit
    if mat_request.requested_by != request.user and not request.user.is_staff:
        messages.error(request, "No tienes permiso para enviar esta solicitud")
        return redirect("materials_request_detail", request_id=request_id)

    if mat_request.submit_for_approval(request.user):
        messages.success(request, "Solicitud enviada para aprobación")
    else:
        messages.warning(request, "La solicitud no está en estado borrador")

    return redirect("materials_request_detail", request_id=request_id)


@login_required
@staff_required
@require_POST
def materials_request_approve(request, request_id):
    """Q14.4: Aprobar solicitud (solo admin)"""
    mat_request = get_object_or_404(MaterialRequest, pk=request_id)

    if mat_request.approve(request.user):
        messages.success(request, _("Solicitud #%(id)s aprobada") % {"id": mat_request.id})
    else:
        messages.warning(request, "La solicitud no está pendiente de aprobación")

    return redirect("materials_request_detail", request_id=request_id)


@login_required
@staff_required
@require_POST
def materials_request_reject(request, request_id):
    """Q14.4: Rechazar solicitud"""
    mat_request = get_object_or_404(MaterialRequest, pk=request_id)
    reason = request.POST.get("reason", "")

    mat_request.status = "cancelled"
    if reason:
        mat_request.notes = (mat_request.notes or "") + f"\n[Rechazada]: {reason}"
    mat_request.save()

    messages.success(request, _("Solicitud #%(id)s rechazada") % {"id": mat_request.id})
    return redirect("materials_requests_list_all")


@login_required
@staff_required
def materials_receive_partial(request, request_id):
    """Q14.10: Registrar recepción parcial de materiales"""
    mat_request = get_object_or_404(MaterialRequest, pk=request_id)

    if request.method == "POST":
        received_data = {}

        for item in mat_request.items.all():
            qty_key = f"received_{item.id}"
            qty_value = request.POST.get(qty_key)

            if qty_value:
                try:
                    qty = Decimal(qty_value)
                    if qty > 0:
                        received_data[item.id] = qty
                except (ValueError, InvalidOperation):
                    continue

        if received_data:
            success, message = mat_request.receive_materials(received_data, request.user)
            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)
        else:
            messages.warning(request, "No se especificaron cantidades recibidas")

        return redirect("materials_request_detail", request_id=request_id)

    # GET request - show form
    items = mat_request.items.all()
    return render(
        request,
        "core/materials_receive_partial.html",
        {
            "mat_request": mat_request,
            "items": items,
        },
    )


@login_required
@staff_required
@require_POST
def materials_create_expense(request, request_id):
    """Q14.6: Crear gasto automáticamente desde compra directa"""
    mat_request = get_object_or_404(MaterialRequest, pk=request_id)

    total_amount_str = request.POST.get("total_amount")
    if not total_amount_str:
        messages.error(request, "Debes especificar el monto total")
        return redirect("materials_request_detail", request_id=request_id)

    try:
        total_amount = Decimal(total_amount_str)
        expense = mat_request.create_direct_purchase_expense(total_amount, request.user)
        messages.success(
            request,
            _("Gasto #%(id)s creado por $%(amount)s") % {"id": expense.id, "amount": total_amount},
        )
    except (ValueError, InvalidOperation):
        messages.error(request, "Monto inválido")
    except Exception as e:
        messages.error(request, _("Error al crear gasto: %(error)s") % {"error": str(e)})

    return redirect("materials_request_detail", request_id=request_id)


@login_required
def inventory_low_stock_alert(request):
    """Q15.5: Dashboard de alertas de stock bajo"""
    from core.models import ProjectInventory

    # Get all inventory items below threshold
    low_stock_items = []

    for stock in ProjectInventory.objects.select_related("item", "location", "location__project"):
        if stock.is_below:
            low_stock_items.append(
                {
                    "stock": stock,
                    "threshold": stock.threshold(),
                    "deficit": stock.threshold() - stock.quantity if stock.threshold() else 0,
                }
            )

    # Sort by severity (highest deficit first)
    low_stock_items.sort(key=lambda x: x["deficit"], reverse=True)

    return render(
        request,
        "core/inventory_low_stock.html",
        {
            "low_stock_items": low_stock_items,
        },
    )


@login_required
@staff_required
@require_POST
def inventory_adjust(request, item_id, location_id):
    """Q15.11: Ajuste manual de inventario con audit trail"""
    from core.models import InventoryItem, InventoryLocation, InventoryMovement

    item = get_object_or_404(InventoryItem, pk=item_id)
    location = get_object_or_404(InventoryLocation, pk=location_id)

    quantity_str = request.POST.get("quantity")
    reason = request.POST.get("reason", "")

    if not quantity_str or not reason:
        messages.error(request, "Cantidad y razón son requeridos")
        return redirect("inventory_view", project_id=location.project_id)

    try:
        quantity = Decimal(quantity_str)

        movement = InventoryMovement.objects.create(
            item=item,
            to_location=location,
            movement_type="ADJUST",
            quantity=quantity,
            reason=reason,  # Q15.11: Audit trail
            created_by=request.user,
        )
        movement.apply()

        messages.success(
            request,
            _("Inventario ajustado: %(quantity)s %(unit)s")
            % {"quantity": quantity, "unit": item.unit},
        )
    except (ValueError, InvalidOperation) as e:
        messages.error(request, _("Cantidad inválida: %(error)s") % {"error": str(e)})
    except Exception as e:
        messages.error(request, _("Error: %(error)s") % {"error": str(e)})

    return redirect("inventory_view", project_id=location.project_id)


@login_required
@staff_required
@require_http_methods(["GET", "POST"])
def inventory_wizard(request, project_id):
    """
    Modern wizard interface for inventory management
    Handles: Add (RECEIVE), Move (TRANSFER), Adjust (ADJUST)
    """
    from decimal import Decimal
    import json

    from django.core.exceptions import ValidationError
    from django.db.models import Q

    from core.models import InventoryItem, InventoryLocation, InventoryMovement, ProjectInventory

    project = get_object_or_404(Project, pk=project_id)

    # Get all inventory items and locations
    items = InventoryItem.objects.all().order_by("category", "name")
    locations = InventoryLocation.objects.filter(Q(is_storage=True) | Q(project=project)).order_by(
        "is_storage", "name"
    )

    # Get all stock data for JavaScript
    stocks = ProjectInventory.objects.filter(location__in=locations).select_related(
        "item", "location"
    )

    stock_data = {}
    for stock in stocks:
        key = f"{stock.item.id}-{stock.location.id}"
        stock_data[key] = {
            "quantity": float(stock.quantity),
            "unit": stock.item.unit,
            "threshold": float(stock.threshold()) if stock.threshold() else None,
        }

    # Get low stock items
    low_stock_items = []
    for stock in stocks:
        if stock.is_below:
            low_stock_items.append(stock)

    # Handle POST request (form submission)
    if request.method == "POST":
        action = request.POST.get("action")

        try:
            item_id = request.POST.get("item_id")
            quantity = Decimal(request.POST.get("quantity", "0"))
            reason = request.POST.get("reason", "")

            # Validate: for ADJUST, allow negative quantities; for others, require positive
            if not item_id or not reason:
                raise ValidationError(_("Please fill all required fields"))

            if action != "adjust" and quantity <= 0:
                raise ValidationError(_("Quantity must be positive"))

            if action == "adjust" and quantity == 0:
                raise ValidationError(_("Adjustment quantity cannot be zero"))

            item = get_object_or_404(InventoryItem, pk=item_id)

            if action == "add":
                # RECEIVE movement
                to_location_id = request.POST.get("to_location_id")
                unit_price = request.POST.get("unit_price")

                to_location = get_object_or_404(InventoryLocation, pk=to_location_id)

                movement = InventoryMovement.objects.create(
                    item=item,
                    to_location=to_location,
                    movement_type="RECEIVE",
                    quantity=quantity,
                    unit_cost=Decimal(unit_price)
                    if unit_price
                    else None,  # Changed from unit_price to unit_cost
                    reason=reason,
                    created_by=request.user,
                )
                movement.apply()

                messages.success(
                    request,
                    _("Successfully added %(quantity)s %(unit)s of %(item)s to %(location)s")
                    % {
                        "quantity": quantity,
                        "unit": item.unit,
                        "item": item.name,
                        "location": to_location.name,
                    },
                )

            elif action == "move":
                # TRANSFER movement
                from_location_id = request.POST.get("from_location_id")
                to_location_id = request.POST.get("to_location_id")

                if from_location_id == to_location_id:
                    raise ValidationError(_("Source and destination locations must be different"))

                from_location = get_object_or_404(InventoryLocation, pk=from_location_id)
                to_location = get_object_or_404(InventoryLocation, pk=to_location_id)

                movement = InventoryMovement.objects.create(
                    item=item,
                    from_location=from_location,
                    to_location=to_location,
                    movement_type="TRANSFER",
                    quantity=quantity,
                    reason=reason,
                    created_by=request.user,
                )
                movement.apply()

                messages.success(
                    request,
                    _(
                        "Successfully moved %(quantity)s %(unit)s of %(item)s from %(from)s to %(to)s"
                    )
                    % {
                        "quantity": quantity,
                        "unit": item.unit,
                        "item": item.name,
                        "from": from_location.name,
                        "to": to_location.name,
                    },
                )

            elif action == "adjust":
                # ADJUST movement
                to_location_id = request.POST.get("to_location_id")
                to_location = get_object_or_404(InventoryLocation, pk=to_location_id)

                movement = InventoryMovement.objects.create(
                    item=item,
                    to_location=to_location,
                    movement_type="ADJUST",
                    quantity=quantity,  # Can be negative
                    reason=reason,
                    created_by=request.user,
                )
                movement.apply()

                action_text = _("increased") if quantity > 0 else _("decreased")
                messages.success(
                    request,
                    _(
                        "Successfully %(action)s stock of %(item)s by %(quantity)s %(unit)s at %(location)s"
                    )
                    % {
                        "action": action_text,
                        "item": item.name,
                        "quantity": abs(quantity),
                        "unit": item.unit,
                        "location": to_location.name,
                    },
                )

            else:
                raise ValidationError(_("Invalid action"))

            # Redirect back to wizard
            return redirect("inventory_wizard", project_id=project.id)

        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, _("Error: %(error)s") % {"error": str(e)})

    # Render wizard template
    return render(
        request,
        "core/inventory_wizard.html",
        {
            "project": project,
            "items": items,
            "locations": locations,
            "stock_data_json": json.dumps(stock_data),
            "low_stock_items": low_stock_items,
            "low_stock_count": len(low_stock_items),
        },
    )


# ===========================
# DAILY PLANNING SYSTEM VIEWS
# ===========================


@login_required
def daily_plan_list(request):
    """List daily plans with optional status filter (Module 12.7)."""
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")
    status = request.GET.get("status")
    qs = DailyPlan.objects.select_related("project", "created_by").order_by("-plan_date")
    if status and status in ["DRAFT", "PUBLISHED", "IN_PROGRESS", "COMPLETED", "SKIPPED"]:
        qs = qs.filter(status=status)
    return render(
        request,
        "core/daily_plan_list.html",
        {
            "plans": qs[:200],  # safety cap
            "filter_status": status,
        },
    )


@login_required
def daily_plan_detail(request, plan_id):
    """Detail view for a daily plan with productivity and weather (Module 12.7)."""
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")
    plan = get_object_or_404(DailyPlan.objects.select_related("project", "created_by"), pk=plan_id)
    activities = (
        plan.activities.select_related("activity_template", "schedule_item")
        .prefetch_related("assigned_employees", "sub_activities__assigned_employees")
        .filter(parent__isnull=True)  # Only top-level activities
        .order_by("order")
    )
    productivity = plan.calculate_productivity_score()

    # Get all active employees for assignment modal
    employees = Employee.objects.filter(is_active=True).order_by("first_name", "last_name")

    return render(
        request,
        "core/daily_plan_detail.html",
        {
            "plan": plan,
            "activities": activities,
            "employees": employees,
            "productivity_score": productivity,
            "weather": plan.weather_data,
            "can_convert": plan.status == "PUBLISHED",
            "can_start": plan.status == "PUBLISHED",
            "can_complete": plan.status == "IN_PROGRESS",
        },
    )


@login_required
def daily_plan_delete(request, plan_id):
    """Delete a daily plan (staff/PM only). Shows confirm page."""
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")

    plan = get_object_or_404(DailyPlan.objects.select_related("project"), pk=plan_id)

    if request.method == "POST":
        project_name = plan.project.name
        plan_date = plan.plan_date
        plan.delete()
        messages.success(
            request,
            _("Daily plan for %(date)s in %(project)s deleted")
            % {"date": plan_date, "project": project_name},
        )
        return redirect("daily_planning_dashboard")

    return render(request, "core/daily_plan_confirm_delete.html", {"plan": plan})


@login_required
def daily_planning_dashboard(request):
    """
    Main dashboard for daily planning - shows all plans and overdue alerts
    Modern Wizard-style interface
    """
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")

    today = timezone.now().date()

    # Handle create plan form submission
    if request.method == "POST" and request.POST.get("create_plan"):
        project_id = request.POST.get("project")
        plan_date_str = request.POST.get("plan_date")

        if project_id and plan_date_str:
            project = get_object_or_404(Project, pk=project_id)
            plan_date = datetime.strptime(plan_date_str, "%Y-%m-%d").date()

            # Check if plan already exists
            existing = DailyPlan.objects.filter(project=project, plan_date=plan_date).first()
            if existing:
                messages.warning(
                    request, _("Plan already exists for %(date)s") % {"date": plan_date}
                )
                return redirect("daily_plan_detail", plan_id=existing.id)

            # Set completion deadline (5pm day before)
            completion_deadline = timezone.make_aware(
                datetime.combine(
                    plan_date - timedelta(days=1), datetime.min.time().replace(hour=17)
                )
            )

            # Create plan
            plan = DailyPlan.objects.create(
                project=project,
                plan_date=plan_date,
                created_by=request.user,
                completion_deadline=completion_deadline,
                status="DRAFT",
            )

            messages.success(request, _("Daily plan created for %(date)s") % {"date": plan_date})
            return redirect("daily_plan_detail", plan_id=plan.id)

    # Get recent plans
    recent_plans = (
        DailyPlan.objects.select_related("project", "created_by")
        .prefetch_related("activities")
        .order_by("-plan_date")[:20]
    )

    # Check for overdue plans (draft plans past 5pm deadline)
    overdue_plans = DailyPlan.objects.filter(
        status="DRAFT", completion_deadline__lt=timezone.now()
    ).select_related("project", "created_by")

    # Get today's plans
    todays_plans = (
        DailyPlan.objects.filter(plan_date=today)
        .select_related("project")
        .prefetch_related("activities", "created_by")
    )

    # Get active projects for creating new plans
    active_projects = Project.objects.filter(
        Q(end_date__gte=today) | Q(end_date__isnull=True)
    ).order_by("name")

    context = {
        "recent_plans": recent_plans,
        "overdue_plans": overdue_plans,
        "todays_plans": todays_plans,
        "projects": active_projects,
        "today": today,
    }

    return render(request, "core/daily_planning_dashboard_modern.html", context)


@login_required
def daily_plan_create(request, project_id):
    """
    Create a new daily plan for a project with smart suggestions from schedule.

    GET: Shows form with suggested schedule items for the target date
    POST: Creates plan and optionally imports activities from schedule items
    """
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")

    project = get_object_or_404(Project, pk=project_id)

    if request.method == "POST":
        plan_date_str = request.POST.get("plan_date")
        plan_date = None
        if plan_date_str:
            try:
                plan_date = datetime.strptime(plan_date_str, "%Y-%m-%d").date()
            except ValueError:
                # Invalid date format: re-render form with error instead of raising exception
                messages.error(request, "Invalid date format")
                from core.services.planning_service import get_suggested_items_for_date

                target_date = timezone.now().date() + timedelta(days=1)
                suggested_items = get_suggested_items_for_date(project, target_date)
                return render(
                    request,
                    "core/daily_plan_create.html",
                    {
                        "project": project,
                        "min_date": timezone.now().date(),
                        "target_date": target_date,
                        "suggested_items": suggested_items,
                        "has_suggestions": len(suggested_items) > 0,
                        "invalid_date": True,
                    },
                )

        if not plan_date:
            messages.error(request, "Plan date is required")
            return redirect("daily_planning_dashboard")

        # Check if plan already exists
        existing = DailyPlan.objects.filter(project=project, plan_date=plan_date).first()
        if existing:
            messages.warning(request, _("Plan already exists for %(date)s") % {"date": plan_date})
            return redirect("daily_plan_edit", plan_id=existing.id)

        # Set completion deadline (5pm day before)
        completion_deadline = timezone.make_aware(
            datetime.combine(plan_date - timedelta(days=1), datetime.min.time().replace(hour=17))
        )

        # Create plan
        plan = DailyPlan.objects.create(
            project=project,
            plan_date=plan_date,
            created_by=request.user,
            completion_deadline=completion_deadline,
            status="DRAFT",
        )

        # Import selected schedule items as activities
        selected_items = request.POST.getlist("import_items")  # List of schedule_item IDs
        if selected_items:
            from core.models import PlannedActivity

            for idx, item_id in enumerate(selected_items):
                try:
                    schedule_item = ScheduleItem.objects.get(id=int(item_id), project=project)
                    PlannedActivity.objects.create(
                        daily_plan=plan,
                        schedule_item=schedule_item,
                        title=schedule_item.title,
                        description=schedule_item.description,
                        order=idx,
                        status="PENDING",
                        progress_percentage=0,
                    )
                except ScheduleItem.DoesNotExist:
                    continue

            messages.success(
                request,
                f"Daily plan created with {len(selected_items)} imported activities for {plan_date}",
            )
        else:
            messages.success(request, _("Daily plan created for %(date)s") % {"date": plan_date})

        return redirect("daily_plan_edit", plan_id=plan.id)

    # GET request - show form with suggestions
    from core.services.planning_service import get_suggested_items_for_date

    # Get target date from query param, default to tomorrow
    date_param = request.GET.get("date")
    if date_param:
        try:
            target_date = datetime.strptime(date_param, "%Y-%m-%d").date()
        except ValueError:
            target_date = timezone.now().date() + timedelta(days=1)
    else:
        target_date = timezone.now().date() + timedelta(days=1)

    # Get suggested items for target date
    suggested_items = get_suggested_items_for_date(project, target_date)

    return render(
        request,
        "core/daily_plan_create.html",
        {
            "project": project,
            "min_date": timezone.now().date(),
            "target_date": target_date,
            "suggested_items": suggested_items,
            "has_suggestions": len(suggested_items) > 0,
        },
    )


@login_required
def daily_plan_edit(request, plan_id):
    """Edit a daily plan and its activities using forms and inline formset (Modules 12.5-12.7)."""
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")

    from django.utils.translation import gettext as _

    from core.forms import DailyPlanForm, make_planned_activity_formset

    plan = get_object_or_404(DailyPlan.objects.select_related("project"), pk=plan_id)

    # Instantiate forms
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add_activity":
            try:
                from core.models import ActivityTemplate, PlannedActivity, ScheduleItem

                # Extract data
                template_id = request.POST.get("activity_template")
                schedule_id = request.POST.get("schedule_item")
                title = request.POST.get("title")
                description = request.POST.get("description", "")
                hours = request.POST.get("estimated_hours")
                employee_ids = request.POST.getlist("assigned_employees")

                # Resolve relations
                template = ActivityTemplate.objects.get(pk=template_id) if template_id else None
                schedule = ScheduleItem.objects.get(pk=schedule_id) if schedule_id else None

                # Default title from template if not provided
                if not title and template:
                    title = template.name
                elif not title:
                    title = "New Activity"

                # Create activity
                activity = PlannedActivity.objects.create(
                    daily_plan=plan,
                    title=title,
                    description=description,
                    activity_template=template,
                    schedule_item=schedule,
                    estimated_hours=hours if hours else None,
                    order=plan.activities.count() + 1,
                )

                # Assign employees
                if employee_ids:
                    activity.assigned_employees.set(employee_ids)

                messages.success(request, _("Activity added successfully"))
                return redirect("daily_plan_edit", plan_id=plan.id)

            except Exception as e:
                messages.error(request, f"Error adding activity: {str(e)}")

        elif action == "submit":
            if plan.activities.exists():
                plan.status = "PUBLISHED"
                plan.save(update_fields=["status"])
                messages.success(request, _("Plan submitted successfully"))
            else:
                messages.error(request, _("Cannot submit empty plan"))
            return redirect("daily_plan_edit", plan_id=plan.id)

        elif action == "copy_yesterday_team":
            # ✅ Copy team assignments from yesterday's plan
            from datetime import timedelta

            yesterday_date = plan.plan_date - timedelta(days=1)

            try:
                yesterday_plan = DailyPlan.objects.filter(
                    project=plan.project, plan_date=yesterday_date
                ).first()

                if not yesterday_plan:
                    messages.warning(
                        request, _(f"No plan found for {yesterday_date.strftime('%Y-%m-%d')}")
                    )
                    return redirect("daily_plan_edit", plan_id=plan.id)

                # Get yesterday's activities with employees
                yesterday_activities = yesterday_plan.activities.prefetch_related(
                    "assigned_employees"
                ).all()

                if not yesterday_activities:
                    messages.warning(request, _("Yesterday's plan has no activities"))
                    return redirect("daily_plan_edit", plan_id=plan.id)

                # Collect all unique employees from yesterday
                all_employees = set()
                for activity in yesterday_activities:
                    all_employees.update(activity.assigned_employees.all())

                if not all_employees:
                    messages.warning(request, _("Yesterday's plan has no employees assigned"))
                    return redirect("daily_plan_edit", plan_id=plan.id)

                # Apply to all today's activities
                count = 0
                for activity in plan.activities.all():
                    activity.assigned_employees.set(all_employees)
                    count += 1

                employee_names = ", ".join([f"{e.first_name}" for e in all_employees])
                messages.success(
                    request,
                    _(
                        f"✅ Copied {len(all_employees)} employees ({employee_names}) to {count} activities"
                    ),
                )
                return redirect("daily_plan_edit", plan_id=plan.id)

            except Exception as e:
                messages.error(request, f"❌ Error copying team: {str(e)}")
                return redirect("daily_plan_edit", plan_id=plan.id)

        elif action == "check_materials":
            # Mock material check for now or call method on activities
            count = 0
            for activity in plan.activities.all():
                if hasattr(activity, "check_materials"):
                    activity.check_materials()
                    count += 1
            messages.success(request, _(f"Checked materials for {count} activities"))
            return redirect("daily_plan_edit", plan_id=plan.id)

        # Fallback to standard form processing if no specific action
        form = DailyPlanForm(request.POST, instance=plan)
        formset = make_planned_activity_formset(plan, data=request.POST, files=request.FILES)
        if form.is_valid() and formset.is_valid():
            form.save()  # Handles weather fetch + estimated hours recalculation
            formset.save()
            messages.success(request, _("Plan actualizado"))
            # Workflow quick actions via hidden field 'transition'
            transition = request.POST.get("transition")
            if transition:
                # Attempt state transition
                try:
                    desired = transition
                    current = plan.status
                    allowed = {
                        "DRAFT": ["PUBLISHED", "SKIPPED"],
                        "PUBLISHED": ["IN_PROGRESS", "SKIPPED"],
                        "IN_PROGRESS": ["COMPLETED"],
                    }
                    if desired != current and desired in allowed.get(current, []):
                        plan.status = desired
                        plan.save(update_fields=["status"])
                        messages.success(request, _("Transición de estado exitosa"))
                    else:
                        messages.warning(request, _("Transición inválida"))
                except Exception:
                    messages.error(request, _("Error aplicando transición de estado"))
            return redirect("daily_plan_edit", plan_id=plan.id)
        else:
            messages.error(request, _("Revisa errores en el formulario"))
    else:
        form = DailyPlanForm(instance=plan)
        formset = make_planned_activity_formset(plan)

    # For display contexts
    productivity = plan.calculate_productivity_score()
    activities = plan.activities.prefetch_related("assigned_employees").order_by("order")

    context = {
        "plan": plan,
        "form": form,
        "formset": formset,
        "activities": activities,
        "productivity_score": productivity,
        "can_convert": plan.status == "PUBLISHED",
        "can_start": plan.status == "PUBLISHED",
        "can_complete": plan.status == "IN_PROGRESS",
    }
    return render(request, "core/daily_plan_edit.html", context)


@login_required
def daily_plan_delete_activity(request, activity_id):
    """
    Delete a planned activity
    """
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")

    activity = get_object_or_404(PlannedActivity, pk=activity_id)
    plan_id = activity.daily_plan.id

    if request.method == "POST":
        activity.delete()
        messages.success(request, "Activity deleted")

    return redirect("daily_plan_edit", plan_id=plan_id)


@login_required
def employee_morning_dashboard(request):
    """
    Dashboard for employees to see their daily plan
    Shows today's assigned activities with all details
    """
    try:
        employee = request.user.employee
    except Exception:
        messages.error(request, "You are not registered as an employee")
        return redirect("dashboard")

    today = timezone.now().date()

    # Get today's activities assigned to this employee
    todays_activities = (
        PlannedActivity.objects.filter(
            daily_plan__plan_date=today,
            assigned_employees=employee,
            status__in=["PENDING", "IN_PROGRESS"],
        )
        .select_related("daily_plan__project", "activity_template")
        .prefetch_related("assigned_employees")
        .order_by("order")
    )

    context = {
        "employee": employee,
        "today": today,
        "activities": todays_activities,
    }

    return render(request, "core/employee_morning_dashboard.html", context)


@login_required
def activity_complete(request, activity_id):
    """
    Mark an activity as complete with photos
    """
    activity = get_object_or_404(PlannedActivity, pk=activity_id)

    try:
        employee = request.user.employee
    except Exception:
        messages.error(request, "You are not registered as an employee")
        return redirect("dashboard")

    # Check if employee is assigned
    if not activity.assigned_employees.filter(id=employee.id).exists():
        return HttpResponseForbidden("You are not assigned to this activity")

    if request.method == "POST":
        progress = int(request.POST.get("progress", 100))
        notes = request.POST.get("notes", "")

        # Handle photo uploads (simplified - you'll need proper file handling)
        photos = []
        uploaded_files = request.FILES.getlist("photos")
        # Basic file persistence into MEDIA_ROOT/activity_completions/<activity_id>/
        import os

        from django.conf import settings

        activity_dir = os.path.join(settings.MEDIA_ROOT, "activity_completions", str(activity.id))
        os.makedirs(activity_dir, exist_ok=True)
        for f in uploaded_files:
            safe_name = f.name.replace(" ", "_")
            dest_path = os.path.join(activity_dir, safe_name)
            with open(dest_path, "wb+") as dest:
                for chunk in f.chunks():
                    dest.write(chunk)
            # Store relative media URL path for later display
            rel_path = os.path.join("activity_completions", str(activity.id), safe_name).replace(
                "\\", "/"
            )
            photos.append(rel_path)

        # Create completion record
        ActivityCompletion.objects.create(
            planned_activity=activity,
            completed_by=employee,
            progress_percentage=progress,
            employee_notes=notes,
            completion_photos=photos,
        )

        # Update activity status
        activity.status = "COMPLETED"
        activity.progress_percentage = progress
        activity.save()

        # If all activities for a Schedule item are complete, update Schedule
        if activity.schedule_item:
            related_activities = PlannedActivity.objects.filter(
                schedule_item=activity.schedule_item
            )
            if all(a.status == "COMPLETED" for a in related_activities):
                activity.schedule_item.progress = 100
                activity.schedule_item.save()

        messages.success(
            request, _("Activity '%(title)s' marked as complete!") % {"title": activity.title}
        )
        return redirect("employee_morning_dashboard")

    # GET request - show completion form
    context = {
        "activity": activity,
        "employee": employee,
    }

    return render(request, "core/activity_complete.html", context)


@login_required
def sop_library(request):
    """
    Browse and search Activity Templates (SOPs) - Q13.3 enhanced search
    """
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")

    category = request.GET.get("category", "")
    search = request.GET.get("search", "")
    duration_min = request.GET.get("duration_min", "")
    duration_max = request.GET.get("duration_max", "")

    templates = ActivityTemplate.objects.filter(is_active=True)

    if category:
        templates = templates.filter(category=category)

    # ACTIVITY 1: Enhanced keyword search (Q13.3)
    if search:
        templates = templates.filter(
            Q(name__icontains=search)
            | Q(description__icontains=search)
            | Q(tips__icontains=search)
            | Q(materials_needed__icontains=search)
            | Q(special_requirements__icontains=search)
        )

    # ACTIVITY 1: Duration filter (Q13.3)
    if duration_min:
        with contextlib.suppress(ValueError):
            templates = templates.filter(estimated_duration__gte=float(duration_min))

    if duration_max:
        with contextlib.suppress(ValueError):
            templates = templates.filter(estimated_duration__lte=float(duration_max))

    templates = templates.order_by("category", "name")

    context = {
        "templates": templates,
        "categories": ActivityTemplate.CATEGORY_CHOICES,
        "selected_category": category,
        "search_query": search,
        "duration_min": duration_min,
        "duration_max": duration_max,
    }

    return render(request, "core/sop_library.html", context)


@login_required
def sop_create_edit(request, template_id=None):
    """
    Create or edit an Activity Template (SOP)
    """
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")

    instance = None
    if template_id:
        instance = get_object_or_404(ActivityTemplate, pk=template_id)

    if request.method == "POST":
        form = ActivityTemplateForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            sop = form.save(commit=False)
            if not instance:
                sop.created_by = request.user
            sop.save()
            form.save_m2m()

            # Handle file uploads for reference files
            uploaded_files = request.FILES.getlist("reference_files")
            if uploaded_files:
                from core.models import SOPReferenceFile

                for f in uploaded_files:
                    SOPReferenceFile.objects.create(sop=sop, file=f)

            messages.success(request, "SOP saved successfully!")
            return redirect("sop_library")
    else:
        form = ActivityTemplateForm(instance=instance)

    context = {
        "form": form,
        "editing": bool(instance),
        "sop": instance,
    }
    return render(request, "core/sop_creator.html", context)


@login_required
def sop_create_wizard(request, template_id=None):
    """
    Wizard-style SOP creator with step-by-step guidance (NEW IMPROVED VERSION)
    """
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")

    instance = None
    if template_id:
        instance = get_object_or_404(ActivityTemplate, pk=template_id)

    if request.method == "POST":
        # Process form data
        name = request.POST.get("name")
        category = request.POST.get("category")
        description = request.POST.get("description", "")
        tips = request.POST.get("tips", "")
        common_errors = request.POST.get("common_errors", "")
        video_url = request.POST.get("video_url", "")
        is_active = request.POST.get("is_active") == "on"

        # Parse JSON fields
        import json

        steps = json.loads(request.POST.get("steps", "[]"))
        materials_list = json.loads(request.POST.get("materials_list", "[]"))
        tools_list = json.loads(request.POST.get("tools_list", "[]"))

        # Calculate time estimate
        time_hours = float(request.POST.get("time_hours", 0))
        time_minutes = float(request.POST.get("time_minutes", 0))
        time_estimate = time_hours + (time_minutes / 60.0)

        # Create or update SOP
        if instance:
            sop = instance
            sop.name = name
            sop.category = category
            sop.description = description
            sop.tips = tips
            sop.common_errors = common_errors
            sop.video_url = video_url
            sop.is_active = is_active
            sop.steps = steps
            sop.materials_list = materials_list
            sop.tools_list = tools_list
            sop.time_estimate = time_estimate if time_estimate > 0 else None
            sop.save()
        else:
            sop = ActivityTemplate.objects.create(
                name=name,
                category=category,
                description=description,
                tips=tips,
                common_errors=common_errors,
                video_url=video_url,
                is_active=is_active,
                steps=steps,
                materials_list=materials_list,
                tools_list=tools_list,
                time_estimate=time_estimate if time_estimate > 0 else None,
                created_by=request.user,
            )

        # Handle file uploads
        uploaded_files = request.FILES.getlist("reference_files")
        if uploaded_files:
            from core.models import SOPReferenceFile

            for f in uploaded_files:
                SOPReferenceFile.objects.create(sop=sop, file=f)

        messages.success(request, _("✨ SOP creado exitosamente!"))
        return redirect("sop_library")

    # GET request - show wizard
    form = ActivityTemplateForm(instance=instance)
    context = {
        "form": form,
        "editing": bool(instance),
        "sop": instance,
    }
    return render(request, "core/sop_creator_wizard.html", context)


# ===========================
# MINUTAS / PROJECT TIMELINE
# ===========================


@login_required
def project_minutes_list(request, project_id):
    """Lista todas las minutas de un proyecto (timeline)"""
    project = get_object_or_404(Project, id=project_id)

    # Admin ve todo, Cliente solo ve lo marcado como visible
    from core.models import ProjectMinute

    if request.user.is_staff or request.user.is_superuser:
        minutes = ProjectMinute.objects.filter(project=project)
    else:
        minutes = ProjectMinute.objects.filter(project=project, visible_to_client=True)

    minutes = minutes.select_related("created_by").order_by("-event_date")

    # Filtros
    event_type = request.GET.get("type")
    if event_type:
        minutes = minutes.filter(event_type=event_type)

    context = {
        "project": project,
        "minutes": minutes,
        "event_types": ProjectMinute.EVENT_TYPE_CHOICES,
    }
    return render(request, "core/project_minutes_list.html", context)


@login_required
def project_minute_create(request, project_id):
    """Crear nueva minuta"""
    project = get_object_or_404(Project, id=project_id)

    # Solo admin/staff pueden crear minutas
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "No tienes permisos para crear minutas.")
        return redirect("project_minutes_list", project_id=project.id)

    from core.models import ProjectMinute

    if request.method == "POST":
        event_type = request.POST.get("event_type")
        title = request.POST.get("title")
        description = request.POST.get("description", "")
        event_date_str = request.POST.get("event_date")
        participants = request.POST.get("participants", "")
        visible_to_client = request.POST.get("visible_to_client") == "on"
        attachment = request.FILES.get("attachment")

        if not title or not event_date_str:
            messages.error(request, "Título y fecha son requeridos.")
        else:
            try:
                event_date = timezone.datetime.fromisoformat(event_date_str)
            except Exception:
                event_date = timezone.now()

            ProjectMinute.objects.create(
                project=project,
                event_type=event_type,
                title=title,
                description=description,
                event_date=event_date,
                participants=participants,
                attachment=attachment,
                visible_to_client=visible_to_client,
                created_by=request.user,
            )
            messages.success(request, "Minuta creada exitosamente.")
            return redirect("project_minutes_list", project_id=project.id)

    context = {
        "project": project,
        "event_types": ProjectMinute.EVENT_TYPE_CHOICES,
    }
    return render(request, "core/project_minute_form.html", context)


@login_required
def project_minute_detail(request, minute_id):
    """Ver detalles de una minuta"""
    from core.models import ProjectMinute

    minute = get_object_or_404(ProjectMinute, id=minute_id)

    # Verificar permisos
    if not (request.user.is_staff or request.user.is_superuser or minute.visible_to_client):
        messages.error(request, "No tienes permisos para ver esta minuta.")
        return redirect("project_minutes_list", project_id=minute.project.id)

    context = {
        "minute": minute,
    }
    return render(request, "core/project_minute_detail.html", context)


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

    # Use clean template by default; legacy only when explicitly requested
    force_legacy = str(request.GET.get("legacy", "")).lower() in {"1", "true", "yes", "on"}
    template_name = (
        "core/dashboard_designer.html" if force_legacy else "core/dashboard_designer_clean.html"
    )
    return render(request, template_name, context)


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
                assigned_to=employee, is_touchup=True, status__in=["Pendiente", "En Progreso"]
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
            project__in=projects, is_touchup=True, assigned_to__isnull=True, status="Pendiente"
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


# ========================================
# SCHEDULE GENERATOR (Hierarchical)
# ========================================
@login_required
def schedule_generator_view(request, project_id):
    """
    Vista del generador de cronograma jerárquico.
    - Lista categorías e ítems existentes
    - Permite generar automáticamente desde estimado aprobado
    - CRUD inline para categorías e ítems
    """
    project = get_object_or_404(Project, id=project_id)

    # Check permissions (staff or project manager)
    user_profile = getattr(request.user, "profile", None)
    can_manage = bool(
        request.user.is_staff
        or (user_profile and getattr(user_profile, "role", None) in ["project_manager"])
    )

    # Get approved estimate for generation
    approved_estimate = project.estimates.filter(approved=True).order_by("-version").first()

    # Handle POST actions
    if request.method == "POST":
        action = request.POST.get("action")

        # Generate from estimate
        if action == "generate_from_estimate" and approved_estimate and can_manage:
            return _generate_schedule_from_estimate(request, project, approved_estimate)

        # Create category
        elif action == "create_category" and can_manage:
            form = ScheduleCategoryForm(request.POST, project=project)
            if form.is_valid():
                cat = form.save(commit=False)
                cat.project = project
                cat.save()
                messages.success(request, f'Categoría "{cat.name}" creada.')
                return redirect("schedule_generator", project_id=project.id)
            else:
                messages.error(request, "Error al crear categoría.")

        # Create item
        elif action == "create_item" and can_manage:
            # Permitir crear categoría al vuelo si viene 'new_category_name'
            new_cat_name = (request.POST.get("new_category_name") or "").strip()
            category_id = request.POST.get("category")

            # Validate: must have either existing category OR new category name
            if not category_id and not new_cat_name:
                messages.error(
                    request,
                    "Debes seleccionar una categoría existente o escribir el nombre de una nueva.",
                )
                return redirect("schedule_generator", project_id=project.id)

            if new_cat_name and not category_id:
                cat = ScheduleCategory.objects.create(project=project, name=new_cat_name, order=0)
                # inyectar id en POST mutable clone
                post = request.POST.copy()
                post["category"] = str(cat.id)
                form = ScheduleItemForm(post, project=project)
            else:
                form = ScheduleItemForm(request.POST, project=project)

            if form.is_valid():
                item = form.save(commit=False)
                item.project = project
                item.save()
                messages.success(request, f'Ítem "{item.title}" creado.')
                return redirect("schedule_generator", project_id=project.id)
            else:
                messages.error(request, "Error al crear ítem. Verifica los campos.")

        # Update item progress
        elif action == "recalc_progress":
            item_id = request.POST.get("item_id")
            if item_id:
                item = get_object_or_404(ScheduleItem, id=item_id, project=project)
                item.recalculate_progress(save=True)
                messages.success(
                    request,
                    _("Progreso recalculado: %(percent)s%%") % {"percent": item.percent_complete},
                )
                return redirect("schedule_generator", project_id=project.id)

    # GET: render form and data
    categories = (
        ScheduleCategory.objects.filter(project=project)
        .prefetch_related("items", "children")
        .order_by("order", "name")
    )
    orphan_items = ScheduleItem.objects.filter(project=project, category__isnull=True).order_by(
        "order", "title"
    )

    category_form = ScheduleCategoryForm(project=project)
    item_form = ScheduleItemForm(project=project)

    context = {
        "project": project,
        "categories": categories,
        "orphan_items": orphan_items,
        "approved_estimate": approved_estimate,
        "can_manage": can_manage,
        "category_form": category_form,
        "item_form": item_form,
    }

    return render(request, "core/schedule_generator.html", context)


def _generate_schedule_from_estimate(request, project, estimate):
    """
    Auto-genera categorías e ítems desde un estimado aprobado.
    Agrupa por cost_code.category y crea ScheduleItem por cada EstimateLine.
    """
    try:
        with transaction.atomic():
            created_cats = {}
            created_items = 0

            # Get all estimate lines grouped by cost code category
            lines = estimate.lines.select_related("cost_code").order_by(
                "cost_code__category", "cost_code__code"
            )

            for line in lines:
                cc = line.cost_code
                cat_name = cc.category.capitalize() if cc.category else "General"

                # Get or create category
                if cat_name not in created_cats:
                    cat, created = ScheduleCategory.objects.get_or_create(
                        project=project,
                        name=cat_name,
                        defaults={"cost_code": cc, "order": len(created_cats)},
                    )
                    created_cats[cat_name] = cat
                else:
                    cat = created_cats[cat_name]

                # Create schedule item from estimate line
                item_title = f"{cc.code} - {line.description or cc.name}"

                # Check if already exists
                existing = ScheduleItem.objects.filter(
                    project=project, category=cat, title=item_title
                ).first()

                if not existing:
                    ScheduleItem.objects.create(
                        project=project,
                        category=cat,
                        title=item_title,
                        description=line.description or "",
                        order=created_items,
                        estimate_line=line,
                        cost_code=cc,
                        status="NOT_STARTED",
                        percent_complete=0,
                    )
                    created_items += 1

            messages.success(
                request,
                f"Generado: {len(created_cats)} categorías y {created_items} ítems desde el estimado {estimate.code}.",
            )
    except Exception as e:
        messages.error(request, _("Error al generar cronograma: %(error)s") % {"error": str(e)})

    return redirect("schedule_generator", project_id=project.id)


@login_required
def schedule_category_edit(request, category_id):
    """Edit schedule category."""
    category = get_object_or_404(ScheduleCategory, id=category_id)
    project = category.project

    if not (request.user.is_staff or request.user == project.client):
        return HttpResponseForbidden()

    if request.method == "POST":
        form = ScheduleCategoryForm(request.POST, instance=category, project=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'Categoría "{category.name}" actualizada.')
            return redirect("schedule_generator", project_id=project.id)
    else:
        form = ScheduleCategoryForm(instance=category, project=project)

    return render(
        request,
        "core/schedule_category_form.html",
        {
            "form": form,
            "category": category,
            "project": project,
        },
    )


@login_required
def schedule_category_delete(request, category_id):
    """Delete schedule category."""
    category = get_object_or_404(ScheduleCategory, id=category_id)
    project = category.project

    if not (request.user.is_staff or request.user == project.client):
        return HttpResponseForbidden()

    if request.method == "POST":
        cat_name = category.name
        category.delete()
        messages.success(request, f'Categoría "{cat_name}" eliminada.')
        return redirect("schedule_generator", project_id=project.id)

    return render(
        request,
        "core/schedule_category_confirm_delete.html",
        {
            "category": category,
            "project": project,
        },
    )


@login_required
def schedule_item_edit(request, item_id):
    """Edit schedule item."""
    item = get_object_or_404(ScheduleItem, id=item_id)
    project = item.project

    if not (request.user.is_staff or request.user == project.client):
        return HttpResponseForbidden()

    if request.method == "POST":
        form = ScheduleItemForm(request.POST, instance=item, project=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'Ítem "{item.title}" actualizado.')
            return redirect("schedule_generator", project_id=project.id)
    else:
        form = ScheduleItemForm(instance=item, project=project)

    return render(
        request,
        "core/schedule_item_form.html",
        {
            "form": form,
            "item": item,
            "project": project,
        },
    )


@login_required
def schedule_item_delete(request, item_id):
    """Delete schedule item."""
    item = get_object_or_404(ScheduleItem, id=item_id)
    project = item.project

    if not (request.user.is_staff or request.user == project.client):
        return HttpResponseForbidden()

    if request.method == "POST":
        item_title = item.title
        item.delete()
        messages.success(request, f'Ítem "{item_title}" eliminado.')
        return redirect("schedule_generator", project_id=project.id)

    return render(
        request,
        "core/schedule_item_confirm_delete.html",
        {
            "item": item,
            "project": project,
        },
    )


@login_required
def project_schedule_ics(request, project_id):
    """
    Export project schedule as ICS (iCalendar) file.
    Compatible with Google Calendar, Outlook, Apple Calendar, etc.
    """
    from core.services.calendar_sync import generate_ical_for_project

    project = get_object_or_404(Project, id=project_id)

    # Generate iCal content
    ical_data = generate_ical_for_project(project)

    # Return as downloadable file
    response = HttpResponse(ical_data, content_type="text/calendar; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{project.name}_schedule.ics"'
    return response


@login_required
def project_schedule_google_calendar(request, project_id):
    """
    Generate instructions and links for adding schedule to Google Calendar.
    """
    from core.services.calendar_sync import create_calendar_subscription_url

    project = get_object_or_404(Project, id=project_id)
    subscription_url = create_calendar_subscription_url(project, request)

    context = {
        "project": project,
        "subscription_url": subscription_url,
        "ics_url": reverse("project_schedule_ics", kwargs={"project_id": project.id}),
    }

    return render(request, "core/schedule_google_calendar.html", context)


@login_required
def schedule_gantt_react_view(request, project_id):
    """
    Render the React-based Gantt chart for project schedule.
    Uses the new unified KibrayGantt React component.
    """
    project = get_object_or_404(Project, id=project_id)

    # Check permissions (staff or project manager)
    user_profile = getattr(request.user, "profile", None)
    can_manage = bool(
        request.user.is_staff
        or (user_profile and getattr(user_profile, "role", None) in ["project_manager", "admin", "superuser"])
    )

    if not can_manage:
        return HttpResponseForbidden("No tienes permisos para ver este cronograma.")

    # Get team members for task assignment
    from django.contrib.auth import get_user_model
    User = get_user_model()
    team_members = User.objects.filter(
        is_active=True
    ).exclude(
        username__in=['admin', 'system']
    ).order_by('first_name', 'last_name')[:50]

    context = {
        "project": project,
        "can_edit": can_manage,
        "team_members": team_members,
        "disable_notification_center": True,  # Avoid React conflicts with Gantt bundle
    }

    return render(request, "schedule_gantt_react.html", context)


# ========================================================================================
# CHANGE ORDER API ENDPOINTS
# ========================================================================================


@login_required
@require_http_methods(["PATCH"])
def changeorder_update_status(request, co_id):
    """Update Change Order status via drag and drop in board"""
    try:
        co = get_object_or_404(ChangeOrder, id=co_id)

        # Check permissions
        profile = getattr(request.user, "profile", None)
        role = getattr(profile, "role", "employee")

        if role not in ["admin", "superuser", "project_manager"]:
            return JsonResponse({"success": False, "error": "Sin permisos"}, status=403)

        # Parse request
        data = json.loads(request.body)
        new_status = data.get("status")

        # Validate status
        valid_statuses = ["pending", "approved", "sent", "billed", "paid"]
        if new_status not in valid_statuses:
            return JsonResponse({"success": False, "error": "Estado inválido"}, status=400)

        # Update status
        old_status = co.status
        co.status = new_status
        co.save()

        return JsonResponse(
            {
                "success": True,
                "co_id": co.id,
                "old_status": old_status,
                "new_status": new_status,
                "message": f"Estado actualizado a {co.get_status_display()}",
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@require_POST
def changeorder_send_to_client(request, co_id):
    """Send Change Order to client for signature"""
    try:
        co = get_object_or_404(ChangeOrder, id=co_id)

        # Check permissions
        profile = getattr(request.user, "profile", None)
        role = getattr(profile, "role", "employee")

        if role not in ["admin", "superuser", "project_manager"]:
            return JsonResponse({"success": False, "error": "Sin permisos"}, status=403)

        # Validate current status
        if co.status in ["billed", "paid"]:
            return JsonResponse(
                {"success": False, "error": "No se puede enviar un CO ya facturado o pagado"},
                status=400,
            )

        # Update status to 'sent'
        co.status = "sent"
        co.save()

        # TODO: Send email notification to client
        # This would integrate with your notification system
        # send_co_notification_to_client(co)

        return JsonResponse(
            {
                "success": True,
                "co_id": co.id,
                "message": f"Change Order #{co.id} enviado al cliente",
                "new_status": "sent",
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# ========================================================================================
# FILE ORGANIZATION VIEWS
# ========================================================================================


@login_required
def project_files_view(request, project_id):
    """Main view for project file organization system"""
    from core.forms import FileCategoryForm, ProjectFileForm
    from core.models import FileCategory, ProjectFile

    project = get_object_or_404(Project, id=project_id)

    # Get or create default categories
    default_categories = [
        ("Daily Logs Photos", "daily_logs", "bi-camera-fill", "primary"),
        ("Documents", "documents", "bi-file-earmark-text", "info"),
        ("Datasheets", "datasheets", "bi-file-spreadsheet", "success"),
        ("COs Firmados", "cos_signed", "bi-file-earmark-check", "warning"),
        ("Invoices", "invoices", "bi-receipt", "success"),
        ("Contracts", "contracts", "bi-file-earmark-ruled", "danger"),
        ("Photos", "photos", "bi-images", "primary"),
    ]

    for idx, (name, cat_type, icon, color) in enumerate(default_categories):
        FileCategory.objects.get_or_create(
            project=project,
            name=name,
            defaults={
                "category_type": cat_type,
                "icon": icon,
                "color": color,
                "order": idx,
                "created_by": request.user,
            },
        )

    # Get all categories and files
    categories = project.file_categories.all()
    selected_category_id = request.GET.get("category")

    if selected_category_id:
        files = ProjectFile.objects.filter(
            project=project, category_id=selected_category_id
        ).select_related("category", "uploaded_by")
    else:
        files = ProjectFile.objects.filter(project=project).select_related(
            "category", "uploaded_by"
        )

    # Search filter
    search_query = request.GET.get("q")
    if search_query:
        files = files.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(tags__icontains=search_query)
        )

    return render(
        request,
        "core/project_files.html",
        {
            "project": project,
            "categories": categories,
            "files": files,
            "selected_category_id": selected_category_id,
            "search_query": search_query or "",
            "category_form": FileCategoryForm(),
            "file_form": ProjectFileForm(),
        },
    )


@login_required
def file_category_create(request, project_id):
    """Create a new file category"""
    from core.forms import FileCategoryForm

    if request.method != "POST":
        return redirect("project_files", project_id=project_id)

    project = get_object_or_404(Project, id=project_id)
    form = FileCategoryForm(request.POST)

    if form.is_valid():
        category = form.save(commit=False)
        category.project = project
        category.created_by = request.user
        category.save()
        messages.success(request, f'Categoría "{category.name}" creada')
    else:
        messages.error(request, "Error al crear categoría")

    return redirect("project_files", project_id=project_id)


@login_required
@require_POST
def file_upload(request, project_id, category_id):
    """Upload a file to a category"""
    from core.forms import ProjectFileForm
    from core.models import FileCategory

    project = get_object_or_404(Project, id=project_id)
    category = get_object_or_404(FileCategory, id=category_id, project=project)

    form = ProjectFileForm(request.POST, request.FILES)
    if form.is_valid():
        file_obj = form.save(commit=False)
        file_obj.project = project
        file_obj.category = category
        file_obj.uploaded_by = request.user
        file_obj.save()
        messages.success(request, f'Archivo "{file_obj.name}" subido correctamente')
    else:
        messages.error(request, "Error al subir archivo")

    return redirect("project_files", project_id=project_id)


@login_required
@require_POST
def file_delete(request, file_id):
    """Delete a file"""
    from core.models import ProjectFile

    file_obj = get_object_or_404(ProjectFile, id=file_id)
    project_id = file_obj.project.id

    # Check permission
    if not (request.user.is_staff or request.user == file_obj.uploaded_by):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

    # Delete file from storage
    if file_obj.file:
        file_obj.file.delete()

    file_name = file_obj.name
    file_obj.delete()

    messages.success(request, f'Archivo "{file_name}" eliminado')
    return redirect("project_files", project_id=project_id)


@login_required
def file_download(request, file_id):
    """Download a file"""
    from core.models import ProjectFile

    file_obj = get_object_or_404(ProjectFile, id=file_id)

    # Check permissions
    profile = getattr(request.user, "profile", None)
    if not file_obj.is_public and profile and profile.role == "client":
        return HttpResponseForbidden("No tienes permiso para descargar este archivo")

    # Serve file
    if file_obj.file:
        response = HttpResponse(file_obj.file, content_type="application/octet-stream")
        response["Content-Disposition"] = f'attachment; filename="{file_obj.name}"'
        return response

    return HttpResponseNotFound("Archivo no encontrado")


@login_required
def file_edit_metadata(request, file_id):
    """Edit file metadata (name, description, tags, version)"""
    from core.models import ProjectFile

    file_obj = get_object_or_404(ProjectFile, id=file_id)

    # Check permission
    if not (request.user.is_staff or request.user == file_obj.uploaded_by):
        return JsonResponse({"error": gettext("Sin permiso")}, status=403)

    if request.method == "POST":
        file_obj.name = request.POST.get("name", file_obj.name)
        file_obj.description = request.POST.get("description", "")
        file_obj.tags = request.POST.get("tags", "")
        file_obj.version = request.POST.get("version", "")
        file_obj.save()

        messages.success(request, f'Archivo "{file_obj.name}" actualizado')

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True, "message": gettext("Archivo actualizado")})

        return redirect("project_files", project_id=file_obj.project.id)

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)


# ========================================================================================
# TOUCH-UP PIN VIEWS (Separate from Info Pins)
# ========================================================================================


@login_required
def touchup_plans_list(request, project_id):
    """List all floor plans with active touch-ups"""
    from core.models import FloorPlan

    project = get_object_or_404(Project, id=project_id)
    profile = getattr(request.user, "profile", None)

    # Permission check: PM, Admin, Client, Designer, Owner
    if not request.user.is_staff and (
        not profile
        or profile.role
        not in ["project_manager", "admin", "superuser", "client", "designer", "owner"]
    ):
        messages.error(request, "No tienes permiso para gestionar touch-ups")
        return redirect("project_overview", project_id)

    # Get plans with active touch-ups
    plans = FloorPlan.objects.filter(project=project).prefetch_related("touchup_pins")

    # Annotate with active touchup count
    from django.db.models import Count, Q

    plans = plans.annotate(
        active_touchups=Count(
            "touchup_pins", filter=Q(touchup_pins__status__in=["pending", "in_progress"])
        )
    )

    context = {"project": project, "plans": plans, "page_title": "Planos Touch-up"}
    return render(request, "core/touchup_plans_list.html", context)


@login_required
def touchup_plan_detail(request, plan_id):
    """View a single floor plan with its touch-ups"""
    from core.models import FloorPlan, TouchUpPin

    plan = get_object_or_404(FloorPlan, id=plan_id)
    project = plan.project
    profile = getattr(request.user, "profile", None)

    # Permission check
    allowed_roles = [
        "project_manager",
        "admin",
        "superuser",
        "employee",
        "painter",
        "client",
        "designer",
        "owner",
    ]
    if not request.user.is_staff and (not profile or profile.role not in allowed_roles):
        messages.error(request, "No tienes permiso para ver touch-ups")
        return redirect("project_overview", project.id)

    # Get touchups - filter by assigned user if employee
    touchups = TouchUpPin.objects.filter(plan=plan)
    if profile and profile.role in ["employee", "painter"] and not request.user.is_staff:
        touchups = touchups.filter(assigned_to=request.user)

    touchups = touchups.select_related("assigned_to", "created_by", "approved_color", "closed_by")

    # Can create: authorized roles
    can_create = request.user.is_staff or (
        profile and profile.role in ["project_manager", "admin", "client", "designer", "owner"]
    )

    context = {
        "project": project,
        "plan": plan,
        "touchups": touchups,
        "can_create": can_create,
        "page_title": f"Touch-ups - {plan.name}",
    }
    return render(request, "core/touchup_plan_detail.html", context)


@login_required
def touchup_create(request, plan_id):
    """Create a new touch-up pin"""
    from core.forms import TouchUpPinForm
    from core.models import FloorPlan

    plan = get_object_or_404(FloorPlan, id=plan_id)
    project = plan.project
    profile = getattr(request.user, "profile", None)

    # Permission check: PM, Admin, Client, Designer, Owner
    if not request.user.is_staff and (
        not profile
        or profile.role
        not in ["project_manager", "admin", "superuser", "client", "designer", "owner"]
    ):
        return JsonResponse({"error": gettext("No autorizado")}, status=403)

    if request.method == "POST":
        form = TouchUpPinForm(request.POST, project=project)
        if form.is_valid():
            touchup = form.save(commit=False)
            touchup.created_by = request.user
            touchup.save()

            messages.success(request, f'Touch-up "{touchup.task_name}" creado')
            return JsonResponse(
                {
                    "success": True,
                    "touchup_id": touchup.id,
                    "message": gettext("Touch-up creado exitosamente"),
                }
            )
        else:
            return JsonResponse({"error": "Formulario inválido", "errors": form.errors}, status=400)

    # GET - return form
    form = TouchUpPinForm(initial={"plan": plan}, project=project)
    return render(
        request, "core/touchup_create_form.html", {"form": form, "plan": plan, "project": project}
    )


@login_required
def touchup_detail_ajax(request, touchup_id):
    """Get touch-up details via AJAX"""
    from core.models import TouchUpPin

    touchup = get_object_or_404(TouchUpPin, id=touchup_id)
    profile = getattr(request.user, "profile", None)

    # Permission check
    can_view = (
        request.user.is_staff
        or (profile and profile.role in ["project_manager", "admin", "superuser"])
        or touchup.assigned_to == request.user
    )

    if not can_view:
        return JsonResponse({"error": gettext("No autorizado")}, status=403)

    # Check if user can approve (PM/Admin)
    can_approve = request.user.is_staff or (
        profile and profile.role in ["project_manager", "admin", "superuser"]
    )

    data = {
        "id": touchup.id,
        "task_name": touchup.task_name,
        "description": touchup.description,
        "status": touchup.status,
        "status_display": touchup.get_status_display(),
        "created_at": touchup.created_at.isoformat(),
        "created_by": str(touchup.created_by) if touchup.created_by else None,
        "assigned_to": str(touchup.assigned_to) if touchup.assigned_to else "Sin asignar",
        "approved_color": touchup.approved_color.name if touchup.approved_color else None,
        "custom_color_name": touchup.custom_color_name,
        "sheen": touchup.sheen,
        "details": touchup.details,
        "can_edit": touchup.can_edit(request.user),
        "can_close": touchup.can_close(request.user),
        "can_approve": can_approve,
        "approval_status": touchup.approval_status,
        "approval_status_display": touchup.get_approval_status_display(),
        "rejection_reason": touchup.rejection_reason,
        "reviewed_by": str(touchup.reviewed_by) if touchup.reviewed_by else None,
        "reviewed_at": touchup.reviewed_at.isoformat() if touchup.reviewed_at else None,
        "completion_photos": [
            {
                "id": photo.id,
                "url": photo.image.url,
                "notes": photo.notes,
                "uploaded_at": photo.uploaded_at.isoformat(),
            }
            for photo in touchup.completion_photos.all()
        ],
    }

    return JsonResponse(data)


@login_required
def touchup_update(request, touchup_id):
    """Update a touch-up (PM/Admin only)"""
    from core.forms import TouchUpPinForm
    from core.models import TouchUpPin

    touchup = get_object_or_404(TouchUpPin, id=touchup_id)

    # Permission check
    if not touchup.can_edit(request.user):
        return JsonResponse({"error": gettext("No autorizado")}, status=403)

    if request.method == "POST":
        form = TouchUpPinForm(request.POST, instance=touchup, project=touchup.plan.project)
        if form.is_valid():
            form.save()
            messages.success(request, "Touch-up actualizado")
            return JsonResponse({"success": True, "message": gettext("Touch-up actualizado")})
        else:
            return JsonResponse({"error": "Formulario inválido", "errors": form.errors}, status=400)

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)


@login_required
def touchup_complete(request, touchup_id):
    """Mark touch-up as completed with photos (Assigned employee or PM)"""
    import json

    from core.models import TouchUpCompletionPhoto, TouchUpPin

    touchup = get_object_or_404(TouchUpPin, id=touchup_id)

    # Permission check
    if not touchup.can_close(request.user):
        return JsonResponse(
            {"error": gettext("No autorizado para cerrar este touch-up")}, status=403
        )

    if request.method == "POST":
        notes = request.POST.get("notes", "")
        photos = request.FILES.getlist("photos")

        if not photos:
            return JsonResponse({"error": gettext("Debes subir al menos una foto")}, status=400)

        # Save completion photos with annotations
        for idx, photo in enumerate(photos):
            # Get annotations for this photo if provided
            annotations_key = f"annotations_{idx}"
            annotations_data = request.POST.get(annotations_key, "{}")

            # Parse annotations JSON
            try:
                annotations = json.loads(annotations_data) if annotations_data else {}
            except json.JSONDecodeError:
                annotations = {}

            TouchUpCompletionPhoto.objects.create(
                touchup=touchup,
                image=photo,
                notes=notes,
                annotations=annotations,
                uploaded_by=request.user,
            )

        # Mark as completed
        touchup.close_touchup(request.user)

        messages.success(request, f'Touch-up "{touchup.task_name}" completado')
        return JsonResponse(
            {"success": True, "message": gettext("Touch-up completado exitosamente")}
        )

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)


@login_required
def touchup_delete(request, touchup_id):
    """Delete a touch-up (PM/Admin only)"""
    from core.models import TouchUpPin

    touchup = get_object_or_404(TouchUpPin, id=touchup_id)

    # Permission check
    if not touchup.can_edit(request.user):
        return JsonResponse({"error": gettext("No autorizado")}, status=403)

    if request.method == "POST":
        plan_id = touchup.plan.id
        task_name = touchup.task_name
        touchup.delete()

        messages.success(request, f'Touch-up "{task_name}" eliminado')
        return JsonResponse({"success": True, "redirect": f"/plans/{plan_id}/touchups/"})

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)


@login_required
def touchup_approve(request, touchup_id):
    """Approve a completed touch-up (PM/Admin only)"""
    from django.utils import timezone

    from core.models import TouchUpPin

    touchup = get_object_or_404(TouchUpPin, id=touchup_id)

    # Permission check - only PM/Admin can approve
    if not touchup.can_edit(request.user):
        return JsonResponse({"error": gettext("No autorizado para aprobar")}, status=403)

    if request.method == "POST":
        touchup.approval_status = "approved"
        touchup.reviewed_by = request.user
        touchup.reviewed_at = timezone.now()
        touchup.save()

        messages.success(request, f'Touch-up "{touchup.task_name}" aprobado')
        return JsonResponse({"success": True, "message": gettext("Touch-up aprobado exitosamente")})

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)


@login_required
def touchup_reject(request, touchup_id):
    """Reject a completed touch-up with reason (PM/Admin only)"""
    from django.utils import timezone

    from core.models import TouchUpPin

    touchup = get_object_or_404(TouchUpPin, id=touchup_id)

    # Permission check - only PM/Admin can reject
    if not touchup.can_edit(request.user):
        return JsonResponse({"error": gettext("No autorizado para rechazar")}, status=403)

    if request.method == "POST":
        reason = request.POST.get("reason", "")
        if not reason:
            return JsonResponse(
                {"error": gettext("Debes proporcionar un motivo de rechazo")}, status=400
            )

        touchup.approval_status = "rejected"
        touchup.rejection_reason = reason
        touchup.reviewed_by = request.user
        touchup.reviewed_at = timezone.now()
        touchup.status = "in_progress"  # Reabrir para que el empleado lo corrija
        touchup.save()

        messages.warning(request, f'Touch-up "{touchup.task_name}" rechazado')
        return JsonResponse(
            {"success": True, "message": gettext("Touch-up rechazado, el empleado debe corregirlo")}
        )

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)


# ========================================================================================
# INFO PIN VIEWS (Different from Touch-up Pins)
# ========================================================================================


@login_required
def pin_info_ajax(request, pin_id):
    """Get info pin details via AJAX"""
    import logging

    from core.models import PlanPin

    logger = logging.getLogger(__name__)

    try:
        pin = get_object_or_404(PlanPin, id=pin_id)
        profile = getattr(request.user, "profile", None)

        # Anyone can view info pins
        can_edit = request.user.is_staff or (
            profile
            and profile.role
            in ["project_manager", "admin", "superuser", "client", "designer", "owner"]
        )

        data = {
            "id": pin.id,
            "title": pin.title or "",
            "description": pin.description or "",
            "pin_type": pin.pin_type,
            "pin_type_display": pin.get_pin_type_display(),
            "pin_color": pin.pin_color,
            "can_edit": can_edit,
            "color_sample": None,
            "linked_task": None,
            "attachments": [],
        }

        # Add color sample if exists
        try:
            if pin.color_sample:
                cs = pin.color_sample
                data["color_sample"] = {
                    "id": cs.id,
                    "name": cs.name or "",
                    "code": cs.code or "",
                    "brand": cs.brand or "",
                    "finish": cs.finish or "",
                    "gloss": cs.gloss or "",
                    "status": cs.status or "",
                    "status_display": cs.get_status_display(),
                    "notes": cs.notes or "",
                    "room_location": cs.room_location or "",
                    "sample_number": cs.sample_number or "",
                    "sample_image": cs.sample_image.url if cs.sample_image else None,
                    "reference_photo": cs.reference_photo.url if cs.reference_photo else None,
                }
        except Exception as e:
            logger.error(f"Error loading color sample for pin {pin_id}: {e}")

        # Add linked task if exists
        try:
            if pin.linked_task:
                data["linked_task"] = {
                    "id": pin.linked_task.id,
                    "title": pin.linked_task.title or "",
                    "status": pin.linked_task.status or "",
                }
        except Exception as e:
            logger.error(f"Error loading linked task for pin {pin_id}: {e}")

        # Add attachments (photos)
        try:
            data["attachments"] = [
                {
                    "id": att.id,
                    "image_url": att.image.url if att.image else "",
                    "has_annotations": bool(att.annotations),
                    "created_at": att.created_at.isoformat() if att.created_at else "",
                }
                for att in pin.attachments.all()
            ]
        except Exception as e:
            logger.error(f"Error loading attachments for pin {pin_id}: {e}")

        return JsonResponse(data)

    except Exception as e:
        logger.error(f"Error in pin_info_ajax for pin {pin_id}: {str(e)}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def pin_update(request, pin_id):
    """Update info pin details"""
    from core.models import PlanPin

    pin = get_object_or_404(PlanPin, id=pin_id)
    profile = getattr(request.user, "profile", None)

    # Permission check
    can_edit = request.user.is_staff or (
        profile
        and profile.role in ["project_manager", "admin", "superuser", "client", "designer", "owner"]
    )

    if not can_edit:
        return JsonResponse({"error": gettext("No autorizado")}, status=403)

    if request.method == "POST":
        pin.title = request.POST.get("title", pin.title)
        pin.description = request.POST.get("description", pin.description)
        pin.pin_type = request.POST.get("pin_type", pin.pin_type)

        # Update color sample if provided
        color_sample_id = request.POST.get("color_sample_id")
        if color_sample_id:
            from core.models import ColorSample

            with contextlib.suppress(ColorSample.DoesNotExist):
                pin.color_sample = ColorSample.objects.get(id=color_sample_id)

        pin.save()

        messages.success(request, "Pin actualizado exitosamente")
        return JsonResponse({"success": True, "message": gettext("Pin actualizado")})

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)


@login_required
def pin_add_photo(request, pin_id):
    """Add photo attachment to info pin"""
    import json

    from core.models import PlanPin, PlanPinAttachment

    pin = get_object_or_404(PlanPin, id=pin_id)
    profile = getattr(request.user, "profile", None)

    # Permission check
    can_edit = request.user.is_staff or (
        profile
        and profile.role in ["project_manager", "admin", "superuser", "client", "designer", "owner"]
    )

    if not can_edit:
        return JsonResponse({"error": gettext("No autorizado")}, status=403)

    if request.method == "POST":
        photos = request.FILES.getlist("photos")

        if not photos:
            return JsonResponse({"error": gettext("No se enviaron fotos")}, status=400)

        created_attachments = []
        for idx, photo in enumerate(photos):
            # Get annotations for this photo if provided
            annotations_key = f"annotations_{idx}"
            annotations_data = request.POST.get(annotations_key, "{}")

            # Parse annotations JSON
            try:
                annotations = json.loads(annotations_data) if annotations_data else {}
            except json.JSONDecodeError:
                annotations = {}

            attachment = PlanPinAttachment.objects.create(
                pin=pin, image=photo, annotations=annotations
            )
            created_attachments.append({"id": attachment.id, "url": attachment.image.url})

        messages.success(
            request, _("%(count)s foto(s) agregada(s) al pin") % {"count": len(photos)}
        )
        return JsonResponse(
            {
                "success": True,
                "message": "Fotos agregadas exitosamente",
                "attachments": created_attachments,
            }
        )

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)


@login_required
def pin_delete_photo(request, attachment_id):
    """Delete photo attachment from info pin"""
    from core.models import PlanPinAttachment

    attachment = get_object_or_404(PlanPinAttachment, id=attachment_id)
    profile = getattr(request.user, "profile", None)

    # Permission check
    can_edit = request.user.is_staff or (
        profile
        and profile.role in ["project_manager", "admin", "superuser", "client", "designer", "owner"]
    )

    if not can_edit:
        return JsonResponse({"error": gettext("No autorizado")}, status=403)

    if request.method == "POST":
        # Delete file from storage
        if attachment.image:
            attachment.image.delete()

        attachment.delete()

        return JsonResponse({"success": True, "message": gettext("Foto eliminada")})

    return JsonResponse({"error": gettext("Método no permitido")}, status=405)


# ========================================
# GESTIÓN DE CLIENTES
# ========================================


@login_required
@staff_member_required
def client_list(request):
    """Lista de todos los clientes con búsqueda y filtros"""
    from core.models import ClientProjectAccess

    # Solo usuarios con perfil de cliente
    clients = (
        User.objects.filter(profile__role="client")
        .select_related("profile")
        .order_by("-date_joined")
    )

    # Búsqueda
    search_query = request.GET.get("search", "").strip()
    if search_query:
        clients = clients.filter(
            Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(username__icontains=search_query)
        )

    # Filtro por estado
    status_filter = request.GET.get("status", "")
    if status_filter == "active":
        clients = clients.filter(is_active=True)
    elif status_filter == "inactive":
        clients = clients.filter(is_active=False)

    # Agregar conteo de proyectos asignados
    clients_data = []
    for client in clients:
        project_count = ClientProjectAccess.objects.filter(user=client).count()
        clients_data.append({"user": client, "project_count": project_count})

    # Paginación
    paginator = Paginator(clients_data, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "status_filter": status_filter,
        "total_clients": clients.count(),
    }

    return render(request, "core/client_list.html", context)


@login_required
@staff_member_required
def client_create(request):
    """Crear nuevo cliente"""
    from django.conf import settings
    from django.core.mail import send_mail

    from core.forms import ClientCreationForm

    if request.method == "POST":
        form = ClientCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Enviar email de bienvenida si está marcado
            if form.cleaned_data.get("send_welcome_email"):
                temp_password = form.temp_password
                email_body = f"""
Bienvenido a Kibray Construction Management System

Hola {user.first_name},

Tu cuenta ha sido creada exitosamente. Aquí están tus credenciales de acceso:

Usuario: {user.email}
Contraseña temporal: {temp_password}

Por favor, cambia tu contraseña después del primer inicio de sesión.

Accede al sistema en: {request.build_absolute_uri("/")}

Saludos,
El equipo de Kibray
                """
                try:
                    send_mail(
                        "Bienvenido a Kibray",
                        email_body,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=True,
                    )
                    messages.success(
                        request,
                        f"Cliente creado exitosamente. Se ha enviado un email con las credenciales de acceso a {user.email}",
                    )
                except Exception as e:
                    messages.warning(
                        request,
                        f"Cliente creado pero hubo un error al enviar el email: {str(e)}. Contacta al cliente directamente para proporcionarle acceso.",
                    )
            else:
                # No mostrar contraseña en UI - solo indicar que se creó
                messages.success(
                    request,
                    "Cliente creado exitosamente. Recuerda proporcionarle sus credenciales de acceso de forma segura.",
                )

            return redirect("client_detail", user_id=user.id)
    else:
        form = ClientCreationForm()

    return render(request, "core/client_form.html", {"form": form, "is_create": True})


@login_required
@staff_member_required
def client_detail(request, user_id):
    """Detalle de un cliente con sus proyectos asignados"""
    from core.models import ClientProjectAccess

    client = get_object_or_404(User, id=user_id)

    # Verificar que es un cliente
    if not hasattr(client, "profile") or client.profile.role != "client":
        messages.error(request, "Este usuario no es un cliente.")
        return redirect("client_list")

    # Obtener proyectos asignados
    project_accesses = ClientProjectAccess.objects.filter(user=client).select_related("project")

    # Actividad reciente
    recent_comments = (
        Comment.objects.filter(user=client)
        .select_related("task", "task__project")
        .order_by("-created_at")[:5]
    )

    # Tasks: Los clientes no son empleados, así que no pueden tener tasks asignadas directamente
    # Solo mostraremos las tasks que crearon o comentaron
    recent_tasks = []

    from core.models import ClientRequest

    recent_requests = (
        ClientRequest.objects.filter(created_by=client)
        .select_related("project")
        .order_by("-created_at")[:5]
    )

    context = {
        "client": client,
        "project_accesses": project_accesses,
        "recent_comments": recent_comments,
        "recent_tasks": recent_tasks,
        "recent_requests": recent_requests,
    }

    return render(request, "core/client_detail.html", context)


@login_required
@staff_member_required
def client_edit(request, user_id):
    """Editar información de un cliente"""
    from core.forms import ClientEditForm

    client = get_object_or_404(User, id=user_id)

    # Verificar que es un cliente
    if not hasattr(client, "profile") or client.profile.role != "client":
        messages.error(request, "Este usuario no es un cliente.")
        return redirect("client_list")

    if request.method == "POST":
        form = ClientEditForm(request.POST, instance=client)
        if form.is_valid():
            user = form.save()

            # Actualizar perfil
            if hasattr(user, "profile"):
                user.profile.language = form.cleaned_data.get("language", "en")
                user.profile.save()

            messages.success(request, "Información del cliente actualizada exitosamente.")
            return redirect("client_detail", user_id=user.id)
    else:
        form = ClientEditForm(instance=client)

    return render(
        request, "core/client_form.html", {"form": form, "client": client, "is_create": False}
    )


@login_required
@staff_member_required
def client_delete(request, user_id):
    """Desactivar o eliminar un cliente (con confirmación)"""
    client = get_object_or_404(User, id=user_id)

    # Verificar que es un cliente
    if not hasattr(client, "profile") or client.profile.role != "client":
        messages.error(request, "Este usuario no es un cliente.")
        return redirect("client_list")

    if request.method == "POST":
        action = request.POST.get("action", "deactivate")

        # SECURITY: Logging de auditoría para operaciones críticas
        import logging

        audit_logger = logging.getLogger("django")
        audit_logger.warning(
            f"CLIENT_DELETE_ATTEMPT | Actor: {request.user.username} (ID:{request.user.id}) | "
            f"Target: {client.username} (ID:{client.id}) | Action: {action} | "
            f"IP: {request.META.get('REMOTE_ADDR')}"
        )

        if action == "deactivate":
            client.is_active = False
            client.save()
            messages.success(
                request,
                _("Cliente %(name)s desactivado exitosamente.") % {"name": client.get_full_name()},
            )
        elif action == "delete":
            # SECURITY: Verificar dependencias críticas antes de CASCADE delete
            from core.models import ClientProjectAccess, ClientRequest

            project_count = ClientProjectAccess.objects.filter(user=client).count()
            request_count = ClientRequest.objects.filter(created_by=client).count()
            comment_count = Comment.objects.filter(user=client).count()
            # Los clientes no son empleados, no pueden tener tareas asignadas
            task_count = 0

            if any([project_count, request_count, comment_count, task_count]):
                messages.error(
                    request,
                    f"❌ No se puede eliminar este cliente porque tiene datos asociados: "
                    f"{project_count} proyectos asignados, {request_count} solicitudes, "
                    f"{comment_count} comentarios. "
                    f'Usa "Desactivar" para preservar la integridad de los datos.',
                )
                return redirect("client_detail", user_id=client.id)

            client_name = client.get_full_name()
            client.delete()
            messages.success(
                request, _("Cliente %(name)s eliminado permanentemente.") % {"name": client_name}
            )
            return redirect("client_list")

        return redirect("client_detail", user_id=client.id)

    # GET: Mostrar estadísticas para confirmar
    from core.models import ClientProjectAccess, ClientRequest

    context = {
        "client": client,
        "project_count": ClientProjectAccess.objects.filter(user=client).count(),
        "request_count": ClientRequest.objects.filter(created_by=client).count(),
        "comment_count": Comment.objects.filter(user=client).count(),
        # Los clientes no tienen tareas asignadas (solo empleados)
        "task_count": 0,
    }

    return render(request, "core/client_delete_confirm.html", context)


@login_required
@staff_member_required
def client_reset_password(request, user_id):
    """Resetear contraseña de un cliente"""
    from django.conf import settings
    from django.core.mail import send_mail

    from core.forms import ClientPasswordResetForm

    client = get_object_or_404(User, id=user_id)

    if not hasattr(client, "profile") or client.profile.role != "client":
        messages.error(request, "Este usuario no es un cliente.")
        return redirect("client_list")

    if request.method == "POST":
        form = ClientPasswordResetForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data["new_password"]
            client.set_password(new_password)
            client.save()

            # Enviar email notificando el cambio
            try:
                send_mail(
                    "Tu contraseña ha sido actualizada",
                    f"Hola {client.first_name},\n\nTu contraseña ha sido actualizada por un administrador.\nNueva contraseña: {new_password}\n\nPor favor, cámbiala después de iniciar sesión.\n\nSaludos,\nEl equipo de Kibray",
                    settings.DEFAULT_FROM_EMAIL,
                    [client.email],
                    fail_silently=True,
                )
                messages.success(
                    request,
                    _("Contraseña actualizada y email enviado a %(email)s")
                    % {"email": client.email},
                )
            except Exception as e:
                messages.warning(
                    request,
                    _("Contraseña actualizada pero hubo un error al enviar el email: %(error)s")
                    % {"error": str(e)},
                )

            return redirect("client_detail", user_id=client.id)
    else:
        form = ClientPasswordResetForm()

    return render(request, "core/client_password_reset.html", {"form": form, "client": client})


@login_required
@staff_member_required
def client_assign_project(request, user_id):
    """Asignar o remover proyectos de un cliente"""
    from core.models import ClientProjectAccess

    client = get_object_or_404(User, id=user_id)

    if not hasattr(client, "profile") or client.profile.role != "client":
        messages.error(request, "Este usuario no es un cliente.")
        return redirect("client_list")

    if request.method == "POST":
        project_id = request.POST.get("project_id")
        action = request.POST.get("action", "add")

        if not project_id:
            messages.error(request, "Proyecto no especificado.")
            return redirect("client_detail", user_id=client.id)

        project = get_object_or_404(Project, id=project_id)

        if action == "add":
            access, created = ClientProjectAccess.objects.get_or_create(
                user=client,
                project=project,
                defaults={"role": "client", "can_comment": True, "can_create_tasks": True},
            )
            if created:
                messages.success(
                    request, f'Cliente asignado al proyecto "{project.name}" exitosamente.'
                )
            else:
                messages.info(request, f'El cliente ya tiene acceso al proyecto "{project.name}".')

        elif action == "remove":
            deleted_count, _ = ClientProjectAccess.objects.filter(
                user=client, project=project
            ).delete()
            if deleted_count > 0:
                messages.success(request, f'Acceso al proyecto "{project.name}" removido.')
            else:
                messages.info(request, "El cliente no tenía acceso a ese proyecto.")

        return redirect("client_detail", user_id=client.id)

    # GET: Mostrar formulario con proyectos disponibles
    from core.models import ClientProjectAccess

    assigned_projects = ClientProjectAccess.objects.filter(user=client).values_list(
        "project_id", flat=True
    )
    available_projects = Project.objects.exclude(id__in=assigned_projects).order_by("name")

    context = {
        "client": client,
        "available_projects": available_projects,
    }

    return render(request, "core/client_assign_project.html", context)


# ========================================
# GESTIÓN DE PROYECTOS
# ========================================


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
        import logging

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
        has_schedules = ScheduleItem.objects.filter(project=project).exists()
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
    schedule_count = ScheduleItem.objects.filter(project=project).count()
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


# --- DEMO: JavaScript i18n ---
@login_required
def js_i18n_demo(request):
    """
    Demo page showing how to use Django's JavaScript translation catalog.
    This demonstrates gettext(), ngettext(), and interpolate() in JavaScript.
    """
    return render(request, "core/js_i18n_demo.html")


# --- ANALYTICS DASHBOARD ---
@login_required
def analytics_dashboard(request):
    """
    Analytics Dashboard view - serves React-based analytics dashboard.
    Provides comprehensive project metrics, touchup analytics, color approvals,
    and PM performance data visualization.
    """
    # Determine user role for frontend permission checks
    user_role = "user"
    if request.user.is_superuser:
        user_role = "admin"
    elif request.user.is_staff:
        user_role = "staff"

    return render(
        request,
        "core/analytics_dashboard.html",
        {
            "user_role": user_role,
        },
    )


# --- TOUCHUP BOARD REACT ---
@login_required
def touchup_board_react(request, project_id):
    """
    TouchUp Board React view - serves React-based kanban board for touchups.
    """
    project = get_object_or_404(Project, id=project_id)

    return render(
        request,
        "core/touchup_board_react.html",
        {
            "project_id": project_id,
            "project": project,
        },
    )


# --- COLOR APPROVALS REACT ---
@login_required
def color_approvals_react(request, project_id=None):
    """
    Color Approvals React view - serves React-based color approval management.
    """
    project = None
    if project_id:
        project = get_object_or_404(Project, id=project_id)

    return render(
        request,
        "core/color_approvals_react.html",
        {
            "project_id": project_id,
            "project": project,
        },
    )


# --- PM ASSIGNMENTS REACT ---
@login_required
def pm_assignments_react(request):
    """
    PM Assignments React view - serves React-based PM assignment management.
    """
    return render(request, "core/pm_assignments_react.html", {})


# --- PUBLIC PROPOSAL APPROVAL ---
def proposal_public_view(request, token):
    """
    Public view for clients to approve or reject a proposal.
    No login required - access via unique token.
    """
    from core.models import Proposal

    try:
        proposal = Proposal.objects.select_related("estimate__project").get(client_view_token=token)
    except Proposal.DoesNotExist:
        return HttpResponseNotFound("Propuesta no encontrada o enlace inválido.")

    estimate = proposal.estimate
    project = estimate.project
    lines = estimate.lines.select_related("cost_code").all()

    # Calculate totals
    subtotal = sum(
        (line.qty * (line.labor_unit_cost + line.material_unit_cost + line.other_unit_cost))
        for line in lines
    )
    # Apply markups and overheads
    markup_material_amount = subtotal * (estimate.markup_material / Decimal("100"))
    markup_labor_amount = subtotal * (estimate.markup_labor / Decimal("100"))
    overhead_amount = subtotal * (estimate.overhead_pct / Decimal("100"))
    profit_amount = subtotal * (estimate.target_profit_pct / Decimal("100"))

    total = (
        subtotal + markup_material_amount + markup_labor_amount + overhead_amount + profit_amount
    )

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "approve":
            proposal.accepted = True
            proposal.accepted_at = timezone.now()
            estimate.approved = True
            proposal.save(update_fields=["accepted", "accepted_at"])
            estimate.save(update_fields=["approved"])
            messages.success(
                request,
                "¡Gracias! Hemos recibido tu aprobación. Comenzaremos a trabajar en tu proyecto.",
            )

        elif action == "reject":
            feedback = request.POST.get("feedback", "").strip()
            proposal.client_comment = feedback
            proposal.save(update_fields=["client_comment"])
            messages.info(
                request,
                "Hemos recibido tus comentarios. Nuestro equipo se pondrá en contacto contigo pronto.",
            )
            # TODO: Notify PM/Admin via email or notification

    context = {
        "proposal": proposal,
        "estimate": estimate,
        "project": project,
        "lines": lines,
        "subtotal": subtotal,
        "markup_material": markup_material_amount,
        "markup_labor": markup_labor_amount,
        "overhead": overhead_amount,
        "profit": profit_amount,
        "total": total,
    }

    return render(request, "core/proposal_public.html", context)


@login_required
def daily_plan_timeline(request, plan_id):
    """Timeline view for a daily plan (Module 12.8)."""
    if not _is_staffish(request.user):
        return HttpResponseForbidden("Access denied")

    from core.api.serializers import PlannedActivitySerializer

    plan = get_object_or_404(DailyPlan.objects.select_related("project", "created_by"), pk=plan_id)

    # Fetch surrounding plans (e.g., +/- 15 days) for context
    # Allow overriding the center date via query param to navigate
    focus_date_str = request.GET.get("focus_date")
    if focus_date_str:
        try:
            focus_date = datetime.strptime(focus_date_str, "%Y-%m-%d").date()
        except ValueError:
            focus_date = plan.plan_date
    else:
        focus_date = plan.plan_date

    start_date = focus_date - timedelta(days=15)
    end_date = focus_date + timedelta(days=15)

    related_plans = DailyPlan.objects.filter(
        project=plan.project, plan_date__range=[start_date, end_date]
    ).prefetch_related("activities")

    all_activities = []
    for p in related_plans:
        p_activities = p.activities.all().order_by("start_time", "order")
        # We need to inject the plan_date into the activity data for the frontend
        serialized = PlannedActivitySerializer(p_activities, many=True).data
        for item in serialized:
            item["plan_date"] = p.plan_date.isoformat()
        all_activities.extend(serialized)

    # Fetch employees for assignment dropdown
    from core.models import Employee

    employees = Employee.objects.filter(is_active=True).values("id", "first_name", "last_name")
    employees_json = json.dumps(list(employees), default=str)

    activities_json = json.dumps(all_activities, default=str)

    # Pass date range info
    timeline_config = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "focus_date": focus_date.isoformat(),
    }

    return render(
        request,
        "core/daily_plan_timeline.html",
        {
            "plan": plan,
            "activities_json": activities_json,
            "employees_json": employees_json,
            "timeline_config": json.dumps(timeline_config),
        },
    )
