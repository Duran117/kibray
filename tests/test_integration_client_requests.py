import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from datetime import date
from core.models import Project, ClientRequest, ClientProjectAccess

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def staff_user(db):
    return User.objects.create_user(username='staff', password='pass123', email='s@example.com', is_staff=True)

@pytest.fixture
def client_user(db):
    u = User.objects.create_user(username='client', password='pass123', email='c@example.com', is_staff=False)
    from core.models import Profile
    Profile.objects.get_or_create(user=u, defaults={'role': 'client'})
    return u

@pytest.fixture
def project(db):
    return Project.objects.create(name='IntegProj', client='ACME', start_date=date.today(), address='123 Main St')

@pytest.mark.django_db
def test_client_request_access_isolation(api_client, client_user, staff_user, project):
    """Verify client users can only see requests for projects they have access to"""
    # Create access for client to project
    ClientProjectAccess.objects.create(user=client_user, project=project, role='client')
    # Staff creates a request
    api_client.force_authenticate(staff_user)
    res1 = api_client.post('/api/v1/client-requests/', {
        'project': project.id,
        'request_type': 'info',
        'title': 'Staff request',
        'description': 'Internal query'
    }, format='json')
    assert res1.status_code in (200, 201)
    
    # Client can see it
    api_client.force_authenticate(client_user)
    lst = api_client.get('/api/v1/client-requests/')
    assert lst.status_code == 200
    assert len(lst.data) >= 1
    
    # Create another project without client access
    other_proj = Project.objects.create(name='OtherProj', client='XYZ', start_date=date.today())
    api_client.force_authenticate(staff_user)
    res2 = api_client.post('/api/v1/client-requests/', {
        'project': other_proj.id,
        'request_type': 'material',
        'title': 'Other request',
        'description': 'Different project'
    }, format='json')
    assert res2.status_code in (200, 201)
    
    # Client should not see the other project request
    api_client.force_authenticate(client_user)
    lst2 = api_client.get('/api/v1/client-requests/')
    assert lst2.status_code == 200
    visible_projects = {r['project'] for r in lst2.data}
    assert other_proj.id not in visible_projects

@pytest.mark.django_db
def test_client_request_status_transitions(api_client, staff_user, project):
    """Verify request approval/rejection actions work and update status"""
    api_client.force_authenticate(staff_user)
    res = api_client.post('/api/v1/client-requests/', {
        'project': project.id,
        'request_type': 'change_order',
        'title': 'Add feature',
        'description': 'Extra work requested'
    }, format='json')
    assert res.status_code in (200, 201)
    rid = res.data['id']
    
    # Approve
    approve = api_client.post(f'/api/v1/client-requests/{rid}/approve/', {}, format='json')
    assert approve.status_code in (200, 201)
    assert approve.data['status'] == 'approved'
    
    # Create another and reject
    res2 = api_client.post('/api/v1/client-requests/', {
        'project': project.id,
        'request_type': 'material',
        'title': 'Wrong material',
        'description': 'Not feasible'
    }, format='json')
    rid2 = res2.data['id']
    reject = api_client.post(f'/api/v1/client-requests/{rid2}/reject/', {'reason': 'Out of scope'}, format='json')
    assert reject.status_code in (200, 201)
    assert reject.data['status'] == 'rejected'
