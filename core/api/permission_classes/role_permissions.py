"""
Role-based permissions for Kibray API.

SECURITY: These permissions enforce role-based access control (RBAC) across all
API viewsets. Employees should only see data relevant to them; financial and
administrative data is restricted to staff/admin/PM roles.
"""

from rest_framework.permissions import BasePermission


def _get_user_role(user):
    """Helper to get user's role from profile."""
    profile = getattr(user, "profile", None)
    return getattr(profile, "role", None) if profile else None


class IsStaffOrAdmin(BasePermission):
    """
    Only staff users, superusers, admins, or project managers can access.
    Blocks employees and clients entirely.
    
    Use for: financial data, payroll, budget, invoices, audit logs, etc.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True
        role = _get_user_role(request.user)
        return role in ("admin", "project_manager", "general_manager")


class IsStaffOrReadOnlyForEmployee(BasePermission):
    """
    Staff/admin/PM get full access.
    Employees get read-only access.
    Clients are blocked.
    
    Use for: tasks, daily plans, color samples, damage reports (operational data).
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True
        role = _get_user_role(request.user)
        if role in ("admin", "project_manager", "general_manager", "designer", "superintendent"):
            return True
        if role == "employee" and request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return False


class DenyEmployeeAccess(BasePermission):
    """
    Deny access to users with 'employee' role.
    All other authenticated users are allowed.
    
    Use for: sensitive administrative endpoints (audit logs, login attempts, etc.)
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = _get_user_role(request.user)
        if role == "employee":
            return False
        return True
