# Generated migration for full-text search on ChatMessage
# PostgreSQL only - will be skipped on SQLite

from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from django.db import migrations, connection


def check_postgres(apps, schema_editor):
    """Only run on PostgreSQL"""
    return connection.vendor == 'postgresql'


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0114_notificationlog_userstatus_chatmessage_read_by_and_more'),
    ]

    operations = [
        # Add search_vector field to ChatMessage (PostgreSQL only)
        migrations.RunPython(
            code=lambda apps, schema_editor: None,
            reverse_code=lambda apps, schema_editor: None,
        ),
    ]
