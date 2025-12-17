from decimal import Decimal

from django import forms
from django.apps import apps
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from .models import (
    RFI,
    ActivityTemplate,
    BudgetLine,
    BudgetProgress,
    ChangeOrder,
    ChangeOrderPhoto,
    ColorSample,
    CostCode,
    DailyLog,
    DailyLogPhoto,
    DailyPlan,
    DamageReport,
    Estimate,
    EstimateLine,
    Expense,
    FileCategory,
    FloorPlan,
    Income,
    InventoryItem,
    InventoryLocation,
    InventoryMovement,
    Invoice,
    InvoiceLine,
    Issue,
    MaterialRequest,
    MaterialRequestItem,
    PayrollPayment,
    PayrollRecord,
    PlannedActivity,
    PlanPin,
    Profile,
    Project,
    ProjectFile,
    ResourceAssignment,
    Risk,
    Schedule,
    ScheduleCategory,
    ScheduleItem,
    SitePhoto,
    Task,
    TimeEntry,
    TouchUpPin,
)


class ActivityTemplateForm(forms.ModelForm):
    class Meta:
        model = ActivityTemplate
        fields = [
            "name",
            "category",
            "description",
            "steps",
            "materials_list",
            "tools_list",
            "tips",
            "common_errors",
            "reference_photos",
            "video_url",
            "is_active",
        ]
        widgets = {
            "steps": forms.HiddenInput(),
            "materials_list": forms.HiddenInput(),
            "tools_list": forms.HiddenInput(),
            "reference_photos": forms.HiddenInput(),
        }

    def clean(self):
        cleaned = super().clean()
        required = ["name", "category", "tips", "materials_list", "tools_list"]
        for field in required:
            val = cleaned.get(field)
            if not val or (isinstance(val, list) and not val):
                self.add_error(field, _("This field is required."))
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
        fields = [
            "employee",
            "project",
            "date",
            "start_time",
            "end_time",
            "hours_worked",
            "change_order",
            "notes",
            "cost_code",
        ]
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


class ResourceAssignmentForm(forms.ModelForm):
    class Meta:
        model = ResourceAssignment
        fields = ["employee", "project", "date", "shift", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "shift": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.TextInput(attrs={"class": "form-control", "placeholder": "Notas (opcional)"}),
            "employee": forms.Select(attrs={"class": "form-select"}),
            "project": forms.Select(attrs={"class": "form-select"}),
        }


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
            "description": forms.TextInput(attrs={"class": "form-control", "placeholder": _("Descripción")}),
            "amount": forms.NumberInput(attrs={"step": "0.01", "class": "form-control", "placeholder": _("Monto")}),
        }


InvoiceLineFormSet = inlineformset_factory(Invoice, InvoiceLine, form=InvoiceLineForm, extra=1, can_delete=True)


class CostCodeForm(forms.ModelForm):
    class Meta:
        model = CostCode
        fields = ["code", "name", "category", "active"]


class BudgetLineForm(forms.ModelForm):
    class Meta:
        model = BudgetLine
        fields = [
            "cost_code",
            "description",
            "qty",
            "unit",
            "unit_cost",
            "allowance",
            "revised_amount",
            "planned_start",
            "planned_finish",
            "weight_override",
        ]


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
    """
    Formulario para crear/editar Daily Logs.
    Incluye selector de tareas completadas y actividad del schedule.
    """

    class Meta:
        model = DailyLog
        fields = [
            "date",
            "weather",
            "crew_count",
            "schedule_item",
            "schedule_progress_percent",
            "completed_tasks",
            "accomplishments",
            "progress_notes",
            "safety_incidents",
            "delays",
            "next_day_plan",
            "is_published",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "weather": forms.TextInput(attrs={"class": "form-control", "placeholder": _("ej: Soleado, 75°F")}),
            "crew_count": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "schedule_item": forms.Select(attrs={"class": "form-select"}),
            "schedule_progress_percent": forms.NumberInput(
                attrs={"class": "form-control", "min": "0", "max": "100", "step": "0.01"}
            ),
            "completed_tasks": forms.CheckboxSelectMultiple(),
            "accomplishments": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": _("Logros del día...")}
            ),
            "progress_notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": _("Notas generales...")}
            ),
            "safety_incidents": forms.Textarea(
                attrs={"class": "form-control", "rows": 2, "placeholder": _("Incidentes de seguridad...")}
            ),
            "delays": forms.Textarea(
                attrs={"class": "form-control", "rows": 2, "placeholder": _("Retrasos o problemas...")}
            ),
            "next_day_plan": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": _("Plan para mañana...")}
            ),
            "is_published": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        help_texts = {
            "schedule_item": _("Actividad principal del calendario (ej: Cubrir y Preparar)"),
            "schedule_progress_percent": _("Porcentaje de progreso de esta actividad"),
            "completed_tasks": _("Selecciona las tareas que se completaron o avanzaron hoy"),
            "is_published": _("Marcar para que sea visible para cliente y owner"),
        }

    def __init__(self, *args, **kwargs):
        project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)

        if project:
            # Filtrar schedule items del proyecto
            self.fields["schedule_item"].queryset = Schedule.objects.filter(project=project).order_by("start_datetime")

            # Filtrar tareas del proyecto
            self.fields["completed_tasks"].queryset = (
                Task.objects.filter(project=project).select_related("assigned_to").order_by("-created_at")
            )


