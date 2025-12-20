from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0072_alter_plannedactivity_schedule_item'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('default_priority', models.CharField(choices=[('Alta', 'Alta'), ('Media', 'Media'), ('Baja', 'Baja')], default='Media', max_length=10)),
                ('estimated_hours', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('tags', models.JSONField(blank=True, default=list, help_text='List of keyword tags for fuzzy search')),
                ('checklist', models.JSONField(blank=True, default=list, help_text='Ordered checklist items strings')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'verbose_name': 'Plantilla de Tarea',
                'verbose_name_plural': 'Plantillas de Tareas',
            },
        ),
        migrations.AddIndex(
            model_name='tasktemplate',
            index=models.Index(fields=['default_priority'], name='core_taskte_default_3b1f5a_idx'),
        ),
    ]
