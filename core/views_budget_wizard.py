"""
Budget Wizard View - Interfaz moderna estilo Asana para gestionar Budget Lines.
Permite agregar, editar, eliminar y usar templates de budget lines.
"""
import csv
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from core.models import BudgetLine, CostCode, Project


# Templates predefinidos de Budget Lines
BUDGET_TEMPLATES = {
    "painting": [
        {"code": "PREP", "name": "Surface Preparation", "unit": "SF"},
        {"code": "PRIME", "name": "Priming", "unit": "SF"},
        {"code": "PAINT-INT", "name": "Interior Painting", "unit": "SF"},
        {"code": "PAINT-EXT", "name": "Exterior Painting", "unit": "SF"},
        {"code": "TRIM", "name": "Trim & Millwork", "unit": "LF"},
        {"code": "CABINET", "name": "Cabinet Finishing", "unit": "EA"},
        {"code": "DOORS", "name": "Doors & Frames", "unit": "EA"},
        {"code": "TOUCH-UP", "name": "Touch-up & Punch List", "unit": "LS"},
    ],
    "drywall": [
        {"code": "FRAME", "name": "Framing", "unit": "SF"},
        {"code": "HANG", "name": "Drywall Hanging", "unit": "SF"},
        {"code": "TAPE", "name": "Taping & Mudding", "unit": "SF"},
        {"code": "SAND", "name": "Sanding", "unit": "SF"},
        {"code": "TEXTURE", "name": "Texturing", "unit": "SF"},
        {"code": "PATCH", "name": "Patching & Repairs", "unit": "EA"},
    ],
    "general": [
        {"code": "DEMO", "name": "Demolition", "unit": "LS"},
        {"code": "LABOR", "name": "General Labor", "unit": "HR"},
        {"code": "MATERIAL", "name": "Materials", "unit": "LS"},
        {"code": "EQUIPMENT", "name": "Equipment Rental", "unit": "DAY"},
        {"code": "SUPERVISION", "name": "Supervision", "unit": "HR"},
        {"code": "CLEANUP", "name": "Cleanup & Disposal", "unit": "LS"},
        {"code": "CONTINGENCY", "name": "Contingency", "unit": "LS"},
    ],
}


@login_required
def budget_wizard_view(request, project_id):
    """
    Vista principal del Budget Wizard.
    Maneja operaciones CRUD y templates.
    """
    project = get_object_or_404(Project, pk=project_id)
    
    # Verificar permisos (staff, PM del proyecto, o superuser)
    if not request.user.is_staff and not request.user.is_superuser:
        # Verificar si es PM del proyecto
        is_pm = hasattr(project, 'pm') and project.pm == request.user
        if not is_pm:
            messages.error(request, _("No tienes permisos para editar este presupuesto."))
            return redirect("project_overview", project_id=project.id)
    
    # Export CSV
    if request.GET.get("export") == "csv":
        return export_budget_csv(project)
    
    # Procesar POST
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "add":
            handle_add_line(request, project)
        elif action == "edit":
            handle_edit_line(request, project)
        elif action == "delete":
            handle_delete_line(request, project)
        elif action == "template":
            handle_template(request, project)
        
        return redirect("budget_wizard", project_id=project.id)
    
    # GET: Mostrar wizard
    lines = BudgetLine.objects.filter(project=project).select_related("cost_code").order_by("cost_code__code")
    cost_codes = CostCode.objects.filter(active=True).order_by("code")
    
    # Calcular totales
    totals = lines.aggregate(
        total_baseline=Sum("baseline_amount"),
        total_revised=Sum("revised_amount")
    )
    
    context = {
        "project": project,
        "lines": lines,
        "lines_count": lines.count(),
        "cost_codes": cost_codes,
        "total_baseline": totals["total_baseline"] or Decimal("0"),
        "total_revised": totals["total_revised"] or Decimal("0"),
        "total_spent": Decimal("0"),  # TODO: Calcular gastos reales
    }
    
    return render(request, "core/budget_wizard.html", context)


