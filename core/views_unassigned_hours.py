from collections import defaultdict
import csv
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _

from core.forms import TimeEntryForm
from core.models import ChangeOrder, CostCode, Employee, Project, TimeEntry
from core.views_assignments import _user_can_assign


def _style_timeentry_form(form):
    """Apply a clean, compact style to form widgets without changing their types."""

    for _name, field in form.fields.items():
        input_type = getattr(field.widget, "input_type", "") or ""
        base_class = "form-control"
        if input_type.lower() == "select" or field.widget.__class__.__name__.lower().startswith("select"):
            base_class = "form-select"

        existing = field.widget.attrs.get("class", "")
        field.widget.attrs["class"] = (existing + " " + base_class + " shadow-sm").strip()
        if input_type in {"time", "date"}:
            field.widget.attrs.setdefault("type", input_type)


@login_required
def unassigned_hours_hub(request):
    """Visualizer and correction hub for hours without a project."""

    can_manage = _user_can_assign(request.user)
    employee_profile = Employee.objects.filter(user=request.user).first()

    employees = Employee.objects.filter(is_active=True).order_by("first_name", "last_name")
    projects = Project.objects.all().order_by("name")
    change_orders = ChangeOrder.objects.select_related("project").order_by("project__name", "id")
    cost_codes = CostCode.objects.filter(active=True).order_by("code")

    base_qs = TimeEntry.objects.select_related("employee__user", "project", "change_order", "cost_code").filter(
        project__isnull=True
    )

    date_from = request.GET.get("from")
    date_to = request.GET.get("to")
    employee_filter = request.GET.get("employee")
    project_filter = request.GET.get("project")
    cost_code_filter = request.GET.get("cost_code")
    selected_day = request.GET.get("week")
    try:
        selected_date = timezone.datetime.fromisoformat(selected_day).date() if selected_day else timezone.localdate()
    except Exception:
        selected_date = timezone.localdate()

    week_start = selected_date - timedelta(days=selected_date.weekday())
    week_days = [week_start + timedelta(days=i) for i in range(7)]
    prev_week = (week_start - timedelta(days=7)).isoformat()
    next_week = (week_start + timedelta(days=7)).isoformat()
    if date_from:
        base_qs = base_qs.filter(date__gte=date_from)
    if date_to:
        base_qs = base_qs.filter(date__lte=date_to)

    base_qs = base_qs.filter(date__gte=week_start, date__lte=week_start + timedelta(days=6))
    if employee_filter:
        base_qs = base_qs.filter(employee_id=employee_filter)
    if project_filter:
        base_qs = base_qs.filter(project_id=project_filter)
    if cost_code_filter:
        base_qs = base_qs.filter(cost_code_id=cost_code_filter)

    unassigned_entries = base_qs.order_by("-date", "-start_time", "-id")
    total_hours = base_qs.aggregate(total=Sum("hours_worked"))["total"] or Decimal("0")
    total_entries = base_qs.count()

    # CSV export
    if request.GET.get("export") == "csv":
        response = _export_unassigned_csv(unassigned_entries)
        return response

    inline_form = None
    inline_error_id = None

    if request.method == "POST":
        action = request.POST.get("action")
        if not can_manage:
            messages.error(request, _("Solo PM o admin pueden corregir horas."))
            return redirect("unassigned_hours_hub")

        if action == "create":
            create_form = TimeEntryForm(request.POST)
            create_form.fields["employee"].queryset = employees
            create_form.fields["project"].queryset = projects
            create_form.fields["change_order"].queryset = change_orders
            create_form.fields["cost_code"].queryset = cost_codes
            _style_timeentry_form(create_form)

            if create_form.is_valid():
                entry = create_form.save(commit=False)
                entry.save()
                messages.success(request, _("Horas registradas correctamente."))
                return redirect("unassigned_hours_hub")
            else:
                messages.error(request, _("Revisa los errores del formulario."))
        elif action == "update":
            entry = get_object_or_404(TimeEntry, pk=request.POST.get("entry_id"))
            form = TimeEntryForm(request.POST, instance=entry)
            form.fields["employee"].queryset = employees
            form.fields["project"].queryset = projects
            form.fields["change_order"].queryset = change_orders
            form.fields["cost_code"].queryset = cost_codes
            _style_timeentry_form(form)

            if form.is_valid():
                form.save()
                messages.success(request, _("Entrada de horas actualizada."))
                return redirect("unassigned_hours_hub")
            else:
                inline_form = form
                inline_error_id = entry.id
                messages.error(request, _("Revisa los errores de la entrada."))
        elif action == "delete":
            entry = get_object_or_404(TimeEntry, pk=request.POST.get("entry_id"))
            entry.delete()
            messages.success(request, _("Entrada eliminada."))
            return redirect("unassigned_hours_hub")
        else:
            messages.error(request, _("Acción no reconocida."))

    create_form = TimeEntryForm(initial={"date": week_start})
    if employee_profile:
        create_form.initial["employee"] = employee_profile.pk
    create_form.fields["employee"].queryset = employees
    create_form.fields["project"].queryset = projects
    create_form.fields["change_order"].queryset = change_orders
    create_form.fields["cost_code"].queryset = cost_codes
    _style_timeentry_form(create_form)

    entry_forms = {}
    for entry in unassigned_entries:
        if inline_form and inline_error_id == entry.id:
            entry_forms[entry.id] = inline_form
            continue
        f = TimeEntryForm(instance=entry)
        f.fields["employee"].queryset = employees
        f.fields["project"].queryset = projects
        f.fields["change_order"].queryset = change_orders
        f.fields["cost_code"].queryset = cost_codes
        _style_timeentry_form(f)
        entry_forms[entry.id] = f

    entries_with_forms = [(entry, entry_forms.get(entry.id)) for entry in unassigned_entries]

    # Build weekly grid by employee and day
    entries_map = defaultdict(list)
    for entry in unassigned_entries:
        entries_map[(entry.employee_id, entry.date)].append(entry)

    employee_ids = {e.employee_id for e in unassigned_entries}
    if employee_filter:
        employee_ids = {int(employee_filter)}
    employee_rows = [emp for emp in employees if emp.id in employee_ids] if employee_ids else []

    weekly_rows = []
    for emp in employee_rows:
        day_cells = []
        for day in week_days:
            day_cells.append({
                "date": day,
                "entries": entries_map.get((emp.id, day), []),
            })
        weekly_rows.append({"employee": emp, "days": day_cells})

    return render(
        request,
        "core/unassigned_hours_hub.html",
        {
            "entries_with_forms": entries_with_forms,
            "unassigned_entries": unassigned_entries,
            "weekly_rows": weekly_rows,
            "week_days": week_days,
            "week_start": week_start,
            "week_end": week_start + timedelta(days=6),
            "prev_week": prev_week,
            "next_week": next_week,
            "total_hours": total_hours,
            "total_entries": total_entries,
            "can_manage": can_manage,
            "create_form": create_form,
            "inline_error_id": inline_error_id,
            "date_from": date_from,
            "date_to": date_to,
            "employee_filter": employee_filter,
            "project_filter": project_filter,
            "cost_code_filter": cost_code_filter,
            "employees": employees,
            "projects": projects,
            "cost_codes": cost_codes,
        },
    )


def _export_unassigned_csv(entries_qs):
    headers = [
        "employee",
        "date",
        "start_time",
        "end_time",
        "hours_worked",
        "project",
        "change_order",
        "cost_code",
        "notes",
    ]
    response = render_csv_response("unassigned_hours.csv", headers, entries_qs)
    return response


def render_csv_response(filename, headers, entries_qs):
    from django.http import HttpResponse

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={filename}"
    writer = csv.writer(response)
    writer.writerow(headers)
    for e in entries_qs:
        writer.writerow(
            [
                str(e.employee),
                e.date.isoformat(),
                e.start_time,
                e.end_time or "",
                e.hours_worked or "",
                e.project.name if e.project else "",
                e.change_order.id if e.change_order else "",
                e.cost_code.code if e.cost_code else "",
                (e.notes or "").strip(),
            ]
        )
    return response
