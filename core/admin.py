from django.contrib import admin
from .models import Employee, Income, Expense, Project, TimeEntry, Schedule, Profile

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
    list_display = ('project_name', 'amount', 'date_received', 'payment_method')
    search_fields = ('project_name', 'payment_method')
    list_filter = ('payment_method', 'date_received')
    date_hierarchy = 'date_received'
    ordering = ('-date_received',)


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
