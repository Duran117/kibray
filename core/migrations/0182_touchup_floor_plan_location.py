"""Add floor plan location fields to TouchUp V2 model."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0181_allow_null_project_phase_for_personal_events"),
    ]

    operations = [
        migrations.AddField(
            model_name="touchup",
            name="floor_plan",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="touchups_v2_on_plan",
                to="core.floorplan",
                help_text="Floor plan where this touch-up is located",
            ),
        ),
        migrations.AddField(
            model_name="touchup",
            name="pin_x",
            field=models.DecimalField(
                blank=True,
                null=True,
                max_digits=6,
                decimal_places=4,
                help_text="Normalized X coordinate on floor plan (0..1)",
            ),
        ),
        migrations.AddField(
            model_name="touchup",
            name="pin_y",
            field=models.DecimalField(
                blank=True,
                null=True,
                max_digits=6,
                decimal_places=4,
                help_text="Normalized Y coordinate on floor plan (0..1)",
            ),
        ),
    ]
