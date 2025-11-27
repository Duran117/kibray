from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Signature",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(help_text="Short label for the signed item", max_length=255)),
                ("signed_at", models.DateTimeField(auto_now_add=True)),
                ("hash_alg", models.CharField(default="sha256", max_length=32)),
                ("content_hash", models.CharField(help_text="Hex digest of signed content", max_length=128)),
                ("note", models.TextField(blank=True)),
                ("file", models.FileField(blank=True, null=True, upload_to="signatures/")),
                (
                    "signer",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="signatures", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "ordering": ["-signed_at"],
            },
        ),
        migrations.AddIndex(
            model_name="signature",
            index=models.Index(fields=["signer", "signed_at"], name="signatures_signer_signed_at_idx"),
        ),
    ]
