"""
Vista para asignar TimeEntries huérfanos a proyectos, budget lines o change orders.
Permite corregir registros de horas que no tienen asignación correcta.
"""
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse

from core.models import (
    TimeEntry,
    Project,
    BudgetLine,
    ChangeOrder,
    Employee,
)


@login_required
def timeentry_assignment_hub(request):
    """
    Hub para asignar TimeEntries huérfanos.
    Muestra entradas sin proyecto, sin budget_line (cuando no son CO), etc.
    """
    # Verificar permisos
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"]:
        messages.error(request, "No tienes permisos para acceder a esta página.")
        return redirect("dashboard")

    # Filtros
    filter_type = request.GET.get("filter", "all")
    project_filter = request.GET.get("project")
    employee_filter = request.GET.get("employee")

    # Base queryset - entradas cerradas (con end_time)
    entries = TimeEntry.objects.filter(
        end_time__isnull=False
    ).select_related(
        "employee", "project", "change_order", "budget_line", "cost_code"
    ).order_by("-date", "-start_time")

    # Aplicar filtros
    if filter_type == "no_project":
        entries = entries.filter(project__isnull=True)
    elif filter_type == "no_budget_line":
        # Sin budget_line Y sin change_order (deberían tener budget_line)
        entries = entries.filter(
            budget_line__isnull=True,
            change_order__isnull=True,
            project__isnull=False
        )
    elif filter_type == "unassigned":
        # Totalmente sin asignar: sin proyecto O (sin budget_line Y sin CO)
        entries = entries.filter(
            Q(project__isnull=True) |
            Q(budget_line__isnull=True, change_order__isnull=True)
        )

    if project_filter:
        entries = entries.filter(project_id=project_filter)
    if employee_filter:
        entries = entries.filter(employee_id=employee_filter)

    # Estadísticas
    total_entries = entries.count()
    total_hours = entries.aggregate(total=Sum("hours_worked"))["total"] or Decimal("0")
    
    no_project_count = TimeEntry.objects.filter(
        project__isnull=True, end_time__isnull=False
    ).count()
    
    no_budget_line_count = TimeEntry.objects.filter(
        budget_line__isnull=True,
        change_order__isnull=True,
        project__isnull=False,
        end_time__isnull=False
    ).count()

    # Datos para filtros
    projects = Project.objects.all().order_by("name")
    employees = Employee.objects.filter(is_active=True).order_by("last_name", "first_name")

    # Procesar POST (asignaciones masivas o individuales)
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "assign_single":
            entry_id = request.POST.get("entry_id")
            project_id = request.POST.get("project_id")
            budget_line_id = request.POST.get("budget_line_id")
            change_order_id = request.POST.get("change_order_id")
            
            try:
                entry = TimeEntry.objects.get(id=entry_id)
                
                if project_id:
                    entry.project_id = project_id
                
                # Si tiene CO, limpiar budget_line (son mutuamente excluyentes)
                if change_order_id:
                    entry.change_order_id = change_order_id
                    entry.budget_line = None
                elif budget_line_id:
                    entry.budget_line_id = budget_line_id
                    entry.change_order = None
                
                entry.save()
                messages.success(request, f"✓ Entrada {entry_id} actualizada correctamente.")
            except TimeEntry.DoesNotExist:
                messages.error(request, f"Entrada {entry_id} no encontrada.")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
            
            return redirect(request.get_full_path())
        
        elif action == "assign_bulk":
            entry_ids = request.POST.getlist("entry_ids")
            project_id = request.POST.get("bulk_project_id")
            budget_line_id = request.POST.get("bulk_budget_line_id")
            
            if entry_ids and project_id:
                updated = TimeEntry.objects.filter(id__in=entry_ids).update(
                    project_id=project_id,
                    budget_line_id=budget_line_id if budget_line_id else None
                )
                messages.success(request, f"✓ {updated} entradas actualizadas.")
            else:
                messages.warning(request, "Selecciona entradas y un proyecto.")
            
            return redirect(request.get_full_path())

    # Limitar resultados para la vista (paginación simple)
    entries = entries[:100]

    context = {
        "entries": entries,
        "total_entries": total_entries,
        "total_hours": total_hours,
        "no_project_count": no_project_count,
        "no_budget_line_count": no_budget_line_count,
        "projects": projects,
        "employees": employees,
        "filter_type": filter_type,
        "project_filter": project_filter,
        "employee_filter": employee_filter,
    }

    return render(request, "core/timeentry_assignment_hub.html", context)


