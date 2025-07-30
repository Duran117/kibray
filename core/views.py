from django.db.models import Sum
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils.timezone import now
from datetime import date, timedelta
from io import BytesIO
from xhtml2pdf import pisa
from .models import Project, Expense, Income, Schedule, TimeEntry, Payroll, PayrollEntry, Employee, Task, Comment
from .forms import ScheduleForm, ExpenseForm, IncomeForm, TimeEntryForm, PayrollForm, PayrollEntryForm
from django.forms import modelformset_factory
import json
from collections import defaultdict
from .models import TimeEntry

@login_required
def dashboard_view(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'employee':
        return redirect('home')  # O muestra un error 403

    user = request.user
    role = getattr(user.profile, "role", "employee")

    # Métricas generales
    total_income = Income.objects.aggregate(t=Sum("amount"))["t"] or 0
    total_expense = Expense.objects.aggregate(t=Sum("amount"))["t"] or 0
    net_profit = total_income - total_expense
    employee_count = user.profile.user.__class__.objects.count()
    active_projects = Project.objects.filter(end_date__isnull=True).count()

    # Proyectos por rol
    if role == "client":
        projects = Project.objects.filter(client=user.username)
    elif role == "project_manager":
        projects = Project.objects.all()
    else:
        projects = Project.objects.filter(timeentry__employee__user=user).distinct()

    projects = projects.annotate(
        project_income=Sum("incomes__amount"),
        project_expense=Sum("expenses__amount")
    )

    # Eventos próximos (30 días)
    future = date.today() + timedelta(days=30)
    if role == "employee":
        schedules = Schedule.objects.filter(assigned_to=user, start_datetime__date__lte=future)
    elif role == "client":
        schedules = Schedule.objects.filter(project__client=user.username, start_datetime__date__lte=future)
    else:
        schedules = Schedule.objects.filter(start_datetime__date__lte=future)
    schedules = schedules.order_by("start_datetime")[:10]

    # Entradas de tiempo y cálculo de horas/costos
    week_ago = date.today() - timedelta(days=7)
    month_ago = date.today() - timedelta(days=30)
    time_entries = TimeEntry.objects.all()
    if role == "employee":
        time_entries = time_entries.filter(employee__user=user)

    def calculate_hours_and_cost(entries):
        week_hours = month_hours = total_hours = labor_cost = 0
        for entry in entries:
            h = entry.hours_worked
            c = entry.labor_cost
            if entry.date >= week_ago:
                week_hours += h
            if entry.date >= month_ago:
                month_hours += h
            total_hours += h
            labor_cost += c
        return week_hours, month_hours, total_hours, labor_cost

    hours_week, hours_month, total_hours, labor_cost = calculate_hours_and_cost(time_entries)

    # Gráficas
    chart_labels = []
    chart_income = []
    chart_expense = []
    chart_net_profit = []

    chart_budget_labels = []
    chart_budget_labor = []
    chart_budget_materials = []
    chart_budget_other = []

    for proj in projects:
        income = proj.project_income or 0
        expense = proj.project_expense or 0
        profit = income - expense

        chart_labels.append(proj.name)
        chart_income.append(income)
        chart_expense.append(expense)
        chart_net_profit.append(profit)

        chart_budget_labels.append(proj.name)
        chart_budget_labor.append(proj.budget_labor or 0)
        chart_budget_materials.append(proj.budget_materials or 0)
        chart_budget_other.append(proj.budget_other or 0)

    # Convierte Decimals a float
    chart_income = [float(x) for x in chart_income]
    chart_expense = [float(x) for x in chart_expense]
    chart_net_profit = [float(x) for x in chart_net_profit]
    chart_budget_labor = [float(x) for x in chart_budget_labor]
    chart_budget_materials = [float(x) for x in chart_budget_materials]
    chart_budget_other = [float(x) for x in chart_budget_other]

    # Resumen de horas por proyecto para cada empleado
    empleados = Employee.objects.filter(is_active=True)
    project_hours_summary_dict = {}
    for employee in empleados:
        # Ejemplo: {'Proyecto A': 5, 'Proyecto B': 10}
        project_hours = obtener_horas_por_proyecto(employee)  # Debes implementar esto
        summary = ', '.join([f"{hours}h - {project}" for project, hours in project_hours.items()])
        project_hours_summary_dict[employee.id] = summary

    context = {
        "role": role,
        "total_income": total_income,
        "total_expense": total_expense,
        "net_profit": net_profit,
        "employee_count": employee_count,
        "active_projects": active_projects,
        "projects": projects,
        "schedules": schedules,
        "hours_week": round(hours_week, 2),
        "hours_month": round(hours_month, 2),
        "total_hours": round(total_hours, 2),
        "labor_cost": round(labor_cost, 2),
        "chart_labels": json.dumps(chart_labels),
        "chart_income": json.dumps(chart_income),
        "chart_expense": json.dumps(chart_expense),
        "chart_net_profit": json.dumps(chart_net_profit),
        "chart_budget_labels": json.dumps(chart_budget_labels),
        "chart_budget_labor": json.dumps(chart_budget_labor),
        "chart_budget_materials": json.dumps(chart_budget_materials),
        "chart_budget_other": json.dumps(chart_budget_other),
        "project_hours_summary_dict": project_hours_summary_dict,
    }

    return render(request, "core/dashboard.html", context)

@login_required
def project_pdf_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    incomes = Income.objects.filter(project=project)
    expenses = Expense.objects.filter(project=project)
    time_entries = TimeEntry.objects.filter(project=project)
    schedules = Schedule.objects.filter(project=project).order_by("start_datetime")

    total_income = incomes.aggregate(total=Sum("amount"))["total"] or 0
    total_expense = expenses.aggregate(total=Sum("amount"))["total"] or 0
    profit = total_income - total_expense

    # CORREGIDO: sumar horas y labor_cost en Python, no en la base de datos
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
        "now": now(),
    }

    template = get_template("core/project_pdf.html")
    html = template.render(context)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type="application/pdf")
    return HttpResponse("Error rendering PDF", status=500)

