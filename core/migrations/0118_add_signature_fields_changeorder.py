from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0117_merge_20251202_2230'),
    ]

    operations = [
        migrations.AlterField(
            model_name='changeorder',
            name='pricing_type',
            field=models.CharField(choices=[('FIXED', 'Fixed'), ('T_AND_M', 'Time & Materials')], default='FIXED', max_length=12),
        ),
        migrations.AddField(
            model_name='changeorder',
            name='signature_image',
            field=models.ImageField(blank=True, null=True, upload_to='changeorders/signatures/'),
        ),
        migrations.AddField(
            model_name='changeorder',
            name='signed_by',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='changeorder',
            name='signed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='changeorder',
            name='signed_ip',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name='changeorder',
            name='signed_user_agent',
            field=models.CharField(blank=True, max_length=512),
        ),
    ]
