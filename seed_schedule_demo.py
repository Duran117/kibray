"""
Script para crear datos de prueba en el cronograma
"""
from datetime import date, timedelta
from core.models import Project, ScheduleCategory, ScheduleItem

# Get first project
project = Project.objects.first()
if not project:
    print("No hay proyectos. Crea uno primero.")
    exit()

print(f"Proyecto: {project.name}")

# Create categories if they don't exist
cat1, _ = ScheduleCategory.objects.get_or_create(
    project=project,
    name="Preparación",
    defaults={'order': 1}
)

cat2, _ = ScheduleCategory.objects.get_or_create(
    project=project,
    name="Construcción",
    defaults={'order': 2}
)

cat3, _ = ScheduleCategory.objects.get_or_create(
    project=project,
    name="Acabados",
    defaults={'order': 3}
)

print(f"Categorías creadas: {cat1.name}, {cat2.name}, {cat3.name}")

# Create items with dates
today = date.today()

items_data = [
    {
        'category': cat1,
        'title': 'Limpieza del sitio',
        'planned_start': today - timedelta(days=7),
        'planned_end': today - timedelta(days=5),
        'status': 'DONE',
        'percent_complete': 100,
    },
    {
        'category': cat1,
        'title': 'Instalación de protección',
        'planned_start': today - timedelta(days=4),
        'planned_end': today - timedelta(days=2),
        'status': 'DONE',
        'percent_complete': 100,
    },
    {
        'category': cat2,
        'title': 'Pintura base',
        'planned_start': today - timedelta(days=1),
        'planned_end': today + timedelta(days=3),
        'status': 'IN_PROGRESS',
        'percent_complete': 50,
    },
    {
        'category': cat2,
        'title': 'Aplicación de acabado',
        'planned_start': today + timedelta(days=4),
        'planned_end': today + timedelta(days=7),
        'status': 'NOT_STARTED',
        'percent_complete': 0,
    },
    {
        'category': cat3,
        'title': 'Inspección final',
        'planned_start': today + timedelta(days=8),
        'planned_end': today + timedelta(days=8),
        'status': 'NOT_STARTED',
        'percent_complete': 0,
        'is_milestone': True,
    },
    {
        'category': cat3,
        'title': 'Limpieza final',
        'planned_start': today + timedelta(days=9),
        'planned_end': today + timedelta(days=10),
        'status': 'NOT_STARTED',
        'percent_complete': 0,
    },
]

for item_data in items_data:
    item, created = ScheduleItem.objects.get_or_create(
        project=project,
        title=item_data['title'],
        defaults=item_data
    )
    if created:
        print(f"✓ Creado: {item.title} ({item.planned_start} - {item.planned_end})")
    else:
        print(f"  Ya existe: {item.title}")

print(f"\nTotal items: {ScheduleItem.objects.filter(project=project).count()}")
print(f"Items con fechas: {ScheduleItem.objects.filter(project=project, planned_start__isnull=False).count()}")
