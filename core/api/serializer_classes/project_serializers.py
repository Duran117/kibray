"""
Project-related serializers for the Kibray API
"""
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.models import ClientOrganization, Project, ClientContact
from .user_serializers import UserMinimalSerializer


class ClientOrganizationMinimalSerializer(serializers.ModelSerializer):
    """Minimal client organization serializer"""
    
    class Meta:
        model = ClientOrganization
        fields = ['id', 'name']


class ClientContactMinimalSerializer(serializers.ModelSerializer):
    """Minimal client contact serializer"""
    full_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    
    class Meta:
        model = ClientContact
        fields = ['id', 'full_name', 'email']
    
    def get_full_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
        return "Unknown"
    
    def get_email(self, obj):
        return obj.user.email if obj.user else ""


class ProjectListSerializer(serializers.ModelSerializer):
    """List serializer for projects with basic info"""
    billing_organization = ClientOrganizationMinimalSerializer(read_only=True)
    project_lead = ClientContactMinimalSerializer(read_only=True)
    progress = serializers.SerializerMethodField()
    total_budget = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'project_code', 'address', 'client', 'start_date', 
            'end_date', 'created_at', 'billing_organization', 'project_lead',
            'progress', 'total_budget', 'status'
        ]
    
    def get_progress(self, obj):
        """Calculate project progress based on completed tasks"""
        total_tasks = obj.tasks.count()
        if total_tasks == 0:
            return 0
        completed_tasks = obj.tasks.filter(status='Completada').count()
        return int((completed_tasks / total_tasks) * 100)
    
    def get_total_budget(self, obj):
        """Sum of all budget fields"""
        return float(obj.budget_total or 0)
    
    def get_status(self, obj):
        """Determine project status based on dates"""
        from django.utils import timezone
        today = timezone.now().date()
        
        if obj.end_date and obj.end_date < today:
            return 'COMPLETED'
        elif obj.start_date > today:
            return 'PENDING'
        else:
            return 'ACTIVE'


class ProjectDetailSerializer(ProjectListSerializer):
    """Detailed project serializer with all information"""
    observers = ClientContactMinimalSerializer(many=True, read_only=True)
    tasks_count = serializers.SerializerMethodField()
    pending_changeorders_count = serializers.SerializerMethodField()
    total_files_count = serializers.SerializerMethodField()
    recent_activity = serializers.SerializerMethodField()
    
    class Meta(ProjectListSerializer.Meta):
        fields = ProjectListSerializer.Meta.fields + [
            'description', 'paint_colors', 'paint_codes', 'stains_or_finishes',
            'number_of_rooms_or_areas', 'budget_labor', 'budget_materials', 
            'budget_other', 'observers', 'tasks_count', 'pending_changeorders_count',
            'total_files_count', 'recent_activity'
        ]
    
    def get_tasks_count(self, obj):
        return obj.tasks.count()
    
    def get_pending_changeorders_count(self, obj):
        return obj.change_orders.filter(status='pending').count()
    
    def get_total_files_count(self, obj):
        # Count task images and change order photos
        task_images = sum(task.images.count() for task in obj.tasks.all())
        co_photos = sum(co.photos.count() for co in obj.change_orders.all())
        return task_images + co_photos
    
    def get_recent_activity(self, obj):
        """Get last 5 activities related to project"""
        from django.utils import timezone
        activities = []
        
        # Recent tasks
        recent_tasks = obj.tasks.order_by('-created_at')[:3]
        for task in recent_tasks:
            activities.append({
                'type': 'task',
                'id': task.id,
                'title': task.title,
                'timestamp': task.created_at,
                'status': task.status
            })
        
        # Recent change orders
        recent_cos = obj.change_orders.order_by('-date_created')[:2]
        for co in recent_cos:
            activities.append({
                'type': 'changeorder',
                'id': co.id,
                'title': f"CO: {co.reference_code or co.id}",
                'timestamp': co.date_created,
                'amount': float(co.amount)
            })
        
        # Sort by timestamp and return last 5
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities[:5]


class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating projects"""
    billing_organization = serializers.PrimaryKeyRelatedField(
        queryset=ClientOrganization.objects.all(),
        required=False,
        allow_null=True
    )
    project_lead = serializers.PrimaryKeyRelatedField(
        queryset=ClientContact.objects.all(),
        required=False,
        allow_null=True
    )
    observers = serializers.PrimaryKeyRelatedField(
        queryset=ClientContact.objects.all(),
        many=True,
        required=False
    )
    
    class Meta:
        model = Project
        fields = [
            'name', 'project_code', 'client', 'address', 'start_date', 'end_date',
            'description', 'paint_colors', 'paint_codes', 'stains_or_finishes',
            'number_of_rooms_or_areas', 'budget_total', 'budget_labor',
            'budget_materials', 'budget_other', 'billing_organization',
            'project_lead', 'observers'
        ]
    
    def validate(self, data):
        """Validate that start_date is before end_date"""
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError({
                    'end_date': _("End date must be after start date")
                })
        return data
    
    def validate_billing_organization(self, value):
        """Validate that organization exists and is active"""
        if value and not value.is_active:
            raise serializers.ValidationError(_("Selected organization is not active"))
        return value


class ProjectStatsSerializer(serializers.Serializer):
    """Serializer for project statistics"""
    project_id = serializers.IntegerField()
    project_name = serializers.CharField()
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    in_progress_tasks = serializers.IntegerField()
    total_budget = serializers.DecimalField(max_digits=10, decimal_places=2)
    spent_budget = serializers.DecimalField(max_digits=10, decimal_places=2)
    budget_variance = serializers.DecimalField(max_digits=10, decimal_places=2)
