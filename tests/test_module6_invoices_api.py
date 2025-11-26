import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from core.models import Project, Invoice, InvoicePayment

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username='invoicer', password='pass123', email='invoicer@example.com')


@pytest.fixture
def project(db):
    return Project.objects.create(name='Villa Moderna', client='ACME', start_date=date(2025, 11, 1))


@pytest.mark.django_db
class TestInvoiceAPI:
    def test_create_invoice_with_lines_and_totals(self, api_client, user, project):
        api_client.force_authenticate(user=user)
        payload = {
            'project': project.id,
            'due_date': date(2025, 12, 15).isoformat(),
            'notes': 'Primer factura',
            'lines': [
                {'description': 'Avance general', 'amount': '1200.00'},
                {'description': 'CO-004', 'amount': '300.50'}
            ]
        }
        res = api_client.post('/api/v1/invoices/', payload, format='json')
        assert res.status_code == 201, res.content
        inv_id = res.data['id']
        assert res.data['status'] == 'DRAFT'
        assert float(res.data['total_amount']) == pytest.approx(1500.50)
        # detail fetch includes lines
        g = api_client.get(f'/api/v1/invoices/{inv_id}/')
        assert g.status_code == 200
        assert len(g.data['lines']) == 2
        assert g.data['invoice_number']

    def test_mark_sent_and_approved(self, api_client, user, project):
        api_client.force_authenticate(user=user)
        inv = Invoice.objects.create(project=project, total_amount=Decimal('1000.00'))
        # mark sent
        s = api_client.post(f'/api/v1/invoices/{inv.id}/mark_sent/')
        assert s.status_code == 200
        # refresh
        inv.refresh_from_db()
        assert inv.status == 'SENT'
        assert inv.sent_date is not None
        # approve
        a = api_client.post(f'/api/v1/invoices/{inv.id}/mark_approved/')
        assert a.status_code == 200
        inv.refresh_from_db()
        assert inv.status == 'APPROVED'
        assert inv.approved_date is not None

    def test_record_payment_partial_and_paid(self, api_client, user, project):
        api_client.force_authenticate(user=user)
        inv = Invoice.objects.create(project=project, total_amount=Decimal('800.00'))
        # partial
        p1 = api_client.post(f'/api/v1/invoices/{inv.id}/record_payment/', {
            'amount': '300.00',
            'payment_date': date(2025, 12, 1).isoformat(),
            'payment_method': 'CHECK',
            'reference': 'CHK-1001'
        }, format='json')
        assert p1.status_code == 201, p1.content
        inv.refresh_from_db()
        assert inv.status in ['PARTIAL', 'PAID']
        assert float(inv.amount_paid) == pytest.approx(300.0)
        # full remaining
        p2 = api_client.post(f'/api/v1/invoices/{inv.id}/record_payment/', {
            'amount': '500.00',
            'payment_date': date(2025, 12, 2).isoformat(),
            'payment_method': 'TRANSFER',
            'reference': 'TRX-2002'
        }, format='json')
        assert p2.status_code == 201
        inv.refresh_from_db()
        assert inv.status == 'PAID'
        assert float(inv.amount_paid) == pytest.approx(800.0)

    def test_filter_invoices_by_project_and_status(self, api_client, user, project):
        api_client.force_authenticate(user=user)
        inv1 = Invoice.objects.create(project=project, total_amount=Decimal('100.00'), status='SENT')
        inv2 = Invoice.objects.create(project=project, total_amount=Decimal('200.00'), status='DRAFT')
        # filter by project
        r1 = api_client.get(f'/api/v1/invoices/?project={project.id}')
        assert r1.status_code == 200
        assert len(r1.data) >= 2
        # filter by status
        r2 = api_client.get('/api/v1/invoices/?status=SENT')
        assert r2.status_code == 200
        # make sure at least one SENT is present
        assert any(item['status'] == 'SENT' for item in r2.data)