class DailyLogPhotoForm(forms.ModelForm):
    """Formulario para agregar fotos a un Daily Log"""

    class Meta:
        model = DailyLogPhoto
        fields = ["image", "caption"]
        widgets = {
            "image": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "caption": forms.TextInput(attrs={"class": "form-control", "placeholder": _("Descripción de la foto...")}),
        }


class DamageReportForm(forms.ModelForm):
    """Form for creating damage reports with multiple photos"""

    class Meta:
        model = DamageReport
        fields = [
            "title",
            "description",
            "category",
            "severity",
            "status",
            "estimated_cost",
            "location_detail",
            "root_cause",
            "plan",
            "pin",
            "linked_touchup",
            "linked_co",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Ej: Grieta en pared del baño principal")}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": _("Describe el daño con el mayor detalle posible..."),
                }
            ),
            "category": forms.Select(attrs={"class": "form-select"}),
            "severity": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "estimated_cost": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "0.00", "step": "0.01", "min": "0"}
            ),
            "location_detail": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Ej: Cocina - Pared Norte")}
            ),
            "root_cause": forms.TextInput(attrs={"class": "form-control", "placeholder": _("Causa raíz (opcional)")}),
            "plan": forms.Select(attrs={"class": "form-select"}),
            "pin": forms.Select(attrs={"class": "form-select"}),
            "linked_touchup": forms.Select(attrs={"class": "form-select"}),
            "linked_co": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, project=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter floor plans and pins by project
        if project:
            self.fields["plan"].queryset = FloorPlan.objects.filter(project=project)
            self.fields["pin"].queryset = PlanPin.objects.filter(plan__project=project)
            self.fields["linked_touchup"].queryset = TouchUpPin.objects.filter(plan__project=project)
            self.fields["linked_co"].queryset = ChangeOrder.objects.filter(project=project)
        else:
            self.fields["plan"].queryset = FloorPlan.objects.none()
            self.fields["pin"].queryset = PlanPin.objects.none()
            self.fields["linked_touchup"].queryset = TouchUpPin.objects.none()
            self.fields["linked_co"].queryset = ChangeOrder.objects.none()

        # Make optional fields
        self.fields["plan"].required = False
        self.fields["pin"].required = False
        self.fields["estimated_cost"].required = False
        self.fields["linked_touchup"].required = False
        self.fields["linked_co"].required = False

        # Empty labels
        self.fields["plan"].empty_label = _("Sin plano asociado")
        self.fields["pin"].empty_label = _("Sin pin asociado")
        self.fields["linked_touchup"].empty_label = _("Sin touch-up vinculado")
        self.fields["linked_co"].empty_label = _("Sin CO vinculado")

        # Add help texts
        self.fields["category"].help_text = _("Tipo de daño reportado")
        self.fields["severity"].help_text = _("Nivel de urgencia del daño")
        self.fields["estimated_cost"].help_text = _("Costo estimado de reparación (opcional)")
        self.fields["plan"].help_text = _("Plano donde se encuentra el daño (opcional)")
        self.fields["pin"].help_text = _("Pin específico si aplica (opcional)")
        self.fields["linked_touchup"].help_text = _("Touch-up relacionado (opcional)")
        self.fields["linked_co"].help_text = _("Change Order relacionado (opcional)")


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
    """Formulario de creación/edición de tareas.
    Incluye prioridad, due_date y dependencias según requerimientos (Q11.1, Q11.6, Q11.7).
    """

    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        help_text=_("Fecha límite opcional"),
    )
    priority = forms.ChoiceField(
        required=True,
        choices=Task.PRIORITY_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
        help_text=_("Prioridad de la tarea"),
    )
    dependencies = forms.ModelMultipleChoiceField(
        queryset=Task.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-control", "size": "5"}),
        help_text=_("Tareas que deben completarse antes de esta"),
    )

    class Meta:
        model = Task
        fields = [
            "project",
            "title",
            "description",
            "status",
            "assigned_to",
            "priority",
            "due_date",
            "dependencies",
            "image",
            "is_touchup",
        ]
        widgets = {
            "project": forms.Select(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": _("Título")}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "assigned_to": forms.Select(attrs={"class": "form-control"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter dependencies to same project and exclude self
        if self.instance and self.instance.pk:
            self.fields["dependencies"].queryset = Task.objects.filter(project=self.instance.project).exclude(
                pk=self.instance.pk
            )
        elif "initial" in kwargs and "project" in kwargs["initial"]:
            project_id = kwargs["initial"]["project"]
            self.fields["dependencies"].queryset = Task.objects.filter(project_id=project_id)


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
        fields = [
            "project", "description", "amount", "status", "notes", "color", "reference_code"
        ]
        widgets = {
            "project": forms.Select(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "amount": forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "color": forms.TextInput(attrs={"type": "color", "class": "form-control"}),
            "reference_code": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Código de referencia del color"}
            ),
        }


class ChangeOrderPhotoForm(forms.ModelForm):
    class Meta:
        model = ChangeOrderPhoto
        fields = ["image", "description", "order"]
        widgets = {
            "image": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "description": forms.TextInput(attrs={"class": "form-control", "placeholder": "Descripción de la foto"}),
            "order": forms.NumberInput(attrs={"class": "form-control", "value": 0}),
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
    change_order = forms.ModelChoiceField(
        queryset=ChangeOrder.objects.filter(status__in=["approved", "sent"]).exclude(status__in=["billed", "paid"]),
        required=False,
        label="Change Order (opcional)"
    )
    cost_code = forms.ModelChoiceField(queryset=CostCode.objects.filter(active=True), required=False, label="Cost Code")
    notes = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), required=False, label="Notas")
    
    def __init__(self, *args, **kwargs):
        # ✅ Permitir filtrar proyectos disponibles
        available_projects = kwargs.pop('available_projects', None)
        super().__init__(*args, **kwargs)
        
        if available_projects is not None:
            self.fields['project'].queryset = available_projects
            
            # Mostrar mensaje si no hay proyectos
            if not available_projects.exists():
                self.fields['project'].empty_label = "No tienes proyectos asignados hoy"
                self.fields['project'].widget.attrs['disabled'] = True

        # Filtrar COs por proyecto enviado para evitar combinaciones inválidas
        project_id = None
        if self.is_bound:
            project_id = self.data.get("project")
        elif self.initial.get("project"):
            project_id = getattr(self.initial.get("project"), "id", self.initial.get("project"))

        if project_id:
            self.fields["change_order"].queryset = ChangeOrder.objects.filter(
                project_id=project_id, status__in=["pending", "approved", "sent"]
            ).order_by("-date_created")
            self.fields["change_order"].empty_label = "Selecciona CO del proyecto"
        else:
            self.fields["change_order"].queryset = ChangeOrder.objects.none()
            self.fields["change_order"].empty_label = "Selecciona un proyecto"

    def clean(self):
        cleaned = super().clean()
        project = cleaned.get("project")
        co = cleaned.get("change_order")

        if project:
            project_cos = ChangeOrder.objects.filter(project=project, status__in=["pending", "approved", "sent"])
            if co and co.project_id != project.id:
                raise forms.ValidationError("El CO seleccionado no pertenece al proyecto elegido.")
            if not co and project_cos.count() == 1:
                cleaned["change_order"] = project_cos.first()
            elif project_cos.exists() and not co:
                raise forms.ValidationError("Selecciona el CO del proyecto para que las horas no queden sin asignar.")

        return cleaned


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
    needed_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"}), label="Fecha requerida"
    )

    save_to_catalog = forms.BooleanField(
        required=False, initial=True, label="Guardar este material en el catálogo del proyecto"
    )

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
                label = " ".join(
                    filter(
                        None,
                        [
                            getattr(c, "brand", None),
                            getattr(c, "name", None),
                            getattr(c, "code", None),
                            getattr(c, "finish", None),
                        ],
                    )
                )
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
    coats = forms.IntegerField(
        initial=1,
        required=False,
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={"class": "form-control", "value": "1"}),
    )

    class Meta:
        model = SitePhoto
        # Guardamos approved_color_id manualmente
        fields = [
            "room",
            "wall_ref",
            "image",
            "photo_type",
            "visibility",
            "caption",
            "color_text",
            "brand",
            "finish",
            "gloss",
            "special_finish",
            "coats",
            "notes",
            "annotations",
            "location_lat",
            "location_lng",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "photo_type": forms.Select(attrs={"class": "form-select"}),
            "visibility": forms.Select(attrs={"class": "form-select"}),
            "caption": forms.TextInput(attrs={"class": "form-control", "placeholder": "Caption/title"}),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [("", "— Seleccionar —")]
        try:
            Color = apps.get_model("core", "Color")
            qs = Color.objects.all()
            if project is not None:
                qs = qs.filter(project=project)
            for c in qs.order_by("name"):
                label = " ".join(
                    filter(
                        None,
                        [
                            getattr(c, "brand", None),
                            getattr(c, "name", None),
                            getattr(c, "code", None),
                            getattr(c, "finish", None),
                        ],
                    )
                )
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
            "project",
            "code",
            "name",
            "brand",
            "finish",
            "gloss",
            "room_location",
            "room_group",
            "sample_image",
            "reference_photo",
            "notes",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "project": forms.Select(attrs={"class": "form-control"}),
            "room_location": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ej: Cocina, Dormitorio Principal"}
            ),
            "room_group": forms.TextInput(attrs={"class": "form-control", "placeholder": "Grupo de habitación"}),
        }


