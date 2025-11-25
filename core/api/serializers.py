from rest_framework import serializers
from django.contrib.auth import get_user_model
from core.models import (
    Notification, ChatChannel, ChatMessage, Task, DamageReport,
    FloorPlan, PlanPin, ColorSample, Project, ScheduleCategory, ScheduleItem,
    Income, Expense, CostCode, BudgetLine, DailyLog, TaskTemplate, WeatherSnapshot
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
    priority = serializers.CharField(read_only=True)
    due_date = serializers.DateField(read_only=True, allow_null=True)
    total_hours = serializers.FloatField(read_only=True)
    time_tracked_hours = serializers.SerializerMethodField()
    dependencies_ids = serializers.SerializerMethodField()
    reopen_events_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'project', 'project_name',
            'assigned_to', 'assigned_to_name', 'status', 'priority',
            'due_date', 'is_touchup', 'created_at', 'started_at',
            'time_tracked_seconds', 'time_tracked_hours', 'total_hours',
            'dependencies_ids', 'reopen_events_count'
        ]
    read_only_fields = ['created_at']

    def get_time_tracked_hours(self, obj):
        return obj.get_time_tracked_hours()

    def get_dependencies_ids(self, obj):
        return list(obj.dependencies.values_list('id', flat=True))

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


# =============================================================================
# FINANCIAL SERIALIZERS
# =============================================================================

class ProjectSerializer(serializers.ModelSerializer):
    """Complete project serializer with financial summary"""
    profit = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    budget_remaining = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    income_count = serializers.SerializerMethodField()
    expense_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'client', 'address', 'start_date', 'end_date',
            'description', 'paint_colors', 'paint_codes', 'stains_or_finishes',
            'number_of_rooms_or_areas', 'number_of_paint_defects',
            'total_income', 'total_expenses', 'profit',
            'budget_total', 'budget_labor', 'budget_materials', 'budget_other',
            'budget_remaining', 'reflection_notes', 'created_at',
            'income_count', 'expense_count'
        ]
        read_only_fields = ['created_at', 'total_income', 'total_expenses', 'profit', 'budget_remaining']
    
    def get_income_count(self, obj):
        return obj.incomes.count()
    
    def get_expense_count(self, obj):
        return obj.expenses.count()


class IncomeSerializer(serializers.ModelSerializer):
    """Income serializer with project details"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_client = serializers.CharField(source='project.client', read_only=True)
    
    class Meta:
        model = Income
        fields = [
            'id', 'project', 'project_name', 'project_client',
            'project_name', 'amount', 'date', 'payment_method',
            'category', 'description', 'invoice', 'notes'
        ]
        read_only_fields = []
    
    def validate_amount(self, value):
        """Ensure amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value
    
    def validate_date(self, value):
        """Ensure date is not in the future"""
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError("Date cannot be in the future.")
        return value


class ExpenseSerializer(serializers.ModelSerializer):
    """Expense serializer with project and cost code details"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    cost_code_name = serializers.CharField(source='cost_code.name', read_only=True, allow_null=True)
    change_order_number = serializers.CharField(source='change_order.number', read_only=True, allow_null=True)
    
    class Meta:
        model = Expense
        fields = [
            'id', 'project', 'project_name', 'amount', 'project_name',
            'date', 'category', 'description', 'receipt', 'invoice',
            'change_order', 'change_order_number', 'cost_code', 'cost_code_name'
        ]
        read_only_fields = []
    
    def validate_amount(self, value):
        """Ensure amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value
    
    def validate_date(self, value):
        """Ensure date is not in the future"""
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError("Date cannot be in the future.")
        return value


class CostCodeSerializer(serializers.ModelSerializer):
    """Cost code serializer"""
    expense_count = serializers.SerializerMethodField()
    total_expenses = serializers.SerializerMethodField()
    
    class Meta:
        model = CostCode
        fields = [
            'id', 'code', 'name', 'category', 'active',
            'expense_count', 'total_expenses'
        ]
        read_only_fields = ['expense_count', 'total_expenses']
    
    def get_expense_count(self, obj):
        return obj.expenses.count()
    
    def get_total_expenses(self, obj):
        from django.db.models import Sum
        total = obj.expenses.aggregate(total=Sum('amount'))['total']
        return total or 0


