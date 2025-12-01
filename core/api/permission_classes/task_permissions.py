"""
Task-related permissions for the Kibray API
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsTaskAssigneeOrProjectMember(BasePermission):
    """
    Permission for task assignee or project members
    """
    message = "You must be the task assignee or a project member"
    
    def has_object_permission(self, request, view, obj):
        # Superusers have full access
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Check if user is the assignee
        if hasattr(obj, 'assigned_to') and obj.assigned_to:
            if hasattr(obj.assigned_to, 'user') and obj.assigned_to.user == request.user:
                return True
        
        # Check if user is project member
        if hasattr(obj, 'project'):
            project = obj.project
            
            # Project lead
            if hasattr(project, 'project_lead') and project.project_lead:
                if hasattr(project.project_lead, 'user') and project.project_lead.user == request.user:
                    return True
            
            # Observers (read-only)
            if request.method in SAFE_METHODS and hasattr(project, 'observers'):
                observers = project.observers.all()
                for observer in observers:
                    if hasattr(observer, 'user') and observer.user == request.user:
                        return True
        
        return False


class CanUpdateTaskStatus(BasePermission):
    """
    Permission to update task status
    """
    message = "You don't have permission to update task status"
    
    def has_object_permission(self, request, view, obj):
        # Superusers and staff can update
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Task assignee can update
        if hasattr(obj, 'assigned_to') and obj.assigned_to:
            if hasattr(obj.assigned_to, 'user') and obj.assigned_to.user == request.user:
                return True
        
        # Project lead can update
        if hasattr(obj, 'project'):
            project = obj.project
            if hasattr(project, 'project_lead') and project.project_lead:
                if hasattr(project.project_lead, 'user') and project.project_lead.user == request.user:
                    return True
        
        return False


class CanDeleteTask(BasePermission):
    """
    Permission to delete tasks
    """
    message = "Only project lead or admin can delete tasks"
    
    def has_object_permission(self, request, view, obj):
        # Only superusers, staff, or project lead can delete
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Project lead can delete
        if hasattr(obj, 'project'):
            project = obj.project
            if hasattr(project, 'project_lead') and project.project_lead:
                if hasattr(project.project_lead, 'user') and project.project_lead.user == request.user:
                    return True
        
        return False
