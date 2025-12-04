# Generated manually to restore Project.is_archived removed by cleanup migration
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0112_cleanup_stale_fields"),
    ]

    operations = [
        # Add nullable field first to avoid NOT NULL constraint issues on existing rows
        migrations.AddField(
            model_name="project",
            name="is_archived",
            field=models.BooleanField(null=True, default=False, help_text="Proyecto archivado (no activo)"),
            preserve_default=True,
        ),
        # Backfill NULLs to False
        migrations.RunSQL(
            sql="UPDATE core_project SET is_archived = 0 WHERE is_archived IS NULL;",
            reverse_sql="",
        ),
        # Make field non-nullable now that data is populated
        migrations.AlterField(
            model_name="project",
            name="is_archived",
            field=models.BooleanField(null=False, default=False, help_text="Proyecto archivado (no activo)"),
            preserve_default=True,
        ),
    ]
