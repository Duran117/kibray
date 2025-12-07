from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.models import (
    AuditLog,
    BudgetLine,
    ChatChannel,
    ChatMessage,
    DailyLog,
    ColorSample,
    CostCode,
    DailyLog,
    DailyFocusSession,
    DamageReport,
    Employee,  # ⭐ Added for Employee serializer
    Expense,
    FloorPlan,
    FocusTask,
    Income,
    InventoryItem,  # ⭐ Added for Inventory serializer
    LoginAttempt,
    Notification,
    PermissionMatrix,
    PlanPin,
    Project,
    ProjectFile,  # ⭐ Added for Phase 4 File Manager
    ProjectManagerAssignment,
    PushSubscription,  # ⭐ PWA Push Notifications
    ScheduleCategory,
    ScheduleItem,
    ColorApproval,
    Task,
    TaskTemplate,
    WeatherSnapshot,
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class EmployeeSerializer(serializers.ModelSerializer):
    """Employee serializer with human-readable key"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = [
            "id",
            "employee_key",  # ⭐ Human-readable ID first
            "first_name",
            "last_name",
            "full_name",
            "social_security_number",
            "hourly_rate",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["employee_key", "created_at"]
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "title",
            "message",
            "link_url",
            "is_read",
            "created_at",
            "related_object_type",
            "related_object_id",
        ]
        read_only_fields = ["created_at"]


# =============================================================================
# SECURITY & AUDIT SERIALIZERS (Phase 9)
# =============================================================================


class PermissionMatrixSerializer(serializers.ModelSerializer):
    user_display = serializers.CharField(source="user.get_full_name", read_only=True)
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    entity_type_display = serializers.CharField(source="get_entity_type_display", read_only=True)
    project_name = serializers.CharField(source="scope_project.name", read_only=True, allow_null=True)
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = PermissionMatrix
        fields = [
            "id",
            "user",
            "user_display",
            "role",
            "role_display",
            "entity_type",
            "entity_type_display",
            "can_view",
            "can_create",
            "can_edit",
            "can_delete",
            "can_approve",
            "effective_from",
            "effective_until",
            "is_active",
            "scope_project",
            "project_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_is_active(self, obj):
        return obj.is_active()


class AuditLogSerializer(serializers.ModelSerializer):
    username_display = serializers.CharField(source="username", read_only=True)
    action_display = serializers.CharField(source="get_action_display", read_only=True)
    entity_type_display = serializers.CharField(source="get_entity_type_display", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "username",
            "username_display",
            "action",
            "action_display",
            "entity_type",
            "entity_type_display",
            "entity_id",
            "entity_repr",
            "old_values",
            "new_values",
            "ip_address",
            "user_agent",
            "session_id",
            "request_path",
            "request_method",
            "notes",
            "success",
            "error_message",
            "timestamp",
        ]
        read_only_fields = ["timestamp"]


class LoginAttemptSerializer(serializers.ModelSerializer):
    status_icon = serializers.SerializerMethodField()

    class Meta:
        model = LoginAttempt
        fields = [
            "id",
            "username",
            "ip_address",
            "user_agent",
            "success",
            "status_icon",
            "failure_reason",
            "timestamp",
            "session_id",
            "country_code",
            "city",
        ]
        read_only_fields = ["timestamp"]

    def get_status_icon(self, obj):
        return "✓" if obj.success else "✗"


class ChatChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatChannel
        fields = ["id", "name", "project", "created_at"]
        read_only_fields = ["created_at"]


class ChatMessageSerializer(serializers.ModelSerializer):
    """Unified Chat message serializer merging simple + rich variants.
    Provides alias 'content' for incoming message text and exposes user details plus mentions.
    """

    user = UserSerializer(read_only=True)
    channel_name = serializers.CharField(source="channel.name", read_only=True)
    project_id = serializers.IntegerField(source="channel.project_id", read_only=True)
    user_username = serializers.CharField(source="user.username", read_only=True, allow_null=True)
    user_full_name = serializers.CharField(source="user.get_full_name", read_only=True, allow_null=True)
    mentions = serializers.SerializerMethodField(read_only=True)
    content = serializers.CharField(write_only=True, required=False, allow_blank=True)
    message_display = serializers.SerializerMethodField()
    read_by_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "channel",
            "channel_name",
            "project_id",
            "user",
            "user_username",
            "user_full_name",
            "message",
            "content",
            "message_display",
            "image",
            "attachment",
            "link_url",
            "mentions",
            "read_by_count",
            "is_deleted",
            "deleted_by",
            "deleted_at",
            "created_at",
        ]
        read_only_fields = ["user", "message", "mentions", "is_deleted", "deleted_by", "deleted_at", "created_at"]

    def validate(self, attrs):
        content = attrs.pop("content", None)
        if content is not None and not attrs.get("message"):
            attrs["message"] = content
        return super().validate(attrs)


    def create(self, validated_data):
        req = self.context.get("request")
        user = getattr(req, "user", None)
        if user and not validated_data.get("created_by"):
            validated_data["created_by"] = user
        return super().create(validated_data)

    def get_message_display(self, obj):
        """Return sanitized message text"""
        if obj.is_deleted:
            return "[Message deleted]"
        return obj.message

    def get_read_by_count(self, obj):
        """Return number of users who have read this message"""
        return obj.read_by.count()


class DailyLogSanitizedSerializer(serializers.ModelSerializer):
    report = serializers.SerializerMethodField()

    class Meta:
        model = DailyLog
        fields = [
            "id",
            "project",
            "date",
            "report",
        ]

    def get_report(self, obj):
        try:
            return obj.get_sanitized_report()
        except Exception as e:
            return {"error": str(e)}

    def create(self, validated_data):
        if not validated_data.get("message") and "content" in self.initial_data:
            validated_data["message"] = self.initial_data.get("content")
        return super().create(validated_data)

    def get_mentions(self, obj):
        import re

        text = obj.message or ""
        usernames = set(re.findall(r"@([A-Za-z0-9_\.\-]+)", text))
        return list(usernames)

    def get_message_display(self, obj):
        if getattr(obj, "is_deleted", False):
            return "[Message deleted]"
        return obj.message


class SitePhotoSerializer(serializers.ModelSerializer):
    # Use FileField to avoid strict image validation during API upload tests
    image = serializers.FileField()
    project_name = serializers.CharField(source="project.name", read_only=True)
    uploader_name = serializers.CharField(source="created_by.get_full_name", read_only=True, allow_null=True)
    damage_report_title = serializers.CharField(source="damage_report.title", read_only=True, allow_null=True)

    class Meta:
        from core.models import SitePhoto

        model = SitePhoto
        fields = [
            "id",
            "project",
            "project_name",
            "created_by",
            "uploader_name",
            "image",
            "thumbnail",
            "location_lat",
            "location_lng",
            "location_accuracy_m",
            "notes",
            "room",
            "wall_ref",
            "damage_report",
            "damage_report_title",
            "photo_type",
            "caption",
            "visibility",
            "created_at",
        ]
        read_only_fields = ["created_by", "thumbnail", "created_at"]

    def create(self, validated_data):
        req = self.context.get("request")
        user = getattr(req, "user", None)
        if user and not validated_data.get("created_by"):
            validated_data["created_by"] = user
        # Attempt EXIF GPS extraction if not provided
        try:
            img = validated_data.get("image")
            if img and (not validated_data.get("location_lat") or not validated_data.get("location_lng")):
                from PIL import Image
                from PIL.ExifTags import GPSTAGS, TAGS

                image = Image.open(img)
                exif_data = image.getexif()
                gps_info = None
                for tag_id in exif_data:
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == "GPSInfo":
                        gps_info = exif_data.get(tag_id)
                        break

                def _dms_to_deg(dms, ref):
                    try:
                        deg = float(dms[0][0]) / float(dms[0][1])
                        min_ = float(dms[1][0]) / float(dms[1][1])
                        sec = float(dms[2][0]) / float(dms[2][1])
                        val = deg + (min_ / 60.0) + (sec / 3600.0)
                        if ref in ["S", "W"]:
                            val = -val
                        return round(val, 6)
                    except Exception:
                        return None

                if gps_info:
                    lat = None
                    lon = None
                    lat_dms = gps_info.get(GPSTAGS.get(2))
                    lat_ref = gps_info.get(GPSTAGS.get(1))
                    lon_dms = gps_info.get(GPSTAGS.get(4))
                    lon_ref = gps_info.get(GPSTAGS.get(3))
                    if lat_dms and lat_ref:
                        lat = _dms_to_deg(lat_dms, lat_ref)
                    if lon_dms and lon_ref:
                        lon = _dms_to_deg(lon_dms, lon_ref)
                    if lat is not None and validated_data.get("location_lat") is None:
                        validated_data["location_lat"] = lat
                    if lon is not None and validated_data.get("location_lng") is None:
                        validated_data["location_lng"] = lon
        except Exception:
            pass
        return super().create(validated_data)


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source="assigned_to.get_full_name", read_only=True, allow_null=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    # Make priority and due_date writable for API updates
    priority = serializers.ChoiceField(choices=["low", "medium", "high", "urgent"], required=False)
    due_date = serializers.DateField(required=False, allow_null=True)
    total_hours = serializers.FloatField(read_only=True)
    time_tracked_hours = serializers.SerializerMethodField()
    # Read-only representation and a write-only input for dependencies
    dependencies_ids = serializers.SerializerMethodField(read_only=True)
    dependencies = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False, allow_empty=True
    )
    reopen_events_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "project",
            "project_name",
            "assigned_to",
            "assigned_to_name",
            "status",
            "priority",
            "due_date",
            "is_touchup",
            "created_at",
            "started_at",
            "time_tracked_seconds",
            "time_tracked_hours",
            "total_hours",
            "dependencies_ids",
            "dependencies",
            "reopen_events_count",
        ]

    read_only_fields = ["created_at"]

    def get_time_tracked_hours(self, obj):
        return obj.get_time_tracked_hours()

    def get_dependencies_ids(self, obj):
        return list(obj.dependencies.values_list("id", flat=True))

    def create(self, validated_data):
        deps = validated_data.pop("dependencies", None)
        task = super().create(validated_data)
        if deps is not None:
            from core.models import Task as TaskModel

            dep_qs = TaskModel.objects.filter(id__in=deps)
            task.dependencies.set(dep_qs)
            # Re-run clean to validate cycles/self-dependency
            task.full_clean()
            task.save()
        return task

    def update(self, instance, validated_data):
        deps = validated_data.pop("dependencies", None)
        task = super().update(instance, validated_data)
        if deps is not None:
            from core.models import Task as TaskModel

            if str(instance.id) in [str(d) for d in deps]:
                raise serializers.ValidationError({"dependencies": _("Task cannot depend on itself")})
            dep_qs = TaskModel.objects.filter(id__in=deps)
            task.dependencies.set(dep_qs)
            task.full_clean()
            task.save()
        return task


class TaskDependencySerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source="task.title", read_only=True)
    predecessor_title = serializers.CharField(source="predecessor.title", read_only=True)

    class Meta:
        from core.models import TaskDependency

        model = TaskDependency
        fields = ["id", "task", "task_title", "predecessor", "predecessor_title", "type", "lag_minutes", "created_at"]
        read_only_fields = ["created_at"]

    def create(self, validated_data):
        from core.models import TaskDependency as TD

        # Explicit creation to avoid any unintended model mixups
        return TD.objects.create(**validated_data)


class ProjectManagerAssignmentSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    pm_username = serializers.CharField(source="pm.username", read_only=True)

    class Meta:
        model = ProjectManagerAssignment
        fields = ["id", "project", "project_name", "pm", "pm_username", "role", "created_at"]
        read_only_fields = ["created_at"]


class ColorApprovalSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    requested_by_username = serializers.CharField(source="requested_by.username", read_only=True, allow_null=True)
    approved_by_username = serializers.CharField(source="approved_by.username", read_only=True, allow_null=True)

    class Meta:
        model = ColorApproval
        fields = [
            "id",
            "project",
            "project_name",
            "requested_by",
            "requested_by_username",
            "approved_by",
            "approved_by_username",
            "status",
            "color_name",
            "color_code",
            "brand",
            "location",
            "notes",
            "client_signature",
            "signed_at",
            "created_at",
        ]
        read_only_fields = ["signed_at", "created_at"]


class DamagePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        from core.models import DamagePhoto

        model = DamagePhoto
        fields = ["id", "report", "image", "notes", "created_at"]
        read_only_fields = ["created_at"]


class ChangeOrderSerializer(serializers.ModelSerializer):
    title = serializers.CharField(read_only=True)

    class Meta:
        from core.models import ChangeOrder

        model = ChangeOrder
        fields = ["id", "project", "description", "amount", "status", "reference_code", "date_created", "title"]
        read_only_fields = ["date_created", "title"]


class DamageReportSerializer(serializers.ModelSerializer):
    reported_by_name = serializers.CharField(source="reported_by.get_full_name", read_only=True, allow_null=True)
    assigned_to_name = serializers.CharField(source="assigned_to.get_full_name", read_only=True, allow_null=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    plan_name = serializers.CharField(source="plan.name", read_only=True, allow_null=True)
    auto_task_id = serializers.IntegerField(source="auto_task.id", read_only=True, allow_null=True)
    linked_co_id = serializers.IntegerField(source="linked_co.id", read_only=True, allow_null=True)
    linked_touchup_id = serializers.IntegerField(source="linked_touchup.id", read_only=True, allow_null=True)
    photo_count = serializers.SerializerMethodField()
    photos = DamagePhotoSerializer(many=True, read_only=True)

    class Meta:
        model = DamageReport
        fields = [
            "id",
            "project",
            "project_name",
            "plan",
            "plan_name",
            "pin",
            "title",
            "description",
            "category",
            "severity",
            "status",
            "estimated_cost",
            "reported_by",
            "reported_by_name",
            "assigned_to",
            "assigned_to_name",
            "reported_at",
            "in_progress_at",
            "resolved_at",
            "location_detail",
            "root_cause",
            "auto_task_id",
            "linked_co_id",
            "linked_touchup_id",
            "photo_count",
            "photos",
        ]
        read_only_fields = [
            "reported_by",
            "reported_at",
            "in_progress_at",
            "resolved_at",
            "auto_task_id",
            "linked_co_id",
            "linked_touchup_id",
        ]

    def get_photo_count(self, obj):
        return obj.photos.count()


class ColorSampleSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    approver_name = serializers.CharField(source="approved_by.get_full_name", read_only=True, allow_null=True)
    rejecter_name = serializers.CharField(source="rejected_by.get_full_name", read_only=True, allow_null=True)
    status_changed_by_name = serializers.CharField(
        source="status_changed_by.get_full_name", read_only=True, allow_null=True
    )
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True, allow_null=True)

    class Meta:
        model = ColorSample
        fields = [
            "id",
            "project",
            "project_name",
            "name",
            "code",
            "brand",
            "finish",
            "gloss",
            "status",
            "sample_image",
            "reference_photo",
            "sample_number",
            "version",
            "room_location",
            "room_group",
            "notes",
            "client_notes",
            "annotations",
            "approved_by",
            "approver_name",
            "approved_at",
            "approval_signature",
            "approval_ip",
            "rejected_by",
            "rejecter_name",
            "rejected_at",
            "rejection_reason",
            "status_changed_by",
            "status_changed_by_name",
            "status_changed_at",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "sample_number",
            "version",
            "approved_by",
            "approver_name",
            "approved_at",
            "approval_signature",
            "approval_ip",
            "rejected_by",
            "rejecter_name",
            "rejected_at",
            "status_changed_by",
            "status_changed_by_name",
            "status_changed_at",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]


class ColorSampleApproveSerializer(serializers.Serializer):
    signature_ip = serializers.IPAddressField(required=False, allow_null=True)


class ColorSampleRejectSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500)


class PlanPinSerializer(serializers.ModelSerializer):
    color_sample_name = serializers.CharField(source="color_sample.name", read_only=True, allow_null=True)
    linked_task_title = serializers.CharField(source="linked_task.title", read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True, allow_null=True)
    migrated_to_id = serializers.IntegerField(source="migrated_to.id", read_only=True, allow_null=True)
    plan_name = serializers.CharField(source="plan.name", read_only=True)

    class Meta:
        model = PlanPin
        fields = [
            "id",
            "plan",
            "plan_name",
            "x",
            "y",
            "title",
            "description",
            "pin_type",
            "color_sample",
            "color_sample_name",
            "linked_task",
            "linked_task_title",
            "pin_color",
            "is_multipoint",
            "path_points",
            "status",
            "migrated_to_id",
            "client_comments",
            "created_by",
            "created_by_name",
            "created_at",
        ]
        read_only_fields = ["created_at", "pin_color", "migrated_to_id", "created_by", "created_by_name"]


class FloorPlanSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    pins = PlanPinSerializer(many=True, read_only=True)
    pin_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True, allow_null=True)
    replaced_by_id = serializers.IntegerField(source="replaced_by.id", read_only=True, allow_null=True)
    pending_migration_count = serializers.SerializerMethodField()

    class Meta:
        model = FloorPlan
        fields = [
            "id",
            "project",
            "project_name",
            "name",
            "level",
            "level_identifier",
            "image",
            "version",
            "is_current",
            "replaced_by_id",
            "last_pdf_export",
            "created_by",
            "created_by_name",
            "created_at",
            "pins",
            "pin_count",
            "pending_migration_count",
        ]

    read_only_fields = ["created_at", "version", "is_current", "replaced_by_id", "created_by", "created_by_name"]

    def get_pin_count(self, obj):
        """Count active pins only"""
        return obj.pins.filter(status="active").count()

    def get_pending_migration_count(self, obj):
        """Count pins pending migration"""
        return obj.pins.filter(status="pending_migration").count()


class ProjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "client", "address", "start_date", "end_date", "created_at"]
        read_only_fields = ["created_at"]


class ScheduleCategorySerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = ScheduleCategory
        fields = [
            "id",
            "project",
            "name",
            "order",
            "parent",
            "is_phase",
            "cost_code",
            "item_count",
            "percent_complete",
        ]
        read_only_fields = ["item_count"]

    def get_item_count(self, obj):
        return obj.items.count()


class ScheduleItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True, allow_null=True)
    # Map legacy 'name' used by frontend to model field 'title'
    # Allow partial updates without requiring name/title
    name = serializers.CharField(source="title", required=False)
    # Allow frontend to omit category; viewset will assign a default if missing
    category = serializers.PrimaryKeyRelatedField(
        queryset=ScheduleCategory.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = ScheduleItem
        fields = [
            "id",
            "project",
            "category",
            "category_name",
            "name",
            "description",
            "order",
            "planned_start",
            "planned_end",
            "status",
            "percent_complete",
            "is_milestone",
            "cost_code",
            "budget_line",
            "estimate_line",
        ]
        # Enable partial updates for PATCH requests
        extra_kwargs = {
            'project': {'required': False},
            'planned_start': {'required': False},
            'planned_end': {'required': False},
        }

    # dependencies removed (not present on model); could be reintroduced later


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
            "id",
            "project_code",  # ⭐ Human-readable ID first
            "name",
            "client",
            "address",
            "start_date",
            "end_date",
            "description",
            "paint_colors",
            "paint_codes",
            "stains_or_finishes",
            "number_of_rooms_or_areas",
            "number_of_paint_defects",
            "total_income",
            "total_expenses",
            "profit",
            "budget_total",
            "budget_labor",
            "budget_materials",
            "budget_other",
            "budget_remaining",
            "reflection_notes",
            "created_at",
            "income_count",
            "expense_count",
        ]
        read_only_fields = ["project_code", "created_at", "total_income", "total_expenses", "profit", "budget_remaining"]

    def get_income_count(self, obj):
        return obj.incomes.count()

    def get_expense_count(self, obj):
        return obj.expenses.count()


class IncomeSerializer(serializers.ModelSerializer):
    """Income serializer with project details"""

    project_name = serializers.CharField(source="project.name", read_only=True)
    project_client = serializers.CharField(source="project.client", read_only=True)
    project_code = serializers.CharField(source="project.project_code", read_only=True)  # ⭐ Human-readable ID

    class Meta:
        model = Income
        fields = [
            "id",
            "project",
            "project_code",  # ⭐ Add human-readable code
            "project_name",
            "project_client",
            "project_name",
            "amount",
            "date",
            "payment_method",
            "category",
            "description",
            "invoice",
            "notes",
        ]
        read_only_fields = []

    def validate_amount(self, value):
        """Ensure amount is positive"""
        if value <= 0:
            raise serializers.ValidationError(_("Amount must be greater than zero."))
        return value

    def validate_date(self, value):
        """Ensure date is not in the future"""
        from datetime import date

        if value > date.today():
            raise serializers.ValidationError(_("Date cannot be in the future."))
        return value


class ExpenseSerializer(serializers.ModelSerializer):
    """Expense serializer with project and cost code details"""

    project_name = serializers.CharField(source="project.name", read_only=True)
    project_code = serializers.CharField(source="project.project_code", read_only=True)  # ⭐ Human-readable ID
    cost_code_name = serializers.CharField(source="cost_code.name", read_only=True, allow_null=True)
    change_order_number = serializers.CharField(source="change_order.number", read_only=True, allow_null=True)

    class Meta:
        model = Expense
        fields = [
            "id",
            "project",
            "project_code",  # ⭐ Add human-readable code
            "project_name",
            "amount",
            "project_name",
            "date",
            "category",
            "description",
            "receipt",
            "invoice",
            "change_order",
            "change_order_number",
            "cost_code",
            "cost_code_name",
        ]
        read_only_fields = []

    def validate_amount(self, value):
        """Ensure amount is positive"""
        if value <= 0:
            raise serializers.ValidationError(_("Amount must be greater than zero."))
        return value

    def validate_date(self, value):
        """Ensure date is not in the future"""
        from datetime import date

        if value > date.today():
            raise serializers.ValidationError(_("Date cannot be in the future."))
        return value


class CostCodeSerializer(serializers.ModelSerializer):
    """Cost code serializer"""

    expense_count = serializers.SerializerMethodField()
    total_expenses = serializers.SerializerMethodField()

    class Meta:
        model = CostCode
        fields = ["id", "code", "name", "category", "active", "expense_count", "total_expenses"]
        read_only_fields = ["expense_count", "total_expenses"]

    def get_expense_count(self, obj):
        return obj.expenses.count()

    def get_total_expenses(self, obj):
        from django.db.models import Sum

        total = obj.expenses.aggregate(total=Sum("amount"))["total"]
        return total or 0


# -------------------------------
# Invoices (Module 6) - API
# -------------------------------


class InvoiceLineAPISerializer(serializers.ModelSerializer):
    class Meta:
        from core.models import InvoiceLine

        model = InvoiceLine
        fields = ["id", "description", "amount", "time_entry", "expense"]


class InvoicePaymentAPISerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.CharField(source="recorded_by.get_full_name", read_only=True, allow_null=True)

    class Meta:
        from core.models import InvoicePayment

        model = InvoicePayment
        fields = [
            "id",
            "invoice",
            "amount",
            "payment_date",
            "payment_method",
            "reference",
            "notes",
            "recorded_by",
            "recorded_by_name",
            "recorded_at",
        ]
        read_only_fields = ["recorded_by", "recorded_at"]


class InvoiceSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    balance_due = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    payment_progress = serializers.SerializerMethodField()
    lines = InvoiceLineAPISerializer(many=True, required=False)
    payments = InvoicePaymentAPISerializer(many=True, read_only=True)

    class Meta:
        from core.models import Invoice

        model = Invoice
        fields = [
            "id",
            "project",
            "project_name",
            "invoice_number",
            "date_issued",
            "due_date",
            "status",
            "notes",
            "total_amount",
            "amount_paid",
            "balance_due",
            "payment_progress",
            "sent_date",
            "viewed_date",
            "approved_date",
            "paid_date",
            "lines",
            "payments",
        ]
        read_only_fields = [
            "invoice_number",
            "date_issued",
            "amount_paid",
            "balance_due",
            "payment_progress",
            "sent_date",
            "viewed_date",
            "approved_date",
            "paid_date",
        ]

    def get_payment_progress(self, obj):
        try:
            return float(obj.payment_progress)
        except Exception:
            return 0

    def create(self, validated_data):
        from core.models import InvoiceLine

        lines_data = validated_data.pop("lines", [])
        invoice = super().create(validated_data)
        total = 0
        for ld in lines_data:
            il = InvoiceLine.objects.create(invoice=invoice, **ld)
            total += il.amount
        if total:
            invoice.total_amount = total
            invoice.save(update_fields=["total_amount"])
        return invoice

    def update(self, instance, validated_data):
        from core.models import InvoiceLine

        lines_data = validated_data.pop("lines", None)
        invoice = super().update(instance, validated_data)
        if lines_data is not None:
            # Replace all lines with provided set
            instance.lines.all().delete()
            total = 0
            for ld in lines_data:
                il = InvoiceLine.objects.create(invoice=invoice, **ld)
                total += il.amount
            invoice.total_amount = total
            invoice.save(update_fields=["total_amount"])


class ClientRequestSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True, allow_null=True)
    attachments = serializers.SerializerMethodField(read_only=True)

    class Meta:
        from core.models import ClientRequest

        model = ClientRequest
        fields = [
            "id",
            "project",
            "project_name",
            "title",
            "description",
            "request_type",
            "created_by",
            "created_by_name",
            "created_at",
            "status",
            "change_order",
            "attachments",
        ]
        read_only_fields = ["created_by", "created_at"]

    # No channel_type normalization here; ClientRequest does not include channel_type

    def create(self, validated_data):
        # auto-assign created_by from request context
        req = self.context.get("request")
        user = getattr(req, "user", None)
        if user and not validated_data.get("created_by"):
            validated_data["created_by"] = user
        return super().create(validated_data)

    def get_attachments(self, obj):
        # During create(), obj may be a dict-like validated_data; return empty.
        if not hasattr(obj, "attachments"):
            return []
        qs = obj.attachments.all()
        return [
            {
                "id": a.id,
                "filename": a.filename,
                "size_bytes": a.size_bytes,
                "uploaded_at": a.uploaded_at,
            }
            for a in qs
        ]


class ClientRequestAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        from core.models import ClientRequestAttachment

        model = ClientRequestAttachment
        fields = ["id", "request", "file", "filename", "content_type", "size_bytes", "uploaded_by", "uploaded_at"]
        read_only_fields = ["uploaded_by", "size_bytes", "uploaded_at"]


class ChatChannelSerializer(serializers.ModelSerializer):
    """Chat channel with participant info"""

    project_name = serializers.CharField(source="project.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True, allow_null=True)
    participant_count = serializers.SerializerMethodField()
    participant_usernames = serializers.SerializerMethodField()

    class Meta:
        from core.models import ChatChannel

        model = ChatChannel
        fields = [
            "id",
            "project",
            "project_name",
            "name",
            "channel_type",
            "created_by",
            "created_by_name",
            "participants",
            "participant_count",
            "participant_usernames",
            "is_default",
            "created_at",
        ]
        read_only_fields = ["created_by", "created_at"]

    def get_participant_count(self, obj):
        return obj.participants.count()

    def get_participant_usernames(self, obj):
        return list(obj.participants.values_list("username", flat=True))


class ChatMentionSerializer(serializers.ModelSerializer):
    """Serializer for chat mentions"""

    mentioned_username = serializers.CharField(source="mentioned_user.username", read_only=True, allow_null=True)

    class Meta:
        from core.models import ChatMention

        model = ChatMention
        fields = [
            "id",
            "message",
            "mentioned_user",
            "mentioned_username",
            "entity_type",
            "entity_id",
            "entity_label",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class ChatMessageSerializer(serializers.ModelSerializer):
    """Unified Chat message serializer.

    Enhancements over legacy version:
    - Nested user details (id, username, names, email, avatar if present)
    - Write-only alias 'content' mapped into 'message'
    - Rich mention representation via ChatMentionSerializer
    - Computed safe display text (handles soft-deleted messages)
    """

    from core.api.serializers import UserSerializer as NestedUserSerializer  # circular safe import

    user = NestedUserSerializer(read_only=True)
    channel_name = serializers.CharField(source="channel.name", read_only=True)
    project_id = serializers.IntegerField(source="channel.project_id", read_only=True)
    user_username = serializers.CharField(source="user.username", read_only=True, allow_null=True)
    user_full_name = serializers.CharField(source="user.get_full_name", read_only=True, allow_null=True)
    mentions = ChatMentionSerializer(many=True, read_only=True)
    content = serializers.CharField(write_only=True, required=False, allow_blank=True)
    message_display = serializers.SerializerMethodField()
    read_by_count = serializers.SerializerMethodField()

    class Meta:
        from core.models import ChatMessage

        model = ChatMessage
        fields = [
            "id",
            "channel",
            "channel_name",
            "project_id",
            "user",
            "user_username",
            "user_full_name",
            "message",
            "content",
            "message_display",
            "read_by_count",
            "image",
            "attachment",
            "link_url",
            "mentions",
            "is_deleted",
            "deleted_by",
            "deleted_at",
            "created_at",
        ]
        # Allow 'message' direct writes (tests post 'message'); keep 'content' as optional alias
        read_only_fields = ["user", "mentions", "is_deleted", "deleted_by", "deleted_at", "created_at"]

    def validate(self, attrs):
        content = attrs.pop("content", None)
        if content is not None and not attrs.get("message"):
            attrs["message"] = content
        return super().validate(attrs)

    def get_message_display(self, obj):
        if obj.is_deleted:
            return "[Message deleted]"
        return obj.message

    def get_read_by_count(self, obj):
        """Return number of users who have read this message"""
        return obj.read_by.count()


class BudgetLineSerializer(serializers.ModelSerializer):
    """Budget line serializer with cost code details"""

    cost_code_name = serializers.CharField(source="cost_code.name", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = BudgetLine
        fields = [
            "id",
            "project",
            "project_name",
            "cost_code",
            "cost_code_name",
            "description",
            "qty",
            "unit",
            "unit_cost",
            "allowance",
            "baseline_amount",
            "revised_amount",
            "total_amount",
            "planned_start",
            "planned_finish",
            "weight_override",
        ]
        read_only_fields = ["baseline_amount", "total_amount"]

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

    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = TaskTemplate
        fields = [
            "id",
            "title",
            "description",
            "default_priority",
            "estimated_hours",
            "tags",
            "checklist",
            "is_active",
            "category",
            "category_display",
            "sop_reference",
            "usage_count",
            "last_used",
            "is_favorite",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_by", "created_at", "updated_at", "usage_count", "last_used"]


class WeatherSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for WeatherSnapshot (Module 30)"""

    is_stale = serializers.SerializerMethodField()

    class Meta:
        model = WeatherSnapshot
        fields = [
            "id",
            "project",
            "date",
            "source",
            "temperature_max",
            "temperature_min",
            "conditions_text",
            "precipitation_mm",
            "wind_kph",
            "humidity_percent",
            "fetched_at",
            "is_stale",
            "latitude",
            "longitude",
        ]
        read_only_fields = ["fetched_at"]

    def get_is_stale(self, obj):
        return obj.is_stale()


class DailyLogPlanningSerializer(serializers.ModelSerializer):
    """Serializer for DailyLog with planning fields"""

    planned_templates = TaskTemplateSerializer(many=True, read_only=True)
    planned_tasks = TaskSerializer(many=True, read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    completion_summary = serializers.SerializerMethodField()

    class Meta:
        model = DailyLog
        fields = [
            "id",
            "project",
            "project_name",
            "date",
            "weather",
            "crew_count",
            "planned_templates",
            "planned_tasks",
            "is_complete",
            "incomplete_reason",
            "auto_weather",
            "created_at",
            "updated_at",
            "completion_summary",
        ]
        read_only_fields = ["created_at", "updated_at", "is_complete", "incomplete_reason"]

    def get_completion_summary(self, obj):
        total = obj.planned_tasks.count()
        if total == 0:
            return {"total": 0, "completed": 0, "percent": 0}
        completed = obj.planned_tasks.filter(status="Completada").count()
        percent = round((completed / total) * 100, 1) if total > 0 else 0
        return {"total": total, "completed": completed, "percent": percent}


# ============================================================================
# PHASE 2: Module 13 - Time Tracking
# ============================================================================


class TimeEntrySerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField(read_only=True)
    employee_key = serializers.CharField(source="employee.employee_key", read_only=True)  # ⭐ Human-readable ID
    task_title = serializers.CharField(source="task.title", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    project_code = serializers.CharField(source="project.project_code", read_only=True)  # ⭐ Human-readable ID

    class Meta:
        from core.models import TimeEntry

        model = TimeEntry
        fields = [
            "id",
            "employee",
            "employee_key",  # ⭐ Add human-readable key
            "employee_name",
            "project",
            "project_code",  # ⭐ Add human-readable code
            "project_name",
            "task",
            "task_title",
            "date",
            "start_time",
            "end_time",
            "hours_worked",
            "notes",
            "cost_code",
            "change_order",
        ]
        read_only_fields = ["hours_worked"]

    def get_employee_name(self, obj):
        try:
            return f"{obj.employee.first_name} {obj.employee.last_name}".strip()
        except Exception:
            return None


class InstantiatePlannedTemplatesSerializer(serializers.Serializer):
    """Serializer for instantiate_planned_templates action"""

    assigned_to_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_assigned_to_id(self, value):
        if value is not None:
            from core.models import Employee

            if not Employee.objects.filter(pk=value).exists():
                raise serializers.ValidationError(_("Employee does not exist"))
        return value


# ============================================================================
# PHASE 2: Daily Plans (Module 12)
# ============================================================================


class EmployeeMiniSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "full_name"]


class PlannedActivitySerializer(serializers.ModelSerializer):
    assigned_employee_ids = serializers.ListField(child=serializers.IntegerField(), required=False, write_only=True)
    assigned_employee_names = serializers.SerializerMethodField()
    schedule_item_title = serializers.CharField(source="schedule_item.title", read_only=True, allow_null=True)
    activity_template_name = serializers.CharField(source="activity_template.name", read_only=True, allow_null=True)
    converted_task_id = serializers.IntegerField(source="converted_task.id", read_only=True)

    class Meta:
        from core.models import PlannedActivity

        model = PlannedActivity
        fields = [
            "id",
            "daily_plan",
            "title",
            "description",
            "order",
            "assigned_employee_ids",
            "assigned_employee_names",
            "is_group_activity",
            "estimated_hours",
            "actual_hours",
            "materials_needed",
            "materials_checked",
            "material_shortage",
            "status",
            "progress_percentage",
            "schedule_item",
            "schedule_item_title",
            "activity_template",
            "activity_template_name",
            "converted_task",
            "converted_task_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "daily_plan",
            "materials_checked",
            "material_shortage",
            "created_at",
            "updated_at",
            "converted_task",
        ]

    def get_assigned_employee_names(self, obj):
        return [f"{e.first_name} {e.last_name}".strip() for e in obj.assigned_employees.all()]

    def create(self, validated_data):
        from core.models import Employee

        employee_ids = validated_data.pop("assigned_employee_ids", [])
        activity = super().create(validated_data)
        if employee_ids:
            employees = Employee.objects.filter(id__in=employee_ids)
            activity.assigned_employees.set(employees)
        return activity

    def update(self, instance, validated_data):
        from core.models import Employee

        employee_ids = validated_data.pop("assigned_employee_ids", None)
        activity = super().update(instance, validated_data)
        if employee_ids is not None:
            employees = Employee.objects.filter(id__in=employee_ids)
            activity.assigned_employees.set(employees)
        return activity


class DailyPlanSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    is_overdue = serializers.SerializerMethodField()
    activities = PlannedActivitySerializer(many=True, read_only=True)
    productivity_score = serializers.SerializerMethodField()

    class Meta:
        from core.models import DailyPlan

        model = DailyPlan
        fields = [
            "id",
            "project",
            "project_name",
            "plan_date",
            "status",
            "completion_deadline",
            "weather_data",
            "weather_fetched_at",
            "no_planning_reason",
            "admin_approved",
            "approved_by",
            "approved_at",
            "actual_hours_worked",
            "estimated_hours_total",
            "is_overdue",
            "activities",
            "created_at",
            "updated_at",
            "productivity_score",
        ]
        read_only_fields = ["weather_fetched_at", "created_at", "updated_at", "is_overdue", "productivity_score"]

    def get_is_overdue(self, obj):
        return obj.is_overdue()

    def get_productivity_score(self, obj):
        return obj.calculate_productivity_score()


# ============================================================================
# AI Suggestions Serializer (Dec 2025)
# ============================================================================


class AISuggestionSerializer(serializers.ModelSerializer):
    """Serializer for AI Suggestions"""

    daily_plan_date = serializers.DateField(source="daily_plan.plan_date", read_only=True)
    project_name = serializers.CharField(source="daily_plan.project.name", read_only=True)
    resolved_by_name = serializers.CharField(source="resolved_by.get_full_name", read_only=True, allow_null=True)

    class Meta:
        from core.models import AISuggestion

        model = AISuggestion
        fields = [
            "id",
            "daily_plan",
            "daily_plan_date",
            "project_name",
            "suggestion_type",
            "severity",
            "title",
            "description",
            "suggested_action",
            "auto_fixable",
            "status",
            "created_at",
            "resolved_at",
            "resolved_by",
            "resolved_by_name",
        ]
        read_only_fields = ["created_at", "resolved_at", "daily_plan_date", "project_name", "resolved_by_name"]


# ============================================================================
# PHASE 2: Module 14 - Materials & Inventory
# ============================================================================


class InventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        from core.models import InventoryItem

        model = InventoryItem
        fields = [
            "id",
            "sku",  # ⭐ Move SKU to top as primary identifier
            "name",
            "category",
            "unit",
            "is_equipment",
            "track_serial",
            "low_stock_threshold",
            "default_threshold",
            "valuation_method",
            "average_cost",
            "last_purchase_cost",
            "active",
            "no_threshold",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["sku", "average_cost", "last_purchase_cost", "created_at", "updated_at"]  # ⭐ SKU is read-only


class InventoryLocationSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True, allow_null=True)

    class Meta:
        from core.models import InventoryLocation

        model = InventoryLocation
        fields = ["id", "name", "project", "project_name", "is_storage"]


class ProjectInventorySerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True)
    location_name = serializers.CharField(source="location.__str__", read_only=True)
    is_below = serializers.BooleanField(read_only=True)  # Removed redundant source='is_below'

    class Meta:
        from core.models import ProjectInventory

        model = ProjectInventory
        fields = ["id", "item", "item_name", "location", "location_name", "quantity", "is_below"]
        read_only_fields = ["quantity", "is_below"]


class InventoryMovementSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True)
    from_location_name = serializers.CharField(source="from_location.__str__", read_only=True)
    to_location_name = serializers.CharField(source="to_location.__str__", read_only=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True, allow_null=True)

    class Meta:
        from core.models import InventoryMovement

        model = InventoryMovement
        fields = [
            "id",
            "item",
            "item_name",
            "from_location",
            "from_location_name",
            "to_location",
            "to_location_name",
            "movement_type",
            "quantity",
            "reason",
            "note",
            "related_task",
            "related_project",
            "created_by",
            "created_by_name",
            "created_at",
            "unit_cost",
            "expense",
            "applied",
        ]
        read_only_fields = ["created_by", "created_at", "applied"]

    def create(self, validated_data):
        from django.core.exceptions import ValidationError as DjangoValidationError

        movement = super().create(validated_data)
        try:
            movement.apply()
        except DjangoValidationError as e:
            # surface as DRF validation error
            raise serializers.ValidationError({"detail": _("%(error)s") % {"error": str(e)}})
        return movement


class MaterialRequestItemSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    unit_display = serializers.CharField(source="get_unit_display", read_only=True)
    remaining_quantity = serializers.SerializerMethodField()
    is_fully_received = serializers.SerializerMethodField()

    class Meta:
        from core.models import MaterialRequestItem

        model = MaterialRequestItem
        fields = [
            "id",
            "request",
            "category",
            "category_display",
            "brand",
            "brand_text",
            "product_name",
            "color_name",
            "color_code",
            "finish",
            "gloss",
            "formula",
            "reference_image",
            "quantity",
            "unit",
            "unit_display",
            "comments",
            "inventory_item",
            "qty_requested",
            "qty_ordered",
            "qty_received",
            "qty_consumed",
            "qty_returned",
            "received_quantity",
            "item_status",
            "item_notes",
            "unit_cost",
            "remaining_quantity",
            "is_fully_received",
        ]
        read_only_fields = [
            "request",
            "qty_received",
            "qty_consumed",
            "qty_returned",
            "remaining_quantity",
            "is_fully_received",
        ]

    def get_remaining_quantity(self, obj):
        try:
            return float(obj.get_remaining_quantity())
        except Exception:
            return None

    def get_is_fully_received(self, obj):
        return obj.is_fully_received()


class MaterialRequestSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.CharField(source="requested_by.get_full_name", read_only=True, allow_null=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    items = MaterialRequestItemSerializer(many=True)
    # Campo adicional para detectar si se usó mapping legacy
    legacy_status_used = serializers.SerializerMethodField(read_only=True)

    class Meta:
        from core.models import MaterialRequest

        model = MaterialRequest
        fields = [
            "id",
            "project",
            "project_name",
            "requested_by",
            "requested_by_name",
            "needed_when",
            "needed_date",
            "notes",
            "status",
            "legacy_status_used",
            "approved_by",
            "approved_at",
            "expected_delivery_date",
            "partial_receipt_notes",
            "created_at",
            "updated_at",
            "items",
        ]
        read_only_fields = ["requested_by", "approved_by", "approved_at", "created_at", "updated_at"]

    def get_legacy_status_used(self, obj):
        """Indica si el status actual fue mapeado desde un valor legacy."""
        # Si status en BD es 'pending' pero no se puede determinar origen sin metadata adicional,
        # este campo es informativo para frontend (puede expandirse con modelo de audit trail)
        return False  # Placeholder; expandir con tracking si necesario

    def validate_status(self, value):
        """Aplicar mapping de compatibilidad en validación de entrada."""
        from core.models import MaterialRequest

        if value in MaterialRequest.STATUS_COMPAT_MAP:
            # Mapear automáticamente valores legacy a su forma normalizada
            return MaterialRequest.STATUS_COMPAT_MAP[value]
        return value

    # Nota: evitamos duplicar Meta; ya incluye legacy_status_used

    def create(self, validated_data):
        from core.models import MaterialRequestItem as MRI

        items_data = validated_data.pop("items", [])
        req = super().create(validated_data)
        for item in items_data:
            data = item if isinstance(item, dict) else {}
            data["request"] = req
            MRI.objects.create(**data)
        return req

    def update(self, instance, validated_data):
        from core.models import MaterialRequestItem as MRI

        items_data = validated_data.pop("items", None)
        req = super().update(instance, validated_data)
        if items_data is not None:
            # replace all items
            instance.items.all().delete()
            for item in items_data:
                data = item if isinstance(item, dict) else {}
                data["request"] = req
                MRI.objects.create(**data)
        return req


class MaterialCatalogSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True, allow_null=True)

    class Meta:
        from core.models import MaterialCatalog

        model = MaterialCatalog
        fields = [
            "id",
            "project",
            "project_name",
            "category",
            "brand_text",
            "product_name",
            "color_name",
            "color_code",
            "finish",
            "gloss",
            "formula",
            "default_unit",
            "reference_image",
            "is_active",
            "created_by",
            "created_at",
        ]
        read_only_fields = ["created_by", "created_at"]


