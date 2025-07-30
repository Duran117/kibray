from django import forms
from .models import Schedule, Expense, Income, TimeEntry, Project, Payroll, PayrollEntry, Employee

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['project', 'title', 'start_datetime', 'assigned_to']

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['project', 'description', 'amount', 'date', 'receipt', 'invoice', 'category']

class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ['project', 'project_name', 'amount', 'date', 'payment_method', 'category', 'description', 'invoice', 'notes']

class TimeEntryForm(forms.ModelForm):
    class Meta:
        model = TimeEntry
        fields = ['employee', 'project', 'date', 'start_time', 'end_time', 'hours_worked', 'labor_cost', 'touch_ups', 'po_reference', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.filter(end_date__isnull=True)
        self.fields['project'].required = False
        self.fields['notes'].required = False

    def clean(self):
        cleaned_data = super().clean()
        touch_ups = cleaned_data.get('touch_ups')
        project = cleaned_data.get('project')
        if not touch_ups and not project:
            self.add_error('project', "You must select a project unless this is a touch up.")
        return cleaned_data

class PayrollForm(forms.ModelForm):
    class Meta:
        model = Payroll
        fields = ['project', 'week_start', 'week_end', 'is_paid', 'payment_reference']

class PayrollEntryForm(forms.ModelForm):
    class Meta:
        model = PayrollEntry
        fields = ['employee', 'hours_worked', 'hourly_rate', 'notes']