class ColorSampleReviewForm(forms.ModelForm):
    class Meta:
        model = ColorSample
        fields = ["status", "client_notes"]
        widgets = {
            "client_notes": forms.Textarea(attrs={"rows": 3}),
            "status": forms.Select(attrs={"class": "form-control"}),
        }

    def clean_status(self):
        st = self.cleaned_data.get("status")
        if st not in ["proposed", "review", "approved", "rejected", "archived"]:
            raise forms.ValidationError("Estado inválido.")
        return st


# ---- Floor Plans ----
class FloorPlanForm(forms.ModelForm):
    class Meta:
        model = FloorPlan
        fields = ["project", "name", "level", "level_identifier", "image"]
        widgets = {
            "project": forms.Select(attrs={"class": "form-control"}),
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ej: Planta Baja, Primer Piso, Ático..."}
            ),
            "level": forms.NumberInput(attrs={"class": "form-control", "min": "-5", "max": "50", "placeholder": "0"}),
            "level_identifier": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ej: Level 0, Ground Floor, Basement..."}
            ),
            "image": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
        }
        help_texts = {
            "level": "Número del nivel: 0=Planta Baja, 1=Nivel 1, -1=Sótano 1, etc.",
            "level_identifier": "Identificador adicional opcional para este nivel",
        }


