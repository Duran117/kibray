"""
core/access.py — Single source of truth for authorization in Kibray.

This module is the canonical location for:
  - Layer 1: role-identity helpers (is_admin, is_pm, is_employee, is_client...)
  - Layer 2: project-access helpers (accessible_projects, can_view_project...)
  - Layer 3: capability checks (can_view_financials, can_view_labor_cost,
                                can_view_change_order_price, ...)

Decorators (Layer 4) live in core/access_decorators.py and call into here.
Sidebar/menu builder (Layer 5) lives in core/nav.py and calls into here.
DRF API permissions (core/api/permissions.py) call into here.

Design rules:
  - One source of truth. If you need to add a new permission, add it here.
  - Whitelist-only. Every helper returns False/empty by default; only the
    documented role conditions return True.
  - No string magic. Use the ROLE_* constants defined below.
  - Fast path for admin/superuser: short-circuit before touching the database.
  - Anonymous users always return False / empty queryset.

See:
  docs/security/PHASE9_AUDIT.md         — what was broken before this module
  docs/security/PHASE9_ARCHITECTURE.md  — design & rollout plan
"""
from __future__ import annotations

from typing import Optional

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Q, QuerySet

# ─────────────────────────────────────────────────────────────────────────────
# Role constants — DO NOT use raw strings anywhere outside this module
# ─────────────────────────────────────────────────────────────────────────────
ROLE_ADMIN = "admin"
ROLE_OWNER = "owner"
ROLE_PM = "project_manager"
ROLE_EMPLOYEE = "employee"
ROLE_CLIENT = "client"
ROLE_DESIGNER = "designer"
ROLE_SUPERINTENDENT = "superintendent"
#: Profit-share partner (socio). Earns a % of each included project's net
#: instead of an hourly wage. DELIBERATELY excluded from INTERNAL_ROLES so a
#: partner never inherits broad internal/financial access. Partner capabilities
#: (see own earnings, view breakdowns of included projects) are granted by
#: explicit capability helpers only — never by role membership.
ROLE_PARTNER = "partner"

ALL_ROLES = frozenset({
    ROLE_ADMIN, ROLE_OWNER, ROLE_PM, ROLE_EMPLOYEE,
    ROLE_CLIENT, ROLE_DESIGNER, ROLE_SUPERINTENDENT, ROLE_PARTNER,
})

#: Internal-staff roles: have access to operational tools (not just their own work).
#: NOTE: ROLE_PARTNER is intentionally NOT here (see note above).
INTERNAL_ROLES = frozenset({
    ROLE_ADMIN, ROLE_OWNER, ROLE_PM, ROLE_DESIGNER, ROLE_SUPERINTENDENT,
})

#: Roles that may have full company-wide visibility (no per-project gate).
ADMIN_LIKE_ROLES = frozenset({ROLE_ADMIN, ROLE_OWNER})


User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# Layer 1 — Role identity
# ─────────────────────────────────────────────────────────────────────────────
def _authed(user) -> bool:
    """True if user is a real authenticated user (not AnonymousUser)."""
    return bool(user and getattr(user, "is_authenticated", False))


def get_role(user) -> Optional[str]:
    """Return the user's Profile.role string, or None if missing/anonymous.

    Does NOT consult is_superuser/is_staff — those are separate signals.
    """
    if not _authed(user):
        return None
    profile = getattr(user, "profile", None)
    return getattr(profile, "role", None) if profile else None


def is_admin(user) -> bool:
    """Admin = Django superuser OR Profile.role == 'admin'.

    NOTE: is_staff alone is NOT admin — many internal users have is_staff
    without being admins. Use is_staffish() if you want the broader gate.
    """
    if not _authed(user):
        return False
    if user.is_superuser:
        return True
    return get_role(user) == ROLE_ADMIN


def is_owner(user) -> bool:
    return _authed(user) and get_role(user) == ROLE_OWNER


def is_pm(user) -> bool:
    return _authed(user) and get_role(user) == ROLE_PM


def is_employee(user) -> bool:
    """True only for non-staff employees. is_staff employees are 'staffish'."""
    if not _authed(user) or user.is_staff:
        return False
    return get_role(user) == ROLE_EMPLOYEE


def is_client(user) -> bool:
    """Strict: client role AND not staff/superuser. Staff impersonating client
    is NOT a client for permission purposes — they keep their staff powers."""
    if not _authed(user) or user.is_superuser or user.is_staff:
        return False
    return get_role(user) == ROLE_CLIENT


