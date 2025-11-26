import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from datetime import date
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Project, ChatChannel, Notification

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def users(db):
    alice = User.objects.create_user(username='alice', password='x', is_staff=True)
    bob = User.objects.create_user(username='bob', password='x', is_staff=True)
    return alice, bob

@pytest.fixture
def project(db):
    return Project.objects.create(name='ChatProj', client='ACME', start_date=date.today(), address='A')

@pytest.fixture
def channel(db, project, users):
    alice, bob = users
    ch = ChatChannel.objects.create(name='General', project=project)
    ch.participants.add(alice)
    ch.participants.add(bob)
    return ch

@pytest.mark.django_db
def test_chat_mentions_create_notifications(api_client, users, channel):
    alice, bob = users
    api_client.force_authenticate(user=alice)
    res = api_client.post('/api/v1/chat/messages/', {
        'channel': channel.id,
        'message': 'Hello @bob, check this out',
    }, format='json')
    assert res.status_code in (200, 201)
    # Bob should get a chat_message notification
    assert Notification.objects.filter(user=bob, notification_type='chat_message').exists()

@pytest.mark.django_db
def test_chat_attachments_upload(api_client, users, channel):
    alice, _ = users
    api_client.force_authenticate(user=alice)
    file_content = b"report contents"
    upload = SimpleUploadedFile('report.pdf', file_content, content_type='application/pdf')
    res = api_client.post('/api/v1/chat/messages/', {
        'channel': channel.id,
        'message': 'Report attached',
        'attachment': upload
    }, format='multipart')
    assert res.status_code in (200, 201)
    # The message should have an attachment URL in representation
    msg = res.data
    assert 'attachment' in msg