@login_required
def timeentry_get_options(request):
    """
    API para obtener budget_lines y change_orders de un proyecto (para select dinámico).
    """
    project_id = request.GET.get("project_id")
    if not project_id:
        return JsonResponse({"budget_lines": [], "change_orders": []})
    
    budget_lines = list(
        BudgetLine.objects.filter(project_id=project_id)
        .select_related("cost_code")
        .values("id", "cost_code__code", "cost_code__name", "description", "qty", "unit")
    )
    
    # Formatear para el frontend
    budget_lines_formatted = [
        {
            "id": bl["id"],
            "label": f"{bl['cost_code__code']} - {bl['cost_code__name'] or bl['description']}",
            "qty": str(bl["qty"]),
            "unit": bl["unit"],
        }
        for bl in budget_lines
    ]
    
    change_orders = list(
        ChangeOrder.objects.filter(
            project_id=project_id,
            status__in=["pending", "approved", "sent"]
        ).values("id", "description", "amount", "status")
    )
    
    change_orders_formatted = [
        {
            "id": co["id"],
            "label": f"CO-{co['id']}: {co['description'][:50]}..." if len(co['description'] or '') > 50 else f"CO-{co['id']}: {co['description'] or 'Sin descripción'}",
            "amount": str(co["amount"]),
            "status": co["status"],
        }
        for co in change_orders
    ]
    
    return JsonResponse({
        "budget_lines": budget_lines_formatted,
        "change_orders": change_orders_formatted,
    })


