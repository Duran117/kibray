from rest_framework import serializers

from core.models import (
    Project,
    ScheduleDependencyV2,
    ScheduleItemV2,
    SchedulePhaseV2,
    ScheduleTaskV2,
)


class ScheduleTaskV2Serializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleTaskV2
        fields = [
            "id",
            "title",
            "status",
            "due_date",
            "order",
            "created_at",
            "updated_at",
        ]


class ScheduleItemV2Serializer(serializers.ModelSerializer):
    tasks = ScheduleTaskV2Serializer(many=True, read_only=True)
    phase_name = serializers.CharField(source="phase.name", read_only=True)
    assigned_to_name = serializers.SerializerMethodField()
    allow_sunday_effective = serializers.SerializerMethodField()

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

    class Meta:
        model = SchedulePhaseV2
        fields = [
            "id",
            "project",
            "name",
            "color",
            "order",
            "allow_sunday",
            "created_at",
            "updated_at",
            "items",
        ]


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
            "order",
            "is_milestone",
            "allow_sunday_override",
        ]

    def validate(self, attrs):
        start_date = attrs.get("start_date") or getattr(self.instance, "start_date", None)
        end_date = attrs.get("end_date") or getattr(self.instance, "end_date", None)

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": "end_date no puede ser anterior a start_date"})

        progress = attrs.get("progress")
        if progress is not None and (progress < 0 or progress > 100):
            raise serializers.ValidationError({"progress": "progress debe estar entre 0 y 100"})

        project = attrs.get("project") or getattr(self.instance, "project", None)
        phase = attrs.get("phase") or getattr(self.instance, "phase", None)
        if project and phase and phase.project_id != project.id:
            raise serializers.ValidationError({"phase": "phase debe pertenecer al mismo proyecto"})

        return attrs


class ScheduleTaskV2WriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleTaskV2
        fields = ["item", "title", "status", "due_date", "order"]

    def validate(self, attrs):
        status = attrs.get("status")
        if status and status not in dict(ScheduleTaskV2._meta.get_field("status").choices):
            raise serializers.ValidationError({"status": "status inválido"})
        return attrs


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
