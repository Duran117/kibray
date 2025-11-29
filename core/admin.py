from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    ActivityCompletion,
    ActivityTemplate,
    BudgetLine,
    BudgetProgress,
    ChangeOrder,
    ChatChannel,
    ChatMessage,
    MeetingMinute,
    ClientProjectAccess,
    ColorSample,
    CostCode,
    DailyPlan,
    DamagePhoto,
    DamageReport,
    DesignChatMessage,
    Employee,
    EmployeeCertification,
    EmployeePerformanceMetric,
    EmployeeSkillLevel,
    EVSnapshot,
    Expense,
    WarrantyTicket,
    ExpenseOCRData,
    FloorPlan,
    GPSCheckIn,
    Income,
    InventoryBarcode,
    InventoryItem,
    InventoryLocation,
    InventoryMovement,
    Invoice,
    InvoiceAutomation,
    InvoiceLine,
    InvoicePayment,
    MaterialCatalog,
    MaterialRequest,
    MaterialRequestItem,
    Notification,
    PlannedActivity,
    PlanPin,
    PlanPinAttachment,
    Profile,
    Project,
    ProjectInventory,
    ProjectManagerAssignment,
    ColorApproval,
    PunchListItem,
    QualityDefect,
    QualityInspection,
    RecurringTask,
    Schedule,
    ScheduleItem,
    SitePhoto,
    SOPCompletion,
    SOPReferenceFile,
    Subcontractor,
    SubcontractorAssignment,
    TaskTemplate,
    TimeEntry,
)


# Empleado
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("employee_key", "first_name", "last_name", "hourly_rate", "is_active")
    search_fields = ("employee_key", "first_name", "last_name", "social_security_number")
    list_filter = ("is_active",)
    ordering = ("employee_key",)
    readonly_fields = ("employee_key", "created_at")


# Ingreso
@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ("project_name", "amount", "date", "payment_method")
    search_fields = ("project_name", "payment_method")
    list_filter = ("payment_method", "date")
    date_hierarchy = "date"
    ordering = ("-date",)


# Gasto
@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("project_name", "category", "amount", "date", "project", "warranty_ticket")
    list_filter = ("category", "date", "project", "warranty_ticket")
    search_fields = ("project_name", "description")
    date_hierarchy = "date"
    ordering = ("-date",)


@admin.register(WarrantyTicket)
class WarrantyTicketAdmin(admin.ModelAdmin):
    list_display = ("ticket_number", "project", "priority", "status", "created_at", "resolved_at")
    list_filter = ("status", "priority", "project")
    search_fields = ("ticket_number", "project__name", "issue_description")
    readonly_fields = ("created_at",)


# Proyecto
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "project_code",
        "name",
        "client",
        "start_date",
        "end_date",
        "budget_total",
        "total_income",
        "total_expenses",
        "profit",
    )
    search_fields = ("project_code", "name", "client")
    list_filter = ("start_date", "end_date")
    ordering = ("-project_code",)
    readonly_fields = ("project_code", "total_income", "total_expenses", "profit")


# Registro de Horas
@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ("employee", "employee_key_display", "project", "project_code_display", "date", "hours_worked", "labor_cost")
    list_filter = ("project", "employee", "date")
    search_fields = ("employee__employee_key", "employee__first_name", "employee__last_name", "project__project_code", "project__name")
    readonly_fields = ("hours_worked", "labor_cost")
    date_hierarchy = "date"
    ordering = ("-date",)
    
    def employee_key_display(self, obj):
        return obj.employee.employee_key if obj.employee else "-"
    employee_key_display.short_description = "Employee Key"
    employee_key_display.admin_order_field = "employee__employee_key"
    
    def project_code_display(self, obj):
        return obj.project.project_code if obj.project else "-"
    project_code_display.short_description = "Project Code"
    project_code_display.admin_order_field = "project__project_code"


# Cronograma
@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ("project", "project_code_display", "title", "start_datetime", "end_datetime", "is_complete", "is_personal")
    list_filter = ("project", "is_complete", "is_personal", "stage")
    search_fields = ("project__project_code", "title", "description", "delay_reason", "advance_reason")
    date_hierarchy = "start_datetime"
    ordering = ("-start_datetime",)
    
    def project_code_display(self, obj):
        return obj.project.project_code if obj.project else "-"
    project_code_display.short_description = "Project Code"
    project_code_display.admin_order_field = "project__project_code"


