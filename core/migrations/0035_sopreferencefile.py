from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0034_activitytemplate_dailyplan_plannedactivity_and_more'),
    ]
    operations = [
        migrations.CreateModel(
            name='SOPReferenceFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='sop_references/%Y/%m/%d/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('sop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reference_files', to='core.activitytemplate')),
            ],
        ),
    ]
