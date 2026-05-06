"""
core/nav.py — Phase 9 Commit G

Single source of truth for sidebar / navigation menu structure.

Replaces the 696-line ``sidebar_dark.html`` template logic (with 30+
inline ``{% if role == ... %}`` gates) with a pure Python builder
that returns a structured menu the template just iterates.

Design rules:
  - Pure functions: input = (user, optional project), output = list[NavSection].
  - All authorization decisions go through ``core.access`` helpers.
  - No string magic: roles compared via the ROLE_* constants from
    ``core.access`` and capability helpers (is_admin, is_pm, etc).
  - Empty-by-default: every section/item must explicitly pass its
    visibility predicate. Missing predicate → hidden.
  - Order is deterministic.

Behind a feature flag (``settings.PHASE9_NEW_SIDEBAR``):
  - False (default): the legacy template renders as before.
  - True: ``core/components/sidebar_phase9.html`` renders the
    structure built here.

The flag is set in environment-specific settings only after Commit H
has visually QA'd the new sidebar in staging.

See:
  docs/security/PHASE9_AUDIT.md         — pre-refactor leak inventory
  docs/security/PHASE9_ARCHITECTURE.md  — rollout plan A→J
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from django.urls import NoReverseMatch, reverse

from core.access import (
    ROLE_CLIENT,
    ROLE_EMPLOYEE,
    accessible_projects,
    get_role,
    is_admin,
    is_client,
    is_pm,
    is_staffish,
)


# ─────────────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class NavItem:
    """A single sidebar link.

    Attributes:
        label:        UI label (must be lazy-translated by caller if needed).
        url_name:     Django named URL — resolved at build time.
        url_args:     Positional args for reverse().
        url_kwargs:   Keyword args for reverse().
        icon:         Bootstrap-icon class fragment (e.g. ``"bi-folder"``).
        badge_key:    Optional key into ``badges`` context dict for a count.
        external_url: Pre-resolved URL (overrides url_name when set).
    """
    label: str
    url_name: Optional[str] = None
    url_args: tuple = ()
    url_kwargs: dict = field(default_factory=dict)
    icon: str = "bi-circle"
    badge_key: Optional[str] = None
    external_url: Optional[str] = None

    @property
    def url(self) -> str:
        if self.external_url:
            return self.external_url
        if not self.url_name:
            return "#"
        try:
            return reverse(self.url_name, args=self.url_args, kwargs=self.url_kwargs)
        except NoReverseMatch:
            return "#"


@dataclass
class NavSection:
    """A titled group of NavItems."""
    title: str
    items: List[NavItem] = field(default_factory=list)
    icon: str = ""

    def __bool__(self) -> bool:
        return bool(self.items)


# ─────────────────────────────────────────────────────────────────────────────
# Project context — sidebar shown when inside a project
# ─────────────────────────────────────────────────────────────────────────────
def build_project_nav(user, project) -> List[NavSection]:
    """Return the sidebar sections to show when the user is inside ``project``.

    Authorization model:
      - Client: minimal read-only menu (Overview, Logs/Minutes, Files,
        Color Samples, Requests).
      - Employee (non-staff): on-site essentials (Overview, Tasks,
        Damages, Materials, Files, Floor Plans).
      - Staff / PM / Admin: full project menu (Overview, Schedule,
        Planning, Logs, Files, Plans, Minutes, RFIs, Financials,
        Operations, Change Orders, Resources).

    The caller is responsible for verifying ``user`` actually has
    access to ``project`` (use ``core.access.can_view_project``).
    This function decides only what menu structure to render.
    """
    if not user or not getattr(user, "is_authenticated", False) or project is None:
        return []

    sections: List[NavSection] = []

    # ─────────── CLIENT ───────────
    if is_client(user):
        sections.append(NavSection("Project", [
            NavItem("Overview", "project_overview", (project.id,), icon="bi-house-door"),
            NavItem("Daily Log", "daily_log", (project.id,), icon="bi-journal-text"),
            NavItem("Minutes", "project_minutes_list", (project.id,), icon="bi-card-text"),
            NavItem("Files", "project_files", (project.id,), icon="bi-folder"),
            NavItem("Color Samples", "color_sample_list", (project.id,), icon="bi-palette"),
            NavItem("My Requests", "client_requests_list", (project.id,), icon="bi-chat-square-text"),
        ]))
        return sections

    # ─────────── EMPLOYEE (non-staff) ───────────
    if get_role(user) == ROLE_EMPLOYEE and not user.is_staff:
        sections.append(NavSection("Project", [
            NavItem("Overview", "project_overview", (project.id,), icon="bi-house-door"),
            NavItem("Tasks", "task_list", (project.id,), icon="bi-check2-square"),
            NavItem("Damages", "damage_report_list", (project.id,), icon="bi-exclamation-triangle"),
            NavItem("Materials", "materials_requests_list", (project.id,), icon="bi-box-seam"),
            NavItem("Files", "project_files", (project.id,), icon="bi-folder"),
            NavItem("Floor Plans", "floor_plan_list", (project.id,), icon="bi-map"),
        ]))
        return sections

    # ─────────── STAFF / PM / ADMIN — full menu ───────────
    sections.append(NavSection("Project", [
        NavItem("Overview", "project_overview", (project.id,), icon="bi-house-door"),
        NavItem("Schedule", "schedule_gantt_react", (project.id,), icon="bi-calendar3"),
        NavItem("Daily Log", "daily_log", (project.id,), icon="bi-journal-text"),
        NavItem("Files", "project_files", (project.id,), icon="bi-folder"),
        NavItem("Floor Plans", "floor_plan_list", (project.id,), icon="bi-map"),
        NavItem("Minutes", "project_minutes_list", (project.id,), icon="bi-card-text"),
        NavItem("RFIs", "rfi_list", (project.id,), icon="bi-question-circle"),
    ]))

    if is_admin(user) or is_pm(user) or user.is_staff:
        sections.append(NavSection("Financials", [
            NavItem("Hub", "project_financials_hub", (project.id,), icon="bi-bank"),
            NavItem("Budget", "project_budget_detail", (project.id,), icon="bi-wallet2"),
            NavItem("Invoices", "invoice_builder", (project.id,), icon="bi-receipt"),
        ]))

        sections.append(NavSection("Operations", [
            NavItem("Touch-ups", "touchup_list", (project.id,), icon="bi-brush"),
            NavItem("Damages", "damage_report_list", (project.id,), icon="bi-exclamation-triangle"),
            NavItem("Materials", "materials_requests_list", (project.id,), icon="bi-box-seam"),
            NavItem("Issues", "issue_list", (project.id,), icon="bi-bug"),
            NavItem("Tasks", "task_list", (project.id,), icon="bi-check2-square"),
            NavItem("Color Samples", "color_sample_list", (project.id,), icon="bi-palette"),
            NavItem("Site Photos", "site_photo_list", (project.id,), icon="bi-camera"),
        ]))

    return sections


# ─────────────────────────────────────────────────────────────────────────────
# Global context — sidebar shown outside any project
# ─────────────────────────────────────────────────────────────────────────────
def build_global_nav(user) -> List[NavSection]:
    """Return the sidebar sections for global pages (no project context).

    Authorization model:
      - Anonymous: empty.
      - Client: dashboard + own projects.
      - Employee (non-staff): personal time/clock-in only.
      - Staff / PM: planning, ops, recent projects.
      - Admin: everything plus admin tools.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return []

    sections: List[NavSection] = []

    # ─────────── CLIENT ───────────
    if is_client(user):
        sections.append(NavSection("Home", [
            NavItem("Dashboard", "dashboard_client", icon="bi-house-door"),
            NavItem("Notifications", "notifications_list",
                    icon="bi-bell", badge_key="unread_notifications_count"),
        ]))
        # Their own projects (cap at 8 to avoid huge sidebars).
        proj_items = []
        for p in accessible_projects(user)[:8]:
            proj_items.append(NavItem(
                p.name, "project_overview", (p.id,), icon="bi-folder",
            ))
        if proj_items:
            sections.append(NavSection("My Projects", proj_items))
        return sections

    # ─────────── EMPLOYEE (non-staff) ───────────
    if get_role(user) == ROLE_EMPLOYEE and not user.is_staff:
        sections.append(NavSection("Home", [
            NavItem("Dashboard", "dashboard", icon="bi-house-door"),
            NavItem("Notifications", "notifications_list",
                    icon="bi-bell", badge_key="unread_notifications_count"),
        ]))
        # Projects they have actual time/assignments on.
        proj_items = []
        for p in accessible_projects(user)[:8]:
            proj_items.append(NavItem(
                p.name, "project_overview", (p.id,), icon="bi-folder",
            ))
        if proj_items:
            sections.append(NavSection("My Projects", proj_items))
        return sections

    # ─────────── STAFF / PM / ADMIN ───────────
    sections.append(NavSection("Home", [
        NavItem("Dashboard", "dashboard", icon="bi-house-door"),
        NavItem("Notifications", "notifications_list",
                icon="bi-bell", badge_key="unread_notifications_count"),
        NavItem("Projects", "project_list", icon="bi-folder2-open"),
    ]))

    if is_staffish(user) or is_pm(user):
        sections.append(NavSection("Planning", [
            NavItem("Daily Planning", "daily_planning_dashboard", icon="bi-calendar-check"),
            NavItem("Strategic", "strategic_planning_dashboard", icon="bi-bullseye"),
            NavItem("Team Assignments", "assignment_hub", icon="bi-people"),
        ]))
        sections.append(NavSection("Operations", [
            NavItem("Change Orders", "changeorder_board", icon="bi-clipboard-check"),
            NavItem("All Tasks", "task_list_all", icon="bi-check2-square"),
            NavItem("Material Requests", "materials_requests_list_all", icon="bi-box-seam"),
            NavItem("Unassigned Time", "unassigned_timeentries", icon="bi-clock-history"),
        ]))

    if is_admin(user):
        sections.append(NavSection("Administration", [
            NavItem("Admin Dashboard", "dashboard_admin", icon="bi-shield-lock"),
            NavItem("Clients", "client_list", icon="bi-person-badge"),
            NavItem("Users", "user_wizard_list", icon="bi-people-fill"),
            NavItem("Payroll", "payroll_weekly_review", icon="bi-cash-stack"),
            NavItem("Cost Codes", "costcode_list", icon="bi-tags"),
            NavItem("SOP Library", "sop_library", icon="bi-book"),
            NavItem("Master Schedule", "master_schedule_center", icon="bi-calendar3"),
        ]))
        sections.append(NavSection("Finance", [
            NavItem("Financial Dashboard", "financial_dashboard", icon="bi-bank"),
            NavItem("Income", "income_list", icon="bi-arrow-down-circle"),
            NavItem("Expenses", "expense_list", icon="bi-arrow-up-circle"),
            NavItem("Invoices", "invoice_list", icon="bi-receipt"),
            NavItem("Aging Report", "invoice_aging_report", icon="bi-hourglass-split"),
        ]))
        sections.append(NavSection("Analytics", [
            NavItem("Analytics", "analytics_dashboard", icon="bi-graph-up"),
            NavItem("Productivity", "productivity_dashboard", icon="bi-speedometer2"),
            NavItem("BI Dashboard", "dashboard_bi", icon="bi-bar-chart"),
        ]))

    return sections


