from django.db.models import Sum, Count
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from .models import Project, Expense, Income, Schedule, TimeEntry

@login_required
def dashboard_view(request):
    user = request.user
    role = getattr(user.profile, "role", "employee")  # Por si no tiene perfil aún

    # Métricas generales
    total_income = Income.objects.aggregate(t=Sum("amount"))["t"] or 0
    total_expense = Expense.objects.aggregate(t=Sum("amount"))["t"] or 0
    net_profit = total_income - total_expense
    employee_count = user.profile.user.__class__.objects.count()
    active_projects = Project.objects.filter(end_date__isnull=True).count()

    # Proyectos según rol
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

    # Resumen de horas trabajadas (calculado en Python)
    week_ago = date.today() - timedelta(days=7)
    month_ago = date.today() - timedelta(days=30)

    time_entries = TimeEntry.objects.all()
    if role == "employee":
        time_entries = time_entries.filter(employee__user=user)

    def calculate_hours_and_cost(entries):
        week_hours = 0
        month_hours = 0
        total_hours = 0
        labor_cost = 0
        for entry in entries:
            h = entry.hours_worked
            cost = entry.labor_cost
            if entry.date >= week_ago:
                week_hours += h
            if entry.date >= month_ago:
                month_hours += h
            total_hours += h
            labor_cost += cost
        return week_hours, month_hours, total_hours, labor_cost

    hours_week, hours_month, total_hours, labor_cost = calculate_hours_and_cost(time_entries)

    # Datos para gráficos
    chart_labels = []
    chart_income = []
    chart_expense = []
    for proj in projects:
        chart_labels.append(proj.name)
        chart_income.append(proj.project_income or 0)
        chart_expense.append(proj.project_expense or 0)

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
        "chart_labels": chart_labels,
        "chart_income": chart_income,
        "chart_expense": chart_expense,
    }

    return render(request, "dashboard.html", context)
