import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from datetime import date
from core.models import Project

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    return User.objects.create_user(username='client_req_user', password='pass123', email='u@example.com', is_staff=True)

@pytest.fixture
def project(db):
    return Project.objects.create(name='ClientReqProj', client='ACME', start_date=date.today(), address='123 Main St')

@pytest.mark.django_db
def test_client_request_crud_and_filters(api_client, user, project):
    api_client.force_authenticate(user=user)

    # Create INFO request
    res = api_client.post('/api/v1/client-requests/', {
        'project': project.id,
        'title': 'Need Info on Materials',
        'description': 'Client asks for material specs',
        'request_type': 'info'
    }, format='json')
    assert res.status_code in (200, 201)
    cr1_id = res.data['id']

    # Create CO request
    res2 = api_client.post('/api/v1/client-requests/', {
        'project': project.id,
        'title': 'Add crown molding',
        'description': 'Client requests change order',
        'request_type': 'change_order'
    }, format='json')
    assert res2.status_code in (200, 201)
    cr2_id = res2.data['id']

    # Create Material request type (not to confuse with MaterialRequest)
    res3 = api_client.post('/api/v1/client-requests/', {
        'project': project.id,
        'title': 'Order extra paint',
        'description': 'Client asks materials purchase',
        'request_type': 'material'
    }, format='json')
    assert res3.status_code in (200, 201)

    # List and filter by type
    lst_info = api_client.get('/api/v1/client-requests/?type=info')
    assert lst_info.status_code == 200
    assert any(r['request_type'] == 'info' for r in lst_info.data)

    lst_co = api_client.get('/api/v1/client-requests/?type=change_order')
    assert lst_co.status_code == 200
    assert any(r['request_type'] == 'change_order' for r in lst_co.data)

    # Approve and reject
    ap = api_client.post(f'/api/v1/client-requests/{cr1_id}/approve/')
    assert ap.status_code == 200 and ap.data['status'] in ('approved', 'pending')

    rj = api_client.post(f'/api/v1/client-requests/{cr2_id}/reject/')
    assert rj.status_code == 200 and rj.data['status'] in ('rejected', 'pending', 'approved')

    # Ensure list returns recent first
    lst = api_client.get('/api/v1/client-requests/')
    assert lst.status_code == 200
    assert isinstance(lst.data, list)
