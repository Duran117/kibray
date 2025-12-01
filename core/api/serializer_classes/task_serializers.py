"""
Task-related serializers for the Kibray API
"""
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.models import Task, Project, Employee
from .user_serializers import UserMinimalSerializer


class TaskListSerializer(serializers.ModelSerializer):
    """List serializer for tasks"""
    project_name = serializers.SerializerMethodField()
    assignee = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority', 
            'due_date', 'created_at', 'project_name', 'assignee', 'is_overdue'
        ]
    
    def get_project_name(self, obj):
        return obj.project.name if obj.project else None
    
    def get_assignee(self, obj):
        if obj.assigned_to:
            # Employee model, return user details
            if hasattr(obj.assigned_to, 'user'):
                return UserMinimalSerializer(obj.assigned_to.user).data
            return {'id': obj.assigned_to.id, 'username': str(obj.assigned_to)}
        return None
    
    def get_is_overdue(self, obj):
        if obj.due_date and obj.status != 'Completada':
            return obj.due_date < timezone.now().date()
        return False


class TaskDetailSerializer(TaskListSerializer):
    """Detailed task serializer with full information"""
    project = serializers.SerializerMethodField()
    assignee_detail = serializers.SerializerMethodField()
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    attachments_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    time_logs = serializers.SerializerMethodField()
    
    class Meta(TaskListSerializer.Meta):
        fields = TaskListSerializer.Meta.fields + [
            'project', 'assignee_detail', 'created_by_detail', 
            'attachments_count', 'comments_count', 'time_logs', 'completed_at'
        ]
    
    def get_project(self, obj):
        from .project_serializers import ProjectListSerializer
        return ProjectListSerializer(obj.project).data
    
    def get_assignee_detail(self, obj):
        if obj.assigned_to:
            if hasattr(obj.assigned_to, 'user'):
                return UserMinimalSerializer(obj.assigned_to.user).data
            return {'id': obj.assigned_to.id, 'name': str(obj.assigned_to)}
        return None
    
    def get_attachments_count(self, obj):
        return obj.images.count() if hasattr(obj, 'images') else 0
    
    def get_comments_count(self, obj):
        return obj.comments.count() if hasattr(obj, 'comments') else 0
    
    def get_time_logs(self, obj):
        """Get time entries for this task"""
        # TimeEntry might be linked via project, simplified version
        return []


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating tasks"""
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Task
        fields = [
            'project', 'title', 'description', 'status', 'priority',
            'due_date', 'assigned_to'
        ]
    
    def validate_due_date(self, value):
        """Validate that due_date is not in the past for new tasks"""
        if value and not self.instance:  # Only for new tasks
            if value < timezone.now().date():
                raise serializers.ValidationError(_("Due date cannot be in the past"))
        return value
    
    def validate_priority(self, value):
        """Validate priority is in valid choices"""
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        if value not in valid_priorities:
            raise serializers.ValidationError(
                _(f"Priority must be one of: {', '.join(valid_priorities)}")
            )
        return value


class TaskStatsSerializer(serializers.Serializer):
    """Serializer for task statistics"""
    status_counts = serializers.DictField(child=serializers.IntegerField())
    priority_counts = serializers.DictField(child=serializers.IntegerField())
    assignee_distribution = serializers.ListField(child=serializers.DictField())
    overdue_count = serializers.IntegerField()
