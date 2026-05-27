"""Data migration: translate existing Spanish invoice line descriptions to English.

The legacy invoice builder hard-coded Spanish strings in line item descriptions
("Mano de Obra CO #X", "Materiales CO #X: costo …", "CO #X (Fijo): …",
"Contrato Base - Estimado vN", "Progreso Estimado: …", "Tiempo & Materiales - … horas",
"T&M para CO #X"). The view has been fixed but historical rows still show
Spanish on rendered PDFs. This migration rewrites those descriptions in-place.
"""
from django.db import migrations
import re


REPLACEMENTS = [
    # Order matters: most specific patterns first.
    (re.compile(r"^Mano de Obra CO #(\d+):"), r"Labor CO #\1:"),
    (re.compile(r"^Materiales CO #(\d+): costo \$([0-9.,]+) \+ ([0-9.,]+)%$"),
     r"Materials CO #\1: cost $\2 + \3% markup"),
    (re.compile(r"^Materiales CO #(\d+):"), r"Materials CO #\1:"),
    (re.compile(r"^CO #(\d+) \(Fijo\):"), r"CO #\1 (Fixed):"),
    (re.compile(r"^T&M para CO #(\d+):"), r"T&M for CO #\1:"),
    (re.compile(r"^Tiempo & Materiales - (.+?) horas @"),
     r"Time & Materials - \1 hours @"),
    (re.compile(r"^Contrato Base - Estimado v"), "Base Contract - Estimate v"),
    (re.compile(r"^Progreso Estimado:"), "Estimate Progress:"),
]


def translate_descriptions(apps, schema_editor):
    InvoiceLine = apps.get_model("core", "InvoiceLine")
    updated = 0
    for line in InvoiceLine.objects.iterator():
        original = line.description or ""
        new = original
        for pattern, replacement in REPLACEMENTS:
            new = pattern.sub(replacement, new)
        if new != original:
            line.description = new
            line.save(update_fields=["description"])
            updated += 1
    if updated:
        print(f"  translated {updated} invoice line description(s) to English")


def noop_reverse(apps, schema_editor):
    # No reverse — we don't want to re-introduce Spanish strings.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0185_clientrequest_color_sample_type"),
    ]

    operations = [
        migrations.RunPython(translate_descriptions, noop_reverse),
    ]
