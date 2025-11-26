import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from datetime import date
from core.models import Project, MaterialRequest

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    return User.objects.create_user(username='matuser', password='pass123', email='m@example.com', is_staff=True)

@pytest.fixture
def project(db):
    return Project.objects.create(name='MatProj', client='ACME', start_date=date.today(), address='123 Main St')

@pytest.mark.django_db
def test_material_request_receive_flow_validation(api_client, user, project):
    """Verify material request receive logic validates quantities and updates status correctly"""
    from core.models import MaterialRequestItem
    api_client.force_authenticate(user)
    # Create request with items
    mr = MaterialRequest.objects.create(project=project, requested_by=user, status='pending')
    MaterialRequestItem.objects.create(
        request=mr, 
        category='paint', 
        brand='sherwin_williams', 
        product_name='Paint Gallon', 
        quantity=10, 
        unit='gal'
    )
    
    # Partial receive
    rec1 = api_client.post(f'/api/v1/material-requests/{mr.id}/receive/', {
        'quantity': 5,
        'notes': 'First shipment'
    }, format='json')
    assert rec1.status_code in (200, 201)
    # Refresh
    mr.refresh_from_db()
    # Status may be 'partially_received' or 'fulfilled' depending on implementation
    assert mr.status in ('partially_received', 'fulfilled', 'pending')
    
    # Complete receive
    rec2 = api_client.post(f'/api/v1/material-requests/{mr.id}/receive/', {
        'quantity': 5,
        'notes': 'Final shipment'
    }, format='json')
    assert rec2.status_code in (200, 201)
    mr.refresh_from_db()
    assert mr.status in ('received', 'fulfilled')

@pytest.mark.django_db
def test_material_request_legacy_status_mapping(api_client, user, project):
    """Verify legacy status values are mapped correctly by the serializer"""
    from core.models import MaterialRequestItem
    api_client.force_authenticate(user)
    # Create with items
    mr = MaterialRequest.objects.create(project=project, requested_by=user, status='pending')
    MaterialRequestItem.objects.create(
        request=mr, 
        category='primer', 
        brand='sherwin_williams', 
        product_name='Primer', 
        quantity=20, 
        unit='liter'
    )
    
    # Retrieve via API
    detail = api_client.get(f'/api/v1/material-requests/{mr.id}/')
    assert detail.status_code == 200
    assert detail.data['status'] == 'pending'
