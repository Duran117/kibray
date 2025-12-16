from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _

from core.forms import ResourceAssignmentForm
from core.models import Employee, Project, ResourceAssignment


def _user_can_assign(user):
    role = getattr(getattr(user, "profile", None), "role", "") or ""
    return user.is_superuser or user.is_staff or role in ["project_manager", "pm", "leader"]


def _employee_is_designer(employee: Employee) -> bool:
    position = (employee.position or "").lower()
    if "designer" in position or "diseñ" in position:
        return True
    profile_role = getattr(getattr(employee.user, "profile", None), "role", "") if employee.user else ""
    return bool(profile_role and "designer" in profile_role)


@login_required
def assignment_hub(request):
    today = timezone.localdate()
    try:
        selected_date = timezone.datetime.fromisoformat(request.GET.get("date", "")).date()
    except Exception:
        selected_date = today

    window_start = selected_date - timedelta(days=2)
    window_end = selected_date + timedelta(days=14)

    assignments = (
        ResourceAssignment.objects.select_related("employee", "project", "created_by")
        .filter(date__gte=window_start, date__lte=window_end)
        .order_by("date", "employee__first_name", "employee__last_name")
    )

    if request.method == "POST":
        form = ResourceAssignmentForm(request.POST)
    else:
        form = ResourceAssignmentForm(initial={"date": selected_date})
    can_assign = _user_can_assign(request.user)

    employees = Employee.objects.filter(is_active=True).order_by("first_name", "last_name")
    projects = Project.objects.all().order_by("name")
    form.fields["employee"].queryset = employees
    form.fields["project"].queryset = projects

    if not can_assign:
        for field in form.fields.values():
            field.disabled = True

    if request.method == "POST":
        if not can_assign:
            messages.error(request, _("Solo PM o admin pueden crear asignaciones."))
        elif form.is_valid():
            assignment: ResourceAssignment = form.save(commit=False)
            assignment.created_by = request.user
            if _employee_is_designer(assignment.employee) and not request.user.is_staff and not request.user.is_superuser:
                messages.error(request, _("Solo Admin puede asignar diseñadores."))
            else:
                assignment.save()
                messages.success(
                    request,
                    _("Asignado %(emp)s a %(proj)s (%(shift)s) el %(date)s.")
                    % {
                        "emp": assignment.employee,
                        "proj": assignment.project,
                        "shift": assignment.get_shift_display(),
                        "date": assignment.date,
                    },
                )
                return redirect("assignment_hub")
        else:
            messages.error(request, _("Revisa los errores del formulario."))

    assignments_by_date = {}
    for a in assignments:
        assignments_by_date.setdefault(a.date, []).append(a)

    return render(
        request,
        "core/assignment_hub.html",
        {
            "form": form,
            "can_assign": can_assign,
            "selected_date": selected_date,
            "assignments_by_date": assignments_by_date,
            "employees": employees,
            "projects": projects,
        },
    )


@login_required
def assignment_edit(request, pk: int):
    assignment = get_object_or_404(ResourceAssignment, pk=pk)
    can_assign = _user_can_assign(request.user)
    if not can_assign:
        messages.error(request, _("Solo PM o admin pueden editar asignaciones."))
        return redirect("assignment_hub")

    if request.method == "POST":
        form = ResourceAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            updated = form.save(commit=False)
            if _employee_is_designer(updated.employee) and not request.user.is_staff and not request.user.is_superuser:
                messages.error(request, _("Solo Admin puede asignar diseñadores."))
            else:
                updated.created_by = assignment.created_by or request.user
                updated.save()
                messages.success(request, _("Asignación actualizada."))
                return redirect("assignment_hub")
        else:
            messages.error(request, _("Revisa los errores del formulario."))
    else:
        form = ResourceAssignmentForm(instance=assignment)

    # Limit choices and keep disabled if needed
    employees = Employee.objects.filter(is_active=True).order_by("first_name", "last_name")
    projects = Project.objects.all().order_by("name")
    form.fields["employee"].queryset = employees
    form.fields["project"].queryset = projects

    return render(
        request,
        "core/assignment_edit.html",
        {"form": form, "assignment": assignment},
    )


@login_required
def assignment_delete(request, pk: int):
    assignment = get_object_or_404(ResourceAssignment, pk=pk)
    if request.method != "POST":
        return redirect("assignment_hub")
    if not _user_can_assign(request.user):
        messages.error(request, _("Solo PM o admin pueden eliminar asignaciones."))
        return redirect("assignment_hub")

    assignment.delete()
    messages.success(request, _("Asignación eliminada."))
    return redirect("assignment_hub")