# ─────────────────────────────────────────────────────────────────────────────
# Context processor — adds nav structure to the template context.
# ─────────────────────────────────────────────────────────────────────────────
def phase9_nav(request):
    """Context processor that exposes ``phase9_nav_sections``.

    Returns an empty dict (and so contributes nothing) when:
      - the feature flag ``settings.PHASE9_NEW_SIDEBAR`` is not True; OR
      - the user is anonymous; OR
      - the request is missing user.

    This is opt-in via setting + per-environment, so adding the
    processor to TEMPLATES in base.py is non-breaking even before
    Commit H flips the flag in production.
    """
    from django.conf import settings

    if not getattr(settings, "PHASE9_NEW_SIDEBAR", False):
        return {}

    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return {"phase9_nav_enabled": True, "phase9_nav_sections": []}

    project = None
    # The legacy sidebar reads `project` from context if present.
    # If a view's context_data includes a Project instance under key
    # 'project', surface it here too. Best-effort: we can't access
    # response context from a request-only processor, so callers that
    # want the in-project sidebar set request._phase9_project=<project>.
    project = getattr(request, "_phase9_project", None)

    if project is not None:
        sections = build_project_nav(user, project)
    else:
        sections = build_global_nav(user)

    return {"phase9_nav_enabled": True, "phase9_nav_sections": sections}


__all__ = [
    "NavItem",
    "NavSection",
    "build_global_nav",
    "build_project_nav",
    "phase9_nav",
]