class PlanPinForm(forms.ModelForm):
    create_task = forms.BooleanField(required=False, initial=False, label="Crear tarea touch-up a partir del pin")

    class Meta:
        model = PlanPin
        fields = ["title", "description", "pin_type", "color_sample"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "pin_type": forms.Select(attrs={"class": "form-control"}),
        }


# ---- Schedule Category & Item Forms ----
class ScheduleCategoryForm(forms.ModelForm):
    """Formulario para crear/editar categorías del cronograma jerárquico."""

    class Meta:
        model = ScheduleCategory
        fields = ["name", "parent", "order", "cost_code"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Preparación"}),
            "parent": forms.Select(attrs={"class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "cost_code": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)
        # Filter parent to same project if editing
        if project:
            self.fields["parent"].queryset = ScheduleCategory.objects.filter(project=project)
            self.fields["cost_code"].queryset = CostCode.objects.filter(active=True)
        else:
            self.fields["parent"].queryset = ScheduleCategory.objects.none()


class ScheduleItemForm(forms.ModelForm):
    """Formulario para crear/editar ítems del cronograma."""

    class Meta:
        model = ScheduleItem
        fields = [
            "category",
            "title",
            "description",
            "order",
            "planned_start",
            "planned_end",
            "status",
            "percent_complete",
            "budget_line",
            "estimate_line",
            "cost_code",
        ]
        widgets = {
            "category": forms.Select(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Enmascarar ventanas"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "planned_start": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "planned_end": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "percent_complete": forms.NumberInput(attrs={"class": "form-control", "min": "0", "max": "100"}),
            "budget_line": forms.Select(attrs={"class": "form-control"}),
            "estimate_line": forms.Select(attrs={"class": "form-control"}),
            "cost_code": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)
        # Make category optional since we can create new one on the fly
        self.fields["category"].required = False
        if project:
            self.fields["category"].queryset = ScheduleCategory.objects.filter(project=project)
            self.fields["budget_line"].queryset = BudgetLine.objects.filter(project=project)
            self.fields["estimate_line"].queryset = EstimateLine.objects.filter(estimate__project=project)
            self.fields["cost_code"].queryset = CostCode.objects.filter(active=True)
        else:
            self.fields["category"].queryset = ScheduleCategory.objects.none()
            self.fields["budget_line"].queryset = BudgetLine.objects.none()
            self.fields["estimate_line"].queryset = EstimateLine.objects.none()

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("planned_start")
        end = cleaned.get("planned_end")
        if start and end and end < start:
            self.add_error("planned_end", "La fecha de fin no puede ser anterior a la de inicio.")
        pct = cleaned.get("percent_complete", 0)
        if pct < 0 or pct > 100:
            self.add_error("percent_complete", "El porcentaje debe estar entre 0 y 100.")

        # Note: category validation is handled in the view since new_category_name is not part of the form
        return cleaned


# ========================================================================================
# DAILY PLAN & PLANNED ACTIVITIES (Module 12.5, 12.6, 12.7)
# ========================================================================================


class DailyPlanForm(forms.ModelForm):
    """Formulario para crear/editar Daily Plans.
    Incluye validación de transiciones de estado y cálculo automático de deadline.
    - completion_deadline: se calcula como (plan_date - 1 día) a las 17:00 si no se provee.
    - status workflow permitido: DRAFT -> PUBLISHED -> IN_PROGRESS -> COMPLETED
      Se permite marcar SKIPPED solo desde DRAFT.
    - fetch_weather opcional (checkbox) para disparar actualización al guardar.
    """

    fetch_weather = forms.BooleanField(
        required=False,
        initial=False,
        help_text=_("Marcar para actualizar clima al guardar"),
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = DailyPlan
        fields = [
            "project",
            "plan_date",
            "status",
            "completion_deadline",
            "no_planning_reason",
            "admin_approved",
            "actual_hours_worked",
            "estimated_hours_total",
        ]
        widgets = {
            "project": forms.Select(attrs={"class": "form-control"}),
            "plan_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "completion_deadline": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "no_planning_reason": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "actual_hours_worked": forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
            "estimated_hours_total": forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
        }
        help_texts = {
            "estimated_hours_total": _("Suma manual (se recalcula al guardar si hay actividades)."),
            "actual_hours_worked": _("Horas reales del día (se puede llenar al finalizar)."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # deadline automático si instancia nueva
        if not self.instance.pk:
            plan_date_val = None
            if self.is_bound:
                # plan_date puede venir como string
                plan_date_val = self.data.get("plan_date")
            else:
                plan_date_val = self.initial.get("plan_date")
            from datetime import date, datetime, time, timedelta

            try:
                if plan_date_val and isinstance(plan_date_val, str):
                    # Parse YYYY-MM-DD
                    plan_dt = datetime.strptime(plan_date_val, "%Y-%m-%d").date()
                elif isinstance(plan_date_val, date):
                    plan_dt = plan_date_val
                else:
                    plan_dt = None
                if plan_dt:
                    deadline_date = plan_dt - timedelta(days=1)
                    # 17:00 local timezone
                    deadline_dt = datetime.combine(deadline_date, time(hour=17, minute=0))
                    # No usar timezone.localize para simplicidad; Django asumirá TZ configurada
                    self.fields["completion_deadline"].initial = deadline_dt
            except Exception:
                pass

        # Si el estado es SKIPPED, hacer obligatorio el motivo
        if self.instance and self.instance.status == "SKIPPED":
            self.fields["no_planning_reason"].required = True
        else:
            self.fields["no_planning_reason"].required = False

    def clean_status(self):
        new_status = self.cleaned_data.get("status")
        if not self.instance or not self.instance.pk:
            # Nuevo plan: permitir solo DRAFT o SKIPPED inicialmente
            if new_status not in ["DRAFT", "SKIPPED"]:
                raise ValidationError(_("Nuevo plan debe iniciar como Draft o Skipped."))
            return new_status
        current = self.instance.status
        allowed_transitions = {
            "DRAFT": ["PUBLISHED", "SKIPPED"],
            "PUBLISHED": ["IN_PROGRESS", "SKIPPED"],
            "IN_PROGRESS": ["COMPLETED"],
            "COMPLETED": [],
            "SKIPPED": [],
        }
        if new_status == current:
            return new_status
        if new_status not in allowed_transitions.get(current, []):
            raise ValidationError(_(f"Transición inválida desde {current} a {new_status}"))
        return new_status

    def clean_completion_deadline(self):
        deadline = self.cleaned_data.get("completion_deadline")
        plan_date = self.cleaned_data.get("plan_date") or (self.instance.plan_date if self.instance else None)
        if deadline and plan_date:
            # Deadline debe ser antes de plan_date
            if deadline.date() >= plan_date:
                raise ValidationError(_("Deadline debe ser antes del día planificado."))
        return deadline

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get("status")
        reason = cleaned.get("no_planning_reason")
        if status == "SKIPPED" and not reason:
            self.add_error("no_planning_reason", _("Debes indicar motivo si el día se omite."))
        return cleaned

    def save(self, commit=True):
        inst: DailyPlan = super().save(commit=False)
        # Recalcular estimated_hours_total basado en actividades si existen
        if inst.pk:
            total = inst.activities.aggregate(Sum("estimated_hours")).get("estimated_hours__sum") or Decimal("0")
            inst.estimated_hours_total = total
        if commit:
            inst.save()
            # Actualizar clima si se solicitó
            if self.cleaned_data.get("fetch_weather"):
                try:
                    inst.fetch_weather()
                except Exception:
                    pass
        return inst


class PlannedActivityForm(forms.ModelForm):
    """Formulario para actividades planificadas dentro de un DailyPlan.
    - materials_needed: Entrada como líneas (una por material) convertidas a lista JSON.
    - Filtra schedule_item y activity_template por proyecto.
    """

    materials_text = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 3, "placeholder": _("Ej: Paint:Sherwin-Williams:2gal\nTape:3roll")}
        ),
        help_text=_("Una línea por material. Formato opcional cantidad al final (ej: Paint:Brand:2gal)."),
    )

    class Meta:
        model = PlannedActivity
        exclude = ["daily_plan", "converted_task", "materials_needed", "created_at", "updated_at"]
        widgets = {
            "schedule_item": forms.Select(attrs={"class": "form-control"}),
            "activity_template": forms.Select(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "assigned_employees": forms.SelectMultiple(attrs={"class": "form-control", "size": "5"}),
            "is_group_activity": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "estimated_hours": forms.NumberInput(attrs={"step": "0.25", "class": "form-control"}),
            "actual_hours": forms.NumberInput(attrs={"step": "0.25", "class": "form-control"}),
            "materials_checked": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "material_shortage": forms.CheckboxInput(attrs={"class": "form-check-input", "disabled": "disabled"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "progress_percentage": forms.NumberInput(attrs={"class": "form-control", "min": "0", "max": "100"}),
        }

    def __init__(self, *args, **kwargs):
        daily_plan = kwargs.pop("daily_plan", None)
        super().__init__(*args, **kwargs)
        if daily_plan:
            # Limitar schedule items del mismo proyecto
            self.fields["schedule_item"].queryset = ScheduleItem.objects.filter(project=daily_plan.project).order_by(
                "order"
            )
            # Limitar activity templates activos
            self.fields["activity_template"].queryset = ActivityTemplate.objects.filter(
                is_active=True, is_latest_version=True
            )
            # Limitar empleados (a través de Employee) – si existe relación de proyecto filtrar; de momento todos activos
            self.fields["assigned_employees"].queryset = (
                apps.get_model("core", "Employee").objects.filter(is_active=True).order_by("first_name")
            )

        # Pre-cargar materials_text desde JSON lista
        if self.instance and self.instance.pk and self.instance.materials_needed:
            try:
                if isinstance(self.instance.materials_needed, list):
                    self.initial["materials_text"] = "\n".join(self.instance.materials_needed)
            except Exception:
                pass

    def clean_progress_percentage(self):
        pct = self.cleaned_data.get("progress_percentage") or 0
        if pct < 0 or pct > 100:
            raise ValidationError(_("El progreso debe estar entre 0 y 100."))
        return pct

    def clean(self):
        cleaned = super().clean()
        est = cleaned.get("estimated_hours")
        act = cleaned.get("actual_hours")
        if act and est and act < 0:
            self.add_error("actual_hours", _("Horas reales no pueden ser negativas."))
        if est and est < 0:
            self.add_error("estimated_hours", _("Horas estimadas no pueden ser negativas."))
        return cleaned

    def save(self, commit=True):
        inst: PlannedActivity = super().save(commit=False)
        # Convert materials_text -> materials_needed list
        txt = self.cleaned_data.get("materials_text")
        if txt is not None:
            lines = [l.strip() for l in txt.splitlines() if l.strip()]
            inst.materials_needed = lines
        if commit:
            inst.save()
            self.save_m2m()
            # Si se marcó materials_checked, ejecutar verificación (solo si no se ha corrido)
            if self.cleaned_data.get("materials_checked") and not inst.materials_checked:
                try:
                    inst.check_materials()
                except Exception:
                    pass
        return inst


PlannedActivityFormSet = inlineformset_factory(
    DailyPlan, PlannedActivity, form=PlannedActivityForm, extra=1, can_delete=True
)


def make_planned_activity_formset(daily_plan, data=None, files=None, **kwargs):
    """Helper para crear un formset con contexto del daily_plan (filtrado de queryset)."""
    FormSet = PlannedActivityFormSet
    fs = FormSet(data=data, files=files, instance=daily_plan, **kwargs)
    for form in fs.forms:
        if hasattr(form, "fields"):
            # Reinyectar daily_plan en cada form para filtrado
            form.__init__(data=form.data if form.is_bound else None, daily_plan=daily_plan, instance=form.instance)
    return fs


# ========================================================================================
# FILE ORGANIZATION FORMS
# ========================================================================================


class FileCategoryForm(forms.ModelForm):
    """Form for creating/editing file categories"""

    class Meta:
        model = FileCategory
        fields = ["name", "category_type", "description", "icon", "color", "order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Contratos, Planos, Fotos..."}),
            "category_type": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Descripción de esta categoría..."}
            ),
            "icon": forms.TextInput(attrs={"class": "form-control", "placeholder": "bi-folder"}),
            "color": forms.Select(
                attrs={"class": "form-select"},
                choices=[
                    ("primary", "Azul"),
                    ("success", "Verde"),
                    ("danger", "Rojo"),
                    ("warning", "Amarillo"),
                    ("info", "Cyan"),
                    ("secondary", "Gris"),
                    ("dark", "Negro"),
                ],
            ),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
        }


class ProjectFileForm(forms.ModelForm):
    """Form for uploading files to a category"""

    class Meta:
        model = ProjectFile
        fields = ["name", "description", "file", "tags", "is_public", "version"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre del archivo..."}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Descripción opcional..."}
            ),
            "file": forms.FileInput(attrs={"class": "form-control"}),
            "tags": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "contrato, firmado, importante (separados por coma)"}
            ),
            "is_public": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "version": forms.TextInput(attrs={"class": "form-control", "placeholder": "v1.0, Rev A, etc."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description"].required = False
        self.fields["tags"].required = False
        self.fields["version"].required = False
        self.fields["is_public"].help_text = "Marcar si el archivo debe ser visible para clientes"


# ========================================================================================
# TOUCH-UP FORMS
# ========================================================================================


class TouchUpPinForm(forms.ModelForm):
    """Form for creating/editing touch-up pins"""

    class Meta:
        model = TouchUpPin
        fields = [
            "plan",
            "x",
            "y",
            "task_name",
            "description",
            "approved_color",
            "custom_color_name",
            "sheen",
            "details",
            "assigned_to",
            "status",
        ]
        widgets = {
            "plan": forms.HiddenInput(),
            "x": forms.HiddenInput(),
            "y": forms.HiddenInput(),
            "task_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ej: Pintura techo sala principal"}
            ),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Descripción detallada del touch-up..."}
            ),
            "approved_color": forms.Select(attrs={"class": "form-select"}),
            "custom_color_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nombre del color (si no usa color aprobado)"}
            ),
            "sheen": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ej: Matte, Satin, Semi-gloss, Gloss"}
            ),
            "details": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Detalles adicionales sobre técnica, herramientas, etc.",
                }
            ),
            "assigned_to": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }
        labels = {
            "task_name": "Nombre de la Tarea",
            "description": "Descripción",
            "approved_color": "Color Aprobado",
            "custom_color_name": "Color Personalizado",
            "sheen": "Brillo",
            "details": "Detalles Adicionales",
            "assigned_to": "Asignar a",
            "status": "Estado",
        }

    def __init__(self, *args, **kwargs):
        project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)

        # Filter color samples by project
        if project:
            self.fields["approved_color"].queryset = ColorSample.objects.filter(project=project).order_by("name")

        # Filter assigned_to by project employees
        if project:
            # Get users with employee profiles in this project
            employee_profiles = Profile.objects.filter(role__in=["employee", "painter", "project_manager"])
            employee_ids = [p.user_id for p in employee_profiles if p.user]
            self.fields["assigned_to"].queryset = User.objects.filter(id__in=employee_ids).order_by(
                "first_name", "last_name"
            )

        # Make some fields optional
        self.fields["description"].required = False
        self.fields["approved_color"].required = False
        self.fields["custom_color_name"].required = False
        self.fields["sheen"].required = False
        self.fields["details"].required = False
        self.fields["assigned_to"].required = False


