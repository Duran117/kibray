from django.contrib import admin
from .models import Employee, Income, Expense, Project, TimeEntry, Schedule

admin.site.register(Employee)

@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('project_name', 'amount', 'date_received', 'payment_method')
    search_fields = ('project_name', 'payment_method')
    list_filter = ('payment_method', 'date_received')

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('project_name', 'category', 'amount', 'date')
    list_filter = ('category', 'date')
    search_fields = ('project_name', 'description')

admin.site.register(Project)

@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'project', 'date', 'hours_worked', 'labor_cost')
    list_filter = ('project', 'employee', 'date')
    search_fields = ('employee__name', 'project__name')

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('project', 'title', 'start_datetime', 'end_datetime', 'is_complete', 'is_personal')
    list_filter = ('project', 'is_complete', 'is_personal', 'stage')
    search_fields = ('title', 'description', 'delay_reason', 'advance_reason')