def is_designer(user) -> bool:
    return _authed(user) and get_role(user) == ROLE_DESIGNER


def is_superintendent(user) -> bool:
    return _authed(user) and get_role(user) == ROLE_SUPERINTENDENT


def is_partner(user) -> bool:
    """True for profit-share partners (socios).

    Partners earn a share of project net instead of an hourly wage. This is an
    IDENTITY check only — it grants NO access on its own. Partner capabilities
    (view own earnings, view breakdowns of included projects, metric check-in)
    are granted by explicit capability helpers, never by INTERNAL_ROLES.
    """
    return _authed(user) and get_role(user) == ROLE_PARTNER


def is_director(user) -> bool:
    """True for the profit-share *director* (the business owner/admin).

    Director is NOT a new role — it is the existing admin/owner. The director
    is the only one who configures rates, marks projects into the profit-share,
    posts advances, and sees the direction-overhead destination. Identified by
    role only (no hardcoded names), so production can promote the real owner via
    the normal role system.
    """
    return _authed(user) and (is_admin(user) or is_owner(user))


def is_internal(user) -> bool:
    """Any internal role (admin/owner/pm/designer/superintendent) OR is_staff.
    Excludes plain employees and clients."""
    if not _authed(user):
        return False
    if user.is_superuser or user.is_staff:
        return True
    return get_role(user) in INTERNAL_ROLES


def is_staffish(user) -> bool:
    """Broad staff-like gate: admin OR pm OR owner OR Django is_staff/superuser.

    Use this for "can see internal-tools menu". Do NOT use this for
    object-level access — use can_view_project() instead.

    NOTE: This includes ROLE_OWNER. If you need the narrower predicate
    that excludes owners (legacy behavior of ``_is_staffish`` /
    ``_is_pm_or_admin``), use :func:`is_admin_or_pm` instead.
    """
    if not _authed(user):
        return False
    if user.is_superuser or user.is_staff:
        return True
    return get_role(user) in {ROLE_ADMIN, ROLE_PM, ROLE_OWNER}


def is_admin_or_pm(user) -> bool:
    """Narrow staff gate: admin OR pm OR Django is_staff/superuser.

    Excludes ROLE_OWNER on purpose — promoted in Phase 9 Commit N from
    the legacy ``_is_staffish`` / ``_is_pm_or_admin`` helpers in
    ``core/views/_helpers.py``. Use this when the original code path
    intended "internal operational role" and an external project owner
    must NOT have access (e.g. financial review, change-order
    approval, daily-plan editing, payroll). For the broader gate that
    includes external owners, use :func:`is_staffish` instead.
    """
    if not _authed(user):
        return False
    if user.is_superuser or user.is_staff:
        return True
    return get_role(user) in {ROLE_ADMIN, ROLE_PM}


# ─────────────────────────────────────────────────────────────────────────────
# Layer 2 — Project-level access
# ─────────────────────────────────────────────────────────────────────────────
def _legacy_client_match_q(user) -> Q:
    """Q object for the legacy text-match: project.client == username/email/full_name.

    Kept for back-compat with projects created before ClientProjectAccess existed.
    Migration recommendation: backfill ClientProjectAccess and remove this fallback.
    """
    candidates = {user.username.strip().lower()}
    if user.email:
        candidates.add(user.email.strip().lower())
    full = user.get_full_name().strip().lower() if hasattr(user, "get_full_name") else ""
    if full:
        candidates.add(full)
    candidates.discard("")
    if not candidates:
        return Q(pk__in=[])  # match nothing
    # Project.client is CharField; compare lowercased
    return Q(client__iexact=user.username) | Q(client__iexact=user.email or "") | Q(
        client__iexact=full or ""
    )


