# Merge migration to resolve multiple leaf nodes
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ("core", "0121_sync_financial_fields"),
        ("core", "0122_restore_project_is_archived"),
    ]

    operations = []
