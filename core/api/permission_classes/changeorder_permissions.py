"""
ChangeOrder-related permissions for the Kibray API
"""
from rest_framework.permissions import BasePermission


class CanApproveChangeOrder(BasePermission):
    """
    Permission to approve or reject change orders
    """
    message = "You don't have permission to approve change orders"

    def has_object_permission(self, request, view, obj):
        # Superusers and staff can approve
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Project lead can approve
        if (
            hasattr(obj, 'project')
            and hasattr(obj.project, 'project_lead')
            and obj.project.project_lead
            and hasattr(obj.project.project_lead, 'user')
            and obj.project.project_lead.user == request.user
        ):
            return True

        # Check if user has specific approval permission in profile
        if hasattr(request.user, 'profile'):
            profile = request.user.profile
            if hasattr(profile, 'can_approve_change_orders') and profile.can_approve_change_orders:
                return True

        return False


class CanSubmitChangeOrder(BasePermission):
    """
    Permission to submit change orders
    """
    message = "You must be a project member to submit change orders"

    def has_object_permission(self, request, view, obj):
        # Superusers and staff can submit
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Project members can submit
        if hasattr(obj, 'project'):
            project = obj.project

            # Project lead
            if (
                hasattr(project, 'project_lead')
                and project.project_lead
                and hasattr(project.project_lead, 'user')
                and project.project_lead.user == request.user
            ):
                return True

            # Check if user is in organization
            if (
                hasattr(request.user, 'profile')
                and hasattr(request.user.profile, 'client_contact')
                and hasattr(project, 'billing_organization')
                and project.billing_organization
                and request.user.profile.client_contact.organization == project.billing_organization
            ):
                return True

        return True  # Allow for list view