# Cronograma jerárquico (ScheduleItem)
@admin.register(ScheduleItem)
class ScheduleItemAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "category", "status", "percent_complete", "order", "is_milestone")
    list_filter = ("project", "status", "is_milestone", "category")
    search_fields = ("title", "project__name", "category__name")
    ordering = ("project", "category__id", "order")


# Perfil de Usuario
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    list_filter = ("role",)
    search_fields = ("user__username",)


@admin.register(ClientProjectAccess)
class ClientProjectAccessAdmin(admin.ModelAdmin):
    list_display = ("user", "project", "role", "can_comment", "can_create_tasks", "granted_at")
    list_filter = ("role", "project")
    search_fields = ("user__username", "project__name")
    autocomplete_fields = ("user", "project")


# Factura
class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 1


class InvoicePaymentInline(admin.TabularInline):
    model = InvoicePayment
    extra = 0
    fields = ("amount", "payment_date", "payment_method", "reference", "recorded_by", "recorded_at")
    readonly_fields = ("recorded_at",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "project", "project_code_display", "status", "total_amount", "amount_paid", "balance_due", "date_issued")
    inlines = [InvoiceLineInline, InvoicePaymentInline]
    search_fields = ("invoice_number", "project__project_code", "project__name", "project__client")
    list_filter = ("status", "is_paid", "project")
    readonly_fields = ("invoice_number", "payment_progress", "balance_due")
    
    def project_code_display(self, obj):
        return obj.project.project_code if obj.project else "-"
    project_code_display.short_description = "Project Code"
    project_code_display.admin_order_field = "project__project_code"


@admin.register(InvoiceLine)
class InvoiceLineAdmin(admin.ModelAdmin):
    list_display = ("invoice", "description", "amount")
    search_fields = ("description",)


@admin.register(InvoicePayment)
class InvoicePaymentAdmin(admin.ModelAdmin):
    list_display = ("invoice", "amount", "payment_date", "payment_method", "reference", "recorded_by")
    list_filter = ("payment_method", "payment_date")
    search_fields = ("invoice__invoice_number", "reference")
    readonly_fields = ("recorded_at",)


class BudgetProgressInline(admin.TabularInline):
    model = BudgetProgress
    extra = 0
    fields = ("date", "percent_complete", "qty_completed", "note")
    ordering = ("-date",)


@admin.register(BudgetLine)
class BudgetLineAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "cost_code", "description", "baseline_amount", "planned_start", "planned_finish")
    list_filter = ("project", "cost_code")
    search_fields = ("description", "cost_code__code", "project__name")
    inlines = [BudgetProgressInline]
    fields = (
        "project",
        "cost_code",
        "description",
        "qty",
        "unit_cost",
        "baseline_amount",
        "planned_start",
        "planned_finish",
        "weight_override",
    )


@admin.register(BudgetProgress)
class BudgetProgressAdmin(admin.ModelAdmin):
    list_display = ("budget_line", "date", "percent_complete", "qty_completed", "note")
    list_filter = ("budget_line__project", "budget_line__cost_code")
    search_fields = ("budget_line__description", "budget_line__cost_code__code")
    ordering = ("-date",)


# Asegúrate de tener CostCode registrado (si no lo estaba):
@admin.register(CostCode)
class CostCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "active")
    list_filter = ("category", "active")
    search_fields = ("code", "name")


class MaterialRequestItemInline(admin.TabularInline):
    model = MaterialRequestItem
    extra = 0


@admin.register(MaterialRequest)
class MaterialRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "requested_by", "status", "needed_when", "needed_date", "created_at")
    list_filter = ("status", "needed_when", "project")
    inlines = [MaterialRequestItemInline]


@admin.register(MaterialCatalog)
class MaterialCatalogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "project",
        "category",
        "brand_text",
        "product_name",
        "color_name",
        "color_code",
        "is_active",
        "created_at",
    )
    list_filter = ("project", "category", "is_active")
    search_fields = ("brand_text", "product_name", "color_name", "color_code")


@admin.register(SitePhoto)
class SitePhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "room", "wall_ref", "approved_color", "brand", "finish", "coats", "created_at")
    list_filter = ("project", "room", "brand", "finish", "special_finish")
    search_fields = ("room", "wall_ref", "brand", "notes", "color_text")


