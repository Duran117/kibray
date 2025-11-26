import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date
from core.models import Project

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    return User.objects.create_user(username='client_attach_user', password='pass123', email='u@example.com', is_staff=True)

@pytest.fixture
def project(db):
    return Project.objects.create(name='ClientAttachProj', client='ACME', start_date=date.today(), address='123 Main St')

@pytest.mark.django_db
def test_client_request_attachments_upload_and_list(api_client, user, project):
    api_client.force_authenticate(user=user)

    # Create a client request
    res = api_client.post('/api/v1/client-requests/', {
        'project': project.id,
        'title': 'Specs upload',
        'description': 'Please see attached specs',
        'request_type': 'info'
    }, format='json')
    assert res.status_code in (200, 201)
    cr_id = res.data['id']

    # Upload attachment
    file_content = b"test file contents"
    upload = SimpleUploadedFile('specs.txt', file_content, content_type='text/plain')
    up = api_client.post('/api/v1/client-request-attachments/', {
        'request': cr_id,
        'file': upload,
        'filename': 'specs.txt',
        'content_type': 'text/plain'
    }, format='multipart')
    assert up.status_code in (200, 201)

    # List attachments
    lst = api_client.get(f'/api/v1/client-request-attachments/?request={cr_id}')
    assert lst.status_code == 200
    assert isinstance(lst.data, list)
    assert any(a['filename'] == 'specs.txt' for a in lst.data)

    # Verify attachments show up in client request detail
    detail = api_client.get(f'/api/v1/client-requests/{cr_id}/')
    assert detail.status_code == 200
    assert any(a['filename'] == 'specs.txt' for a in detail.data.get('attachments', []))
