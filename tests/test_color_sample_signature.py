"""
Pruebas para firma de cliente en muestras de color.
Phase 3: Color Sample Client Signatures

Tests enfocados en validacion de logica de firma y BD.
Los templates se validan en tests E2E separados.
"""
import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from django.core import signing
from core.models import ColorSample, ColorApproval, Project, Profile
from django.urls import reverse
from datetime import date


@pytest.mark.django_db
class ColorSampleSignatureLogicTests(TestCase):
    """Pruebas de logica sin dependencias de templates"""

    def setUp(self):
        """Configuracion para tests"""
        self.project = Project.objects.create(
            name="Test Project Sig",
            address="123 Test St",
            start_date=date(2025, 1, 1),
        )

        self.color_sample = ColorSample.objects.create(
            project=self.project,
            name="Test Blue",
            code="BLUE-001",
            brand="Benjamin Moore",
            finish="Matte",
            status="pending",
        )

    def test_color_sample_can_be_created(self):
        """Test que ColorSample se crea correctamente"""
        assert self.color_sample.id is not None
        assert self.color_sample.status == "pending"
        # approval_signature puede ser un string vacío o None
        assert self.color_sample.approval_signature is not None or self.color_sample.approval_signature == ""

    def test_color_approval_can_be_created(self):
        """Test que ColorApproval se crea correctamente"""
        approval = ColorApproval.objects.create(
            project=self.project,
            color_name="Test Blue",
            color_code="BLUE-001",
            brand="Benjamin Moore",
            status="APPROVED",
        )

        assert approval.id is not None
        assert approval.color_name == "Test Blue"
        assert approval.status == "APPROVED"

    def test_color_approval_timestamp_tracking(self):
        """Test que ColorApproval registra timestamp"""
        approval = ColorApproval.objects.create(
            project=self.project,
            color_name="Test Client",
            color_code="TEST-001",
            status="APPROVED",
        )

        assert approval.created_at is not None
        # signed_at se establece cuando se aprueba
        assert approval.signed_at is None  # Inicialmente nulo

    def test_token_generation_and_validation(self):
        """Test que tokens HMAC se pueden generar y validar"""
        payload = {"sample_id": self.color_sample.id}
        token = signing.dumps(payload)

        # Validar token
        decoded = signing.loads(token, max_age=60 * 60 * 24 * 7)
        assert decoded["sample_id"] == self.color_sample.id

    def test_token_validation_with_wrong_sample_id(self):
        """Test que token con ID diferente falla"""
        payload = {"sample_id": 999}  # Sample ID incorrecto
        token = signing.dumps(payload)

        decoded = signing.loads(token)
        assert decoded["sample_id"] != self.color_sample.id

    def test_color_sample_status_transitions(self):
        """Test transiciones de estado de ColorSample"""
        assert self.color_sample.status == "pending"

        # Cambiar a approved
        self.color_sample.status = "approved"
        self.color_sample.save()

        self.color_sample.refresh_from_db()
        assert self.color_sample.status == "approved"

    def test_multiple_color_samples_per_project(self):
        """Test que proyecto puede tener multiples muestras"""
        sample2 = ColorSample.objects.create(
            project=self.project,
            name="Test Red",
            code="RED-001",
            brand="Benjamin Moore",
            finish="Glossy",
            status="pending",
        )

        samples = ColorSample.objects.filter(project=self.project)
        assert samples.count() == 2
        assert self.color_sample in samples
        assert sample2 in samples

    def test_color_approval_queryset_filtering(self):
        """Test que ColorApproval puede ser filtrado por proyecto"""
        approval = ColorApproval.objects.create(
            project=self.project,
            color_name="Client A",
            status="PENDING",
        )

        filtered = ColorApproval.objects.filter(project=self.project)
        assert filtered.count() >= 1
        assert approval in filtered

    def test_signature_file_field_assignment(self):
        """Test que archivo de firma se puede asignar a ColorApproval"""
        approval = ColorApproval.objects.create(
            project=self.project,
            color_name="Test Client",
            status="APPROVED",
        )

        # En produccion se usaria un ContentFile real
        # Aqui solo verificamos que el campo existe
        assert hasattr(approval, "client_signature")


class ColorSampleURLRoutingTests(TestCase):
    """Tests de enrutamiento de URLs"""

    def setUp(self):
        self.project = Project.objects.create(
            name="URL Test Project",
            address="123 Test St",
            start_date=date(2025, 1, 1),
        )

        self.color_sample = ColorSample.objects.create(
            project=self.project,
            name="Test Color",
            code="TEST-001",
            brand="Test Brand",
            finish="Matte",
            status="pending",
        )

    def test_color_sample_signature_url_exists(self):
        """Test que URL de firma existe"""
        url = reverse("color_sample_client_signature", args=[self.color_sample.id])
        assert url is not None
        assert "colors/sample" in url
        assert "sign" in url

    def test_color_sample_signature_token_url_exists(self):
        """Test que URL con token existe"""
        token = "test-token"
        url = reverse(
            "color_sample_client_signature_token",
            args=[self.color_sample.id, token],
        )
        assert url is not None
        assert token in url


