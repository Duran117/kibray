"""Project CRUD views — list, create, edit, delete, activation, status, PDF."""
from core.views._helpers import *  # noqa: F401, F403
from core.views._helpers import (
    _generate_basic_pdf_from_html,
    _check_user_project_access,
    _is_admin_user,
    _is_pm_or_admin,
    _is_staffish,
    _require_admin_or_redirect,
    _require_roles,
    _parse_date,
    _ensure_inventory_item,
    staff_required,
    logger,
    pisa,
    ROLES_ADMIN,
    ROLES_PM,
    ROLES_STAFF,
    ROLES_FIELD,
    ROLES_ALL_INTERNAL,
    ROLES_CLIENT_SIDE,
    ROLES_PROJECT_ACCESS,
)
from django.utils.translation import gettext_lazy as _  # noqa: F811




# --- PROJECT PDF ---
@login_required
def project_pdf_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have access to this project."))
        return redirect(redirect_url)
    
    incomes = Income.objects.filter(project=project).select_related("change_order")
    expenses = Expense.objects.filter(project=project).select_related("change_order", "cost_code")
    time_entries = TimeEntry.objects.filter(project=project).select_related("employee")
    schedules = Schedule.objects.filter(project=project).order_by("start_datetime")

    total_income = incomes.aggregate(total=Sum("amount"))["total"] or 0
    total_expense = expenses.aggregate(total=Sum("amount"))["total"] or 0
    profit = total_income - total_expense
    total_hours = sum([te.hours_worked for te in time_entries])
    labor_cost = sum([te.labor_cost for te in time_entries])

    context = {
        "project": project,
        "incomes": incomes,
        "expenses": expenses,
        "schedules": schedules,
        "total_income": total_income,
        "total_expense": total_expense,
        "profit": profit,
        "total_hours": total_hours,
        "labor_cost": labor_cost,
        "logo_url": request.build_absolute_uri("/static/Kibray.jpg"),
        "user": request.user,
        "now": timezone.now(),  # <-- reemplazo
    }

    template = get_template("core/project_pdf.html")
    html = template.render(context)
    # Prefer xhtml2pdf if available; otherwise fallback to basic PDF
    if pisa:
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        if not pdf.err:
            return HttpResponse(result.getvalue(), content_type="application/pdf")
    fallback_bytes = _generate_basic_pdf_from_html(html)
    return HttpResponse(fallback_bytes, content_type="application/pdf")




