import uuid
from decimal import Decimal
import pytest
from django.urls import reverse
from django.test import Client, override_settings
from django.utils import timezone
from django.core import mail
from django.contrib.auth import get_user_model

from core.models import Project, Estimate, EstimateLine, CostCode, Proposal, ProposalEmailLog

@pytest.mark.django_db
class TestEstimateSendEmailView:
    @pytest.fixture
    def project(self):
        return Project.objects.create(
            name="EmailProj",
            start_date=timezone.now().date(),
            client="client@example.com",
        )

    @pytest.fixture
    def estimate(self, project):
        est = Estimate.objects.create(
            project=project,
            version=1,
            markup_material=Decimal("10.00"),
            markup_labor=Decimal("15.00"),
            overhead_pct=Decimal("5.00"),
            target_profit_pct=Decimal("10.00"),
            approved=False,
        )
        cc = CostCode.objects.create(code="01.01", name="Prep", category="labor")
        EstimateLine.objects.create(
            estimate=est,
            cost_code=cc,
            qty=Decimal("2"),
            unit="hrs",
            labor_unit_cost=Decimal("50"),
            material_unit_cost=Decimal("10"),
            other_unit_cost=Decimal("0"),
        )
        return est

    @pytest.fixture
    def auth_client(self, db):
        """Authenticated client (login required for estimate_send_email view)."""
        User = get_user_model()
        user = User.objects.create_user(username="pm_sender", password="testpass123")
        c = Client()
        assert c.login(username="pm_sender", password="testpass123") is True
        return c

    def test_get_modal_partial_loads(self, auth_client, estimate):
        url = reverse('estimate_send_email', kwargs={'estimate_id': estimate.id}) + '?partial=1'
        response = auth_client.get(url)
        assert response.status_code == 200
        assert 'Enviar Ahora' in response.content.decode()
        # Ensure proposal created
        assert Proposal.objects.filter(estimate=estimate).exists()

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_post_sends_email_and_logs(self, auth_client, estimate):
        # Prefetch proposal view (ensures proposal exists and initial recipient set)
        Proposal.objects.get_or_create(estimate=estimate, defaults={'client_view_token': str(uuid.uuid4())})
        url = reverse('estimate_send_email', kwargs={'estimate_id': estimate.id})
        data = {
            'subject': 'Cotización Test',
            'recipient': 'client@example.com',
            'message': 'Hola Cliente, revisa la cotización. Gracias.'
        }
        response = auth_client.post(url, data, follow=True)
        assert response.status_code == 200
        # Email sent
        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert 'Cotización Test' in email.subject
        assert 'Hola Cliente' in email.body
        # Logging
        log = ProposalEmailLog.objects.first()
        assert log is not None
        assert log.recipient == 'client@example.com'
        assert log.success is True
        assert 'Hola Cliente' in log.message_preview

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_error_handling_logs_failure(self, monkeypatch, auth_client, estimate):
        # Force send failure
        def fake_send(*a, **kw):
            raise Exception('SMTP failure')
        from django.core.mail import EmailMultiAlternatives
        monkeypatch.setattr(EmailMultiAlternatives, 'send', fake_send)
        Proposal.objects.get_or_create(estimate=estimate, defaults={'client_view_token': str(uuid.uuid4())})
        url = reverse('estimate_send_email', kwargs={'estimate_id': estimate.id})
        data = {
            'subject': 'Cotización Test',
            'recipient': 'client@example.com',
            'message': 'Hola Cliente, revisa la cotización.'
        }
        response = auth_client.post(url, data, follow=True)
        assert response.status_code == 200
        # Email not sent
        assert len(mail.outbox) == 0
        log = ProposalEmailLog.objects.first()
        assert log is not None
        assert log.success is False
        assert 'SMTP failure' in (log.error_message or '')
