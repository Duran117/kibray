"""
Migration to convert Task status from Spanish to English
"""
from django.db import migrations


def migrate_status_to_english(apps, schema_editor):
    """Convert Spanish status values to English"""
    Task = apps.get_model('core', 'Task')
    
    status_mapping = {
        'Pendiente': 'Pending',
        'En Progreso': 'In Progress',
        'En Revisión': 'Under Review',
        'Completada': 'Completed',
        'Cancelada': 'Cancelled',
    }
    
    for spanish, english in status_mapping.items():
        updated = Task.objects.filter(status=spanish).update(status=english)
        if updated:
            print(f"  Migrated {updated} tasks from '{spanish}' to '{english}'")


def migrate_status_to_spanish(apps, schema_editor):
    """Reverse: Convert English status values back to Spanish"""
    Task = apps.get_model('core', 'Task')
    
    status_mapping = {
        'Pending': 'Pendiente',
        'In Progress': 'En Progreso',
        'Under Review': 'En Revisión',
        'Completed': 'Completada',
        'Cancelled': 'Cancelada',
    }
    
    for english, spanish in status_mapping.items():
        Task.objects.filter(status=english).update(status=spanish)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0153_alter_dailylog_accomplishments_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_status_to_english, migrate_status_to_spanish),
    ]
