"""Add 'color_sample' to ClientRequest.request_type choices.

Lets clients submit a request for a new color sample (max 3 pending
per project) without granting them direct create access to ColorSample.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0184_contract_attachments_and_lifecycle"),
    ]

    operations = [
        migrations.AlterField(
            model_name="clientrequest",
            name="request_type",
            field=models.CharField(
                choices=[
                    ("material", "Material"),
                    ("change_order", "Cambio"),
                    ("info", "Información"),
                    ("color_sample", "Color Sample"),
                ],
                default="info",
                max_length=20,
            ),
        ),
    ]