@login_required  
def project_cost_variance_report(request, project_id):
    """
    Reporte de varianza de costos por fase del proyecto.
    Compara horas estimadas vs horas reales por budget line.
    """
    project = get_object_or_404(Project, pk=project_id)
    
    # Budget lines con horas usadas
    budget_lines = BudgetLine.objects.filter(project=project).select_related("cost_code")
    
    report_data = []
    total_estimated_hours = Decimal("0")
    total_actual_hours = Decimal("0")
    total_estimated_cost = Decimal("0")
    total_actual_cost = Decimal("0")
    
    for bl in budget_lines:
        # Horas reales de TimeEntries asignados a este budget_line
        actual_hours = TimeEntry.objects.filter(
            budget_line=bl,
            end_time__isnull=False
        ).aggregate(total=Sum("hours_worked"))["total"] or Decimal("0")
        
        # Costo real (hours * hourly_rate del empleado)
        actual_cost = Decimal("0")
        entries = TimeEntry.objects.filter(
            budget_line=bl,
            end_time__isnull=False
        ).select_related("employee")
        
        for entry in entries:
            if entry.hours_worked and entry.employee and entry.employee.hourly_rate:
                actual_cost += entry.hours_worked * entry.employee.hourly_rate
        
        # Estimado del budget line
        estimated_hours = bl.qty if bl.unit in ["hr", "hrs", "hour", "hours", "hora", "horas"] else Decimal("0")
        estimated_cost = bl.baseline_amount
        
        variance_hours = estimated_hours - actual_hours
        variance_cost = estimated_cost - actual_cost
        variance_pct = ((actual_hours / estimated_hours) * 100 - 100) if estimated_hours > 0 else Decimal("0")
        
        # Estado
        if variance_pct <= -10:
            status = "under"  # Bajo presupuesto (bien)
        elif variance_pct <= 10:
            status = "on_track"  # En presupuesto
        else:
            status = "over"  # Sobre presupuesto (mal)
        
        report_data.append({
            "budget_line": bl,
            "cost_code": bl.cost_code,
            "estimated_hours": estimated_hours,
            "actual_hours": actual_hours,
            "variance_hours": variance_hours,
            "estimated_cost": estimated_cost,
            "actual_cost": actual_cost,
            "variance_cost": variance_cost,
            "variance_pct": variance_pct,
            "status": status,
        })
        
        total_estimated_hours += estimated_hours
        total_actual_hours += actual_hours
        total_estimated_cost += estimated_cost
        total_actual_cost += actual_cost
    
    # Change Orders (extras - no cuentan contra presupuesto base)
    co_data = []
    change_orders = ChangeOrder.objects.filter(project=project).exclude(status="cancelled")
    
    for co in change_orders:
        co_hours = TimeEntry.objects.filter(
            change_order=co,
            end_time__isnull=False
        ).aggregate(total=Sum("hours_worked"))["total"] or Decimal("0")
        
        co_cost = Decimal("0")
        for entry in TimeEntry.objects.filter(change_order=co, end_time__isnull=False).select_related("employee"):
            if entry.hours_worked and entry.employee and entry.employee.hourly_rate:
                co_cost += entry.hours_worked * entry.employee.hourly_rate
        
        co_data.append({
            "change_order": co,
            "hours": co_hours,
            "cost": co_cost,
            "billed_amount": co.amount,
        })
    
    total_co_hours = sum(c["hours"] for c in co_data)
    total_co_cost = sum(c["cost"] for c in co_data)
    
    # Entradas sin asignar (problema)
    unassigned_entries = TimeEntry.objects.filter(
        project=project,
        budget_line__isnull=True,
        change_order__isnull=True,
        end_time__isnull=False
    )
    unassigned_hours = unassigned_entries.aggregate(total=Sum("hours_worked"))["total"] or Decimal("0")
    unassigned_count = unassigned_entries.count()
    
    context = {
        "project": project,
        "report_data": report_data,
        "co_data": co_data,
        "total_estimated_hours": total_estimated_hours,
        "total_actual_hours": total_actual_hours,
        "total_estimated_cost": total_estimated_cost,
        "total_actual_cost": total_actual_cost,
        "total_variance_hours": total_estimated_hours - total_actual_hours,
        "total_variance_cost": total_estimated_cost - total_actual_cost,
        "total_co_hours": total_co_hours,
        "total_co_cost": total_co_cost,
        "unassigned_hours": unassigned_hours,
        "unassigned_count": unassigned_count,
    }
    
    return render(request, "core/project_cost_variance_report.html", context)


@login_required
def timeentry_options_api(request):
    """
    API para obtener budget_lines y change_orders de un proyecto.
    Se usa para cargar selectores dinámicos.
    """
    project_id = request.GET.get("project_id")
    
    if not project_id:
        return JsonResponse({"budget_lines": [], "change_orders": []})
    
    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return JsonResponse({"budget_lines": [], "change_orders": []})
    
    # Budget Lines
    budget_lines = BudgetLine.objects.filter(
        project=project
    ).select_related("cost_code").order_by("cost_code__code")
    
    budget_line_data = [
        {
            "id": bl.id,
            "label": f"{bl.cost_code.code} - {bl.cost_code.name}" if bl.cost_code else f"BL-{bl.id}",
            "code": bl.cost_code.code if bl.cost_code else "",
            "estimated_hours": float(bl.estimated_hours or 0),
        }
        for bl in budget_lines
    ]
    
    # Change Orders
    change_orders = ChangeOrder.objects.filter(
        project=project
    ).order_by("id")
    
    change_order_data = [
        {
            "id": co.id,
            "label": f"CO-{co.id}: {co.title or 'Sin título'}" if hasattr(co, 'title') else f"CO-{co.id}",
            "status": getattr(co, "status", ""),
        }
        for co in change_orders
    ]
    
    return JsonResponse({
        "budget_lines": budget_line_data,
        "change_orders": change_order_data,
    })

