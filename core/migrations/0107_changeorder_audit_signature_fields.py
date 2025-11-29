from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0106_changeorder_signed_pdf"),
    ]

    operations = [
        migrations.AddField(
            model_name="changeorder",
            name="signed_ip",
            field=models.GenericIPAddressField(null=True, blank=True, help_text="IP address of signer"),
        ),
        migrations.AddField(
            model_name="changeorder",
            name="signed_user_agent",
            field=models.CharField(max_length=512, null=True, blank=True, help_text="User-Agent header of signer"),
        ),
    ]
