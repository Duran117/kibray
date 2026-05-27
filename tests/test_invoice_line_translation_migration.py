"""Test the 0186 data migration that translates legacy Spanish invoice line
descriptions to English. We re-import the migration's transformation function
and apply it to a fresh set of legacy strings."""
from importlib import import_module

import pytest


def test_translate_descriptions_in_place():
    mod = import_module("core.migrations.0186_translate_invoice_line_descriptions")
    pairs = [
        ("Mano de Obra CO #32: 7.18 hrs @ $50.00/hr",
         "Labor CO #32: 7.18 hrs @ $50.00/hr"),
        ("Materiales CO #32: costo $105.94 + 15.00%",
         "Materials CO #32: cost $105.94 + 15.00% markup"),
        ("CO #33 (Fijo): exterior chinking",
         "CO #33 (Fixed): exterior chinking"),
        ("Contrato Base - Estimado v2",
         "Base Contract - Estimate v2"),
        ("Progreso Estimado: P-100 - Interior paint (50%)",
         "Estimate Progress: P-100 - Interior paint (50%)"),
        ("Tiempo & Materiales - 12.5 horas @ $50/hr",
         "Time & Materials - 12.5 hours @ $50/hr"),
        ("T&M para CO #5: extra prep - 3.0 hrs @ $50/hr",
         "T&M for CO #5: extra prep - 3.0 hrs @ $50/hr"),
        # Already-English strings stay untouched
        ("Labor CO #1: 1 hrs @ $50/hr",
         "Labor CO #1: 1 hrs @ $50/hr"),
    ]
    for original, expected in pairs:
        new = original
        for pattern, replacement in mod.REPLACEMENTS:
            new = pattern.sub(replacement, new)
        assert new == expected, f"{original!r} -> {new!r}, expected {expected!r}"


@pytest.mark.django_db
def test_migration_translates_existing_rows(db):
    """Smoke test: apply the migration's callable to real DB rows."""
    from datetime import date
    from decimal import Decimal
    from django.apps import apps as django_apps

    from core.models import Invoice, InvoiceLine, Project

    project = Project.objects.create(
        name="MigProj", client="X", start_date=date.today()
    )
    inv = Invoice.objects.create(project=project, total_amount=Decimal("0"), status="DRAFT")
    InvoiceLine.objects.create(invoice=inv, description="Mano de Obra CO #7: 1.0 hrs @ $50/hr", amount=50)
    InvoiceLine.objects.create(invoice=inv, description="CO #8 (Fijo): test", amount=100)
    InvoiceLine.objects.create(invoice=inv, description="Already english", amount=10)

    mod = import_module("core.migrations.0186_translate_invoice_line_descriptions")
    mod.translate_descriptions(django_apps, None)

    descs = list(InvoiceLine.objects.filter(invoice=inv).order_by("id").values_list("description", flat=True))
    assert descs[0].startswith("Labor CO #7")
    assert descs[1].startswith("CO #8 (Fixed)")
    assert descs[2] == "Already english"
