from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("core", "0101_profile_rejections_count_task_is_visible_to_client_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProposalEmailLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("recipient", models.EmailField(max_length=254)),
                ("subject", models.CharField(max_length=200)),
                ("message_preview", models.TextField()),
                ("sent_at", models.DateTimeField(auto_now_add=True)),
                ("success", models.BooleanField(default=True)),
                ("error_message", models.TextField(blank=True, null=True)),
                (
                    "estimate",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="email_logs", to="core.estimate"),
                ),
                (
                    "proposal",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="email_logs", to="core.proposal"),
                ),
            ],
            options={"ordering": ["-sent_at"],},
        ),
    ]
