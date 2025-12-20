"""
ChangeOrder-related serializers for the Kibray API
"""
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.models import ChangeOrder, Project


class ChangeOrderListSerializer(serializers.ModelSerializer):
    """List serializer for change orders"""
    project_name = serializers.SerializerMethodField()
    project_id = serializers.IntegerField(source='project.id', read_only=True)
    submitted_date = serializers.DateField(source='date_created', read_only=True)
    number = serializers.SerializerMethodField()
    days_pending = serializers.SerializerMethodField()

    class Meta:
        model = ChangeOrder
        fields = [
            'id', 'number', 'description', 'amount', 'status',
            'submitted_date', 'project_id', 'project_name', 'days_pending'
        ]

    def get_project_name(self, obj):
        return obj.project.name if obj.project else None

    def get_number(self, obj):
        return obj.reference_code or f"CO-{obj.id}"

    def get_days_pending(self, obj):
        if obj.status == 'pending':
            delta = timezone.now().date() - obj.date_created
            return delta.days
        return None


class ChangeOrderDetailSerializer(ChangeOrderListSerializer):
    """Detailed change order serializer"""
    project = serializers.SerializerMethodField()
    photos_count = serializers.SerializerMethodField()

    class Meta(ChangeOrderListSerializer.Meta):
        fields = ChangeOrderListSerializer.Meta.fields + [
            'project', 'notes', 'color', 'reference_code', 'photos_count'
        ]

    def get_project(self, obj):
        from .project_serializers import ProjectListSerializer
        return ProjectListSerializer(obj.project).data

    def get_photos_count(self, obj):
        return obj.photos.count() if hasattr(obj, 'photos') else 0


class ChangeOrderCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating change orders"""
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())

    class Meta:
        model = ChangeOrder
        fields = [
            'project', 'description', 'amount', 'notes',
            'color', 'reference_code', 'status'
        ]

    def validate_amount(self, value):
        """Validate amount is positive"""
        if value < 0:
            raise serializers.ValidationError(_("Amount must be positive"))
        return value

    def validate_reference_code(self, value):
        """Validate reference_code is unique per project"""
        if value:
            project = self.initial_data.get('project')
            if project:
                # Check for existing change orders with same reference_code in same project
                query = ChangeOrder.objects.filter(
                    project_id=project,
                    reference_code=value
                )
                if self.instance:
                    query = query.exclude(pk=self.instance.pk)

                if query.exists():
                    raise serializers.ValidationError(
                        _("A change order with this reference code already exists for this project")
                    )
        return value


class ChangeOrderApprovalSerializer(serializers.Serializer):
    """Serializer for approving/rejecting change orders"""
    approved = serializers.BooleanField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True)