@admin.register(ColorSample)
class ColorSampleAdmin(admin.ModelAdmin):
    list_display = ("project", "name", "code", "brand", "status", "version", "approved_by", "approved_at", "created_at")
    list_filter = ("project", "status", "brand")
    search_fields = ("name", "code", "brand", "notes")
    readonly_fields = ("approved_at", "created_at", "updated_at")


@admin.register(ColorApproval)
class ColorApprovalAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "project",
        "color_name",
        "color_code",
        "brand",
        "location",
        "status",
        "requested_by",
        "approved_by",
        "created_at",
        "signed_at",
    )
    list_filter = ("project", "status", "brand")
    search_fields = ("color_name", "color_code", "brand", "location", "project__name")
    readonly_fields = ("signed_at", "created_at")
    autocomplete_fields = ("project", "requested_by")

    actions = ["approve_selected", "reject_selected"]

    def has_approve_permission(self, request, obj):
        # Allow if admin or assigned PM for the project
        if request.user.is_superuser or request.user.is_staff:
            return True
        from .models import ProjectManagerAssignment

        return ProjectManagerAssignment.objects.filter(project=obj.project, pm=request.user).exists()

    def approve_selected(self, request, queryset):
        approved = 0
        for obj in queryset:
            if obj.status == "APPROVED":
                continue
            if not self.has_approve_permission(request, obj):
                self.message_user(request, f"No permission to approve {obj}", level="error")
                continue
            obj.approve(approver=request.user)
            approved += 1
        self.message_user(request, f"Approved {approved} color approvals.")

    approve_selected.short_description = "Approve selected color approvals"

    def reject_selected(self, request, queryset):
        rejected = 0
        for obj in queryset:
            if obj.status == "REJECTED":
                continue
            if not self.has_approve_permission(request, obj):
                self.message_user(request, f"No permission to reject {obj}", level="error")
                continue
            obj.reject(approver=request.user, reason="Rejected via admin action")
            rejected += 1
        self.message_user(request, f"Rejected {rejected} color approvals.")

    reject_selected.short_description = "Reject selected color approvals"


class PlanPinAttachmentInline(admin.TabularInline):
    model = PlanPinAttachment
    extra = 0


class PlanPinInline(admin.TabularInline):
    model = PlanPin
    extra = 0
    fields = ("x", "y", "title", "pin_type", "color_sample", "linked_task", "created_by")


@admin.register(FloorPlan)
class FloorPlanAdmin(admin.ModelAdmin):
    list_display = ("project", "name", "created_by", "created_at")
    list_filter = ("project",)
    search_fields = ("project__name", "name")
    inlines = [PlanPinInline]


@admin.register(ProjectManagerAssignment)
class ProjectManagerAssignmentAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "pm", "created_at")
    list_filter = ("project", "pm")
    search_fields = ("project__name", "pm__username", "pm__first_name", "pm__last_name")
    autocomplete_fields = ("project", "pm")


@admin.register(PlanPin)
class PlanPinAdmin(admin.ModelAdmin):
    list_display = ("plan", "pin_type", "title", "x", "y", "color_sample", "linked_task", "created_by", "created_at")
    list_filter = ("pin_type", "plan__project")
    search_fields = ("title", "description", "plan__name", "plan__project__name")
    inlines = [PlanPinAttachmentInline]


@admin.register(DamageReport)
class DamageReportAdmin(admin.ModelAdmin):
    list_display = ("project", "title", "severity", "status", "reported_by", "reported_at")
    list_filter = ("project", "severity", "status")
    search_fields = ("title", "description", "project__name")


@admin.register(DamagePhoto)
class DamagePhotoAdmin(admin.ModelAdmin):
    list_display = ("report", "created_at", "notes")
    list_filter = ("report",)


@admin.register(DesignChatMessage)
class DesignChatMessageAdmin(admin.ModelAdmin):
    list_display = ("project", "user", "created_at", "pinned")
    list_filter = ("project", "pinned")
    search_fields = ("message", "project__name", "user__username")


# Chat canales
class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("user", "created_at")
    fields = ("user", "message", "link_url", "image", "created_at")


@admin.register(ChatChannel)
class ChatChannelAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "channel_type", "is_default", "created_at")
    list_filter = ("channel_type", "is_default")
    search_fields = ("name", "project__name")
    filter_horizontal = ("participants",)
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("channel", "user", "message", "created_at")
    list_filter = ("created_at", "channel__project")
    search_fields = ("message", "user__username")
    readonly_fields = ("created_at",)


