"""
Custom DRF permissions for the Kibray API.

THIN WRAPPERS over core.access — the canonical authorization layer.

Phase 9 fix (G1): the legacy implementations of IsOwnerOrPM,
IsOwnerOrPMOrSuperintendent, and CanAccessProject compared
``profile.role`` against the literal string ``"pm"``, but Profile.role
choices use ``"project_manager"``. Result: every Project Manager was
silently denied access to API endpoints protected by these classes.

All classes now delegate to ``core.access`` — the single source of truth.
Backwards-compatible: same class names, same behavior contract; just no
longer broken for PMs.
"""
from rest_framework import permissions

from core import access


class IsOwner(permissions.BasePermission):
    """Only Profile.role == 'owner' (or admin/superuser)."""

    message = "Owner role required."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return access.is_admin(user) or access.is_owner(user)


class IsOwnerOrPM(permissions.BasePermission):
    """Owner OR Project Manager (or admin/superuser)."""

    message = "Owner or Project Manager role required."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if access.is_admin(user) or user.is_superuser:
            return True
        return access.is_owner(user) or access.is_pm(user)


class IsOwnerOrPMOrSuperintendent(permissions.BasePermission):
    """Owner, PM, or Superintendent (or admin/superuser)."""

    message = "Owner, Project Manager, or Superintendent role required."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if access.is_admin(user) or user.is_superuser:
            return True
        return (
            access.is_owner(user)
            or access.is_pm(user)
            or access.is_superintendent(user)
        )


class CanAccessProject(permissions.BasePermission):
    """Object-level: user has access to this specific project.

    Works on either a Project instance or any object with a ``.project``
    attribute (Task, TimeEntry, ChangeOrder, etc.). NOTE the legacy
    implementation had a bug: ``obj if hasattr(obj, "project") else obj``
    always returned obj itself. This version correctly resolves the related
    Project instance.
    """

    message = "You do not have access to this project."

    def has_object_permission(self, request, view, obj):
        from core.models import Project
        if isinstance(obj, Project):
            project = obj
        else:
            project = getattr(obj, "project", None)
            if project is None:
                pid = getattr(obj, "project_id", None)
                if pid is None:
                    return False
                project = Project.objects.filter(pk=pid).first()
        return access.can_view_project(request.user, project)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Read for any authenticated user; write only for Owner/admin."""

    message = "Only Owner can modify this resource."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return access.is_admin(user) or access.is_owner(user)


class IsAdminOrPM(permissions.BasePermission):
    """Admin/Owner/PM gate (used for sensitive data like Payroll).

    Django ``is_staff`` and ``is_superuser`` always pass.
    """

    message = "Admin, Owner, or Project Manager role required."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or user.is_superuser:
            return True
        return (
            access.is_admin(user)
            or access.is_owner(user)
            or access.is_pm(user)
        )


__all__ = [
    "IsOwner",
    "IsOwnerOrPM",
    "IsOwnerOrPMOrSuperintendent",
    "CanAccessProject",
    "IsOwnerOrReadOnly",
    "IsAdminOrPM",
]