def accessible_projects(user) -> "QuerySet":
    """Return the QuerySet of Project objects the user is allowed to see.

    Rules:
      - anonymous          → empty
      - admin/superuser    → all projects
      - is_staff           → all projects (internal employee with admin login)
      - PM                 → projects via ProjectManagerAssignment(pm=user)
      - employee           → projects via ResourceAssignment OR TimeEntry
      - client             → projects via active ClientProjectAccess
                             OR legacy soft-match on project.client text field
      - other internal roles (designer/superintendent/owner) → all projects
        (default; tighten when business rules clarify)
    """
    # Lazy import to avoid circular imports at module load
    from core.models import Project

    if not _authed(user):
        return Project.objects.none()

    # Fast path: full access
    if user.is_superuser or user.is_staff or is_admin(user):
        return Project.objects.all()

    role = get_role(user)

    if role in {ROLE_OWNER, ROLE_DESIGNER, ROLE_SUPERINTENDENT}:
        # Internal roles default to full access until business rules tighten them.
        return Project.objects.all()

    if role == ROLE_PM:
        return Project.objects.filter(pm_assignments__pm=user).distinct()

    if role == ROLE_EMPLOYEE:
        from core.models import TimeEntry
        time_project_ids = TimeEntry.objects.filter(
            employee__user=user, project__isnull=False
        ).values("project_id")
        return Project.objects.filter(
            Q(resource_assignments__employee__user=user) | Q(pk__in=time_project_ids)
        ).distinct()

    if role == ROLE_CLIENT:
        from core.models import ClientProjectAccess
        explicit = Q(pk__in=ClientProjectAccess.objects.filter(
            user=user, is_active=True
        ).values("project_id"))
        return Project.objects.filter(explicit | _legacy_client_match_q(user)).distinct()

    return Project.objects.none()


def can_view_project(user, project) -> bool:
    """True if user is allowed to view this specific project.

    Implementation short-circuits per role rather than evaluating
    accessible_projects() — keeps O(1) for admin and per-project lookups cheap.
    """
    if not _authed(user) or project is None:
        return False
    if user.is_superuser or user.is_staff or is_admin(user):
        return True

    role = get_role(user)

    if role in {ROLE_OWNER, ROLE_DESIGNER, ROLE_SUPERINTENDENT}:
        return True

    if role == ROLE_PM:
        return project.pm_assignments.filter(pm=user).exists()

    if role == ROLE_EMPLOYEE:
        from core.models import ResourceAssignment, TimeEntry
        if ResourceAssignment.objects.filter(employee__user=user, project=project).exists():
            return True
        if TimeEntry.objects.filter(employee__user=user, project=project).exists():
            return True
        return False

    if role == ROLE_CLIENT:
        return _client_has_project_access(user, project)

    return False


def can_edit_project(user, project) -> bool:
    """True if user may modify the project record itself."""
    if not _authed(user) or project is None:
        return False
    if user.is_superuser or is_admin(user):
        return True
    if user.is_staff:
        return True
    if is_pm(user):
        return project.pm_assignments.filter(pm=user).exists()
    return False


def get_client_access(user, project):
    """Return the ClientProjectAccess row for this user/project, or None.

    Used by capability checks like can_view_financials() to read per-row flags.
    """
    if not is_client(user) or project is None:
        return None
    from core.models import ClientProjectAccess
    return ClientProjectAccess.objects.filter(
        user=user, project=project, is_active=True
    ).first()


def _client_has_project_access(user, project) -> bool:
    """Internal: True if a client user can access this project (explicit or legacy)."""
    from core.models import ClientProjectAccess
    if ClientProjectAccess.objects.filter(
        user=user, project=project, is_active=True
    ).exists():
        return True
    # Legacy fallback: project.client text matches username/email/full_name
    client_text = (project.client or "").strip().lower()
    if not client_text:
        return False
    candidates = {user.username.strip().lower()}
    if user.email:
        candidates.add(user.email.strip().lower())
    full = user.get_full_name().strip().lower() if hasattr(user, "get_full_name") else ""
    if full:
        candidates.add(full)
    candidates.discard("")
    return client_text in candidates


def _has_relation(model, related_name: str) -> bool:
    """Reserved for future defensive checks. Currently unused."""
    try:
        model._meta.get_field(related_name)
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Layer 3 — Capability checks (feature × project)
# ─────────────────────────────────────────────────────────────────────────────
# Financial visibility ───────────────────────────────────────────────────────

def can_view_financials(user, project) -> bool:
    """Generic 'can this user see ANY financial data for this project'.

    - Admin / owner / superuser / is_staff → True (with project access).
    - PM → True for assigned projects.
    - Employee → False (always).
    - Client → True only if ClientProjectAccess.can_view_financials is set.
    - Designer / superintendent → False (operational roles, not financial).
    """
    if not _authed(user) or project is None:
        return False
    if not can_view_project(user, project):
        return False
    if user.is_superuser or is_admin(user) or is_owner(user) or user.is_staff:
        return True
    if is_pm(user):
        return True
    if is_client(user):
        access = get_client_access(user, project)
        return bool(access and access.can_view_financials)
    return False


def can_view_budget(user, project) -> bool:
    return can_view_financials(user, project)