@login_required
def schedule_create_view(request):
    # Only allow admin, superuser, or project_manager
    role = getattr(request.user.profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"]:
        return redirect('dashboard')

    if request.method == "POST":
        form = ScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ScheduleForm()
    return render(request, "core/schedule_form.html", {"form": form})

@login_required
def expense_create_view(request):
    # Only allow admin, superuser, or project_manager
    role = getattr(request.user.profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"]:
        return redirect('dashboard')

    if request.method == "POST":
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ExpenseForm()
    return render(request, "core/expense_form.html", {"form": form})

@login_required
def income_create_view(request):
    # Only allow admin, superuser, or project_manager
    role = getattr(request.user.profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"]:
        return redirect('dashboard')

    if request.method == "POST":
        form = IncomeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = IncomeForm()
    return render(request, "core/income_form.html", {"form": form})

@login_required
def timeentry_create_view(request):
    if request.method == "POST":
        form = TimeEntryForm(request.POST)
        if form.is_valid():
            time_entry = form.save(commit=False)
            # Si es touch ups, guarda la info en notes
            if form.cleaned_data.get('touch_ups'):
                po = form.cleaned_data.get('po_reference', '')
                note = form.cleaned_data.get('notes', '')
                time_entry.notes = f"TOUCH UPS - PO: {po}. {note}"
                time_entry.project = None  # No proyecto asignado
            time_entry.employee = request.user.employee  # Ajusta si tu relación es diferente
            time_entry.save()
            return redirect('dashboard')
    else:
        form = TimeEntryForm()
    return render(request, "core/timeentry_form.html", {"form": form})

@login_required
def payroll_create_view(request):
    role = getattr(request.user.profile, "role", "employee")
    if role not in ["admin", "superuser", "project_manager"]:
        return redirect('dashboard')

    PayrollEntryFormSet = modelformset_factory(PayrollEntry, form=PayrollEntryForm, extra=0, can_delete=False)

    if request.method == "POST":
        payroll_form = PayrollForm(request.POST)
        formset = PayrollEntryFormSet(request.POST, queryset=PayrollEntry.objects.none())
        if payroll_form.is_valid() and formset.is_valid():
            payroll = payroll_form.save(commit=False)
            payroll.created_by = request.user
            payroll.save()
            for entry_form in formset:
                entry = entry_form.save(commit=False)
                entry.payroll = payroll
                entry.save()
            return redirect('dashboard')
    else:
        payroll_form = PayrollForm()
        employees = Employee.objects.filter(is_active=True)
        initial_data = [{'employee': emp} for emp in employees]
        formset = PayrollEntryFormSet(queryset=PayrollEntry.objects.none(), initial=initial_data)

    # Agrega este bloque antes del return render
    employees = Employee.objects.filter(is_active=True)
    project_hours_summary_dict = {}
    for employee in employees:
        project_hours = obtener_horas_por_proyecto(employee)
        summary = ', '.join([f"{hours}h - {project}" for project, hours in project_hours.items()])
        project_hours_summary_dict[employee.id] = summary

    return render(request, "core/payroll_form.html", {
        "payroll_form": payroll_form,
        "formset": formset,
        "project_hours_summary_dict": project_hours_summary_dict,  # <-- agrega esto
    })

def obtener_horas_por_proyecto(employee):
    entries = TimeEntry.objects.filter(employee=employee)
    resumen = defaultdict(float)
    for entry in entries:
        if entry.project:
            resumen[entry.project.name] += float(entry.hours_worked)
    return resumen

from django.shortcuts import render, get_object_or_404
from .models import Project, Schedule, Task, Comment

def client_project_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    schedules = Schedule.objects.filter(project=project)
    tasks = Task.objects.filter(project=project)
    comments = Comment.objects.filter(project=project)
    context = {
        'project': project,
        'schedules': schedules,
        'tasks': tasks,
        'comments': comments,
    }
    return render(request, "core/client_project_view.html", context)

def agregar_tarea(request, project_id):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        project = get_object_or_404(Project, id=project_id)
        Task.objects.create(project=project, title=title, description=description, status="Pendiente")
    return redirect('client_project_view', project_id=project_id)

def agregar_comentario(request, project_id):
    if request.method == "POST":
        text = request.POST.get("text")
        image = request.FILES.get("image")
        project = get_object_or_404(Project, id=project_id)
        Comment.objects.create(project=project, user=request.user, text=text, image=image)
    return redirect('client_project_view', project_id=project_id)