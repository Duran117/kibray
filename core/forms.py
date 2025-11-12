from decimal import Decimal
from django import forms
from django.forms import inlineformset_factory
from django.apps import apps

from .models import (
    Schedule, Expense, Income, TimeEntry, Project, PayrollRecord, PayrollPeriod, PayrollPayment,
    Invoice, InvoiceLine, ChangeOrder, CostCode, BudgetLine,
    Estimate, EstimateLine, Proposal, DailyLog, RFI, Issue, Risk,
    BudgetProgress, MaterialRequest, MaterialRequestItem,
    SitePhoto, InventoryItem, InventoryMovement, InventoryLocation, ProjectInventory,
    ActivityTemplate,
    ColorSample,
    FloorPlan, PlanPin, Task,
    ScheduleCategory, ScheduleItem
)

class ActivityTemplateForm(forms.ModelForm):
    class Meta:
        model = ActivityTemplate
        fields = [
            'name', 'category', 'description', 'steps', 'materials_list', 'tools_list',
            'tips', 'common_errors', 'reference_photos', 'video_url', 'is_active'
        ]
        widgets = {
            'steps': forms.HiddenInput(),
            'materials_list': forms.HiddenInput(),
            'tools_list': forms.HiddenInput(),
            'reference_photos': forms.HiddenInput(),
        }

    def clean(self):
        cleaned = super().clean()
        required = ['name', 'category', 'tips', 'materials_list', 'tools_list']
        for field in required:
            val = cleaned.get(field)
            if not val or (isinstance(val, list) and not val):
                self.add_error(field, 'This field is required.')
        return cleaned

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = "__all__"

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = "__all__"

class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = "__all__"

class PayrollRecordForm(forms.ModelForm):
    """Formulario para editar un registro de nómina (horas, tasa, notas)"""
    class Meta:
        model = PayrollRecord
        fields = ["total_hours", "hourly_rate", "adjusted_rate", "notes"]
        widgets = {
            "total_hours": forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
            "hourly_rate": forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
            "adjusted_rate": forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
            "notes": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }

class PayrollPaymentForm(forms.ModelForm):
    """Formulario para registrar un pago de nómina"""
    class Meta:
        model = PayrollPayment
        fields = ["amount", "payment_date", "payment_method", "check_number", "reference", "notes"]
        widgets = {
            "amount": forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
            "payment_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "payment_method": forms.Select(attrs={"class": "form-control"}),
            "check_number": forms.TextInput(attrs={"class": "form-control"}),
            "reference": forms.TextInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }

class TimeEntryForm(forms.ModelForm):
    class Meta:
        model = TimeEntry
        fields = ["employee", "project", "date", "start_time", "end_time", "hours_worked", "change_order", "notes", "cost_code"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "end_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "change_order": forms.Select(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned = super().clean()
        st = cleaned.get("start_time")
        et = cleaned.get("end_time")
        if st and et:
            total = (et.hour * 60 + et.minute) - (st.hour * 60 + st.minute)
            if total < 0:
                total += 24 * 60
            cleaned["hours_worked"] = round(total / 60.0, 2)
        return cleaned

class InvoiceForm(forms.ModelForm):
    change_orders = forms.ModelMultipleChoiceField(
        queryset=ChangeOrder.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Invoice
        fields = ["project", "due_date", "notes", "total_amount", "change_orders"]
        widgets = {
            "project": forms.Select(attrs={"class": "form-control", "id": "id_project"}),
            "due_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "notes": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project_id = None
        if self.is_bound:
            project_id = self.data.get("project")
        elif self.instance and self.instance.pk:
            project_id = self.instance.project_id
        if project_id:
            self.fields["change_orders"].queryset = ChangeOrder.objects.filter(project_id=project_id).order_by("id")
        else:
            self.fields["change_orders"].queryset = ChangeOrder.objects.none()

class InvoiceLineForm(forms.ModelForm):
    class Meta:
        model = InvoiceLine
        fields = ["description", "amount"]
        widgets = {
            "description": forms.TextInput(attrs={"class": "form-control", "placeholder": "Descripción"}),
            "amount": forms.NumberInput(attrs={"step": "0.01", "class": "form-control", "placeholder": "Monto"}),
        }

InvoiceLineFormSet = inlineformset_factory(
    Invoice, InvoiceLine, form=InvoiceLineForm, extra=1, can_delete=True
)

class CostCodeForm(forms.ModelForm):
    class Meta:
        model = CostCode
        fields = ["code", "name", "category", "active"]

class BudgetLineForm(forms.ModelForm):
    class Meta:
        model = BudgetLine
        fields = ["cost_code", "description", "qty", "unit", "unit_cost", "allowance", "revised_amount", "planned_start", "planned_finish", "weight_override"]

EstimateLineFormSet = inlineformset_factory(
    Estimate,
    EstimateLine,
    fields=["cost_code", "description", "qty", "unit", "labor_unit_cost", "material_unit_cost", "other_unit_cost"],
    extra=1,
    can_delete=True,
)

class EstimateForm(forms.ModelForm):
    class Meta:
        model = Estimate
        fields = ["markup_material", "markup_labor", "overhead_pct", "target_profit_pct", "notes"]

class DailyLogForm(forms.ModelForm):
    class Meta:
        model = DailyLog
        fields = ["date", "weather", "crew_count", "progress_notes", "safety_incidents", "delays"]
        widgets = {"date": forms.DateInput(attrs={"type": "date", "class": "form-control"})}

class RFIForm(forms.ModelForm):
    class Meta:
        model = RFI
        fields = ["question"]

class RFIAnswerForm(forms.ModelForm):
    class Meta:
        model = RFI
        fields = ["answer", "status"]

class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ["title", "description", "severity", "status"]

class RiskForm(forms.ModelForm):
    class Meta:
        model = Risk
        fields = ["title", "probability", "impact", "mitigation", "status"]

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["project", "title", "description", "status", "assigned_to", "image", "is_touchup"]
        widgets = {
            "project": forms.Select(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Título"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "assigned_to": forms.Select(attrs={"class": "form-control"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

# DEPRECATED: PayrollForm y PayrollEntryForm
# class PayrollForm(forms.ModelForm):
#     class Meta:
#         model = Payroll
#         fields = ["project", "week_start", "week_end", "is_paid", "payment_reference"]

# class PayrollEntryForm(forms.ModelForm):
#     class Meta:
#         model = PayrollEntry
#         fields = ["employee", "hours_worked", "hourly_rate", "notes", "payment_reference"]

class ChangeOrderForm(forms.ModelForm):
    class Meta:
        model = ChangeOrder
        fields = ["project", "description", "amount", "status", "notes"]
        widgets = {
            "project": forms.Select(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "amount": forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }

class ChangeOrderStatusForm(forms.ModelForm):
    class Meta:
        model = ChangeOrder
        fields = ["status", "notes"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }

class BudgetProgressForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), input_formats=["%Y-%m-%d", "%m/%d/%Y"])

    class Meta:
        model = BudgetProgress
        fields = ["budget_line", "date", "qty_completed", "percent_complete", "note"]

    def clean(self):
        cleaned = super().clean()
        bl: BudgetLine = cleaned.get("budget_line")
        qty_completed = cleaned.get("qty_completed") or Decimal("0")
        percent = cleaned.get("percent_complete")

        if (qty_completed is None or qty_completed == 0) and (percent is None or percent == 0):
            raise forms.ValidationError("Ingresa Qty completed o Percent complete.")

        if percent is not None:
            try:
                p = Decimal(percent)
            except Exception:
                raise forms.ValidationError("Percent complete inválido.")
            if p < 0 or p > 100:
                self.add_error("percent_complete", "Debe estar entre 0 y 100.")

        if (percent is None or percent == 0) and bl and getattr(bl, "qty", None):
            if bl.qty and bl.qty != 0:
                auto = min(Decimal("100"), (Decimal(qty_completed) / Decimal(bl.qty)) * Decimal("100"))
                cleaned["percent_complete"] = auto

        if qty_completed is not None and Decimal(qty_completed) < 0:
            self.add_error("qty_completed", "No puede ser negativo.")

        return cleaned

class BudgetLineScheduleForm(forms.ModelForm):
    class Meta:
        model = BudgetLine
        fields = ["planned_start", "planned_finish", "weight_override"]
        widgets = {
            "planned_start": forms.DateInput(attrs={"type": "date"}),
            "planned_finish": forms.DateInput(attrs={"type": "date"}),
        }

class BudgetProgressEditForm(forms.ModelForm):
    class Meta:
        model = BudgetProgress
        fields = ["date", "percent_complete", "qty_completed", "note"]

    def clean_percent_complete(self):
        v = self.cleaned_data.get("percent_complete") or 0
        if v < 0 or v > 100:
            raise forms.ValidationError("Percent must be 0–100.")
        return v

    def clean_qty_completed(self):
        v = self.cleaned_data.get("qty_completed") or 0
        if v < 0:
            raise forms.ValidationError("Qty must be >= 0.")
        return v

class ClockInForm(forms.Form):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), label="Proyecto")
    cost_code = forms.ModelChoiceField(queryset=CostCode.objects.filter(active=True), required=False, label="Cost Code")
    notes = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), required=False, label="Notas")