@login_required
def project_activation_view(request, project_id):
    """
    Project Activation Wizard - Automates transition from Sales to Production.

    Converts approved estimate into operational entities:
    - ScheduleItems for Gantt
    - BudgetLines for financial control
    - Tasks for daily operations
    - Invoice for deposit/advance
    """
    from core.services.activation_service import ProjectActivationService

    project = get_object_or_404(Project, pk=project_id)

    # Check permissions (PM, admin, superuser only)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"]:
        messages.error(request, "No tienes permisos para activar proyectos")
        return redirect("dashboard")

    # Get approved estimate
    estimate = project.estimates.filter(approved=True).order_by("-version").first()

    if not estimate:
        messages.error(request, "No hay estimado aprobado para este proyecto")
        return redirect("project_overview", project_id=project.id)

    # Check if already activated
    has_schedule = project.schedule_items.exists()
    has_budget = project.budget_lines.exists()

    if request.method == "POST":
        form = ActivationWizardForm(request.POST, estimate=estimate)

        if form.is_valid():
            try:
                # Initialize service
                service = ProjectActivationService(project=project, estimate=estimate)

                # Get form data
                start_date = form.cleaned_data["start_date"]
                create_schedule = form.cleaned_data["create_schedule"]
                create_budget = form.cleaned_data["create_budget"]
                create_tasks = form.cleaned_data["create_tasks"]
                deposit_percent = form.cleaned_data.get("deposit_percent", 0)
                items_to_schedule = form.cleaned_data.get("items_to_schedule")
                # Selected line IDs (spec wants passing IDs)
                selected_line_ids = (
                    [line.id for line in items_to_schedule]
                    if items_to_schedule and items_to_schedule.exists()
                    else None
                )

                # Get employee from user if exists (for task assignment)
                from core.models import Employee

                employee = Employee.objects.filter(user=request.user).first()

                # Activate project
                result = service.activate_project(
                    start_date=start_date,
                    create_schedule=create_schedule,
                    create_budget=create_budget,
                    create_tasks=create_tasks,
                    deposit_percent=deposit_percent,
                    items_to_schedule=None,  # keep backward compatibility not used now
                    selected_line_ids=selected_line_ids,
                    assigned_to=employee,
                )

                # Build success message
                summary = result["summary"]
                msg_parts = ["Proyecto activado exitosamente:"]

                if summary["schedule_items_count"] > 0:
                    msg_parts.append(
                        f"✓ {summary['schedule_items_count']} ítems de cronograma creados"
                    )

                if summary["budget_lines_count"] > 0:
                    msg_parts.append(
                        f"✓ {summary['budget_lines_count']} líneas de presupuesto creadas"
                    )

                if summary["tasks_count"] > 0:
                    msg_parts.append(f"✓ {summary['tasks_count']} tareas operativas creadas")

                if summary["invoice_created"]:
                    msg_parts.append(f"✓ Factura de anticipo creada (${summary['invoice_amount']})")

                messages.success(request, " | ".join(msg_parts))

                # Redirect to Gantt if schedule was created, otherwise to project detail
                if create_schedule:
                    return redirect("schedule_generator", project_id=project.id)
                else:
                    return redirect("project_overview", project_id=project.id)

            except ValueError as e:
                messages.error(request, _("Error de validación: %(error)s") % {"error": str(e)})
            except Exception as e:
                messages.error(
                    request, _("Error al activar proyecto: %(error)s") % {"error": str(e)}
                )
    else:
        form = ActivationWizardForm(estimate=estimate)

    # Calculate estimate summary
    estimate_lines = estimate.lines.all()
    direct_cost = sum(line.direct_cost() for line in estimate_lines)
    material_markup = (
        (direct_cost * (estimate.markup_material / 100)) if estimate.markup_material else 0
    )
    labor_markup = (direct_cost * (estimate.markup_labor / 100)) if estimate.markup_labor else 0
    overhead = (direct_cost * (estimate.overhead_pct / 100)) if estimate.overhead_pct else 0
    profit = (direct_cost * (estimate.target_profit_pct / 100)) if estimate.target_profit_pct else 0
    estimate_total = direct_cost + material_markup + labor_markup + overhead + profit

    context = {
        "project": project,
        "estimate": estimate,
        "estimate_lines": estimate_lines,
        "estimate_total": estimate_total,
        "form": form,
        "has_schedule": has_schedule,
        "has_budget": has_budget,
        "is_reactivation": has_schedule or has_budget,
    }

    return render(request, "core/project_activation.html", context)




@login_required
def project_list(request):
    """List projects filtered by user role.
    
    - Clients: Only see projects they have access to
    - Employees: Only see projects they are assigned to
    - Staff/Admin/PM: See all projects
    """
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", None) if profile else None
    
    # If user is a client, only show their projects
    if role == "client":
        # Get projects via ClientProjectAccess
        access_projects = Project.objects.filter(client_accesses__user=request.user)
        # Get projects via legacy client field
        legacy_projects = Project.objects.filter(client=request.user.username)
        # Combine both querysets
        projects = access_projects.union(legacy_projects).order_by("-start_date")
    elif role == "employee":
        # SECURITY: Employees can only see projects they have time entries for
        # or projects they are scheduled to work on (via daily plan activities)
        emp = getattr(request.user, "employee", None)
        if emp:
            from core.models import TimeEntry
            time_entry_projects = Project.objects.filter(
                timeentry__employee=emp
            ).distinct()
            # Also check daily plan assignments
            activity_projects = Project.objects.filter(
                daily_plans__activities__assigned_employees=emp
            ).distinct()
            projects = (time_entry_projects | activity_projects).distinct().order_by("-start_date")
        else:
            projects = Project.objects.none()
    else:
        # Staff, admin, PM - show all projects
        projects = Project.objects.all().order_by("id")
    
    return render(request, "core/project_list.html", {"projects": projects})




@login_required
def pickup_view(request, project_id: int):
    project = get_object_or_404(Project, pk=project_id)
    # SECURITY: Check project access
    has_access, redirect_url = _check_user_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("Access denied."))
        return redirect(redirect_url or "dashboard")
    return render(request, "core/pickup_view.html", {"project": project})