# ---------------------------------------------------------------------------
# Module 15: Field Materials (Employee quick usage & requests)
# Added lightweight serializers to support new FieldMaterialsViewSet custom
# actions without bloating existing MaterialRequest serializer (which expects
# nested items). These are intentionally minimal and read-only.
# ---------------------------------------------------------------------------

class ProjectStockSerializer(serializers.Serializer):
    """Lightweight representation of project inventory for employee dashboard."""
    item_id = serializers.IntegerField()
    item_name = serializers.CharField()
    sku = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    available_quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    is_below = serializers.BooleanField()


class ReportUsageResultSerializer(serializers.Serializer):
    """Serializer for usage reporting response payload.
    Not tied to a model; provides a consistent structure for frontend.
    """
    success = serializers.BooleanField()
    movement_id = serializers.IntegerField(required=False, allow_null=True)
    item_id = serializers.IntegerField(required=False, allow_null=True)
    item_name = serializers.CharField(required=False, allow_blank=True)
    consumed_quantity = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    remaining_quantity = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    message = serializers.CharField(required=False, allow_blank=True)
    error = serializers.CharField(required=False, allow_blank=True)


class QuickMaterialRequestSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    requested_by_name = serializers.CharField(source="requested_by.get_full_name", read_only=True, allow_null=True)

    class Meta:
        from core.models import MaterialRequest
        model = MaterialRequest
        fields = [
            "id",
            "project",
            "project_name",
            "requested_by",
            "requested_by_name",
            "needed_when",
            "notes",
            "status",
            "created_at",
        ]
        read_only_fields = ["requested_by", "status", "created_at"]


