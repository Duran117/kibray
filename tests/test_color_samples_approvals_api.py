import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from datetime import date
from core.models import Project, ColorSample

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    return User.objects.create_user(username='approver', password='pass123', email='a@example.com', is_staff=True)

@pytest.fixture
def project(db):
    return Project.objects.create(name='ColorsProj', client='ACME', start_date=date.today(), address='123 Main St')

@pytest.mark.django_db
def test_color_sample_submit_and_approve(api_client, user, project):
    api_client.force_authenticate(user=user)
    # Create sample
    sample = ColorSample.objects.create(project=project, name='Ocean Blue', code='SW-123', brand='Sherwin')
    # Approve
    res = api_client.post(f'/api/v1/color-samples/{sample.id}/approve/', {'signature_ip': '203.0.113.10'}, format='json')
    assert res.status_code in (200, 201)
    data = res.data
    assert data['status'] == 'approved'
    assert data['approved_by'] == user.id
    assert data['approval_ip'] == '203.0.113.10'
    assert data['sample_number'].startswith('ACMEM')  # KPISM-like numbering

@pytest.mark.django_db
def test_color_sample_reject_requires_reason(api_client, user, project):
    api_client.force_authenticate(user=user)
    sample = ColorSample.objects.create(project=project, name='Sunset', code='MS-77', brand='Milesi')
    # Missing reason should fail validation
    res = api_client.post(f'/api/v1/color-samples/{sample.id}/reject/', {}, format='json')
    assert res.status_code == 400
    # Provide reason
    res2 = api_client.post(f'/api/v1/color-samples/{sample.id}/reject/', {'reason': 'Does not match spec'}, format='json')
    assert res2.status_code in (200, 201)
    assert res2.data['status'] == 'rejected'
    assert res2.data['rejection_reason'] == 'Does not match spec'
