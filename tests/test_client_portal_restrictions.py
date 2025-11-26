import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from datetime import date
from core.models import Project, ClientProjectAccess

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def staff(db):
    return User.objects.create_user(username='staff', password='pass', is_staff=True)

@pytest.fixture
def client_user(db):
    return User.objects.create_user(username='client', password='pass', is_staff=False)

@pytest.fixture
def project_a(db):
    return Project.objects.create(name='ProjA', client='ACME', start_date=date.today(), address='A')

@pytest.fixture
def project_b(db):
    return Project.objects.create(name='ProjB', client='ACME', start_date=date.today(), address='B')

@pytest.mark.django_db
def test_client_visibility_restricted_to_access(api_client, client_user, project_a, project_b):
    # Grant access only to project A
    ClientProjectAccess.objects.create(user=client_user, project=project_a, role='client')

    api_client.force_authenticate(user=client_user)

    # Create CR in project A (allowed)
    res_a = api_client.post('/api/v1/client-requests/', {
        'project': project_a.id,
        'title': 'Info A',
        'description': 'A',
        'request_type': 'info'
    }, format='json')
    assert res_a.status_code in (200, 201)

    # Attempt create in project B (forbidden)
    res_b = api_client.post('/api/v1/client-requests/', {
        'project': project_b.id,
        'title': 'Info B',
        'description': 'B',
        'request_type': 'info'
    }, format='json')
    assert res_b.status_code == 403

    # Listing should only show project A requests
    lst = api_client.get('/api/v1/client-requests/')
    assert lst.status_code == 200
    assert all(r['project'] == project_a.id for r in lst.data)

@pytest.mark.django_db
def test_staff_sees_all(api_client, staff, project_a, project_b):
    api_client.force_authenticate(user=staff)

    # Create CRs in both projects
    res_a = api_client.post('/api/v1/client-requests/', {
        'project': project_a.id,
        'title': 'Staff A',
        'description': 'A',
        'request_type': 'info'
    }, format='json')
    res_b = api_client.post('/api/v1/client-requests/', {
        'project': project_b.id,
        'title': 'Staff B',
        'description': 'B',
        'request_type': 'info'
    }, format='json')
    assert res_a.status_code in (200, 201) and res_b.status_code in (200, 201)

    # Staff listing returns both
    lst = api_client.get('/api/v1/client-requests/')
    assert lst.status_code == 200
    projects = set(r['project'] for r in lst.data)
    assert project_a.id in projects and project_b.id in projects
