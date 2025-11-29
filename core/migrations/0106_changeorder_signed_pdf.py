from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0105_add_customer_signature_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="changeorder",
            name="signed_pdf",
            field=models.FileField(
                upload_to="signatures/change_orders/pdf/",
                null=True,
                blank=True,
                help_text="PDF snapshot of signed Change Order",
            ),
        ),
    ]