@login_required
@staff_member_required
def project_create(request):
    """Crear nuevo proyecto"""
    from core.forms import ProjectCreateForm

    if request.method == "POST":
        form = ProjectCreateForm(request.POST)
        if form.is_valid():
            project = form.save()
            messages.success(request, f'Proyecto "{project.name}" creado exitosamente.')
            return redirect("project_overview", project_id=project.id)
    else:
        form = ProjectCreateForm()

    return render(request, "core/project_form.html", {"form": form, "is_create": True})




@login_required
@staff_member_required
def project_edit(request, project_id):
    """Editar proyecto existente"""
    from core.forms import ProjectEditForm

    project = get_object_or_404(Project, id=project_id)

    if request.method == "POST":
        form = ProjectEditForm(request.POST, instance=project)
        if form.is_valid():
            project = form.save()
            messages.success(request, f'Proyecto "{project.name}" actualizado exitosamente.')
            return redirect("project_overview", project_id=project.id)
    else:
        form = ProjectEditForm(instance=project)

    return render(
        request, "core/project_form.html", {"form": form, "project": project, "is_create": False}
    )




@login_required
@staff_member_required
def project_delete(request, project_id):
    """Eliminar proyecto (con confirmación y validación de dependencias)"""
    project = get_object_or_404(Project, id=project_id)

    if request.method == "POST":
        # SECURITY: Logging de auditoría

        audit_logger = logging.getLogger("django")
        audit_logger.warning(
            f"PROJECT_DELETE_ATTEMPT | Actor: {request.user.username} (ID:{request.user.id}) | "
            f"Project: {project.name} (ID:{project.id}) | "
            f"IP: {request.META.get('REMOTE_ADDR')}"
        )

        # SECURITY: Verificar dependencias críticas ANTES de permitir eliminación
        has_expenses = Expense.objects.filter(project=project).exists()
        has_incomes = Income.objects.filter(project=project).exists()
        has_timeentries = TimeEntry.objects.filter(project=project).exists()
        has_changeorders = ChangeOrder.objects.filter(project=project).exists()
        has_dailylogs = DailyLog.objects.filter(project=project).exists()
        has_schedules = ScheduleItemV2.objects.filter(project=project).exists()
        has_invoices = Invoice.objects.filter(project=project).exists()

        if any(
            [
                has_expenses,
                has_incomes,
                has_timeentries,
                has_changeorders,
                has_dailylogs,
                has_schedules,
                has_invoices,
            ]
        ):
            messages.error(
                request,
                "❌ No se puede eliminar este proyecto porque tiene datos financieros o operacionales asociados. "
                "Considera marcarlo como completado en lugar de eliminarlo para preservar la integridad de los datos.",
            )
            return redirect("project_overview", project_id=project.id)

        project_name = project.name
        project.delete()
        messages.success(request, f'Proyecto "{project_name}" eliminado permanentemente.')
        return redirect("project_list")

    # GET: Calcular estadísticas detalladas para confirmación

    expense_count = Expense.objects.filter(project=project).count()
    income_count = Income.objects.filter(project=project).count()
    timeentry_count = TimeEntry.objects.filter(project=project).count()
    co_count = ChangeOrder.objects.filter(project=project).count()
    task_count = Task.objects.filter(project=project).count()
    dailylog_count = DailyLog.objects.filter(project=project).count()
    schedule_count = ScheduleItemV2.objects.filter(project=project).count()
    invoice_count = Invoice.objects.filter(project=project).count()

    context = {
        "project": project,
        "expense_count": expense_count,
        "income_count": income_count,
        "timeentry_count": timeentry_count,
        "co_count": co_count,
        "task_count": task_count,
        "dailylog_count": dailylog_count,
        "schedule_count": schedule_count,
        "invoice_count": invoice_count,
        "has_critical_data": any(
            [
                expense_count,
                income_count,
                timeentry_count,
                co_count,
                dailylog_count,
                schedule_count,
                invoice_count,
            ]
        ),
    }

    return render(request, "core/project_delete_confirm.html", context)




@login_required
@staff_member_required
def project_status_toggle(request, project_id):
    """Cambiar estado del proyecto (activo/completado)"""
    project = get_object_or_404(Project, id=project_id)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "complete":
            if not project.end_date:
                project.end_date = timezone.localdate()
                project.save()
                messages.success(request, f'Proyecto "{project.name}" marcado como completado.')
        elif action == "reopen":
            project.end_date = None
            project.save()
            messages.success(request, f'Proyecto "{project.name}" reabierto.')

        return redirect("project_overview", project_id=project.id)

    return redirect("project_overview", project_id=project.id)