def handle_add_line(request, project):
    """Agregar nueva línea de presupuesto."""
    try:
        cost_code_id = request.POST.get("cost_code")
        if not cost_code_id:
            messages.error(request, _("Debes seleccionar un cost code."))
            return
        
        cost_code = CostCode.objects.get(pk=cost_code_id)
        
        qty = Decimal(request.POST.get("qty") or "1")
        unit_cost = Decimal(request.POST.get("unit_cost") or "0")
        
        line = BudgetLine.objects.create(
            project=project,
            cost_code=cost_code,
            description=request.POST.get("description", ""),
            qty=qty,
            unit=request.POST.get("unit", "LS"),
            unit_cost=unit_cost,
            allowance=request.POST.get("allowance") == "on",
            planned_start=request.POST.get("planned_start") or None,
            planned_finish=request.POST.get("planned_finish") or None,
        )
        
        messages.success(request, _(f"✓ Línea '{cost_code.code}' agregada al presupuesto."))
        
    except CostCode.DoesNotExist:
        messages.error(request, _("Cost code no encontrado."))
    except Exception as e:
        messages.error(request, _(f"Error al agregar línea: {str(e)}"))


def handle_edit_line(request, project):
    """Editar línea existente."""
    try:
        line_id = request.POST.get("line_id")
        line = BudgetLine.objects.get(pk=line_id, project=project)
        
        cost_code_id = request.POST.get("cost_code")
        if cost_code_id:
            line.cost_code_id = cost_code_id
        
        line.description = request.POST.get("description", "")
        line.qty = Decimal(request.POST.get("qty") or "0")
        line.unit = request.POST.get("unit", "LS")
        line.unit_cost = Decimal(request.POST.get("unit_cost") or "0")
        
        revised = request.POST.get("revised_amount")
        if revised:
            line.revised_amount = Decimal(revised)
        
        line.planned_start = request.POST.get("planned_start") or None
        line.planned_finish = request.POST.get("planned_finish") or None
        
        line.save()
        messages.success(request, _("✓ Línea actualizada."))
        
    except BudgetLine.DoesNotExist:
        messages.error(request, _("Línea no encontrada."))
    except Exception as e:
        messages.error(request, _(f"Error al editar: {str(e)}"))


def handle_delete_line(request, project):
    """Eliminar línea."""
    try:
        line_id = request.POST.get("line_id")
        line = BudgetLine.objects.get(pk=line_id, project=project)
        code = line.cost_code.code
        line.delete()
        messages.success(request, _(f"✓ Línea '{code}' eliminada."))
    except BudgetLine.DoesNotExist:
        messages.error(request, _("Línea no encontrada."))


def handle_template(request, project):
    """Cargar template de budget lines."""
    template_type = request.POST.get("template_type")
    template_lines = BUDGET_TEMPLATES.get(template_type, [])
    
    if not template_lines:
        messages.error(request, _("Template no encontrado."))
        return
    
    created_count = 0
    for tpl in template_lines:
        # Buscar o crear cost code
        cost_code, _ = CostCode.objects.get_or_create(
            code=tpl["code"],
            defaults={
                "name": tpl["name"],
                "category": "labor",
                "active": True,
            }
        )
        
        # Crear budget line si no existe
        existing = BudgetLine.objects.filter(project=project, cost_code=cost_code).exists()
        if not existing:
            BudgetLine.objects.create(
                project=project,
                cost_code=cost_code,
                description=tpl["name"],
                unit=tpl["unit"],
                qty=Decimal("1"),
                unit_cost=Decimal("0"),
            )
            created_count += 1
    
    if created_count > 0:
        messages.success(request, _(f"✓ {created_count} líneas creadas desde template '{template_type}'."))
    else:
        messages.info(request, _("No se crearon líneas (ya existen en el presupuesto)."))


def export_budget_csv(project):
    """Exportar budget a CSV."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="budget_{project.id}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        "Cost Code", "Name", "Description", "Qty", "Unit", 
        "Unit Cost", "Total", "Revised", "Start", "End"
    ])
    
    lines = BudgetLine.objects.filter(project=project).select_related("cost_code").order_by("cost_code__code")
    
    for line in lines:
        writer.writerow([
            line.cost_code.code,
            line.cost_code.name,
            line.description,
            line.qty,
            line.unit,
            line.unit_cost,
            line.baseline_amount,
            line.revised_amount,
            line.planned_start or "",
            line.planned_finish or "",
        ])
    
    return response