class TouchUpCompletionForm(forms.Form):
    """Form for closing a touch-up with completion photos"""

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Notas sobre la finalización del trabajo (opcional)...",
            }
        ),
        label="Notas de Finalización",
    )
    photos = forms.FileField(
        required=True,
        widget=forms.ClearableFileInput(
            attrs={
                "class": "form-control",
                "accept": "image/*",
            }
        ),
        label="Fotos de Finalización",
        help_text="Sube al menos una foto mostrando el trabajo completado",
    )


# ===== GESTIÓN DE CLIENTES =====
class ClientCreationForm(forms.ModelForm):
    """Formulario para crear un nuevo usuario cliente"""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "correo@ejemplo.com"}),
        label="Correo Electrónico",
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre"}),
        label="Nombre",
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Apellido"}),
        label="Apellido",
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "(123) 456-7890"}),
        label="Teléfono",
    )
    company = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre de la empresa"}),
        label="Empresa",
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Dirección completa"}),
        label="Dirección",
    )
    language = forms.ChoiceField(
        choices=[("en", "English"), ("es", "Español")],
        initial="en",
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Idioma Preferido",
    )
    send_welcome_email = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Enviar correo de bienvenida con credenciales",
    )

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name"]

    def clean_email(self):
        """Validación estricta de email con normalización y verificación de duplicados"""
        email = self.cleaned_data.get("email")

        if not email:
            raise ValidationError("El correo electrónico es obligatorio.")

        # Normalizar: lowercase y eliminar whitespace
        email = email.lower().strip()

        # Validación de formato más estricta
        import re

        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_regex, email):
            raise ValidationError("Formato de correo electrónico inválido.")

        # Verificar duplicados (case-insensitive)
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Ya existe un usuario con este correo electrónico.")

        # Validación adicional: rechazar emails desechables comunes
        disposable_domains = ["tempmail.com", "guerrillamail.com", "10minutemail.com", "mailinator.com"]
        domain = email.split("@")[1]
        if domain in disposable_domains:
            raise ValidationError("No se permiten correos electrónicos desechables.")

        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]  # Usar email como username

        # SECURITY: Generar contraseña temporal FUERTE (16 caracteres con símbolos)
        import secrets
        import string

        alphabet = string.ascii_letters + string.digits + string.punctuation
        temp_password = "".join(secrets.choice(alphabet) for i in range(16))

        # Asegurar que cumple requisitos mínimos de complejidad
        while not (
            any(c.isupper() for c in temp_password)
            and any(c.islower() for c in temp_password)
            and any(c.isdigit() for c in temp_password)
            and any(c in string.punctuation for c in temp_password)
        ):
            temp_password = "".join(secrets.choice(alphabet) for i in range(16))

        user.set_password(temp_password)

        if commit:
            user.save()
            # Crear perfil de cliente
            from core.models import Profile

            profile, created = Profile.objects.get_or_create(
                user=user, defaults={"role": "client", "language": self.cleaned_data.get("language", "en")}
            )
            if not created:
                profile.role = "client"
                profile.language = self.cleaned_data.get("language", "en")
                profile.save()

            # Guardar información adicional en sesión para email
            self.temp_password = temp_password

        return user