class BudgetLineSerializer(serializers.ModelSerializer):
    """Budget line serializer with cost code details"""
    cost_code_name = serializers.CharField(source='cost_code.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    total_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = BudgetLine
        fields = [
            'id', 'project', 'project_name', 'cost_code', 'cost_code_name',
            'description', 'qty', 'unit', 'unit_cost', 'allowance',
            'baseline_amount', 'revised_amount', 'total_amount',
            'planned_start', 'planned_finish', 'weight_override'
        ]
        read_only_fields = ['baseline_amount', 'total_amount']
    
    def get_total_amount(self, obj):
        """Return revised amount if set, otherwise baseline"""
        return obj.revised_amount if obj.revised_amount else obj.baseline_amount


class ProjectBudgetSummarySerializer(serializers.Serializer):
    """Summary serializer for project budget tracking"""
    project_id = serializers.IntegerField()
    project_name = serializers.CharField()
    budget_total = serializers.DecimalField(max_digits=14, decimal_places=2)
    budget_labor = serializers.DecimalField(max_digits=14, decimal_places=2)
    budget_materials = serializers.DecimalField(max_digits=14, decimal_places=2)
    budget_other = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_expenses = serializers.DecimalField(max_digits=14, decimal_places=2)
    budget_remaining = serializers.DecimalField(max_digits=14, decimal_places=2)
    percent_spent = serializers.DecimalField(max_digits=5, decimal_places=2)
    is_over_budget = serializers.BooleanField()


# ============================================================================
# PHASE 1: DailyLog Planning Serializers
# ============================================================================

class TaskTemplateSerializer(serializers.ModelSerializer):
    """Serializer for TaskTemplate (Module 29)"""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = TaskTemplate
        fields = [
            'id', 'title', 'description', 'default_priority',
            'estimated_hours', 'tags', 'checklist', 'is_active',
            'category', 'category_display', 'sop_reference',
            'usage_count', 'last_used', 'is_favorite',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'usage_count', 'last_used']


class WeatherSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for WeatherSnapshot (Module 30)"""
    is_stale = serializers.SerializerMethodField()
    
    class Meta:
        model = WeatherSnapshot
        fields = [
            'id', 'project', 'date', 'source',
            'temperature_max', 'temperature_min', 'conditions_text',
            'precipitation_mm', 'wind_kph', 'humidity_percent',
            'fetched_at', 'is_stale', 'latitude', 'longitude'
        ]
        read_only_fields = ['fetched_at']
    
    def get_is_stale(self, obj):
        return obj.is_stale()


class DailyLogPlanningSerializer(serializers.ModelSerializer):
    """Serializer for DailyLog with planning fields"""
    planned_templates = TaskTemplateSerializer(many=True, read_only=True)
    planned_tasks = TaskSerializer(many=True, read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    completion_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = DailyLog
        fields = [
            'id', 'project', 'project_name', 'date', 'weather',
            'crew_count', 'planned_templates', 'planned_tasks',
            'is_complete', 'incomplete_reason', 'auto_weather',
            'created_at', 'updated_at', 'completion_summary'
        ]
        read_only_fields = ['created_at', 'updated_at', 'is_complete', 'incomplete_reason']
    
    def get_completion_summary(self, obj):
        total = obj.planned_tasks.count()
        if total == 0:
            return {'total': 0, 'completed': 0, 'percent': 0}
        completed = obj.planned_tasks.filter(status='Completada').count()
        percent = round((completed / total) * 100, 1) if total > 0 else 0
        return {
            'total': total,
            'completed': completed,
            'percent': percent
        }


class InstantiatePlannedTemplatesSerializer(serializers.Serializer):
    """Serializer for instantiate_planned_templates action"""
    assigned_to_id = serializers.IntegerField(required=False, allow_null=True)
    
    def validate_assigned_to_id(self, value):
        if value is not None:
            from core.models import Employee
            if not Employee.objects.filter(pk=value).exists():
                raise serializers.ValidationError("Employee does not exist")
        return value

