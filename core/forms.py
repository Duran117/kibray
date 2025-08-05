from django import forms
from .models import Schedule, Expense, Income, TimeEntry, Project, Payroll, PayrollEntry, Employee, ChangeOrder, PayrollRecord

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['project', 'title', 'start_datetime', 'assigned_to']

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = [
            'project',
            'amount',
            'project_name',
            'date',
            'category',
            'description',
            'receipt',
            'invoice',
            'change_order',  # <-- asegúrate de incluirlo
        ]

class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ['project', 'project_name', 'amount', 'date', 'payment_method', 'category', 'description', 'invoice', 'notes']

class TimeEntryForm(forms.ModelForm):
    class Meta:
        model = TimeEntry
        fields = [
            'employee',
            'project',
            'date',
            'start_time',
            'end_time',
            'hours_worked',
            'touch_ups',
            'change_order',
            'notes'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'required': True, 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'required': True, 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'required': True, 'class': 'form-control'}),
            'employee': forms.Select(attrs={'required': True, 'class': 'form-control'}),
            'change_order': forms.Select(attrs={'required': True, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.filter(end_date__isnull=True)
        self.fields['project'].required = False  # Solo obligatorio si no es touch up
        self.fields['notes'].required = False
        self.fields['employee'].required = True
        self.fields['date'].required = True
        self.fields['start_time'].required = True
        self.fields['end_time'].required = True
        self.fields['change_order'].required = True  # Si debe ser obligatorio

    def clean(self):
        cleaned_data = super().clean()
        touch_ups = cleaned_data.get('touch_ups')
        project = cleaned_data.get('project')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        employee = cleaned_data.get('employee')
        date = cleaned_data.get('date')
        change_order = cleaned_data.get('change_order')

        if not touch_ups and not project:
            self.add_error('project', "You must select a project unless this is a touch up.")
        if not employee:
            self.add_error('employee', "Employee is required.")
        if not date:
            self.add_error('date', "Date is required.")
        if not start_time:
            self.add_error('start_time', "Start time is required.")
        if not end_time:
            self.add_error('end_time', "End time is required.")
        if not change_order:
            self.add_error('change_order', "Change order is required.")
        return cleaned_data

class PayrollForm(forms.ModelForm):
    class Meta:
        model = Payroll
        fields = ['project', 'week_start', 'week_end', 'is_paid', 'payment_reference']

class PayrollEntryForm(forms.ModelForm):
    class Meta:
        model = PayrollEntry
        fields = ['employee', 'hours_worked', 'hourly_rate', 'notes']

class ChangeOrderForm(forms.ModelForm):
    class Meta:
        model = ChangeOrder
        fields = ['project', 'description', 'status', 'notes']

class PayrollRecordForm(forms.ModelForm):
    class Meta:
        model = PayrollRecord
        fields = ['paid', 'pay_date', 'check_number']