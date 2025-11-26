from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0084_chatmessage_attachment'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitephoto',
            name='damage_report',
            field=models.ForeignKey(null=True, blank=True, on_delete=models.SET_NULL, related_name='site_photos', to='core.damagereport'),
        ),
        migrations.AddField(
            model_name='sitephoto',
            name='location_accuracy_m',
            field=models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text='GPS accuracy in meters'),
        ),
    ]
