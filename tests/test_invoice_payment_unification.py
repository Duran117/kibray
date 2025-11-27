from decimal import Decimal

import pytest
from django.utils import timezone


@pytest.mark.django_db
def test_invoice_payment_unification(django_user_model):
    from core.models import Invoice, Project

    user = django_user_model.objects.create_user(username="invtester", password="x")
    project = Project.objects.create(name="PayProj", client="ClientX", start_date=timezone.now().date())

    # Crear factura inicial sin pago
    invoice = Invoice.objects.create(project=project, total_amount=Decimal("500.00"), status="SENT")
    assert invoice.amount_paid == Decimal("0")
    assert invoice.is_paid is False
    assert invoice.fully_paid is False
    assert invoice.status in ["SENT", "DRAFT"]

    # Pagar parcialmente
    invoice.amount_paid = Decimal("200.00")
    invoice.save()
    invoice.refresh_from_db()
    assert invoice.is_paid is False
    assert invoice.fully_paid is False
    assert invoice.status == "PARTIAL"
    assert invoice.balance_due == Decimal("300.00")

    # Pagar completamente
    invoice.amount_paid = Decimal("500.00")
    invoice.save()
    invoice.refresh_from_db()
    assert invoice.fully_paid is True
    assert invoice.is_paid is True  # Legacy sincronizado
    assert invoice.status == "PAID"
    assert invoice.balance_due == Decimal("0")
    assert invoice.payment_progress == pytest.approx(100.0)

    # Verificar que no se vuelve negativo balance_due si se paga de más
    invoice.amount_paid = Decimal("600.00")
    invoice.save()
    invoice.refresh_from_db()
    assert invoice.balance_due == Decimal("0")
    assert invoice.payment_progress == pytest.approx(120.0)  # Puede exceder 100 si sobrepago
