from django.contrib import admin
from .models import Employee, Income, Expense, Project, TimeEntry, Schedule, Profile, Invoice, InvoiceLine, InvoicePayment
from .models import ClientProjectAccess
from .models import BudgetLine, BudgetProgress, CostCode
from .models import MaterialRequest, MaterialRequestItem
from .models import MaterialCatalog, SitePhoto
from .models import ColorSample, FloorPlan, PlanPin, PlanPinAttachment, DamageReport, DamagePhoto, DesignChatMessage
from .models import ChatChannel, ChatMessage
from .models import Notification
from .models import (
    InventoryItem, InventoryLocation, ProjectInventory, InventoryMovement,
)
from .models import ActivityTemplate, DailyPlan, PlannedActivity, ActivityCompletion, SOPReferenceFile

# Empleado
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'hourly_rate', 'phone', 'is_active')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    list_filter = ('is_active', 'position')
    ordering = ('-hire_date',)

# Ingreso
@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('project_name', 'amount', 'date', 'payment_method')
    search_fields = ('project_name', 'payment_method')
    list_filter = ('payment_method', 'date')
    date_hierarchy = 'date'
    ordering = ('-date',)

# Gasto
@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('project_name', 'category', 'amount', 'date')
    list_filter = ('category', 'date')
    search_fields = ('project_name', 'description')
    date_hierarchy = 'date'
    ordering = ('-date',)

# Proyecto
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'client', 'start_date', 'end_date',
        'budget_labor', 'budget_materials', 'budget_other', 'budget_total',
        'total_income', 'total_expenses', 'profit'
    )
    search_fields = ('name', 'client')
    list_filter = ('start_date', 'end_date')
    ordering = ('-start_date',)

# Registro de Horas
@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'project', 'date', 'hours_worked', 'labor_cost')
    list_filter = ('project', 'employee', 'date')
    search_fields = ('employee__first_name', 'employee__last_name', 'project__name')
    readonly_fields = ('hours_worked', 'labor_cost')
    date_hierarchy = 'date'
    ordering = ('-date',)

# Cronograma
@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('project', 'title', 'start_datetime', 'end_datetime', 'is_complete', 'is_personal')
    list_filter = ('project', 'is_complete', 'is_personal', 'stage')
    search_fields = ('title', 'description', 'delay_reason', 'advance_reason')
    date_hierarchy = 'start_datetime'
    ordering = ('-start_datetime',)

# Perfil de Usuario
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username',)

@admin.register(ClientProjectAccess)
class ClientProjectAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'role', 'can_comment', 'can_create_tasks', 'granted_at')
    list_filter = ('role', 'project')
    search_fields = ('user__username', 'project__name')
    autocomplete_fields = ('user', 'project')

# Factura
class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 1

class InvoicePaymentInline(admin.TabularInline):
    model = InvoicePayment
    extra = 0
    fields = ('amount', 'payment_date', 'payment_method', 'reference', 'recorded_by', 'recorded_at')
    readonly_fields = ('recorded_at',)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'project', 'status', 'total_amount', 'amount_paid', 'balance_due', 'date_issued')
    inlines = [InvoiceLineInline, InvoicePaymentInline]
    search_fields = ('invoice_number', 'project__name', 'project__client')
    list_filter = ('status', 'is_paid', 'project')
    readonly_fields = ('invoice_number', 'payment_progress', 'balance_due')

@admin.register(InvoiceLine)
class InvoiceLineAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'description', 'amount')
    search_fields = ('description',)

@admin.register(InvoicePayment)
class InvoicePaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'amount', 'payment_date', 'payment_method', 'reference', 'recorded_by')
    list_filter = ('payment_method', 'payment_date')
    search_fields = ('invoice__invoice_number', 'reference')
    readonly_fields = ('recorded_at',)

class BudgetProgressInline(admin.TabularInline):
    model = BudgetProgress
    extra = 0
    fields = ('date', 'percent_complete', 'qty_completed', 'note')
    ordering = ('-date',)

