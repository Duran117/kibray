import decimal

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0102_proposal_email_log"),
    ]

    operations = [
        migrations.AddField(
            model_name="changeorder",
            name="pricing_type",
            field=models.CharField(default="FIXED", help_text="Tipo de facturación para este CO", max_length=10, choices=[("FIXED", "Precio Fijo"), ("T_AND_M", "Tiempo y Materiales")]),
        ),
        migrations.AddField(
            model_name="changeorder",
            name="billing_hourly_rate",
            field=models.DecimalField(default=decimal.Decimal("0.00"), help_text="Tarifa por hora cobrada al cliente (venta) en modalidad T&M", max_digits=7, decimal_places=2),
        ),
        migrations.AddField(
            model_name="changeorder",
            name="material_markup_pct",
            field=models.DecimalField(default=decimal.Decimal("20.00"), help_text="Markup (%) sobre materiales para T&M", max_digits=6, decimal_places=2),
        ),
        migrations.AddField(
            model_name="timeentry",
            name="invoice_line",
            field=models.ForeignKey(blank=True, help_text="Línea de factura que cobró esta entrada (para evitar doble facturación)", null=True, on_delete=models.deletion.SET_NULL, related_name="time_entries_billed", to="core.invoiceline"),
        ),
        migrations.AddField(
            model_name="expense",
            name="invoice_line",
            field=models.ForeignKey(blank=True, help_text="Línea de factura que facturó este gasto (evita duplicados en T&M)", null=True, on_delete=models.deletion.SET_NULL, related_name="expenses_billed", to="core.invoiceline"),
        ),
    ]