class ColorApprovalModelTests(TestCase):
    """Tests del modelo ColorApproval"""

    def setUp(self):
        self.project = Project.objects.create(
            name="Model Test Project",
            address="123 Test St",
            start_date=date(2025, 1, 1),
        )

    def test_color_approval_creation_with_minimal_fields(self):
        """Test creacion de ColorApproval con campos minimos"""
        approval = ColorApproval.objects.create(
            project=self.project,
            color_name="Test Client",
        )

        assert approval.id is not None
        assert approval.project == self.project
        assert approval.color_name == "Test Client"

    def test_color_approval_creation_with_all_fields(self):
        """Test creacion con todos los campos"""
        approval = ColorApproval.objects.create(
            project=self.project,
            color_name="Full Client",
            color_code="FC-001",
            brand="Test Brand",
            location="Room 1",
            status="APPROVED",
        )

        assert approval.color_name == "Full Client"
        assert approval.color_code == "FC-001"
        assert approval.brand == "Test Brand"
        assert approval.location == "Room 1"
        assert approval.status == "APPROVED"

    def test_color_approval_status_choices(self):
        """Test que ColorApproval respeta choices de status"""
        valid_statuses = ["PENDING", "APPROVED", "REJECTED"]

        for status in valid_statuses:
            approval = ColorApproval.objects.create(
                project=self.project,
                color_name=f"Color {status}",
                status=status,
            )
            assert approval.status == status

    def test_multiple_approvals_per_project(self):
        """Test que un proyecto puede tener multiples aprobaciones"""
        approval1 = ColorApproval.objects.create(
            project=self.project,
            color_name="Color 1",
            status="PENDING",
        )

        approval2 = ColorApproval.objects.create(
            project=self.project,
            color_name="Color 2",
            status="APPROVED",
        )

        approvals = ColorApproval.objects.filter(project=self.project)
        assert approvals.count() == 2


@pytest.mark.django_db
class ColorSampleRejectByTokenTests(TestCase):
    """Public 'decline with reason' flow through the shareable token link.

    An external owner/designer opens the copied link (no login) and either
    approves or says "this isn't the right color". These tests cover the
    reject branch added to the public signing view.
    """

    def setUp(self):
        self.project = Project.objects.create(
            name="Reject Token Project",
            address="123 Test St",
            start_date=date(2025, 1, 1),
        )
        self.sample = ColorSample.objects.create(
            project=self.project,
            name="Test Green",
            code="GREEN-001",
            brand="Benjamin Moore",
            finish="Matte",
            status="review",
        )
        self.token = self.sample.generate_signature_token()
        self.url = reverse(
            "color_sample_client_signature_token",
            args=[self.sample.id, self.token],
        )

    def test_reject_with_reason_sets_status_and_renders_feedback(self):
        """A valid reason rejects the sample and shows the feedback page."""
        resp = self.client.post(self.url, {"action": "reject", "reason": "Too dark"})

        assert resp.status_code == 200
        self.sample.refresh_from_db()
        assert self.sample.status == "rejected"
        assert "Too dark" in (self.sample.rejection_reason or "")
        # Reason is also mirrored into the timeline notes for the PM.
        assert "Too dark" in (self.sample.client_notes or "")
        # Standalone English feedback page is rendered (not the form).
        assert b"Thanks for the feedback" in resp.content
        assert b"Too dark" in resp.content

    def test_reject_without_reason_rerenders_form_with_error(self):
        """No reason = nothing happens; the form re-renders with a prompt."""
        resp = self.client.post(self.url, {"action": "reject", "reason": ""})

        assert resp.status_code == 200
        self.sample.refresh_from_db()
        # Status untouched — we never reject without a reason.
        assert self.sample.status == "review"
        assert b"Please pick a reason" in resp.content

    def test_reject_with_invalid_token_is_forbidden(self):
        """A tampered token cannot reject the sample."""
        bad_url = reverse(
            "color_sample_client_signature_token",
            args=[self.sample.id, "not-the-real-token"],
        )
        resp = self.client.post(bad_url, {"action": "reject", "reason": "Too dark"})

        assert resp.status_code == 403
        self.sample.refresh_from_db()
        assert self.sample.status == "review"
