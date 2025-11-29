"""
Tests for Change Order Customer Signature functionality.
"""
import pytest
import base64
from datetime import date
from decimal import Decimal
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Project, ChangeOrder


@pytest.fixture
def project(db):
    """Create a test project."""
    return Project.objects.create(
        name="Test Project",
        client="Test Client",
        start_date=date(2024, 1, 1),
        budget_labor=Decimal("100000.00"),
        budget_materials=Decimal("50000.00")
    )


@pytest.fixture
def fixed_change_order(db, project):
    """Create a FIXED price Change Order."""
    return ChangeOrder.objects.create(
        project=project,
        description="Fixed price work - Paint entire house",
        amount=Decimal("5000.00"),
        pricing_type='FIXED',
        status='sent'
    )


@pytest.fixture
def tm_change_order(db, project):
    """Create a T&M Change Order."""
    return ChangeOrder.objects.create(
        project=project,
        description="Time & Materials work - Kitchen remodel",
        amount=Decimal("0.00"),
        pricing_type='T_AND_M',
        billing_hourly_rate=Decimal("85.00"),
        material_markup_pct=Decimal("25.00"),
        status='sent'
    )


@pytest.fixture
def signature_data():
    """Create a sample signature image as base64."""
    # Create a small 1x1 PNG image
    png_data = base64.b64encode(
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01\x00\x00'
        b'\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    ).decode('utf-8')
    return f"data:image/png;base64,{png_data}"


@pytest.mark.django_db
class TestCustomerSignatureView:
    """Tests for the customer signature view."""

    def test_signature_view_accessible_without_login(self, client, fixed_change_order):
        """Test that signature view is accessible without authentication."""
        url = reverse('changeorder_customer_signature', args=[fixed_change_order.id])
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'changeorder' in response.context
        assert response.context['changeorder'] == fixed_change_order

    def test_fixed_price_displays_amount(self, client, fixed_change_order):
        """Test that FIXED price CO displays the fixed amount."""
        url = reverse('changeorder_customer_signature', args=[fixed_change_order.id])
        response = client.get(url)
        
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'Precio Fijo' in content
        assert '5000' in content  # Amount is shown somewhere
        assert 'Acuerdo de Precio Fijo' in content

    def test_tm_displays_rates(self, client, tm_change_order):
        """Test that T&M CO displays hourly rate and markup."""
        url = reverse('changeorder_customer_signature', args=[tm_change_order.id])
        response = client.get(url)
        
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'Tiempo y Materiales' in content
        assert '85' in content  # Hourly rate is shown
        assert '25' in content  # Markup percentage is shown
        assert 'Acuerdo de Tiempo y Materiales' in content

    def test_signature_submission_success(self, client, fixed_change_order, signature_data):
        """Test successful signature submission."""
        url = reverse('changeorder_customer_signature', args=[fixed_change_order.id])
        
        response = client.post(url, {
            'signature_data': signature_data,
            'signer_name': 'John Doe'
        })
        
        assert response.status_code == 200
        
        # Refresh from database
        fixed_change_order.refresh_from_db()
        
        # Check that signature was saved
        assert fixed_change_order.signed_by == 'John Doe'
        assert fixed_change_order.signed_at is not None
        assert fixed_change_order.signature_image is not None
        assert fixed_change_order.status == 'approved'

    def test_signature_submission_without_name_fails(self, client, fixed_change_order, signature_data):
        """Test that submission without name shows error."""
        url = reverse('changeorder_customer_signature', args=[fixed_change_order.id])
        
        response = client.post(url, {
            'signature_data': signature_data,
            'signer_name': ''
        })
        
        assert response.status_code == 200
        assert 'error' in response.context
        assert 'nombre' in response.context['error'].lower()

    def test_signature_submission_without_signature_fails(self, client, fixed_change_order):
        """Test that submission without signature data shows error."""
        url = reverse('changeorder_customer_signature', args=[fixed_change_order.id])
        
        response = client.post(url, {
            'signature_data': '',
            'signer_name': 'John Doe'
        })
        
        assert response.status_code == 200
        assert 'error' in response.context
        assert 'firma' in response.context['error'].lower()

    def test_already_signed_shows_message(self, client, fixed_change_order, signature_data):
        """Test that already signed CO shows appropriate message."""
        # First, sign the CO
        url = reverse('changeorder_customer_signature', args=[fixed_change_order.id])
        client.post(url, {
            'signature_data': signature_data,
            'signer_name': 'John Doe'
        })
        
        # Try to access signature page again
        response = client.get(url)
        
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'Ya Firmado' in content or 'ya ha sido firmado' in content

    def test_signature_success_page_shows_details(self, client, tm_change_order, signature_data):
        """Test that success page shows all relevant details."""
        url = reverse('changeorder_customer_signature', args=[tm_change_order.id])
        
        response = client.post(url, {
            'signature_data': signature_data,
            'signer_name': 'Jane Smith'
        })
        
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'Exitosa' in content or 'exitosa' in content
        assert 'Jane Smith' in content
        assert 'Tiempo y Materiales' in content

    def test_signature_creates_image_file(self, client, fixed_change_order, signature_data):
        """Test that signature creates an actual image file."""
        url = reverse('changeorder_customer_signature', args=[fixed_change_order.id])
        
        client.post(url, {
            'signature_data': signature_data,
            'signer_name': 'Test User'
        })
        
        fixed_change_order.refresh_from_db()
        
        # Check that image file exists
        assert fixed_change_order.signature_image
        assert fixed_change_order.signature_image.name
        assert 'signature_co_' in fixed_change_order.signature_image.name
        assert fixed_change_order.signature_image.name.endswith('.png')

    def test_multiple_cos_can_be_signed(self, client, fixed_change_order, tm_change_order, signature_data):
        """Test that multiple COs can be signed independently."""
        # Sign first CO
        url1 = reverse('changeorder_customer_signature', args=[fixed_change_order.id])
        client.post(url1, {
            'signature_data': signature_data,
            'signer_name': 'Person A'
        })
        
        # Sign second CO
        url2 = reverse('changeorder_customer_signature', args=[tm_change_order.id])
        client.post(url2, {
            'signature_data': signature_data,
            'signer_name': 'Person B'
        })
        
        # Check both are signed independently
        fixed_change_order.refresh_from_db()
        tm_change_order.refresh_from_db()
        
        assert fixed_change_order.signed_by == 'Person A'
        assert tm_change_order.signed_by == 'Person B'
        assert fixed_change_order.signature_image
        assert tm_change_order.signature_image

    def test_signature_url_with_token_parameter(self, client, fixed_change_order):
        """Test that URL with token parameter is accessible."""
        url = reverse('changeorder_customer_signature_token', 
                     args=[fixed_change_order.id, 'test-token-123'])
        response = client.get(url)
        
        # Should be accessible (token validation not implemented yet)
        assert response.status_code == 200
        assert 'changeorder' in response.context

    def test_signature_preserves_co_description(self, client, fixed_change_order, signature_data):
        """Test that signing doesn't modify CO description."""
        original_description = fixed_change_order.description
        url = reverse('changeorder_customer_signature', args=[fixed_change_order.id])
        
        client.post(url, {
            'signature_data': signature_data,
            'signer_name': 'Test User'
        })
        
        fixed_change_order.refresh_from_db()
        assert fixed_change_order.description == original_description

    def test_signature_preserves_pricing_details(self, client, tm_change_order, signature_data):
        """Test that signing doesn't modify pricing details."""
        original_rate = tm_change_order.billing_hourly_rate
        original_markup = tm_change_order.material_markup_pct
        
        url = reverse('changeorder_customer_signature', args=[tm_change_order.id])
        client.post(url, {
            'signature_data': signature_data,
            'signer_name': 'Test User'
        })
        
        tm_change_order.refresh_from_db()
        assert tm_change_order.billing_hourly_rate == original_rate
        assert tm_change_order.material_markup_pct == original_markup
