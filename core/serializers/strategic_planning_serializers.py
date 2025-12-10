from rest_framework import serializers
from core.models import (
    StrategicPlanningSession,
    StrategicDay,
    StrategicItem,
    StrategicTask,
    StrategicSubtask,
    StrategicMaterialRequirement,
    StrategicDependency,
    Employee,
    ActivityTemplate,
    TaskTemplate,
    MaterialCatalog,
    InventoryItem
)

class StrategicSubtaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategicSubtask
        fields = ['id', 'description', 'order', 'exported_to_daily_plan']
        read_only_fields = ['exported_to_daily_plan']

class StrategicTaskSerializer(serializers.ModelSerializer):
    subtasks = StrategicSubtaskSerializer(many=True, read_only=True)
    
    class Meta:
        model = StrategicTask
        fields = [
            'id', 'strategic_item', 'description', 'order', 'estimated_hours', 
            'assigned_to', 'linked_task_template', 
            'subtasks', 'subtasks_count', 'exported_to_daily_plan'
        ]
        read_only_fields = ['exported_to_daily_plan']

class StrategicMaterialRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategicMaterialRequirement
        fields = [
            'id', 'strategic_item', 'name', 'quantity', 'unit', 'notes',
            'linked_catalog_item', 'linked_inventory_item',
            'is_on_hand'
        ]

class StrategicItemSerializer(serializers.ModelSerializer):
    tasks = StrategicTaskSerializer(many=True, read_only=True)
    material_requirements = StrategicMaterialRequirementSerializer(many=True, read_only=True)
    assigned_to_names = serializers.SerializerMethodField()
    
    class Meta:
        model = StrategicItem
        fields = [
            'id', 'strategic_day', 'title', 'description', 'order', 'priority',
            'estimated_hours', 'assigned_to', 'assigned_to_names',
            'location_area', 'linked_activity_template',
            'tasks', 'material_requirements', 'tasks_count',
            'exported_to_daily_plan'
        ]
        read_only_fields = ['exported_to_daily_plan']

    def get_assigned_to_names(self, obj):
        return [f"{e.first_name} {e.last_name}" for e in obj.assigned_to.all()]

class StrategicDaySerializer(serializers.ModelSerializer):
    items = StrategicItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = StrategicDay
        fields = [
            'id', 'target_date', 'notes', 'estimated_total_hours',
            'linked_schedule_item', 'items', 'items_count', 'day_name'
        ]

class StrategicPlanningSessionSerializer(serializers.ModelSerializer):
    """Serializer for list view (no nested days)"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    created_by_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = StrategicPlanningSession
        fields = [
            'id', 'project', 'project_name', 'user', 'created_by_name',
            'date_range_start', 'date_range_end', 'status',
            'notes', 'is_approved', 'total_days',
            'exported_to_daily_plan', 'created_at'
        ]
        read_only_fields = ['user', 'status', 'exported_to_daily_plan']

class StrategicPlanningSessionDetailSerializer(StrategicPlanningSessionSerializer):
    """Serializer for detail view (includes full nested structure)"""
    days = StrategicDaySerializer(many=True, read_only=True)
    
    class Meta(StrategicPlanningSessionSerializer.Meta):
        fields = StrategicPlanningSessionSerializer.Meta.fields + ['days']

class StrategicDependencySerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategicDependency
        fields = '__all__'
