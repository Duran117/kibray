from rest_framework import serializers

from core.models import (
    Project,
    ScheduleDependencyV2,
    ScheduleItemV2,
    SchedulePhaseV2,
    ScheduleTaskV2,
    TaskChecklistItem,
)


class TaskChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskChecklistItem
        fields = [
            "id",
            "description",
            "is_completed",
            "order",
            "sop_reference",
            "created_at",
        ]


class ScheduleTaskV2Serializer(serializers.ModelSerializer):
    checklist_items = TaskChecklistItemSerializer(many=True, read_only=True)
    assigned_to_name = serializers.SerializerMethodField()
    completed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ScheduleTaskV2
        fields = [
            "id",
            "title",
            "description",
            "status",
            "weight_percent",
            "assigned_to",
            "assigned_to_name",
            "due_date",
            "completed_at",
            "completed_by",
            "completed_by_name",
            "order",
            "created_at",
            "updated_at",
            "checklist_items",
        ]

    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.get_full_name() or obj.assigned_to.username
        return None

    def get_completed_by_name(self, obj):
        if obj.completed_by:
            return obj.completed_by.get_full_name() or obj.completed_by.username
        return None


class ScheduleItemV2Serializer(serializers.ModelSerializer):
    tasks = ScheduleTaskV2Serializer(many=True, read_only=True)
    phase_name = serializers.CharField(source="phase.name", read_only=True)
    assigned_to_name = serializers.SerializerMethodField()
    allow_sunday_effective = serializers.SerializerMethodField()
    calculated_progress = serializers.ReadOnlyField()
    remaining_weight_percent = serializers.ReadOnlyField()

    class Meta:
        model = ScheduleItemV2
        fields = [
            "id",
            "project",
            "phase",
            "phase_name",
            "name",
            "description",
            "start_date",
            "end_date",
            "assigned_to",
            "assigned_to_name",
            "color",
            "status",
            "progress",
            "weight_percent",
            "calculated_progress",
            "remaining_weight_percent",
            "order",
            "is_milestone",
            "allow_sunday_override",
            "allow_sunday_effective",
            "created_at",
            "updated_at",
            "tasks",
        ]

    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.get_full_name() or obj.assigned_to.username
        return None

    def get_allow_sunday_effective(self, obj):
        # precedence: item override -> phase flag -> False
        if obj.allow_sunday_override:
            return True
        return bool(obj.phase and obj.phase.allow_sunday)


class SchedulePhaseV2Serializer(serializers.ModelSerializer):
    items = ScheduleItemV2Serializer(many=True, read_only=True)
    calculated_progress = serializers.ReadOnlyField()
    remaining_weight_percent = serializers.ReadOnlyField()

    class Meta:
        model = SchedulePhaseV2
        fields = [
            "id",
            "project",
            "name",
            "color",
            "order",
            "weight_percent",
            "calculated_progress",
            "remaining_weight_percent",
            "allow_sunday",
            "created_at",
            "updated_at",
            "items",
        ]


