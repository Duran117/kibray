from django.db.models import Sum
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils.timezone import now
from datetime import date, timedelta
from io import BytesIO
from xhtml2pdf import pisa
from .models import Project, Expense, Income, Schedule, TimeEntry

@login_required
def dashboard_view(request):
    user = request.user
    role = getattr(user.profile, "role", "employee")

    total_income = Income.objects.aggregate(t=Sum("amount"))["t"] or 0
    total_expense = Expense.objects.aggregate(t=Sum("amount"))["t"] or 0
    net_profit = total_income - total_expense
    employee_count = user.profile.user.__class__.objects.count()
    active_projects = Project.objects.filter(end_date__isnull=True).count()

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

    # Upcoming Events
    future = date.today() + timedelta(days=30)
    if role == "employee":
        schedules = Schedule.objects.filter(assigned_to=user, start_datetime__date__lte=future)
    elif role == "client":
        schedules = Schedule.objects.filter(project__client=user.username, start_datetime__date__lte=future)
    else:
        schedules = Schedule.objects.filter(start_datetime__date__lte=future)
    schedules = schedules.order_by("start_datetime")[:10]

    # Time Tracking
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

    # Charts
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
        "chart_net_profit": chart_net_profit,
        "chart_budget_labels": chart_budget_labels,
        "chart_budget_labor": chart_budget_labor,
        "chart_budget_materials": chart_budget_materials,
        "chart_budget_other": chart_budget_other,
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

    total_hours = time_entries.aggregate(total=Sum("hours_worked"))["total"] or 0
    labor_cost = time_entries.aggregate(total=Sum("labor_cost"))["total"] or 0

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
