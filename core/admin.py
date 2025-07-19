from django.contrib import admin
from .models import Employee, Income, Expense, Project, TimeEntry, Schedule

# Empleado
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'hourly_rate', 'phone', 'is_active')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    list_filter = ('is_active', 'position')

# Ingreso
@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('project_name', 'amount', 'date_received', 'payment_method')
    search_fields = ('project_name', 'payment_method')
    list_filter = ('payment_method', 'date_received')

# Gasto
@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('project_name', 'category', 'amount', 'date')
    list_filter = ('category', 'date')
    search_fields = ('project_name', 'description')

# Proyecto
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'client', 'start_date', 'end_date', 'total_income', 'total_expenses')
    search_fields = ('name', 'client')
    list_filter = ('start_date',)

# Registro de horas
@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'project', 'date', 'hours_worked', 'labor_cost')
    list_filter = ('project', 'employee', 'date')
    search_fields = ('employee__first_name', 'employee__last_name', 'project__name')

# Cronograma
@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('project', 'title', 'start_datetime', 'end_datetime', 'is_complete', 'is_personal')
    list_filter = ('project', 'is_complete', 'is_personal', 'stage')
    search_fields = ('title', 'description', 'delay_reason', 'advance_reason')
