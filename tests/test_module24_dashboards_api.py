import pytest
from decimal import Decimal
from django.utils import timezone

@pytest.mark.django_db
class TestDashboardsAPI:
    def test_invoice_dashboard(self, client, django_user_model):
        from core.models import Project, Invoice
        user = django_user_model.objects.create_user(username="dash", password="x", is_staff=True)
        client.force_login(user)
        p1 = Project.objects.create(name="P1", client="Acme", start_date=timezone.now().date())
        p2 = Project.objects.create(name="P2", client="Globex", start_date=timezone.now().date())
        Invoice.objects.create(project=p1, invoice_number="I1", date_issued=timezone.now().date(), due_date=timezone.now().date(), status='PAID', total_amount=Decimal('100'))
        Invoice.objects.create(project=p1, invoice_number="I2", date_issued=timezone.now().date(), due_date=timezone.now().date(), status='OVERDUE', total_amount=Decimal('50'))
        Invoice.objects.create(project=p2, invoice_number="I3", date_issued=timezone.now().date(), due_date=timezone.now().date(), status='SENT', total_amount=Decimal('25'))

        resp = client.get('/api/v1/dashboards/invoices/')
        assert resp.status_code == 200
        data = resp.json()
        assert data['total_invoices'] == 3
        assert Decimal(str(data['total_amount'])) == Decimal('175')
        assert Decimal(str(data['paid_amount'])) == Decimal('100')
        assert data['overdue_count'] == 1
        assert Decimal(str(data['outstanding_amount'])) == Decimal('75')
        assert isinstance(data['top_clients'], list)

    def test_materials_dashboard(self, client, django_user_model):
        from core.models import InventoryItem, InventoryLocation, ProjectInventory, InventoryMovement
        user = django_user_model.objects.create_user(username="dash2", password="x", is_staff=True)
        client.force_login(user)
        item1 = InventoryItem.objects.create(name="Paint", category="PINTURA", average_cost=Decimal('12.00'))
        item2 = InventoryItem.objects.create(name="Brush", category="HERRAMIENTA", average_cost=Decimal('5.00'))
        loc = InventoryLocation.objects.create(name="WH", is_storage=True)
        ProjectInventory.objects.create(item=item1, location=loc, quantity=Decimal('2'))
        ProjectInventory.objects.create(item=item2, location=loc, quantity=Decimal('3'))
        InventoryMovement.objects.create(item=item1, to_location=loc, movement_type="RECEIVE", quantity=Decimal('1'))

        resp = client.get('/api/v1/dashboards/materials/')
        assert resp.status_code == 200
        data = resp.json()
        assert data['total_items'] >= 2
        assert data['recent_movements'] >= 1
        # total_stock_value = 2*12 + 3*5 = 39
        assert Decimal(str(data['total_stock_value'])) == Decimal('39')
        assert isinstance(data['items_by_category'], list)
