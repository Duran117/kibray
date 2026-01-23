"""
Task-related serializers for the Kibray API
"""

from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.models import Employee, Project, Task

from .user_serializers import UserMinimalSerializer


class TaskListSerializer(serializers.ModelSerializer):
    """List serializer for tasks"""

    project_name = serializers.SerializerMethodField()
    assignee = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "created_at",
            "project",
            "is_touchup",
            "project_name",
            "assignee",
            "is_overdue",
        ]

    def get_project_name(self, obj):
        return obj.project.name if obj.project else None

    def get_assignee(self, obj):
        if obj.assigned_to:
            # Employee model, return user details
            if hasattr(obj.assigned_to, "user"):
                return UserMinimalSerializer(obj.assigned_to.user).data
            return {"id": obj.assigned_to.id, "username": str(obj.assigned_to)}
        return None

    def get_is_overdue(self, obj):
        if obj.due_date and obj.status != "Completed":
            return obj.due_date < timezone.now().date()
        return False


class TaskDetailSerializer(TaskListSerializer):
    """Detailed task serializer with full information"""

    project = serializers.SerializerMethodField()
    assignee_detail = serializers.SerializerMethodField()
    created_by_detail = UserMinimalSerializer(source="created_by", read_only=True)
    attachments_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    time_logs = serializers.SerializerMethodField()

    class Meta(TaskListSerializer.Meta):
        fields = TaskListSerializer.Meta.fields + [
            "project",
            "assignee_detail",
            "created_by_detail",
            "attachments_count",
            "comments_count",
            "time_logs",
            "completed_at",
        ]

    def get_project(self, obj):
        from .project_serializers import ProjectListSerializer

        return ProjectListSerializer(obj.project).data

    def get_assignee_detail(self, obj):
        if obj.assigned_to:
            if hasattr(obj.assigned_to, "user"):
                return UserMinimalSerializer(obj.assigned_to.user).data
            return {"id": obj.assigned_to.id, "name": str(obj.assigned_to)}
        return None

    def get_attachments_count(self, obj):
        return obj.images.count() if hasattr(obj, "images") else 0

    def get_comments_count(self, obj):
        return obj.comments.count() if hasattr(obj, "comments") else 0

    def get_time_logs(self, obj):
        """Get time entries for this task"""
        # TimeEntry might be linked via project, simplified version
        return []


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating tasks"""

    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), required=False, allow_null=True
    )
    # Accept dependencies from clients; expose computed dependencies_ids in responses
    dependencies = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )
    dependencies_ids = serializers.SerializerMethodField(read_only=True)
    progress_percent = serializers.IntegerField(required=False)
    reopen_events_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Task
        fields = [
            "project",
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "assigned_to",
            "dependencies",
            "dependencies_ids",
            "progress_percent",
            "reopen_events_count",
        ]

    def validate_due_date(self, value):
        """Validate that due_date is not in the past for new tasks"""
        if value and not self.instance and value < timezone.now().date():  # Only for new tasks
            raise serializers.ValidationError(_("Due date cannot be in the past"))
        return value

    def validate_priority(self, value):
        """Validate priority is in valid choices"""
        valid_priorities = ["low", "medium", "high", "urgent"]
        if value not in valid_priorities:
            raise serializers.ValidationError(
                _(f"Priority must be one of: {', '.join(valid_priorities)}")
            )
        return value

    def create(self, validated_data):
        dep_ids = validated_data.pop("dependencies", [])
        task = super().create(validated_data)
        if dep_ids:
            from core.models import Task as TaskModel

            deps = TaskModel.objects.filter(id__in=dep_ids)
            task.dependencies.add(*deps)
        return task

    def update(self, instance, validated_data):
        dep_ids = validated_data.pop("dependencies", None)
        task = super().update(instance, validated_data)
        if dep_ids is not None:
            from core.models import Task as TaskModel

            deps = TaskModel.objects.filter(id__in=dep_ids)
            task.dependencies.set(deps)
        return task

    def get_dependencies_ids(self, obj):
        try:
            return list(obj.dependencies.values_list("id", flat=True))
        except Exception:
            return []

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Ensure dependencies_ids always present in responses
        data["dependencies_ids"] = self.get_dependencies_ids(instance)
        data["reopen_events_count"] = getattr(instance, "reopen_events_count", 0)
        return data


class TaskStatsSerializer(serializers.Serializer):
    """Serializer for task statistics"""

    status_counts = serializers.DictField(child=serializers.IntegerField())
    priority_counts = serializers.DictField(child=serializers.IntegerField())
    assignee_distribution = serializers.ListField(child=serializers.DictField())
    overdue_count = serializers.IntegerField()