class SchedulePhaseV2WriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating stages with weight validation."""
    
    class Meta:
        model = SchedulePhaseV2
        fields = [
            "project",
            "name",
            "color",
            "order",
            "weight_percent",
            "allow_sunday",
        ]

    def validate(self, attrs):
        project = attrs.get("project") or getattr(self.instance, "project", None)
        weight_percent = attrs.get("weight_percent")
        
        if weight_percent is not None and project:
            # Calculate remaining weight available for this project
            current_weight = float(self.instance.weight_percent) if self.instance else 0
            other_phases = SchedulePhaseV2.objects.filter(project=project)
            if self.instance:
                other_phases = other_phases.exclude(id=self.instance.id)
            used = sum(float(p.weight_percent) for p in other_phases)
            remaining = 100 - used
            
            if float(weight_percent) > remaining:
                raise serializers.ValidationError({
                    "weight_percent": f"El porcentaje no puede exceder {remaining}% disponible en el proyecto"
                })
        
        return attrs


class ScheduleDependencyV2Serializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleDependencyV2
        fields = [
            "id",
            "source_item",
            "target_item",
            "dependency_type",
            "created_at",
        ]


class ProjectMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "start_date", "end_date", "project_code", "is_archived"]


class ScheduleItemV2WriteSerializer(serializers.ModelSerializer):
    phase = serializers.PrimaryKeyRelatedField(
        queryset=SchedulePhaseV2.objects.all(),
        required=False,
        allow_null=True,
    )
    
    class Meta:
        model = ScheduleItemV2
        fields = [
            "project",
            "phase",
            "name",
            "description",
            "start_date",
            "end_date",
            "assigned_to",
            "color",
            "status",
            "progress",
            "weight_percent",
            "order",
            "is_milestone",
            "allow_sunday_override",
        ]

    def validate(self, attrs):
        start_date = attrs.get("start_date") or getattr(self.instance, "start_date", None)
        end_date = attrs.get("end_date") or getattr(self.instance, "end_date", None)

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                {"end_date": "end_date no puede ser anterior a start_date"}
            )

        progress = attrs.get("progress")
        if progress is not None and (progress < 0 or progress > 100):
            raise serializers.ValidationError({"progress": "progress debe estar entre 0 y 100"})

        project = attrs.get("project") or getattr(self.instance, "project", None)
        phase = attrs.get("phase") or getattr(self.instance, "phase", None)
        if project and phase and phase.project_id != project.id:
            raise serializers.ValidationError({"phase": "phase debe pertenecer al mismo proyecto"})

        # Validate weight_percent doesn't exceed remaining
        weight_percent = attrs.get("weight_percent")
        if weight_percent is not None and phase:
            current_weight = float(self.instance.weight_percent) if self.instance else 0
            remaining = phase.remaining_weight_percent + current_weight
            if float(weight_percent) > remaining:
                raise serializers.ValidationError({
                    "weight_percent": f"El porcentaje no puede exceder {remaining}% disponible en el stage"
                })

        return attrs

        return attrs
    
    def create(self, validated_data):
        # If no phase provided, get or create a default "General" phase for the project
        if not validated_data.get("phase"):
            project = validated_data.get("project")
            if project:
                default_phase, _ = SchedulePhaseV2.objects.get_or_create(
                    project=project,
                    name="General",
                    defaults={
                        "color": "#6366f1",
                        "order": 999,
                    }
                )
                validated_data["phase"] = default_phase
        return super().create(validated_data)


class ScheduleTaskV2WriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleTaskV2
        fields = [
            "item",
            "title",
            "description",
            "status",
            "weight_percent",
            "assigned_to",
            "due_date",
            "order",
        ]

    def validate(self, attrs):
        status = attrs.get("status")
        if status and status not in dict(ScheduleTaskV2._meta.get_field("status").choices):
            raise serializers.ValidationError({"status": "status inválido"})
        
        # Validate weight_percent doesn't exceed remaining
        weight_percent = attrs.get("weight_percent")
        item = attrs.get("item") or getattr(self.instance, "item", None)
        if weight_percent is not None and item:
            current_weight = float(self.instance.weight_percent) if self.instance else 0
            remaining = item.remaining_weight_percent + current_weight
            if float(weight_percent) > remaining:
                raise serializers.ValidationError({
                    "weight_percent": f"El porcentaje no puede exceder {remaining}% disponible en el item"
                })
        
        return attrs


class TaskChecklistItemWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskChecklistItem
        fields = ["task", "description", "is_completed", "order", "sop_reference"]


class ScheduleDependencyV2WriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleDependencyV2
        fields = ["source_item", "target_item", "dependency_type"]

    def validate(self, attrs):
        source = attrs.get("source_item")
        target = attrs.get("target_item")
        if source and target:
            if source.id == target.id:
                raise serializers.ValidationError("No se permite dependencia consigo mismo")
            if source.project_id != target.project_id:
                raise serializers.ValidationError("Los items deben pertenecer al mismo proyecto")

        dep_type = attrs.get("dependency_type", "FS")
        if dep_type not in dict(ScheduleDependencyV2._meta.get_field("dependency_type").choices):
            raise serializers.ValidationError({"dependency_type": "Tipo de dependencia inválido"})

        return attrs
