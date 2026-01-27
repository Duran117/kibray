# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0156_add_co_title_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='colorsample',
            name='requires_client_signature',
            field=models.BooleanField(default=False, help_text='If True, this sample will appear in client dashboard for signature'),
        ),
        migrations.AddField(
            model_name='colorsample',
            name='client_signature',
            field=models.ImageField(blank=True, help_text="Client's digital signature image", null=True, upload_to='color_samples/signatures/'),
        ),
        migrations.AddField(
            model_name='colorsample',
            name='client_signed_at',
            field=models.DateTimeField(blank=True, help_text='When client signed', null=True),
        ),
        migrations.AddField(
            model_name='colorsample',
            name='client_signed_name',
            field=models.CharField(blank=True, help_text='Name entered by client when signing', max_length=200),
        ),
        migrations.AddField(
            model_name='colorsample',
            name='signature_token',
            field=models.CharField(blank=True, help_text='Unique token for public signature URL', max_length=64, null=True, unique=True),
        ),
    ]