@admin.register(MeetingMinute)
class MeetingMinuteAdmin(admin.ModelAdmin):
    list_display = ("project", "date", "created_by", "created_at", "tasks_summary")
    list_filter = ("project", "date")
    search_fields = ("project__name", "content")
    readonly_fields = ("created_at",)

    def tasks_summary(self, obj: MeetingMinute):
        """Show count of tasks created from this minute and link to Task admin filtered view if available."""
        try:
            from core.models import Task  # type: ignore
        except Exception:
            return "—"
        # If Task has FK `source_minute`, provide link; else show em dash
        if hasattr(Task, "source_minute"):
            count = Task.objects.filter(source_minute=obj).count()
            if count == 0:
                return "0"
            try:
                url = reverse("admin:core_task_changelist") + f"?source_minute__id__exact={obj.id}"
                return format_html("<a href='{}'>{} task(s)</a>", url, count)
            except Exception:
                return str(count)
        return "—"

    tasks_summary.short_description = "Tasks from minute"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "notification_type", "title", "is_read", "created_at")
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = ("title", "message", "user__username")
    readonly_fields = ("created_at",)


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "category", "unit", "default_threshold", "active")
    list_filter = ("category", "active")
    search_fields = ("sku", "name", "category")
    ordering = ("sku",)
    readonly_fields = ("sku",)


@admin.register(InventoryLocation)
class InventoryLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "is_storage")
    list_filter = ("is_storage", "project")
    search_fields = ("name",)


@admin.register(ProjectInventory)
class ProjectInventoryAdmin(admin.ModelAdmin):
    list_display = ("item", "item_sku_display", "location", "quantity", "threshold_override")
    list_filter = ("location__project", "item__category")
    search_fields = ("item__sku", "item__name", "location__name")
    
    def item_sku_display(self, obj):
        return obj.item.sku if obj.item else "-"
    item_sku_display.short_description = "SKU"
    item_sku_display.admin_order_field = "item__sku"


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ("created_at", "movement_type", "item", "quantity", "from_location", "to_location", "created_by")
    list_filter = ("movement_type", "item__category", "item", "created_by")
    search_fields = ("item__name", "from_location__name", "to_location__name", "note")
    readonly_fields = ("created_at", "created_by")

    def save_model(self, request, obj, form, change):
        # Al crear: guarda, aplica al stock y bloquea ediciones posteriores
        if not change:
            obj.created_by = request.user
            super().save_model(request, obj, form, change)
            obj.apply()
        else:
            super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        # Evitar re-editar movimientos (auditoría simple)
        return False


# ===========================
# DAILY PLANNING SYSTEM ADMIN
# ===========================


class SOPReferenceFileInline(admin.TabularInline):
    model = SOPReferenceFile
    extra = 1
    fields = ("file", "uploaded_at")
    readonly_fields = ("uploaded_at",)