def can_view_expenses(user, project) -> bool:
    """Expenses are internal-cost data: never visible to clients."""
    if is_client(user):
        return False
    return can_view_financials(user, project)


def can_view_incomes(user, project) -> bool:
    return can_view_financials(user, project)


def can_view_labor_cost(user, project) -> bool:
    """Labor cost = sensitive internal data. Admin/owner only.

    PM may see assigned-project labor cost (operational need); clients and
    employees never see it.
    """
    if not _authed(user) or project is None or not can_view_project(user, project):
        return False
    if user.is_superuser or is_admin(user) or is_owner(user):
        return True
    if is_pm(user):
        return True
    return False


def can_view_profit(user, project) -> bool:
    """Profit = revenue − cost. Admin/owner only — not even PMs by default."""
    if not _authed(user) or project is None or not can_view_project(user, project):
        return False
    if user.is_superuser or is_admin(user) or is_owner(user):
        return True
    return False


# Schedule / calendar ────────────────────────────────────────────────────────

def can_view_schedule(user, project) -> bool:
    """Anyone with project access can read the schedule."""
    return can_view_project(user, project)


def can_create_schedule_event(user, project) -> bool:
    if not can_view_project(user, project):
        return False
    if user.is_superuser or is_admin(user) or user.is_staff:
        return True
    if is_pm(user):
        return True
    return False


def can_edit_schedule_event(user, event) -> bool:
    if event is None:
        return False
    project = getattr(event, "project", None)
    return can_create_schedule_event(user, project)


# Change orders ─────────────────────────────────────────────────────────────

def can_view_change_order(user, co) -> bool:
    if co is None:
        return False
    return can_view_project(user, getattr(co, "project", None))


def can_create_change_order(user, project) -> bool:
    if not can_view_project(user, project):
        return False
    if user.is_superuser or is_admin(user) or user.is_staff:
        return True
    if is_pm(user):
        return True
    return False


def can_approve_change_order(user, co) -> bool:
    if not can_view_change_order(user, co):
        return False
    if user.is_superuser or is_admin(user):
        return True
    if is_client(user):
        access = get_client_access(user, co.project)
        return bool(access and access.can_approve_change_orders)
    return False


def can_view_change_order_price(user, co) -> bool:
    """Price visibility = financial visibility.

    A client without can_view_financials sees the change order existence and
    description, but not the dollar amount.
    """
    if not can_view_change_order(user, co):
        return False
    return can_view_financials(user, co.project)


# Internal / employee data ───────────────────────────────────────────────────

def can_view_employee_data(user) -> bool:
    """Employee directory, pay rates: admin/owner only."""
    if not _authed(user):
        return False
    return user.is_superuser or is_admin(user) or is_owner(user)


def can_edit_employee_data(user) -> bool:
    return can_view_employee_data(user)


def can_view_internal_notes(user, project) -> bool:
    """Internal notes = visible only to internal staff with project access."""
    if not can_view_project(user, project):
        return False
    return is_internal(user)


# Client portal ─────────────────────────────────────────────────────────────

def can_access_client_portal(user, project) -> bool:
    """Client portal pages: clients (with access) plus admin (impersonating)."""
    if not _authed(user) or project is None:
        return False
    if user.is_superuser or is_admin(user) or user.is_staff:
        return True
    if is_client(user):
        return _client_has_project_access(user, project)
    return False


def can_view_client_safe_data(user, project) -> bool:
    """Always-safe project metadata visible to anyone with project access."""
    return can_view_project(user, project)


# ─────────────────────────────────────────────────────────────────────────────
# Convenience
# ─────────────────────────────────────────────────────────────────────────────
def assert_can_view_project(user, project) -> None:
    """Raise PermissionDenied if the user cannot view the project."""
    if not can_view_project(user, project):
        raise PermissionDenied("You do not have access to this project.")


def filter_by_project_access(user, qs, project_field: str = "project"):
    """Restrict any QuerySet to objects whose `project_field` is accessible.

    Example:
        expenses = filter_by_project_access(request.user, Expense.objects.all())
    """
    if not _authed(user):
        return qs.none()
    if user.is_superuser or user.is_staff or is_admin(user):
        return qs
    project_ids = list(accessible_projects(user).values_list("pk", flat=True))
    return qs.filter(**{f"{project_field}_id__in": project_ids})


