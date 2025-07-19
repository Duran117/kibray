from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Project, Schedule

def home(request):
    return HttpResponse("Welcome to Kibray Dashboard!")

def resumen_proyectos(request):
    projects = Project.objects.all()

    if not projects:
        return render(request, 'core/resumen.html', {'error': 'No hay proyectos registrados aún.'})

    mayor = max(projects, key=lambda p: p.total_income)
    menor = min(projects, key=lambda p: p.total_income)

    return render(request, 'core/resumen.html', {
        'mayor': mayor,
        'menor': menor,
    })

@login_required
def public_schedule_view(request):
    user = request.user

    if not user.is_superuser:
        schedules = Schedule.objects.filter(is_personal=False).filter(
            assigned_to=user
        ) | Schedule.objects.filter(
            project__in=user.project_set.all()
        )
    else:
        schedules = Schedule.objects.all()

    context = {
        'schedules': schedules.order_by('start_datetime')
    }
    return render(request, 'schedule/public_schedule.html', context)