class MaterialsRequestForm(forms.Form):
    catalog_item = forms.ChoiceField(required=False, label="Material del catálogo")
    approved_color = forms.ChoiceField(required=False, label="Colores aprobados del proyecto")
    product_preset = forms.ChoiceField(required=False, label="Producto sugerido")

    category = forms.ChoiceField(choices=MaterialRequestItem.CATEGORY_CHOICES, label="Categoría")
    brand = forms.ChoiceField(choices=MaterialRequestItem.BRAND_CHOICES, label="Marca")
    brand_other = forms.CharField(required=False, label="Marca (especificar)")
    product_name = forms.CharField(required=False, label="Producto / Línea")
    color_name = forms.CharField(required=False, label="Nombre del color")
    color_code = forms.CharField(required=False, label="Código")
    finish = forms.CharField(required=False, label="Acabado")
    gloss = forms.CharField(required=False, label="Brillo (si aplica)")
    formula = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), required=False, label="Fórmula (si aplica)")
    reference_image = forms.FileField(required=False, label="Imagen / muestra")

    quantity = forms.DecimalField(min_value=0.01, max_digits=8, decimal_places=2, label="Cantidad")
    unit = forms.ChoiceField(choices=MaterialRequestItem.UNIT_CHOICES, label="Unidad")
    comments = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), required=False, label="Comentarios/Notas")

    needed_when = forms.ChoiceField(choices=MaterialRequest.NEEDED_WHEN_CHOICES, label="Cuándo se ocupa")
    needed_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="Fecha requerida")

    save_to_catalog = forms.BooleanField(required=False, initial=True, label="Guardar este material en el catálogo del proyecto")

    def __init__(self, *args, colors=None, presets=None, catalog=None, **kwargs):
        super().__init__(*args, **kwargs)

        cat_choices = [("", "— Seleccionar —")]
        if catalog:
            for m in catalog:
                cat_choices.append((str(m.id), str(m)))
        self.fields["catalog_item"].choices = cat_choices

        color_choices = [("", "— Seleccionar —")]
        if colors:
            for c in colors:
                label = " ".join(filter(None, [
                    getattr(c, "brand", None),
                    getattr(c, "name", None),
                    getattr(c, "code", None),
                    getattr(c, "finish", None),
                ]))
                color_choices.append((str(c.id), label or f"Color {c.id}"))
        self.fields["approved_color"].choices = color_choices

        preset_choices = [("", "— Seleccionar —")]
        if presets:
            for i, p in enumerate(presets):
                preset_choices.append((str(i), f"{p['brand_label']} · {p['product_name']} ({p['category_label']})"))
        self.fields["product_preset"].choices = preset_choices

# ---- Site Photo ----
class SitePhotoForm(forms.ModelForm):
    annotations = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = SitePhoto
        # Guardamos approved_color_id manualmente
        fields = [
            "room", "wall_ref", "image",
            "color_text", "brand", "finish", "gloss",
            "special_finish", "coats", "notes", "annotations",
        ]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [("", "— Seleccionar —")]
        try:
            Color = apps.get_model("core", "Color")
            qs = Color.objects.all()
            if project is not None:
                qs = qs.filter(project=project)
            for c in qs.order_by("name"):
                label = " ".join(filter(None, [
                    getattr(c, "brand", None),
                    getattr(c, "name", None),
                    getattr(c, "code", None),
                    getattr(c, "finish", None),
                ]))
                choices.append((str(c.id), label or f"Color {c.id}"))
        except Exception:
            pass
        self.fields["approved_color"] = forms.ChoiceField(choices=choices, required=False, label="Color aprobado")

    def save(self, commit=True):
        inst: SitePhoto = super().save(commit=False)
        ac = self.cleaned_data.get("approved_color")
        inst.approved_color_id = int(ac) if ac else None
        if commit:
            inst.save()
        return inst