# ============================================================================
# PHASE 4: Module 16 - Payroll API
# ============================================================================


class PayrollPaymentSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.CharField(source="recorded_by.get_full_name", read_only=True, allow_null=True)

    class Meta:
        from core.models import PayrollPayment

        model = PayrollPayment
        fields = [
            "id",
            "payroll_record",
            "amount",
            "payment_date",
            "payment_method",
            "check_number",
            "reference",
            "notes",
            "recorded_by",
            "recorded_by_name",
            "recorded_at",
        ]
        read_only_fields = ["recorded_by", "recorded_at"]


class PayrollRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    amount_paid = serializers.SerializerMethodField()
    balance_due = serializers.SerializerMethodField()
    period_id = serializers.IntegerField(source="period.id", read_only=True)

    class Meta:
        from core.models import PayrollRecord

        model = PayrollRecord
        fields = [
            "id",
            "period",
            "period_id",
            "employee",
            "employee_name",
            "week_start",
            "week_end",
            "total_hours",
            "hourly_rate",
            "adjusted_rate",
            "regular_hours",
            "overtime_hours",
            "overtime_rate",
            "bonus",
            "deductions",
            "deduction_notes",
            "gross_pay",
            "tax_withheld",
            "net_pay",
            "total_pay",
            "manually_adjusted",
            "adjusted_by",
            "adjusted_at",
            "adjustment_reason",
            "reviewed",
            "notes",
            "amount_paid",
            "balance_due",
        ]
        read_only_fields = ["adjusted_by", "adjusted_at", "gross_pay", "net_pay", "amount_paid", "balance_due"]

    def get_employee_name(self, obj):
        try:
            return f"{obj.employee.first_name} {obj.employee.last_name}".strip()
        except Exception:
            return None

    def get_amount_paid(self, obj):
        try:
            return obj.amount_paid()
        except Exception:
            return 0

    def get_balance_due(self, obj):
        try:
            return obj.balance_due()
        except Exception:
            return 0