class ClientEditForm(forms.ModelForm):
    """Formulario para editar información de un cliente existente"""

    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "(123) 456-7890"}),
        label="Teléfono",
    )
    company = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre de la empresa"}),
        label="Empresa",
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Dirección completa"}),
        label="Dirección",
    )
    language = forms.ChoiceField(
        choices=[("en", "English"), ("es", "Español")],
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Idioma Preferido",
    )
    is_active = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}), label="Usuario Activo"
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "is_active"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Cargar datos del perfil si existe
            if hasattr(self.instance, "profile"):
                self.fields["language"].initial = self.instance.profile.language


class ClientPasswordResetForm(forms.Form):
    """Formulario para resetear la contraseña de un cliente"""

    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Nueva contraseña"}),
        label="Nueva Contraseña",
        min_length=8,
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirmar contraseña"}),
        label="Confirmar Contraseña",
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("new_password")
        confirm = cleaned_data.get("confirm_password")

        if password and confirm and password != confirm:
            raise ValidationError("Las contraseñas no coinciden.")

        return cleaned_data


# ===== GESTIÓN DE PROYECTOS =====
class ProjectCreateForm(forms.ModelForm):
    """Formulario para crear un nuevo proyecto"""

    class Meta:
        model = Project
        fields = [
            "name",
            "client",
            "address",
            "start_date",
            "end_date",
            "description",
            "budget_total",
            "budget_labor",
            "budget_materials",
            "budget_other",
            "paint_colors",
            "paint_codes",
            "stains_or_finishes",
            "number_of_rooms_or_areas",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre del proyecto"}),
            "client": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre del cliente"}),
            "address": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Dirección completa del proyecto"}
            ),
            "start_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Descripción del proyecto"}
            ),
            "budget_total": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0", "placeholder": "0.00"}
            ),
            "budget_labor": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0", "placeholder": "0.00"}
            ),
            "budget_materials": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0", "placeholder": "0.00"}
            ),
            "budget_other": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0", "placeholder": "0.00"}
            ),
            "paint_colors": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Ej: SW 7008 Alabaster, SW 6258 Tricorn Black",
                }
            ),
            "paint_codes": forms.Textarea(
                attrs={"class": "form-control", "rows": 2, "placeholder": "Códigos de pintura específicos"}
            ),
            "stains_or_finishes": forms.Textarea(
                attrs={"class": "form-control", "rows": 2, "placeholder": "Ej: Milesi Butternut 072 - 2 coats"}
            ),
            "number_of_rooms_or_areas": forms.NumberInput(
                attrs={"class": "form-control", "min": "0", "placeholder": "0"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Campos opcionales
        self.fields["end_date"].required = False
        self.fields["description"].required = False
        self.fields["client"].required = False
        self.fields["address"].required = False
        self.fields["paint_colors"].required = False
        self.fields["paint_codes"].required = False
        self.fields["stains_or_finishes"].required = False
        self.fields["number_of_rooms_or_areas"].required = False

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date < start_date:
            raise ValidationError("La fecha de finalización no puede ser anterior a la fecha de inicio.")

        # Validar presupuestos
        budget_total = cleaned_data.get("budget_total", Decimal("0"))
        budget_labor = cleaned_data.get("budget_labor", Decimal("0"))
        budget_materials = cleaned_data.get("budget_materials", Decimal("0"))
        budget_other = cleaned_data.get("budget_other", Decimal("0"))

        sum_budgets = budget_labor + budget_materials + budget_other
        if budget_total > 0 and sum_budgets > budget_total:
            self.add_error(
                "budget_total",
                f"La suma de presupuestos parciales (${sum_budgets}) excede el presupuesto total (${budget_total})",
            )

        return cleaned_data


class ProjectEditForm(ProjectCreateForm):
    """Formulario para editar un proyecto existente - hereda de ProjectCreateForm"""

    class Meta(ProjectCreateForm.Meta):
        fields = ProjectCreateForm.Meta.fields + ["reflection_notes"]
        widgets = ProjectCreateForm.Meta.widgets.copy()
        widgets["reflection_notes"] = forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Notas sobre aprendizajes, errores o mejoras para próximos proyectos",
            }
        )