# ─────────────────────────────────────────────────────────────────────────────
# View-helper conveniences (promoted from core/views/_helpers.py in Phase 9
# Commit M). These return Django primitives (HttpResponse / tuples) rather
# than booleans so view callers can drop them in directly.
# ─────────────────────────────────────────────────────────────────────────────
def check_project_access(user, project):
    """Project-access check that returns ``(ok, redirect_destination)``.

    Used by view modules that follow the pattern::

        ok, dest = check_project_access(request.user, project)
        if not ok:
            messages.error(request, "Access denied.")
            return redirect(dest)

    The boolean comes from :func:`can_view_project`. The legacy
    ``project.assigned_to`` many-to-many is honored as a back-compat
    fallback so users explicitly attached to a project keep access
    even if no other relationship exists.

    The redirect destination is role-aware:
      - ``"dashboard_client"`` for client-role users
      - ``"dashboard"`` otherwise
    """
    if can_view_project(user, project):
        return True, None
    if (
        project is not None
        and hasattr(project, "assigned_to")
        and project.assigned_to.filter(id=user.id).exists()
    ):
        return True, None
    return False, ("dashboard_client" if is_client(user) else "dashboard")


def require_admin_or_redirect(request):
    """Guard for admin-only function-based views.

    Returns ``None`` when the request user is admin-like (canonical
    :func:`is_admin` OR ``user.is_staff`` for back-compat with internal
    employees who have an admin login). Otherwise flashes an error
    message and returns a ``redirect("dashboard")`` response that the
    view should ``return`` directly::

        guard = require_admin_or_redirect(request)
        if guard is not None:
            return guard
    """
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.utils.translation import gettext as _

    user = request.user
    if is_admin(user) or bool(getattr(user, "is_staff", False)):
        return None
    messages.error(
        request, _("You don't have permission to access this feature.")
    )
    return redirect("dashboard")


def require_director_or_redirect(request):
    """Guard for director-only profit-share pages (panel, calculator, rates).

    Director = admin or owner (see :func:`is_director`). Plain ``is_staff`` is
    NOT enough here — these pages expose money levers. Returns ``None`` when
    allowed, otherwise a ``redirect`` the view should return directly.
    """
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.utils.translation import gettext as _

    if is_director(request.user):
        return None
    messages.error(
        request, _("You don't have permission to access this feature.")
    )
    return redirect("dashboard")


def require_profit_share_access_or_redirect(request):
    """Guard for the "My Earnings" page: partners OR the director.

    A socio sees their own earnings; the director sees theirs too. Everyone
    else (employees, clients, anonymous) is redirected. Returns ``None`` when
    allowed, otherwise a ``redirect`` the view should return directly.
    """
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.utils.translation import gettext as _

    user = request.user
    if is_director(user) or is_partner(user):
        return None
    messages.error(
        request, _("You don't have permission to access this feature.")
    )
    return redirect("dashboard")


__all__ = [
    # Constants
    "ROLE_ADMIN", "ROLE_OWNER", "ROLE_PM", "ROLE_EMPLOYEE",
    "ROLE_CLIENT", "ROLE_DESIGNER", "ROLE_SUPERINTENDENT", "ROLE_PARTNER",
    "ALL_ROLES", "INTERNAL_ROLES", "ADMIN_LIKE_ROLES",
    # Layer 1
    "get_role", "is_admin", "is_owner", "is_pm", "is_employee",
    "is_client", "is_designer", "is_superintendent",
    "is_partner", "is_director",
    "is_internal", "is_staffish", "is_admin_or_pm",
    # Layer 2
    "accessible_projects", "can_view_project", "can_edit_project",
    "get_client_access",
    # Layer 3 — financial
    "can_view_financials", "can_view_budget", "can_view_expenses",
    "can_view_incomes", "can_view_labor_cost", "can_view_profit",
    # Layer 3 — schedule
    "can_view_schedule", "can_create_schedule_event", "can_edit_schedule_event",
    # Layer 3 — change orders
    "can_view_change_order", "can_create_change_order",
    "can_approve_change_order", "can_view_change_order_price",
    # Layer 3 — internal
    "can_view_employee_data", "can_edit_employee_data",
    "can_view_internal_notes",
    # Layer 3 — client portal
    "can_access_client_portal", "can_view_client_safe_data",
    # Convenience
    "assert_can_view_project", "filter_by_project_access",
    # View-helper conveniences (Phase 9 Commit M)
    "check_project_access", "require_admin_or_redirect",
    # Profit-share guards
    "require_director_or_redirect", "require_profit_share_access_or_redirect",
]
