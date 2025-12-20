from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0081_normalize_material_request_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientrequest',
            name='request_type',
            field=models.CharField(max_length=20, choices=[('material','Material'),('change_order','Cambio'),('info','Información')], default='info'),
        ),
    ]