class InventoryMovementForm(forms.Form):
    item = forms.ModelChoiceField(queryset=InventoryItem.objects.filter(active=True))
    movement_type = forms.ChoiceField(choices=InventoryMovement.TYPE_CHOICES)
    from_location = forms.ModelChoiceField(queryset=InventoryLocation.objects.all(), required=False)
    to_location = forms.ModelChoiceField(queryset=InventoryLocation.objects.all(), required=False)
    quantity = forms.DecimalField(min_value=0.01, max_digits=10, decimal_places=2)
    note = forms.CharField(required=False)

    # NUEVO: control de gasto rápido
    add_expense = forms.BooleanField(required=False, label="Agregar gasto ahora")
    no_expense = forms.BooleanField(required=False, label="Sin gasto para este material")

    def clean(self):
        c = super().clean()
        t = c.get("movement_type")
        if t in ("RECEIVE", "RETURN") and not c.get("to_location"):
            self.add_error("to_location", "Requerido.")
        if t in ("ISSUE", "CONSUME") and not c.get("from_location"):
            self.add_error("from_location", "Requerido.")
        if t == "TRANSFER":
            if not c.get("from_location") or not c.get("to_location"):
                self.add_error(None, "Requiere origen y destino.")
            elif c.get("from_location") == c.get("to_location"):
                self.add_error(None, "Origen y destino deben ser distintos.")
        # Validación UX gasto
        if c.get("add_expense") and c.get("no_expense"):
            self.add_error(None, "Elige una opción: agregar gasto o marcar sin gasto, no ambas.")
        return c

# ---- Color Samples ----
class ColorSampleForm(forms.ModelForm):
    class Meta:
        model = ColorSample
        fields = [
            'project', 'code', 'name', 'brand', 'finish', 'gloss', 'sample_image',
            'reference_photo', 'notes'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows':3}),
            'project': forms.Select(attrs={'class':'form-control'}),
        }

class ColorSampleReviewForm(forms.ModelForm):
    class Meta:
        model = ColorSample
        fields = ['status', 'client_notes']
        widgets = {
            'client_notes': forms.Textarea(attrs={'rows':3}),
            'status': forms.Select(attrs={'class':'form-control'}),
        }

    def clean_status(self):
        st = self.cleaned_data.get('status')
        if st not in ['proposed','review','approved','rejected','archived']:
            raise forms.ValidationError('Estado inválido.')
        return st

# ---- Floor Plans ----
class FloorPlanForm(forms.ModelForm):
    class Meta:
        model = FloorPlan
        fields = ['project','name','image']
        widgets = {
            'project': forms.Select(attrs={'class':'form-control'}),
        }

class PlanPinForm(forms.ModelForm):
    create_task = forms.BooleanField(required=False, initial=False, label='Crear tarea touch-up a partir del pin')
    class Meta:
        model = PlanPin
        fields = ['title','description','pin_type','color_sample']
        widgets = {
            'description': forms.Textarea(attrs={'rows':3}),
            'pin_type': forms.Select(attrs={'class':'form-control'}),
        }

# ---- Schedule Category & Item Forms ----
class ScheduleCategoryForm(forms.ModelForm):
    """Formulario para crear/editar categorías del cronograma jerárquico."""
    class Meta:
        model = ScheduleCategory
        fields = ['name', 'parent', 'order', 'cost_code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Preparación'}),
            'parent': forms.Select(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'cost_code': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        # Filter parent to same project if editing
        if project:
            self.fields['parent'].queryset = ScheduleCategory.objects.filter(project=project)
            self.fields['cost_code'].queryset = CostCode.objects.filter(active=True)
        else:
            self.fields['parent'].queryset = ScheduleCategory.objects.none()


class ScheduleItemForm(forms.ModelForm):
    """Formulario para crear/editar ítems del cronograma."""
    class Meta:
        model = ScheduleItem
        fields = [
            'category', 'title', 'description', 'order',
            'planned_start', 'planned_end', 'status', 'percent_complete',
            'budget_line', 'estimate_line', 'cost_code'
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Enmascarar ventanas'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'planned_start': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'planned_end': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'percent_complete': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'}),
            'budget_line': forms.Select(attrs={'class': 'form-control'}),
            'estimate_line': forms.Select(attrs={'class': 'form-control'}),
            'cost_code': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        # Make category optional since we can create new one on the fly
        self.fields['category'].required = False
        if project:
            self.fields['category'].queryset = ScheduleCategory.objects.filter(project=project)
            self.fields['budget_line'].queryset = BudgetLine.objects.filter(project=project)
            self.fields['estimate_line'].queryset = EstimateLine.objects.filter(estimate__project=project)
            self.fields['cost_code'].queryset = CostCode.objects.filter(active=True)
        else:
            self.fields['category'].queryset = ScheduleCategory.objects.none()
            self.fields['budget_line'].queryset = BudgetLine.objects.none()
            self.fields['estimate_line'].queryset = EstimateLine.objects.none()

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('planned_start')
        end = cleaned.get('planned_end')
        if start and end and end < start:
            self.add_error('planned_end', 'La fecha de fin no puede ser anterior a la de inicio.')
        pct = cleaned.get('percent_complete', 0)
        if pct < 0 or pct > 100:
            self.add_error('percent_complete', 'El porcentaje debe estar entre 0 y 100.')
        
        # Note: category validation is handled in the view since new_category_name is not part of the form
        return cleaned
