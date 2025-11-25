from datetime import date
import io
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Project, Task

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    return User.objects.create_user(username='pm28', password='pass123', email='pm28@example.com')

@pytest.fixture
def project(db):
    return Project.objects.create(name='TouchUp Project', client='ACME', start_date=date.today())


def test_cannot_complete_touchup_without_photo(api_client, user, project):
    api_client.force_authenticate(user=user)
    # Create a touch-up task
    t = Task.objects.create(project=project, title='Fix scratch', is_touchup=True, status='Pendiente', created_by=user)
    # Try to complete without photo
    resp = api_client.post(f'/api/v1/tasks/{t.id}/update_status/', {'status': 'Completada'}, format='json')
    assert resp.status_code == 400
    assert 'requires a photo' in resp.data['error']


def test_complete_touchup_after_photo(api_client, user, project):
    api_client.force_authenticate(user=user)
    t = Task.objects.create(project=project, title='Fix dent', is_touchup=True, status='Pendiente', created_by=user)
    # Upload a small fake image
    image_content = SimpleUploadedFile('test.jpg', b'\xff\xd8\xff\xe0' + b'0'*100, content_type='image/jpeg')
    up = api_client.post(f'/api/v1/tasks/{t.id}/add_image/', {'image': image_content, 'caption': 'after'}, format='multipart')
    assert up.status_code in (200, 201)
    # Now complete
    resp = api_client.post(f'/api/v1/tasks/{t.id}/update_status/', {'status': 'Completada'}, format='json')
    assert resp.status_code == 200