@admin.register(ActivityTemplate)
class ActivityTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "time_estimate", "is_active", "created_at")
    list_filter = ("category", "is_active", "created_at")
    search_fields = ("name", "description", "tips")
    ordering = ("category", "name")
    readonly_fields = ("created_by", "created_at", "updated_at")
    inlines = [SOPReferenceFileInline]

    fieldsets = (
        ("Basic Info", {"fields": ("name", "category", "description", "time_estimate", "is_active")}),
        ("SOP Details", {"fields": ("steps", "materials_list", "tools_list", "tips", "common_errors")}),
        ("Media", {"fields": ("reference_photos", "video_url")}),
        ("Metadata", {"fields": ("created_by", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Creating new
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SOPReferenceFile)
class SOPReferenceFileAdmin(admin.ModelAdmin):
    list_display = ("sop", "filename", "uploaded_at")
    list_filter = ("uploaded_at", "sop")
    search_fields = ("sop__name",)
    readonly_fields = ("uploaded_at",)


class PlannedActivityInline(admin.TabularInline):
    model = PlannedActivity
    extra = 1
    fields = (
        "order",
        "title",
        "activity_template",
        "schedule_item",
        "estimated_hours",
        "status",
        "progress_percentage",
    )
    autocomplete_fields = ["activity_template", "schedule_item"]


@admin.register(DailyPlan)
class DailyPlanAdmin(admin.ModelAdmin):
    list_display = ("project", "plan_date", "status", "created_by", "completion_deadline", "is_overdue")
    list_filter = ("status", "plan_date", "project")
    search_fields = ("project__name", "no_planning_reason")
    date_hierarchy = "plan_date"
    ordering = ("-plan_date",)
    readonly_fields = ("created_by", "created_at", "updated_at", "approved_by", "approved_at")
    inlines = [PlannedActivityInline]

    fieldsets = (
        ("Plan Details", {"fields": ("project", "plan_date", "status", "completion_deadline")}),
        (
            "Skip Planning (if applicable)",
            {
                "fields": ("no_planning_reason", "admin_approved", "approved_by", "approved_at"),
                "classes": ("collapse",),
            },
        ),
        ("Metadata", {"fields": ("created_by", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        if obj.status == "APPROVED" and not obj.approved_by:
            obj.approved_by = request.user
            from django.utils import timezone

            obj.approved_at = timezone.now()
        super().save_model(request, obj, form, change)

    def is_overdue(self, obj):
        return obj.is_overdue()

    is_overdue.boolean = True
    is_overdue.short_description = "Overdue?"


@admin.register(PlannedActivity)
class PlannedActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "daily_plan", "status", "progress_percentage", "materials_checked", "material_shortage")
    list_filter = ("status", "is_group_activity", "materials_checked", "material_shortage", "daily_plan__plan_date")
    search_fields = ("title", "description", "daily_plan__project__name")
    ordering = ("daily_plan__plan_date", "order")
    filter_horizontal = ("assigned_employees",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Activity Info", {"fields": ("daily_plan", "title", "description", "order", "status", "progress_percentage")}),
        ("Links", {"fields": ("schedule_item", "activity_template")}),
        ("Assignment", {"fields": ("assigned_employees", "is_group_activity", "estimated_hours")}),
        ("Materials", {"fields": ("materials_needed", "materials_checked", "material_shortage")}),
        ("Metadata", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    actions = ["check_materials_action"]

    def check_materials_action(self, request, queryset):
        for activity in queryset:
            activity.check_materials()
        self.message_user(request, f"Materials checked for {queryset.count()} activities")

    check_materials_action.short_description = "Check material availability"


@admin.register(ActivityCompletion)
class ActivityCompletionAdmin(admin.ModelAdmin):
    list_display = ("planned_activity", "completed_by", "completion_datetime", "progress_percentage", "verified_by")
    list_filter = ("completion_datetime", "verified_by", "completed_by")
    search_fields = ("planned_activity__title", "employee_notes")
    ordering = ("-completion_datetime",)
    readonly_fields = ("completion_datetime",)

    fieldsets = (
        (
            "Completion Info",
            {"fields": ("planned_activity", "completed_by", "completion_datetime", "progress_percentage")},
        ),
        ("Documentation", {"fields": ("completion_photos", "employee_notes")}),
        ("Verification", {"fields": ("verified_by", "verified_at")}),
    )

    def save_model(self, request, obj, form, change):
        if not change and not obj.verified_by:
            # Auto-verify if PM is completing
            from django.utils import timezone

            obj.verified_by = request.user
            obj.verified_at = timezone.now()
        super().save_model(request, obj, form, change)


# ===========================
# NEW MODELS - ADVANCED FEATURES
# ===========================


@admin.register(EVSnapshot)
class EVSnapshotAdmin(admin.ModelAdmin):
    list_display = ("project", "date", "earned_value", "actual_cost", "spi", "cpi", "percent_complete")
    list_filter = ("project", "date")
    search_fields = ("project__name",)
    date_hierarchy = "date"
    ordering = ("-date",)
    readonly_fields = (
        "spi",
        "cpi",
        "schedule_variance",
        "cost_variance",
        "estimate_at_completion",
        "estimate_to_complete",
        "variance_at_completion",
    )


@admin.register(QualityInspection)
class QualityInspectionAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "inspection_type",
        "scheduled_date",
        "status",
        "overall_score",
        "ai_defect_count",
        "manual_defect_count",
        "inspector",
    )
    list_filter = ("status", "inspection_type", "project", "scheduled_date")
    search_fields = ("project__name", "inspector__username", "notes")
    date_hierarchy = "scheduled_date"
    readonly_fields = ("ai_defect_count", "manual_defect_count")
    fieldsets = (
        (
            "Inspection Details",
            {"fields": ("project", "inspection_type", "scheduled_date", "completed_date", "inspector", "status")},
        ),
        ("Results", {"fields": ("overall_score", "ai_defect_count", "manual_defect_count", "notes")}),
        ("Checklist", {"fields": ("checklist_data",)}),
        ("Warranty", {"fields": ("warranty_expiration", "warranty_notes"), "classes": ("collapse",)}),
    )


@admin.register(QualityDefect)
class QualityDefectAdmin(admin.ModelAdmin):
    list_display = ("inspection", "severity", "category", "detected_by_ai", "ai_confidence", "resolved", "resolved_by")
    list_filter = ("severity", "category", "detected_by_ai", "resolved", "inspection__project")
    search_fields = ("description", "location", "resolution_notes")
    readonly_fields = ("ai_confidence", "ai_pattern_match")
    fieldsets = (
        ("Defect Info", {"fields": ("inspection", "severity", "category", "description", "location")}),
        ("AI Detection", {"fields": ("detected_by_ai", "ai_confidence", "ai_pattern_match")}),
        ("Photos", {"fields": ("photo", "resolution_photo")}),
        ("Resolution", {"fields": ("resolved", "resolved_date", "resolved_by", "resolution_notes")}),
    )


@admin.register(RecurringTask)
class RecurringTaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "project",
        "frequency",
        "start_date",
        "end_date",
        "assigned_to",
        "active",
        "last_generated",
    )
    list_filter = ("frequency", "active", "project")
    search_fields = ("title", "description", "project__name")
    readonly_fields = ("last_generated",)
    fieldsets = (
        ("Task Info", {"fields": ("project", "title", "description", "frequency", "estimated_hours")}),
        ("Schedule", {"fields": ("start_date", "end_date", "last_generated", "active")}),
        ("Assignment", {"fields": ("assigned_to", "cost_code")}),
        ("Checklist", {"fields": ("checklist",)}),
    )


@admin.register(GPSCheckIn)
class GPSCheckInAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "project",
        "check_in_time",
        "check_out_time",
        "within_geofence",
        "distance_from_project",
        "flagged_for_review",
    )
    list_filter = ("within_geofence", "flagged_for_review", "auto_break_detected", "project", "employee")
    search_fields = ("employee__first_name", "employee__last_name", "project__name", "review_notes")
    readonly_fields = ("distance_from_project", "auto_break_detected", "auto_break_minutes")
    date_hierarchy = "check_in_time"
    fieldsets = (
        ("Basic Info", {"fields": ("employee", "project", "time_entry")}),
        ("Check In", {"fields": ("check_in_time", "check_in_latitude", "check_in_longitude", "check_in_accuracy")}),
        (
            "Check Out",
            {"fields": ("check_out_time", "check_out_latitude", "check_out_longitude", "check_out_accuracy")},
        ),
        (
            "Geofence Validation",
            {"fields": ("within_geofence", "distance_from_project", "flagged_for_review", "review_notes")},
        ),
        ("Auto Break Detection", {"fields": ("auto_break_detected", "auto_break_minutes"), "classes": ("collapse",)}),
    )


@admin.register(ExpenseOCRData)
class ExpenseOCRDataAdmin(admin.ModelAdmin):
    list_display = (
        "expense",
        "vendor_name",
        "transaction_date",
        "total_amount",
        "ocr_confidence",
        "verified",
        "verified_by",
    )
    list_filter = ("verified", "ocr_confidence", "ai_suggestion_confidence")
    search_fields = ("vendor_name", "raw_text", "verification_notes")
    readonly_fields = ("ocr_confidence", "ai_suggestion_confidence", "raw_text")
    fieldsets = (
        ("Expense Link", {"fields": ("expense",)}),
        (
            "OCR Extracted Data",
            {
                "fields": (
                    "vendor_name",
                    "transaction_date",
                    "total_amount",
                    "tax_amount",
                    "line_items",
                    "raw_text",
                    "ocr_confidence",
                )
            },
        ),
        ("AI Suggestions", {"fields": ("suggested_category", "suggested_cost_code", "ai_suggestion_confidence")}),
        ("Verification", {"fields": ("verified", "verified_by", "verification_notes")}),
    )


@admin.register(InvoiceAutomation)
class InvoiceAutomationAdmin(admin.ModelAdmin):
    list_display = (
        "invoice",
        "is_recurring",
        "recurrence_frequency",
        "next_recurrence_date",
        "auto_send_on_creation",
        "auto_remind_before_due",
        "last_reminder_sent",
    )
    list_filter = (
        "is_recurring",
        "recurrence_frequency",
        "auto_send_on_creation",
        "auto_remind_before_due",
        "auto_remind_after_due",
        "apply_late_fees",
    )
    search_fields = ("invoice__invoice_number", "stripe_payment_intent_id", "payment_link")
    readonly_fields = ("stripe_payment_intent_id", "payment_link", "last_reminder_sent")
    fieldsets = (
        ("Invoice Link", {"fields": ("invoice",)}),
        (
            "Recurrence",
            {"fields": ("is_recurring", "recurrence_frequency", "next_recurrence_date", "recurrence_end_date")},
        ),
        (
            "Automation Settings",
            {
                "fields": (
                    "auto_send_on_creation",
                    "auto_remind_before_due",
                    "auto_remind_after_due",
                    "reminder_frequency_days",
                )
            },
        ),
        ("Late Fees", {"fields": ("apply_late_fees", "late_fee_percentage", "late_fee_grace_days")}),
        (
            "Payment Integration",
            {"fields": ("stripe_payment_intent_id", "payment_link", "last_reminder_sent"), "classes": ("collapse",)},
        ),
    )


@admin.register(InventoryBarcode)
class InventoryBarcodeAdmin(admin.ModelAdmin):
    list_display = (
        "item",
        "barcode_type",
        "barcode_value",
        "enable_auto_reorder",
        "reorder_point",
        "reorder_quantity",
        "preferred_vendor",
    )
    list_filter = ("barcode_type", "enable_auto_reorder", "item__category")
    search_fields = ("barcode_value", "item__name", "preferred_vendor")
    readonly_fields = ("barcode_image",)
    fieldsets = (
        ("Barcode Info", {"fields": ("item", "barcode_type", "barcode_value", "barcode_image")}),
        ("Auto Reorder", {"fields": ("enable_auto_reorder", "reorder_point", "reorder_quantity", "preferred_vendor")}),
    )


# ===========================
# NUEVOS MODELOS 2025
# ===========================


@admin.register(PunchListItem)
class PunchListItemAdmin(admin.ModelAdmin):
    list_display = ("project", "location", "priority", "category", "status", "assigned_to", "created_at")
    list_filter = ("status", "priority", "category", "created_at")
    search_fields = ("project__name", "location", "description")
    readonly_fields = ("created_at", "created_by", "completed_at", "verified_at", "verified_by")
    fieldsets = (
        ("Item Details", {"fields": ("project", "location", "description", "priority", "category")}),
        ("Assignment", {"fields": ("assigned_to", "status")}),
        ("Media", {"fields": ("photo",)}),
        (
            "Tracking",
            {
                "fields": ("created_at", "created_by", "completed_at", "verified_at", "verified_by", "notes"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Subcontractor)
class SubcontractorAdmin(admin.ModelAdmin):
    list_display = ("company_name", "specialty", "contact_name", "phone", "rating", "insurance_verified", "is_active")
    list_filter = ("specialty", "insurance_verified", "w9_on_file", "is_active")
    search_fields = ("company_name", "contact_name", "email", "phone")
    readonly_fields = ("created_at",)
    fieldsets = (
        ("Company Info", {"fields": ("company_name", "specialty", "contact_name", "email", "phone", "address")}),
        ("Rates & Rating", {"fields": ("hourly_rate", "rating")}),
        ("Compliance", {"fields": ("insurance_verified", "insurance_expires", "w9_on_file", "license_number")}),
        ("Status", {"fields": ("is_active", "notes", "created_at")}),
    )


@admin.register(SubcontractorAssignment)
class SubcontractorAssignmentAdmin(admin.ModelAdmin):
    list_display = ("project", "subcontractor", "status", "start_date", "end_date", "contract_amount", "balance_due")
    list_filter = ("status", "start_date")
    search_fields = ("project__name", "subcontractor__company_name")
    readonly_fields = ("created_at", "balance_due")
    fieldsets = (
        ("Assignment", {"fields": ("project", "subcontractor", "scope_of_work", "status")}),
        ("Timeline", {"fields": ("start_date", "end_date")}),
        ("Financials", {"fields": ("contract_amount", "amount_paid", "balance_due")}),
        ("Notes", {"fields": ("notes", "created_at"), "classes": ("collapse",)}),
    )


@admin.register(EmployeePerformanceMetric)
class EmployeePerformanceMetricAdmin(admin.ModelAdmin):
    list_display = ("employee", "year", "month", "productivity_rate", "quality_rating", "bonus_amount", "bonus_paid")
    list_filter = ("year", "month", "bonus_paid")
    search_fields = ("employee__first_name", "employee__last_name")
    readonly_fields = ("created_at", "updated_at", "overall_score")
    fieldsets = (
        ("Period", {"fields": ("employee", "year", "month")}),
        (
            "Auto-Calculated Metrics",
            {
                "fields": (
                    "total_hours_worked",
                    "billable_hours",
                    "productivity_rate",
                    "defects_created",
                    "tasks_completed",
                    "tasks_on_time",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Attendance", {"fields": ("days_worked", "days_late", "days_absent")}),
        ("Manual Ratings", {"fields": ("quality_rating", "attitude_rating", "teamwork_rating", "overall_score")}),
        ("Bonus", {"fields": ("bonus_amount", "bonus_notes", "bonus_paid", "bonus_paid_date")}),
        ("Metadata", {"fields": ("notes", "created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(EmployeeCertification)
class EmployeeCertificationAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "certification_name",
        "skill_category",
        "date_earned",
        "expires_at",
        "is_expired",
        "verified_by",
    )
    list_filter = ("skill_category", "date_earned", "expires_at")
    search_fields = ("employee__first_name", "employee__last_name", "certification_name", "certificate_number")
    readonly_fields = ("date_earned", "is_expired")
    fieldsets = (
        ("Certification", {"fields": ("employee", "certification_name", "skill_category", "certificate_number")}),
        ("Dates", {"fields": ("date_earned", "expires_at", "is_expired")}),
        ("Verification", {"fields": ("verified_by", "notes")}),
    )


@admin.register(EmployeeSkillLevel)
class EmployeeSkillLevelAdmin(admin.ModelAdmin):
    list_display = ("employee", "skill", "level", "total_points", "assessments_passed", "last_assessment_date")
    list_filter = ("level", "last_assessment_date")
    search_fields = ("employee__first_name", "employee__last_name", "skill")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Skill Info", {"fields": ("employee", "skill", "level")}),
        ("Progress", {"fields": ("assessments_passed", "total_points", "last_assessment_date")}),
        ("Notes", {"fields": ("notes", "created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(SOPCompletion)
class SOPCompletionAdmin(admin.ModelAdmin):
    list_display = ("employee", "sop", "completed_at", "passed", "score", "points_awarded", "badge_awarded")
    list_filter = ("passed", "completed_at", "badge_awarded")
    search_fields = ("employee__first_name", "employee__last_name", "sop__name")
    readonly_fields = ("completed_at",)
    fieldsets = (
        ("Completion", {"fields": ("employee", "sop", "completed_at", "time_taken")}),
        ("Results", {"fields": ("score", "passed", "points_awarded", "badge_awarded")}),
        ("Notes", {"fields": ("notes",), "classes": ("collapse",)}),
    )


# Change Order Admin - Redirige al CO Board después de crear/editar
@admin.register(ChangeOrder)
class ChangeOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "description_short", "amount", "status", "date_created")
    list_filter = ("status", "date_created", "project")
    search_fields = ("project__name", "description")
    readonly_fields = ("date_created",)
    date_hierarchy = "date_created"
    ordering = ("-date_created",)

    def description_short(self, obj):
        """Muestra una versión corta de la descripción"""
        return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description

    description_short.short_description = "Description"

    def response_add(self, request, obj, post_url_continue=None):
        """Redirige al CO Board después de crear un CO"""
        return redirect("changeorder_board")

    def response_change(self, request, obj):
        """Redirige al CO Board después de editar un CO"""
        return redirect("changeorder_board")


@admin.register(TaskTemplate)
class TaskTemplateAdmin(admin.ModelAdmin):
    list_display = ("title", "default_priority", "estimated_hours", "is_active", "created_at")
    search_fields = ("title", "description", "tags")
    list_filter = ("default_priority", "is_active")
    readonly_fields = ("created_at", "updated_at")
