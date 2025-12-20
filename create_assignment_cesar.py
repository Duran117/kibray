import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kibray.settings')
django.setup()

from core.models import Employee, Project, ResourceAssignment
from django.utils import timezone

employee = Employee.objects.filter(user__username='cesar123').first()
project = Project.objects.get(id=308)
today = timezone.localdate()

assignment, created = ResourceAssignment.objects.get_or_create(
    employee=employee,
    project=project,
    date=today,
    defaults={'shift': 'MORNING', 'notes': 'Asignación automática para testing'}
)

print(f"{'✅ Creado' if created else '✅ Ya existe'}: {employee} → {project.name} ({today})")
