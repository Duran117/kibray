"""
Custom permissions for the Kibray API

Role hierarchy:
- Owner: Full access to everything
- PM (Project Manager): Access to assigned projects + financial data
- Superintendent: Field management (change orders, daily logs, schedules)
- Employee: Time entries, tasks, limited project view
- Client: Read-only access to their projects
"""

from rest_framework import permissions

from core.models import ClientProjectAccess, Profile


class IsOwner(permissions.BasePermission):
    """
    Only users with 'owner' role can access
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            return request.user.profile.role == "owner"
        except Profile.DoesNotExist:
            return False


class IsOwnerOrPM(permissions.BasePermission):
    """
    Owner or Project Manager can access
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            return request.user.profile.role in ["owner", "pm"]
        except Profile.DoesNotExist:
            return False


class IsOwnerOrPMOrSuperintendent(permissions.BasePermission):
    """
    Owner, PM, or Superintendent can access
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            return request.user.profile.role in ["owner", "pm", "superintendent"]
        except Profile.DoesNotExist:
            return False


class CanAccessProject(permissions.BasePermission):
    """
    User has access to this specific project
    - Owner/PM: All projects
    - Superintendent: Assigned projects
    - Employee: Projects they have time entries on
    - Client: Projects explicitly granted access via ClientProjectAccess
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        project = obj if hasattr(obj, "project") else obj

        try:
            profile = user.profile

            # Owner and PM have access to all projects
            if profile.role in ["owner", "pm"]:
                return True

            # Superintendent: Check if assigned to project
            if profile.role == "superintendent":
                # Add logic here when superintendent assignment is implemented
                return True

            # Client: Check ClientProjectAccess
            if profile.role == "client":
                return ClientProjectAccess.objects.filter(user=user, project=project, is_active=True).exists()

            # Employee: Has time entries or tasks on this project
            if profile.role == "employee":
                from core.models import Task, TimeEntry

                has_time = TimeEntry.objects.filter(employee__user=user, project=project).exists()
                has_tasks = Task.objects.filter(assigned_to=user, project=project).exists()
                return has_time or has_tasks

            return False
        except Profile.DoesNotExist:
            return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Owner can edit, others can only read
    Useful for financial data, cost codes, etc.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for owner
        try:
            return request.user.profile.role == "owner"
        except Profile.DoesNotExist:
            return False
