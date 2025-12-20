from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0109_add_strategic_planner_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='changeorder',
            name='pricing_type',
            field=models.CharField(choices=[('FIXED', 'Fixed'), ('TM', 'Time & Materials')], default='FIXED', max_length=10),
        ),
    ]