# ========================================================================================
# PROPOSAL EMAIL FORM
# ========================================================================================
class ProposalEmailForm(forms.Form):
    """Formulario para enviar la propuesta (Estimate/Proposal) por email al cliente.

    Campos:
      - subject: Asunto del correo.
      - recipient: Email destino.
      - message: Cuerpo editable (texto plano) que incluirá el link público.
    """

    subject = forms.CharField(
        label="Asunto",
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Asunto del correo"}),
    )
    recipient = forms.EmailField(
        label="Para",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "cliente@correo.com"}),
    )
    message = forms.CharField(
        label="Mensaje",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 10,
                "placeholder": "Texto del correo. Puedes editar libremente antes de enviar...",
                "style": "resize:vertical;",
            }
        ),
    )

    def clean_subject(self):
        s = self.cleaned_data.get("subject", "").strip()
        if not s:
            raise ValidationError("El asunto es obligatorio.")
        return s

    def clean_message(self):
        m = self.cleaned_data.get("message", "").strip()
        if not m:
            raise ValidationError("El mensaje no puede estar vacío.")
        # Recomendación básica: incluir saludo y link
        return m


# ========================================================================================
# PROJECT ACTIVATION WIZARD FORM
# ========================================================================================
class ActivationWizardForm(forms.Form):
    """Formulario para activar proyecto desde estimado aprobado.
    
    Permite configurar:
    - Fecha de inicio
    - Qué entidades crear (cronograma, presupuesto, tareas)
    - Porcentaje de anticipo para factura inicial
    - Selección de líneas específicas del estimado para cronograma
    """
    
    start_date = forms.DateField(
        label="Fecha de inicio del proyecto",
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
                "placeholder": "Selecciona fecha de inicio"
            }
        ),
        help_text="Fecha en que inicia la obra/proyecto",
    )
    
    create_schedule = forms.BooleanField(
        label="Crear cronograma",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text="Genera ScheduleItems para visualizar en Gantt",
    )
    
    create_budget = forms.BooleanField(
        label="Generar Presupuesto Base",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text="Genera BudgetLines para control financiero",
    )
    
    create_tasks = forms.BooleanField(
        label="Crear tareas operativas",
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text="Genera Tasks diarias basadas en el cronograma",
    )
    
    deposit_percent = forms.IntegerField(
        label="% Anticipo (0 = No facturar)",
        required=False,
        initial=0,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "0-100",
                "min": "0",
                "max": "100"
            }
        ),
        help_text="Porcentaje del total para factura de anticipo (0 = sin anticipo)",
    )
    
    items_to_schedule = forms.ModelMultipleChoiceField(
        label="Líneas del estimado a incluir en cronograma",
        queryset=EstimateLine.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        help_text="Deja vacío para incluir todas las líneas",
    )

    def __init__(self, *args, **kwargs):
        """Initialize form with estimate context."""
        estimate = kwargs.pop('estimate', None)
        super().__init__(*args, **kwargs)
        
        if estimate:
            # Set queryset for items_to_schedule
            self.fields['items_to_schedule'].queryset = estimate.lines.all()
            
            # Pre-select all lines by default
            if not self.is_bound:
                self.initial['items_to_schedule'] = estimate.lines.all()

    def clean_deposit_percent(self):
        """Validate deposit percentage."""
        percent = self.cleaned_data.get('deposit_percent')
        if percent is None:
            return 0
        if percent < 0 or percent > 100:
            raise ValidationError("El porcentaje debe estar entre 0 y 100")
        return percent

    def clean(self):
        """Validate form data."""
        cleaned_data = super().clean()
        
        create_schedule = cleaned_data.get('create_schedule')
        create_tasks = cleaned_data.get('create_tasks')
        
        # Tasks require schedule
        if create_tasks and not create_schedule:
            raise ValidationError(
                "Para crear tareas operativas, primero debes crear el cronograma"
            )
        
        # At least one action must be selected
        if not any([
            cleaned_data.get('create_schedule'),
            cleaned_data.get('create_budget'),
            cleaned_data.get('deposit_percent', 0) > 0
        ]):
            raise ValidationError(
                "Debes seleccionar al menos una acción (cronograma, presupuesto o anticipo)"
            )
        
        return cleaned_data