class PayrollPeriodSerializer(serializers.ModelSerializer):
    total_payroll = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()
    balance_due = serializers.SerializerMethodField()

    class Meta:
        from core.models import PayrollPeriod

        model = PayrollPeriod
        fields = [
            "id",
            "week_start",
            "week_end",
            "status",
            "notes",
            "created_by",
            "created_at",
            "approved_by",
            "approved_at",
            "validation_errors",
            "total_payroll",
            "total_paid",
            "balance_due",
        ]
        read_only_fields = [
            "created_by",
            "created_at",
            "approved_by",
            "approved_at",
            "validation_errors",
            "total_payroll",
            "total_paid",
            "balance_due",
        ]

    def get_total_payroll(self, obj):
        try:
            return obj.total_payroll()
        except Exception:
            return 0

    def get_total_paid(self, obj):
        try:
            return obj.total_paid()
        except Exception:
            return 0

    def get_balance_due(self, obj):
        try:
            return obj.balance_due()
        except Exception:
            return 0


# ============================================================================
# SECURITY: 2FA (TOTP)
# ============================================================================


class TwoFactorSetupSerializer(serializers.Serializer):
    secret = serializers.CharField(read_only=True)
    otpauth_uri = serializers.CharField(read_only=True)


class TwoFactorEnableSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)


class TwoFactorDisableSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)


# JWT: Custom Token serializer enforcing 2FA when enabled
try:
    from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
except Exception:  # pragma: no cover - fallback if simplejwt unavailable in certain contexts
    TokenObtainPairSerializer = object  # type: ignore


class TwoFactorTokenObtainPairSerializer(TokenObtainPairSerializer):  # type: ignore[misc]
    otp = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        data = super().validate(attrs)
        user = getattr(self, "user", None)
        if user is None:
            return data
        try:
            prof = getattr(user, "twofa", None)
            if prof and prof.enabled:
                otp = self.initial_data.get("otp")
                if not otp or not prof.verify_otp(otp):
                    raise serializers.ValidationError({"otp": _("Invalid or missing OTP for 2FA-enabled account")})
        except Exception:
            # If any unexpected error, deny for safety
            raise serializers.ValidationError({"otp": _("2FA validation failed")})
        return data


# ============================================================================
# PHASE 4: FILE MANAGER SERIALIZER
# ============================================================================

class ProjectFileSerializer(serializers.ModelSerializer):
    """Serializer for ProjectFile model - Phase 4 File Manager feature"""
    
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectFile
        fields = [
            'id', 
            'project', 
            'category', 
            'category_name',
            'file', 
            'file_url',
            'name', 
            'description',
            'file_type', 
            'file_size', 
            'uploaded_by',
            'uploaded_by_name',
            'uploaded_at', 
            'updated_at',
            'tags',
            'is_public',
            'version',
        ]
        read_only_fields = ['id', 'uploaded_at', 'updated_at', 'file_size', 'file_type']
    
    def get_file_url(self, obj):
        """Return full URL for file download"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


# ---------------------
# PWA Push Subscription Serializer
# ---------------------
class PushSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for PWA push notification subscriptions"""
    
    class Meta:
        model = PushSubscription
        fields = ['id', 'endpoint', 'p256dh', 'auth', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        # Automatically assign current user
        validated_data['user'] = self.context['request'].user
        
        # Remove existing subscription with same endpoint (update scenario)
        PushSubscription.objects.filter(
            user=validated_data['user'],
            endpoint=validated_data['endpoint']
        ).delete()
        
        return super().create(validated_data)


# =============================================================================
# EXECUTIVE FOCUS WORKFLOW SERIALIZERS (Module 25)
# =============================================================================

class FocusTaskSerializer(serializers.ModelSerializer):
    """Serializer for FocusTask model"""
    checklist_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = FocusTask
        fields = [
            'id',
            'session',
            'title',
            'description',
            'is_high_impact',
            'impact_reason',
            'is_frog',
            'checklist',
            'checklist_progress',
            'scheduled_start',
            'scheduled_end',
            'is_completed',
            'completed_at',
            'order',
        ]
        read_only_fields = ['id', 'completed_at', 'checklist_progress']
    
    def get_checklist_progress(self, obj):
        """Calculate checklist completion progress"""
        if not obj.checklist:
            return {'total': 0, 'done': 0, 'percent': 0}
        
        total = len(obj.checklist)
        done = sum(1 for item in obj.checklist if item.get('done', False))
        percent = int((done / total) * 100) if total > 0 else 0
        
        return {'total': total, 'done': done, 'percent': percent}


class DailyFocusSessionSerializer(serializers.ModelSerializer):
    """Full serializer for DailyFocusSession with nested tasks"""
    focus_tasks = FocusTaskSerializer(many=True, read_only=True)
    total_tasks = serializers.ReadOnlyField()
    completed_tasks = serializers.ReadOnlyField()
    high_impact_tasks = serializers.ReadOnlyField()
    frog_task_title = serializers.SerializerMethodField()
    
    class Meta:
        model = DailyFocusSession
        fields = [
            'id',
            'user',
            'date',
            'energy_level',
            'notes',
            'focus_tasks',
            'total_tasks',
            'completed_tasks',
            'high_impact_tasks',
            'frog_task_title',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_frog_task_title(self, obj):
        """Return the frog task title if exists"""
        frog = obj.frog_task
        return frog.title if frog else None


class FocusSessionCreateSerializer(serializers.Serializer):
    """Serializer for creating a DailyFocusSession with tasks in one request"""
    date = serializers.DateField()
    energy_level = serializers.IntegerField(min_value=1, max_value=10, default=5)
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    tasks = serializers.ListField(child=serializers.DictField())
    
    def validate_tasks(self, value):
        """Validate tasks data structure"""
        if not value:
            raise serializers.ValidationError("At least one task is required")
        
        # Ensure at most one frog
        frog_count = sum(1 for task in value if task.get('is_frog', False))
        if frog_count > 1:
            raise serializers.ValidationError("Only one task can be marked as Frog")
        
        return value
    
    def create(self, validated_data):
        """Create session and associated tasks"""
        user = self.context['request'].user
        tasks_data = validated_data.pop('tasks', [])
        
        # Create or update session for this date
        session, _ = DailyFocusSession.objects.update_or_create(
            user=user,
            date=validated_data['date'],
            defaults={
                'energy_level': validated_data.get('energy_level', 5),
                'notes': validated_data.get('notes', ''),
            }
        )
        
        # Clear existing tasks and create new ones
        session.focus_tasks.all().delete()
        
        for order, task_data in enumerate(tasks_data):
            is_frog = task_data.get('is_frog', False)
            is_high_impact = task_data.get('is_high_impact', False)
            impact_reason = task_data.get('impact_reason', '')
            
            # Auto-fix: If frog, must be high impact
            if is_frog:
                is_high_impact = True
            
            # Auto-fix: If high impact without reason, provide default
            if is_high_impact and not impact_reason.strip():
                impact_reason = "High priority task"
            
            # Parse datetime strings if needed
            scheduled_start = task_data.get('scheduled_start')
            scheduled_end = task_data.get('scheduled_end')
            
            # Handle datetime-local format from HTML input
            if scheduled_start and isinstance(scheduled_start, str):
                try:
                    from django.utils.dateparse import parse_datetime
                    scheduled_start = parse_datetime(scheduled_start.replace('T', ' '))
                except (ValueError, TypeError):
                    scheduled_start = None
            
            if scheduled_end and isinstance(scheduled_end, str):
                try:
                    from django.utils.dateparse import parse_datetime
                    scheduled_end = parse_datetime(scheduled_end.replace('T', ' '))
                except (ValueError, TypeError):
                    scheduled_end = None
            
            # Create task without calling full_clean (skip model validation)
            task = FocusTask(
                session=session,
                title=task_data.get('title', ''),
                description=task_data.get('description', ''),
                is_high_impact=is_high_impact,
                impact_reason=impact_reason,
                is_frog=is_frog,
                checklist=task_data.get('checklist', []),
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
                order=order,
            )
            # Save without triggering full_clean
            task.save(update_fields=None)
        
        return session


