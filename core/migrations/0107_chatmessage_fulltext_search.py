# Generated migration for full-text search on ChatMessage

from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0106_devicetoken_notificationpreference'),  # Adjust to your last migration
    ]

    operations = [
        # Add search_vector field to ChatMessage
        migrations.AddField(
            model_name='chatmessage',
            name='search_vector',
            field=SearchVectorField(null=True, blank=True),
        ),
        
        # Add GIN index for full-text search
        migrations.AddIndex(
            model_name='chatmessage',
            index=GinIndex(
                fields=['search_vector'],
                name='chatmessage_search_idx',
            ),
        ),
        
        # Update existing records with search vectors
        migrations.RunSQL(
            sql="""
                UPDATE core_chatmessage
                SET search_vector = to_tsvector('english', COALESCE(message, ''))
                WHERE search_vector IS NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
