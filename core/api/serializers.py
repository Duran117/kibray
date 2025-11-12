from rest_framework import serializers
from django.contrib.auth import get_user_model
from core.models import (
    Notification, ChatChannel, ChatMessage, Task, DamageReport,
    FloorPlan, PlanPin, ColorSample, Project, ScheduleCategory, ScheduleItem
)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'link_url', 'is_read', 'created_at']
        read_only_fields = ['created_at']

class ChatChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatChannel
        fields = ['id', 'name', 'project', 'created_at']
        read_only_fields = ['created_at']

class ChatMessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'channel', 'user', 'message', 'link_url', 'image', 'created_at']
        read_only_fields = ['user', 'created_at']

class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True, allow_null=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'project', 'project_name',
            'assigned_to', 'assigned_to_name', 'status', 'is_touchup',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class DamageReportSerializer(serializers.ModelSerializer):
    reported_by_name = serializers.CharField(source='reported_by.get_full_name', read_only=True, allow_null=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = DamageReport
        fields = [
            'id', 'project', 'project_name', 'title', 'description',
            'severity', 'status', 'reported_by', 'reported_by_name',
            'photo', 'created_at', 'updated_at'
        ]
        read_only_fields = ['reported_by', 'created_at', 'updated_at']

class ColorSampleSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = ColorSample
        fields = [
            'id', 'project', 'project_name', 'name', 'code', 'brand',
            'status', 'swatch_image', 'created_at'
        ]
        read_only_fields = ['created_at']

class PlanPinSerializer(serializers.ModelSerializer):
    color_sample_name = serializers.CharField(source='color_sample.name', read_only=True, allow_null=True)
    linked_task_title = serializers.CharField(source='linked_task.title', read_only=True, allow_null=True)
    
    class Meta:
        model = PlanPin
        fields = [
            'id', 'plan', 'x', 'y', 'title', 'description', 'pin_type',
            'color_sample', 'color_sample_name', 'linked_task', 'linked_task_title',
            'pin_color', 'is_multipoint', 'path_points', 'created_at'
        ]
        read_only_fields = ['created_at', 'pin_color']

class FloorPlanSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    pins = PlanPinSerializer(many=True, read_only=True)
    
    class Meta:
        model = FloorPlan
        fields = ['id', 'project', 'project_name', 'name', 'image', 'created_at', 'pins']
        read_only_fields = ['created_at']

class ProjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'client', 'address', 'start_date', 'end_date', 'created_at']
        read_only_fields = ['created_at']

class ScheduleCategorySerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ScheduleCategory
        fields = [
            'id', 'project', 'name', 'description', 'order', 'parent',
            'is_phase', 'item_count', 'planned_start', 'planned_end',
            'status', 'percent_complete'
        ]
        read_only_fields = ['item_count']
    
    def get_item_count(self, obj):
        return obj.items.count()

class ScheduleItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    dependencies_list = serializers.SerializerMethodField()
    
    class Meta:
        model = ScheduleItem
        fields = [
            'id', 'project', 'category', 'category_name', 'name', 'description',
            'order', 'planned_start', 'planned_end', 'actual_start', 'actual_end',
            'status', 'percent_complete', 'is_milestone', 'dependencies',
            'dependencies_list', 'cost_code', 'budget_line', 'estimate_line'
        ]
    
    def get_dependencies_list(self, obj):
        """Return comma-separated list of dependency IDs for Frappe Gantt format"""
        if obj.dependencies:
            return ','.join(str(dep.id) for dep in obj.dependencies.all())
        return ''