@admin.register(BudgetLine)
class BudgetLineAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'cost_code', 'description', 'baseline_amount', 'planned_start', 'planned_finish')
    list_filter = ('project', 'cost_code')
    search_fields = ('description', 'cost_code__code', 'project__name')
    inlines = [BudgetProgressInline]
    fields = (
        'project', 'cost_code', 'description',
        'qty', 'unit_cost', 'baseline_amount',
        'planned_start', 'planned_finish', 'weight_override'
    )

@admin.register(BudgetProgress)
class BudgetProgressAdmin(admin.ModelAdmin):
    list_display = ('budget_line', 'date', 'percent_complete', 'qty_completed', 'note')
    list_filter = ('budget_line__project', 'budget_line__cost_code')
    search_fields = ('budget_line__description', 'budget_line__cost_code__code')
    ordering = ('-date',)

# Asegúrate de tener CostCode registrado (si no lo estaba):
@admin.register(CostCode)
class CostCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'active')
    list_filter = ('category', 'active')
    search_fields = ('code', 'name')

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
    list_display = ("id", "project", "category", "brand_text", "product_name", "color_name", "color_code", "is_active", "created_at")
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

class PlanPinAttachmentInline(admin.TabularInline):
    model = PlanPinAttachment
    extra = 0

class PlanPinInline(admin.TabularInline):
    model = PlanPin
    extra = 0
    fields = ("x","y","title","pin_type","color_sample","linked_task","created_by")

@admin.register(FloorPlan)
class FloorPlanAdmin(admin.ModelAdmin):
    list_display = ("project","name","created_by","created_at")
    list_filter = ("project",)
    search_fields = ("project__name","name")
    inlines = [PlanPinInline]

@admin.register(PlanPin)
class PlanPinAdmin(admin.ModelAdmin):
    list_display = ("plan","pin_type","title","x","y","color_sample","linked_task","created_by","created_at")
    list_filter = ("pin_type","plan__project")
    search_fields = ("title","description","plan__name","plan__project__name")
    inlines = [PlanPinAttachmentInline]

@admin.register(DamageReport)
class DamageReportAdmin(admin.ModelAdmin):
    list_display = ("project","title","severity","status","reported_by","reported_at")
    list_filter = ("project","severity","status")
    search_fields = ("title","description","project__name")

@admin.register(DamagePhoto)
class DamagePhotoAdmin(admin.ModelAdmin):
    list_display = ("report","created_at","notes")
    list_filter = ("report",)

@admin.register(DesignChatMessage)
class DesignChatMessageAdmin(admin.ModelAdmin):
    list_display = ("project","user","created_at","pinned")
    list_filter = ("project","pinned")
    search_fields = ("message","project__name","user__username")

# Chat canales
class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('user','created_at')
    fields = ('user','message','link_url','image','created_at')

@admin.register(ChatChannel)
class ChatChannelAdmin(admin.ModelAdmin):
    list_display = ('name','project','channel_type','is_default','created_at')
    list_filter = ('channel_type','is_default')
    search_fields = ('name','project__name')
    filter_horizontal = ('participants',)
    inlines = [ChatMessageInline]

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('channel','user','message','created_at')
    list_filter = ('created_at','channel__project')
    search_fields = ('message','user__username')
    readonly_fields = ('created_at',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user','notification_type','title','is_read','created_at')
    list_filter = ('notification_type','is_read','created_at')
    search_fields = ('title','message','user__username')
    readonly_fields = ('created_at',)

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "unit", "default_threshold", "active")
    list_filter = ("category", "active")
    search_fields = ("name",)

@admin.register(InventoryLocation)
class InventoryLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "is_storage")
    list_filter = ("is_storage", "project")
    search_fields = ("name",)

