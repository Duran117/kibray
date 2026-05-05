"""
core/access_decorators.py — View decorators that delegate to core.access.

These are the canonical decorators for protecting Django function-based views.
All authorization logic lives in core/access.py; these are thin wrappers.

Usage:
    from core.access_decorators import (
        require_login, require_admin, require_role, require_internal,
        require_project_access, require_can_view_financials,
    )

    @require_admin
    def admin_dashboard(request): ...

    @require_role("project_manager", "admin")
    def pm_view(request): ...

    @require_project_access(project_arg="project_id")
    def project_detail(request, project_id): ...

    @require_can_view_financials(project_arg="project_id")
    def project_financials(request, project_id): ...

Behavior:
  - Anonymous users → redirect to LOGIN_URL (or 403 if return_403=True).
  - Authenticated but unauthorized → 403 PermissionDenied.
  - PermissionDenied is raised (not redirect) for object-level failures so
    Django's standard 403.html / DRF handler is reused.
"""
from __future__ import annotations

from functools import wraps
from typing import Callable, Iterable

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404

from core import access


# ─────────────────────────────────────────────────────────────────────────────
# Identity-only gates
# ─────────────────────────────────────────────────────────────────────────────
def require_login(view_func: Callable) -> Callable:
    """Plain alias for django.contrib.auth.decorators.login_required.

    Provided so views import everything from one place.
    """
    return login_required(view_func)


def require_admin(view_func: Callable) -> Callable:
    """Allow only admin (Profile.role == 'admin' OR is_superuser)."""

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not access.is_admin(request.user):
            raise PermissionDenied("Admin access required.")
        return view_func(request, *args, **kwargs)

    return _wrapped


def require_internal(view_func: Callable) -> Callable:
    """Allow any internal staff (admin/owner/pm/designer/super OR is_staff)."""

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not access.is_internal(request.user):
            raise PermissionDenied("Internal staff access required.")
        return view_func(request, *args, **kwargs)

    return _wrapped


def require_staffish(view_func: Callable) -> Callable:
    """Allow staff-like users (admin/pm/owner OR is_staff/superuser)."""

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not access.is_staffish(request.user):
            raise PermissionDenied("Staff access required.")
        return view_func(request, *args, **kwargs)

    return _wrapped


def require_role(*roles: str) -> Callable:
    """Allow only users with one of the given Profile.role values.

    Admin and superuser ALWAYS pass (unless explicitly excluded). This prevents
    accidentally locking out admins from sub-role-specific views.

    Example:
        @require_role("project_manager", "designer")
        def schedule_editor(request): ...
    """
    valid = frozenset(roles)
    unknown = valid - access.ALL_ROLES
    if unknown:
        raise ValueError(f"Unknown role(s) in @require_role: {sorted(unknown)}")

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if access.is_admin(user) or access.get_role(user) in valid:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied(
                f"Requires one of these roles: {sorted(valid)}"
            )

        return _wrapped

    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# Object-level gates
# ─────────────────────────────────────────────────────────────────────────────
def _resolve_project(request, args, kwargs, project_arg: str):
    """Look up Project by id from kwargs (or args), 404 if missing."""
    from core.models import Project

    project_id = kwargs.get(project_arg)
    if project_id is None:
        # Fall back to positional args by name (rare for Django views)
        raise Http404(f"Missing project id ({project_arg}).")
    return get_object_or_404(Project, pk=project_id)


def require_project_access(project_arg: str = "project_id") -> Callable:
    """Require user can view the Project identified by ``project_arg`` kwarg.

    The project is fetched via get_object_or_404 and injected into the view as
    ``project`` keyword argument so the view can reuse it without a second
    DB hit.

    Example:
        @require_project_access(project_arg="project_id")
        def project_detail(request, project_id, project=None):
            return render(request, ..., {"project": project})
    """

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            project = _resolve_project(request, args, kwargs, project_arg)
            if not access.can_view_project(request.user, project):
                raise PermissionDenied("You do not have access to this project.")
            kwargs.setdefault("project", project)
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def require_can_view_financials(project_arg: str = "project_id") -> Callable:
    """Require user can view financial data for the project."""

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            project = _resolve_project(request, args, kwargs, project_arg)
            if not access.can_view_financials(request.user, project):
                raise PermissionDenied(
                    "You do not have access to financial data for this project."
                )
            kwargs.setdefault("project", project)
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def require_can_edit_project(project_arg: str = "project_id") -> Callable:
    """Require user can modify the project record."""

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            project = _resolve_project(request, args, kwargs, project_arg)
            if not access.can_edit_project(request.user, project):
                raise PermissionDenied("You cannot edit this project.")
            kwargs.setdefault("project", project)
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


__all__ = [
    "require_login",
    "require_admin",
    "require_internal",
    "require_staffish",
    "require_role",
    "require_project_access",
    "require_can_view_financials",
    "require_can_edit_project",
]
