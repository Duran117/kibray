"""Shared helpers, constants, and imports used across all view modules.

Extracted from legacy_views.py during Phase 8 split.
"""
from collections import defaultdict  # noqa: F401
import contextlib  # noqa: F401
import csv  # noqa: F401
from datetime import date, datetime, timedelta  # noqa: F401
from decimal import Decimal, InvalidOperation  # noqa: F401
from functools import wraps  # noqa: F401
import io  # noqa: F401
from io import BytesIO  # noqa: F401
import json  # noqa: F401
import logging  # noqa: F401
import re  # noqa: F401

from django.conf import settings  # noqa: F401
from django.contrib import messages  # noqa: F401
from django.contrib.admin.views.decorators import staff_member_required  # noqa: F401
from django.contrib.auth.decorators import login_required  # noqa: F401
from django.contrib.auth.models import User  # noqa: F401
from django.core import signing  # noqa: F401
from django.core.exceptions import ValidationError  # noqa: F401
from django.core.paginator import Paginator  # noqa: F401
from django.db import IntegrityError, transaction  # noqa: F401
from django.db.models import Count, Max, Q, Sum  # noqa: F401
from django.db.models.functions import Coalesce  # noqa: F401
from django.http import (  # noqa: F401
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render  # noqa: F401
from django.template.loader import get_template  # noqa: F401
from django.urls import reverse  # noqa: F401
from django.utils import timezone, translation  # noqa: F401
from django.utils.translation import gettext  # noqa: F401
from django.utils.translation import gettext_lazy as _  # noqa: F401
from django.views.decorators.http import require_http_methods, require_POST  # noqa: F401

try:
    from xhtml2pdf import pisa
except Exception:
    pisa = None

from core import models  # noqa: E402, F401
from core.forms import (  # noqa: E402, F401
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
from core.models import (  # noqa: E402, F401
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
    Notification,
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
    TouchUp,
    TouchUpPhoto,
)
from core.services.earned_value import compute_project_ev  # noqa: E402, F401
from core.services.financial_service import FinancialAnalyticsService  # noqa: E402, F401

logger = logging.getLogger(__name__)

# ─── Role Constants ──────────────────────────────────────────────────
ROLES_ADMIN = {"admin", "superuser"}
ROLES_PM = {"project_manager"}
ROLES_STAFF = ROLES_ADMIN | ROLES_PM
ROLES_FIELD = ROLES_STAFF | {"superintendent"}
ROLES_ALL_INTERNAL = ROLES_FIELD | {"employee", "painter"}
ROLES_CLIENT_SIDE = {"client", "designer", "owner"}
ROLES_PROJECT_ACCESS = ROLES_STAFF | ROLES_CLIENT_SIDE


def _generate_basic_pdf_from_html(html: str) -> bytes:
    """Very small fallback: strip tags and render lines into a single-page PDF."""
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


def _check_user_project_access(user, project):
    """SECURITY: Verify if a user has access to a specific project."""
    from core.models import ClientProjectAccess

    if user.is_staff or user.is_superuser:
        return True, None

    has_explicit_access = ClientProjectAccess.objects.filter(
        user=user, project=project
    ).exists()
    if has_explicit_access:
        return True, None

    if project.client:
        client_text = project.client.strip().lower()
        if client_text and (
            client_text == user.email.lower()
            or client_text == user.get_full_name().lower()
            or client_text == user.username.lower()
        ):
            return True, None

    if hasattr(project, 'assigned_to') and project.assigned_to.filter(id=user.id).exists():
        return True, None

    profile = getattr(user, "profile", None)
    if profile and profile.role == "client":
        return False, "dashboard_client"
    return False, "dashboard"


def _is_admin_user(user):
    """Return True if user is superuser or has admin role."""
    if user.is_superuser or user.is_staff:
        return True
    profile = getattr(user, "profile", None)
    return profile and getattr(profile, "role", None) in ROLES_ADMIN


def _require_admin_or_redirect(request):
    """SECURITY: Guard for admin-only views. Returns None if admin, redirect otherwise."""
    if not _is_admin_user(request.user):
        messages.error(request, _("No tienes permiso para acceder a esta función."))
        return redirect("dashboard")
    return None


def _require_roles(request, allowed_roles, *, allow_staff=True):
    """SECURITY: Guard for role-restricted views. Returns None if allowed, redirect otherwise."""
    if allow_staff and (request.user.is_superuser or request.user.is_staff):
        return None
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", None)
    if role in allowed_roles:
        return None
    messages.error(request, _("No tienes permiso para acceder a esta función."))
    return redirect("dashboard")


def _is_staffish(user):
    """Return True for admin, superuser, or project_manager roles."""
    if user.is_superuser or user.is_staff:
        return True
    profile = getattr(user, "profile", None)
    return profile and getattr(profile, "role", None) in ROLES_STAFF


def _is_pm_or_admin(user):
    """Return True for PM or admin roles."""
    if user.is_superuser or user.is_staff:
        return True
    profile = getattr(user, "profile", None)
    return profile and getattr(profile, "role", None) in ROLES_STAFF


def _parse_date(s):
    """Try to parse a date string in various formats."""
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime((s or "").strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Fecha inválida: {s}")


def staff_required(view_func):
    """Decorator that requires staff/admin/PM role."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if _is_staffish(request.user):
            return view_func(request, *args, **kwargs)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return HttpResponseForbidden("Forbidden")
        messages.error(request, _("No tienes permisos para esta acción."))
        project_id = kwargs.get("project_id")
        return (
            redirect("project_ev", project_id=project_id) if project_id else redirect("dashboard")
        )
    return _wrapped


def _ensure_inventory_item(name: str, category_key: str, unit: str, *, no_threshold=False):
    """
    Busca o crea un InventoryItem con el nombre dado.
    Si no existe, lo crea con umbrales por categoría:
    - Consumibles (tape, plastic, etc.): threshold=5
    - Resto: threshold=1 (a menos que no_threshold=True)
    """
    from core.models import InventoryItem

    consumable_categories = {
        "tape", "plastic", "masking_paper", "floor_paper", "sandpaper",
        "tray_liner", "blades", "gloves", "mask", "respirator", "caulk",
    }

    category_map = {
        "tape": "MATERIAL", "plastic": "MATERIAL", "masking_paper": "MATERIAL",
        "floor_paper": "MATERIAL", "sandpaper": "MATERIAL",
        "paint": "PINTURA", "primer": "PINTURA", "stain": "PINTURA",
        "ladder": "ESCALERA", "sander": "LIJADORA", "sprayer": "SPRAY",
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

    if not created and not item.no_threshold and item.default_threshold is None:
        item.default_threshold = 5 if category_key in consumable_categories else 1
        item.save(update_fields=["default_threshold"])

    return item