@admin.register(ProjectInventory)
class ProjectInventoryAdmin(admin.ModelAdmin):
    list_display = ("item", "location", "quantity", "threshold_override")
    list_filter = ("location__project", "item__category")
    search_fields = ("item__name", "location__name")

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
    fields = ('file', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


@admin.register(ActivityTemplate)
class ActivityTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'time_estimate', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'tips')
    ordering = ('category', 'name')
    readonly_fields = ('created_by', 'created_at', 'updated_at')
    inlines = [SOPReferenceFileInline]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'category', 'description', 'time_estimate', 'is_active')
        }),
        ('SOP Details', {
            'fields': ('steps', 'materials_list', 'tools_list', 'tips', 'common_errors')
        }),
        ('Media', {
            'fields': ('reference_photos', 'video_url')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SOPReferenceFile)
class SOPReferenceFileAdmin(admin.ModelAdmin):
    list_display = ('sop', 'filename', 'uploaded_at')
    list_filter = ('uploaded_at', 'sop')
    search_fields = ('sop__name',)
    readonly_fields = ('uploaded_at',)


class PlannedActivityInline(admin.TabularInline):
    model = PlannedActivity
    extra = 1
    fields = ('order', 'title', 'activity_template', 'schedule_item', 'estimated_hours', 'status', 'progress_percentage')
    autocomplete_fields = ['activity_template', 'schedule_item']


@admin.register(DailyPlan)
class DailyPlanAdmin(admin.ModelAdmin):
    list_display = ('project', 'plan_date', 'status', 'created_by', 'completion_deadline', 'is_overdue')
    list_filter = ('status', 'plan_date', 'project')
    search_fields = ('project__name', 'no_planning_reason')
    date_hierarchy = 'plan_date'
    ordering = ('-plan_date',)
    readonly_fields = ('created_by', 'created_at', 'updated_at', 'approved_by', 'approved_at')
    inlines = [PlannedActivityInline]
    
    fieldsets = (
        ('Plan Details', {
            'fields': ('project', 'plan_date', 'status', 'completion_deadline')
        }),
        ('Skip Planning (if applicable)', {
            'fields': ('no_planning_reason', 'admin_approved', 'approved_by', 'approved_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        if obj.status == 'APPROVED' and not obj.approved_by:
            obj.approved_by = request.user
            from django.utils import timezone
            obj.approved_at = timezone.now()
        super().save_model(request, obj, form, change)
    
    def is_overdue(self, obj):
        return obj.is_overdue()
    is_overdue.boolean = True
    is_overdue.short_description = 'Overdue?'


@admin.register(PlannedActivity)
class PlannedActivityAdmin(admin.ModelAdmin):
    list_display = ('title', 'daily_plan', 'status', 'progress_percentage', 'materials_checked', 'material_shortage')
    list_filter = ('status', 'is_group_activity', 'materials_checked', 'material_shortage', 'daily_plan__plan_date')
    search_fields = ('title', 'description', 'daily_plan__project__name')
    ordering = ('daily_plan__plan_date', 'order')
    filter_horizontal = ('assigned_employees',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Activity Info', {
            'fields': ('daily_plan', 'title', 'description', 'order', 'status', 'progress_percentage')
        }),
        ('Links', {
            'fields': ('schedule_item', 'activity_template')
        }),
        ('Assignment', {
            'fields': ('assigned_employees', 'is_group_activity', 'estimated_hours')
        }),
        ('Materials', {
            'fields': ('materials_needed', 'materials_checked', 'material_shortage')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['check_materials_action']
    
    def check_materials_action(self, request, queryset):
        for activity in queryset:
            activity.check_materials()
        self.message_user(request, f"Materials checked for {queryset.count()} activities")
    check_materials_action.short_description = "Check material availability"


@admin.register(ActivityCompletion)
class ActivityCompletionAdmin(admin.ModelAdmin):
    list_display = ('planned_activity', 'completed_by', 'completion_datetime', 'progress_percentage', 'verified_by')
    list_filter = ('completion_datetime', 'verified_by', 'completed_by')
    search_fields = ('planned_activity__title', 'employee_notes')
    ordering = ('-completion_datetime',)
    readonly_fields = ('completion_datetime',)
    
    fieldsets = (
        ('Completion Info', {
            'fields': ('planned_activity', 'completed_by', 'completion_datetime', 'progress_percentage')
        }),
        ('Documentation', {
            'fields': ('completion_photos', 'employee_notes')
        }),
        ('Verification', {
            'fields': ('verified_by', 'verified_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change and not obj.verified_by:
            # Auto-verify if PM is completing
            from django.utils import timezone
            obj.verified_by = request.user
            obj.verified_at = timezone.now()
        super().save_model(request, obj, form, change)