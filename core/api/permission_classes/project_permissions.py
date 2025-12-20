"""
Custom permissions for the Kibray API
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsProjectMember(BasePermission):
    """
    Permission to check if user is a project member (lead, assigned, or observer)
    """
    message = "You must be a project member to perform this action"

    def has_object_permission(self, request, view, obj):
        # Allow safe methods (GET, HEAD, OPTIONS) for all authenticated users
        if request.method in SAFE_METHODS:
            return True

        # Superusers have full access
        if request.user.is_superuser:
            return True

        # Check if user is project lead (via ClientContact)
        if (
            hasattr(obj, 'project_lead')
            and obj.project_lead
            and hasattr(obj.project_lead, 'user')
            and obj.project_lead.user == request.user
        ):
            return True

        # Check if user is in assigned users (for projects with User assignments)
        # Note: Current Project model uses ClientContact, not User directly
        # This is for future compatibility

        # Observers have read-only access
        if hasattr(obj, 'observers'):
            observers = obj.observers.all()
            for observer in observers:
                if hasattr(observer, 'user') and observer.user == request.user:
                    # Observers can only read
                    return request.method in SAFE_METHODS

        return False


class IsProjectLeadOrReadOnly(BasePermission):
    """
    Permission to allow only project lead to modify, others can read
    """
    message = "Only the project lead can modify this project"

    def has_object_permission(self, request, view, obj):
        # Read permissions for all authenticated users
        if request.method in SAFE_METHODS:
            return True

        # Superusers can modify
        if request.user.is_superuser:
            return True

        # Check if user is project lead
        if (
            hasattr(obj, 'project_lead')
            and obj.project_lead
            and hasattr(obj.project_lead, 'user')
        ):
            return obj.project_lead.user == request.user

        return False


class IsBillingOrganizationMember(BasePermission):
    """
    Permission to check if user is member of billing organization
    """
    message = "You must be a member of the billing organization"

    def has_object_permission(self, request, view, obj):
        # Superusers have access
        if request.user.is_superuser:
            return True

        # Check if user's profile has client_contact linked to organization
        return (
            hasattr(request.user, 'profile')
            and hasattr(request.user.profile, 'client_contact')
            and hasattr(obj, 'billing_organization')
            and obj.billing_organization
            and request.user.profile.client_contact.organization == obj.billing_organization
        )


class CanManageProject(BasePermission):
    """
    Combined permission for complex project management checks
    """
    message = "You don't have permission to manage this project"

    def has_object_permission(self, request, view, obj):
        # Superusers can manage
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Project lead can manage
        if (
            hasattr(obj, 'project_lead')
            and obj.project_lead
            and hasattr(obj.project_lead, 'user')
            and obj.project_lead.user == request.user
        ):
            return True

        # Billing organization members can view
        return (
            request.method in SAFE_METHODS
            and hasattr(request.user, 'profile')
            and hasattr(request.user.profile, 'client_contact')
            and hasattr(obj, 'billing_organization')
            and obj.billing_organization
            and request.user.profile.client_contact.organization == obj.billing_organization
        )
