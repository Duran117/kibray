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
    touch_ups = forms.BooleanField(
        required=False,
        label="¿Es Touch Ups?",
        help_text="Marca si es un trabajo de touch ups para un proyecto antiguo o externo."
    )
    po_reference = forms.CharField(
        required=False,
        label="PO o referencia de proyecto",
        help_text="Si es Touch Ups, escribe el PO o referencia"
    )

    class Meta:
        model = TimeEntry
        fields = ['date', 'start_time', 'end_time', 'project', 'touch_ups', 'po_reference', 'notes']
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

class PayrollForm(forms.ModelForm):
    class Meta:
        model = Payroll
        fields = ['project', 'week_start', 'week_end', 'is_paid', 'payment_reference']

class PayrollEntryForm(forms.ModelForm):
    class Meta:
        model = PayrollEntry
        fields = ['employee', 'hours_worked', 'hourly_rate', 'notes']