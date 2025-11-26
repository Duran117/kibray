"""
Comprehensive tests for Chat API - MÓDULO 22 (Communication)

Tests cover:
- ChatChannel CRUD operations
- ChatMessage CRUD with @mentions
- Entity linking (tasks, damages, etc.)
- File attachments
- Soft deletion (admin only)
- Permissions (ClientProjectAccess enforcement)
- Mention notifications
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from datetime import date
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import (
    Project, ChatChannel, ChatMessage, ChatMention, Notification, 
    ClientProjectAccess, Task, DamageReport
)

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user(db):
    return User.objects.create_user(username='admin', password='x', is_staff=True)

@pytest.fixture
def regular_user(db):
    return User.objects.create_user(username='alice', password='x', is_staff=False)

@pytest.fixture
def mentioned_user(db):
    return User.objects.create_user(username='bob', password='x', is_staff=False)

@pytest.fixture
def project(db):
    return Project.objects.create(
        name='ChatTestProject', 
        client='ACME', 
        start_date=date.today(),
        address='123 Test St'
    )

@pytest.fixture
def project_access(db, regular_user, project):
    """Grant regular_user access to project"""
    return ClientProjectAccess.objects.create(
        user=regular_user, 
        project=project, 
        role='client'
    )

@pytest.fixture
def channel(db, project, admin_user):
    ch = ChatChannel.objects.create(
        name='General',
        project=project,
        created_by=admin_user
    )
    ch.participants.add(admin_user)
    return ch


# ==================== ChatChannel Tests ====================

@pytest.mark.django_db
def test_chat_channel_crud(api_client, admin_user, project):
    """Test CRUD operations for ChatChannel"""
    api_client.force_authenticate(user=admin_user)
    
    # CREATE
    res = api_client.post('/api/v1/chat/channels/', {
        'project': project.id,
        'name': 'Dev Team',
        'channel_type': 'group'
    }, format='json')
    assert res.status_code in (200, 201)
    channel_id = res.data['id']
    assert res.data['name'] == 'Dev Team'
    assert res.data['project_name'] == 'ChatTestProject'
    
    # READ
    res = api_client.get(f'/api/v1/chat/channels/{channel_id}/')
    assert res.status_code == 200
    assert res.data['name'] == 'Dev Team'
    
    # UPDATE
    res = api_client.patch(f'/api/v1/chat/channels/{channel_id}/', {
        'name': 'Development Team'
    }, format='json')
    assert res.status_code == 200
    assert res.data['name'] == 'Development Team'
    
    # DELETE
    res = api_client.delete(f'/api/v1/chat/channels/{channel_id}/')
    assert res.status_code == 204


@pytest.mark.django_db
def test_channel_add_remove_participants(api_client, admin_user, regular_user, channel):
    """Test adding/removing participants to channel"""
    api_client.force_authenticate(user=admin_user)
    
    # Add participant
    res = api_client.post(f'/api/v1/chat/channels/{channel.id}/add_participant/', {
        'user_id': regular_user.id
    }, format='json')
    assert res.status_code == 200
    assert 'success' in res.data
    
    # Verify participant added
    channel.refresh_from_db()
    assert regular_user in channel.participants.all()
    
    # Remove participant
    res = api_client.post(f'/api/v1/chat/channels/{channel.id}/remove_participant/', {
        'user_id': regular_user.id
    }, format='json')
    assert res.status_code == 200
    
    # Verify participant removed
    channel.refresh_from_db()
    assert regular_user not in channel.participants.all()


@pytest.mark.django_db
def test_channel_access_restriction_by_project(api_client, regular_user, project, project_access, admin_user):
    """Non-staff users only see channels for projects they have access to"""
    # Create channel in project user has access to
    ch1 = ChatChannel.objects.create(name='Allowed', project=project, created_by=admin_user)
    
    # Create another project without access
    project2 = Project.objects.create(name='Forbidden', client='XYZ', start_date=date.today(), address='456')
    ch2 = ChatChannel.objects.create(name='NotAllowed', project=project2, created_by=admin_user)
    
    api_client.force_authenticate(user=regular_user)
    
    # List channels
    res = api_client.get('/api/v1/chat/channels/')
    assert res.status_code == 200
    
    # Access results from paginated response or list
    data = res.data.get('results', res.data) if isinstance(res.data, dict) else res.data
    channel_ids = [ch['id'] for ch in data]
    assert ch1.id in channel_ids
    assert ch2.id not in channel_ids  # Should not see channels from projects without access


# ==================== ChatMessage Tests ====================

@pytest.mark.django_db
def test_chat_message_crud(api_client, admin_user, channel):
    """Test CRUD operations for ChatMessage"""
    api_client.force_authenticate(user=admin_user)
    
    # CREATE
    res = api_client.post('/api/v1/chat/messages/', {
        'channel': channel.id,
        'message': 'Hello team!',
    }, format='json')
    assert res.status_code in (200, 201)
    msg_id = res.data['id']
    assert res.data['message'] == 'Hello team!'
    assert res.data['user_username'] == 'admin'
    
    # READ
    res = api_client.get(f'/api/v1/chat/messages/{msg_id}/')
    assert res.status_code == 200
    assert res.data['message'] == 'Hello team!'
    
    # UPDATE
    res = api_client.patch(f'/api/v1/chat/messages/{msg_id}/', {
        'message': 'Hello team! Updated.'
    }, format='json')
    assert res.status_code == 200
    assert 'Updated' in res.data['message']


@pytest.mark.django_db
def test_mention_parsing_user(api_client, admin_user, mentioned_user, channel):
    """Test @username mention parsing and notification creation"""
    api_client.force_authenticate(user=admin_user)
    
    # Send message with @mention
    res = api_client.post('/api/v1/chat/messages/', {
        'channel': channel.id,
        'message': 'Hey @bob, check this out!',
    }, format='json')
    assert res.status_code in (200, 201)
    msg_id = res.data['id']
    
    # Verify mention was created
    mentions = ChatMention.objects.filter(message_id=msg_id)
    assert mentions.count() == 1
    mention = mentions.first()
    assert mention.mentioned_user == mentioned_user
    assert mention.entity_type == 'user'
    
    # Verify notification was created for mentioned user
    notif = Notification.objects.filter(
        user=mentioned_user,
        notification_type='chat_message'
    )
    assert notif.exists()
    assert 'mentioned you' in notif.first().title


@pytest.mark.django_db
def test_mention_parsing_entity_linking(api_client, admin_user, channel, project):
    """Test entity linking mentions like @task#123"""
    # Create a task to reference (without assigned_to since it requires Employee)
    task = Task.objects.create(
        project=project,
        title='Paint walls'
    )
    
    api_client.force_authenticate(user=admin_user)
    
    # Send message with entity link
    res = api_client.post('/api/v1/chat/messages/', {
        'channel': channel.id,
        'message': f'Check out @task#{task.id} for details',
    }, format='json')
    assert res.status_code in (200, 201)
    msg_id = res.data['id']
    
    # Verify mention was created with entity linking
    mentions = ChatMention.objects.filter(message_id=msg_id)
    assert mentions.count() == 1
    mention = mentions.first()
    assert mention.entity_type == 'task'
    assert mention.entity_id == task.id
    assert 'Paint walls' in mention.entity_label


@pytest.mark.django_db
def test_mention_multiple_types(api_client, admin_user, mentioned_user, channel, project):
    """Test message with both user mentions and entity links"""
    task = Task.objects.create(project=project, title='Fix bug')
    
    api_client.force_authenticate(user=admin_user)
    
    res = api_client.post('/api/v1/chat/messages/', {
        'channel': channel.id,
        'message': f'@bob please review @task#{task.id} asap',
    }, format='json')
    assert res.status_code in (200, 201)
    msg_id = res.data['id']
    
    # Should have 2 mentions: 1 user + 1 task
    mentions = ChatMention.objects.filter(message_id=msg_id)
    assert mentions.count() == 2
    
    entity_types = list(mentions.values_list('entity_type', flat=True))
    assert 'user' in entity_types
    assert 'task' in entity_types


@pytest.mark.django_db
def test_chat_message_with_image_attachment(api_client, admin_user, channel):
    """Test uploading image with chat message"""
    api_client.force_authenticate(user=admin_user)
    
    # Create a minimal 1x1 PNG image (valid format)
    import base64
    # 1x1 transparent PNG
    png_data = base64.b64decode(
        b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
    )
    upload = SimpleUploadedFile('photo.png', png_data, content_type='image/png')
    
    res = api_client.post('/api/v1/chat/messages/', {
        'channel': str(channel.id),
        'message': 'Check out this photo',
        'image': upload
    }, format='multipart')
    assert res.status_code in (200, 201), f"Response: {res.data}"
    
    # Verify image was saved
    msg = ChatMessage.objects.get(id=res.data['id'])
    assert msg.image
    assert 'photo' in msg.image.name


@pytest.mark.django_db
def test_chat_message_with_file_attachment(api_client, admin_user, channel):
    """Test uploading file attachment with chat message"""
    api_client.force_authenticate(user=admin_user)
    
    # Create PDF file
    file_content = b"fake pdf content"
    upload = SimpleUploadedFile('report.pdf', file_content, content_type='application/pdf')
    
    res = api_client.post('/api/v1/chat/messages/', {
        'channel': channel.id,
        'message': 'Report attached',
        'attachment': upload
    }, format='multipart')
    assert res.status_code in (200, 201)
    
    # Verify attachment was saved
    msg = ChatMessage.objects.get(id=res.data['id'])
    assert msg.attachment
    assert 'report' in msg.attachment.name


@pytest.mark.django_db
def test_soft_delete_admin_only(api_client, admin_user, regular_user, channel, project, project_access):
    """Test that only admins can soft-delete messages"""
    # Grant regular_user access to project so they can see messages
    # (project_access fixture already does this)
    
    # Create message
    api_client.force_authenticate(user=admin_user)
    res = api_client.post('/api/v1/chat/messages/', {
        'channel': channel.id,
        'message': 'Message to delete',
    }, format='json')
    msg_id = res.data['id']
    
    # Try to delete as regular user (should fail with 403 Forbidden)
    api_client.force_authenticate(user=regular_user)
    res = api_client.post(f'/api/v1/chat/messages/{msg_id}/soft_delete/')
    # May be 403 (Forbidden) or 404 (Not Found due to queryset filtering)
    assert res.status_code in (403, 404)
    
    # Verify message not deleted
    msg = ChatMessage.objects.get(id=msg_id)
    assert not msg.is_deleted
    
    # Delete as admin (should succeed)
    api_client.force_authenticate(user=admin_user)
    res = api_client.post(f'/api/v1/chat/messages/{msg_id}/soft_delete/')
    assert res.status_code == 200
    
    # Verify message soft-deleted
    msg.refresh_from_db()
    assert msg.is_deleted
    assert msg.deleted_by == admin_user
    assert msg.deleted_at is not None


@pytest.mark.django_db
def test_soft_deleted_messages_hidden(api_client, admin_user, channel):
    """Test that soft-deleted messages show as [deleted]"""
    api_client.force_authenticate(user=admin_user)
    
    # Create and soft-delete message
    res = api_client.post('/api/v1/chat/messages/', {
        'channel': channel.id,
        'message': 'Secret message',
    }, format='json')
    msg_id = res.data['id']
    
    api_client.post(f'/api/v1/chat/messages/{msg_id}/soft_delete/')
    
    # Retrieve message
    res = api_client.get(f'/api/v1/chat/messages/{msg_id}/')
    assert res.status_code == 200
    assert res.data['message_display'] == '[Message deleted]'
    assert res.data['is_deleted'] is True


@pytest.mark.django_db
def test_my_mentions_endpoint(api_client, admin_user, mentioned_user, channel, project):
    """Test /my_mentions/ endpoint returns messages where user is mentioned"""
    # Grant mentioned_user access to project so they can see messages
    ClientProjectAccess.objects.create(user=mentioned_user, project=project, role='client')
    
    # Create messages with and without mentions
    api_client.force_authenticate(user=admin_user)
    
    # Message 1: mentions bob
    res1 = api_client.post('/api/v1/chat/messages/', {
        'channel': channel.id,
        'message': '@bob please review',
    }, format='json')
    
    # Message 2: no mentions
    res2 = api_client.post('/api/v1/chat/messages/', {
        'channel': channel.id,
        'message': 'General message',
    }, format='json')
    
    # Message 3: mentions bob again
    res3 = api_client.post('/api/v1/chat/messages/', {
        'channel': channel.id,
        'message': '@bob urgent',
    }, format='json')
    
    # Switch to bob and query my_mentions
    api_client.force_authenticate(user=mentioned_user)
    res = api_client.get('/api/v1/chat/messages/my_mentions/')
    assert res.status_code == 200
    
    # Handle paginated or list response
    data = res.data.get('results', res.data) if isinstance(res.data, dict) else res.data
    msg_ids = [msg['id'] for msg in data]
    assert res1.data['id'] in msg_ids
    assert res3.data['id'] in msg_ids
    assert res2.data['id'] not in msg_ids


@pytest.mark.django_db
def test_message_access_restriction_by_project(api_client, regular_user, project, project_access, admin_user):
    """Non-staff users only see messages from projects they have access to"""
    # Create channel and message in project user has access to
    ch1 = ChatChannel.objects.create(name='Allowed', project=project, created_by=admin_user)
    msg1 = ChatMessage.objects.create(channel=ch1, user=admin_user, message='Allowed msg')
    
    # Create another project without access
    project2 = Project.objects.create(name='Forbidden', client='XYZ', start_date=date.today(), address='456')
    ch2 = ChatChannel.objects.create(name='NotAllowed', project=project2, created_by=admin_user)
    msg2 = ChatMessage.objects.create(channel=ch2, user=admin_user, message='Forbidden msg')
    
    api_client.force_authenticate(user=regular_user)
    
    # List messages
    res = api_client.get('/api/v1/chat/messages/')
    assert res.status_code == 200
    
    # Handle paginated or list response
    data = res.data.get('results', res.data) if isinstance(res.data, dict) else res.data
    msg_ids = [msg['id'] for msg in data]
    assert msg1.id in msg_ids
    assert msg2.id not in msg_ids  # Should not see messages from projects without access


@pytest.mark.django_db
def test_filter_messages_by_channel(api_client, admin_user, project):
    """Test filtering messages by channel"""
    ch1 = ChatChannel.objects.create(name='Ch1', project=project, created_by=admin_user)
    ch2 = ChatChannel.objects.create(name='Ch2', project=project, created_by=admin_user)
    
    ChatMessage.objects.create(channel=ch1, user=admin_user, message='Msg1')
    ChatMessage.objects.create(channel=ch2, user=admin_user, message='Msg2')
    ChatMessage.objects.create(channel=ch1, user=admin_user, message='Msg3')
    
    api_client.force_authenticate(user=admin_user)
    
    # Filter by ch1
    res = api_client.get(f'/api/v1/chat/messages/?channel={ch1.id}')
    assert res.status_code == 200
    results = res.data.get('results', res.data)
    assert len(results) == 2
    
    # Filter by ch2
    res = api_client.get(f'/api/v1/chat/messages/?channel={ch2.id}')
    assert res.status_code == 200
    results = res.data.get('results', res.data)
    assert len(results) == 1


@pytest.mark.django_db
def test_filter_messages_by_user(api_client, admin_user, regular_user, channel):
    """Test filtering messages by user"""
    ChatMessage.objects.create(channel=channel, user=admin_user, message='Admin msg 1')
    ChatMessage.objects.create(channel=channel, user=regular_user, message='User msg')
    ChatMessage.objects.create(channel=channel, user=admin_user, message='Admin msg 2')
    
    api_client.force_authenticate(user=admin_user)
    
    # Filter by admin
    res = api_client.get(f'/api/v1/chat/messages/?user={admin_user.id}')
    assert res.status_code == 200
    results = res.data.get('results', res.data)
    assert len(results) == 2
    
    # Filter by regular_user
    res = api_client.get(f'/api/v1/chat/messages/?user={regular_user.id}')
    assert res.status_code == 200
    results = res.data.get('results', res.data)
    assert len(results) == 1


@pytest.mark.django_db
def test_mentions_serializer_includes_data(api_client, admin_user, mentioned_user, channel):
    """Test that ChatMessageSerializer includes mentions data"""
    api_client.force_authenticate(user=admin_user)
    
    res = api_client.post('/api/v1/chat/messages/', {
        'channel': channel.id,
        'message': '@bob check this',
    }, format='json')
    assert res.status_code in (200, 201)
    
    # GET message and verify mentions field
    msg_id = res.data['id']
    res = api_client.get(f'/api/v1/chat/messages/{msg_id}/')
    assert res.status_code == 200
    
    assert 'mentions' in res.data
    assert len(res.data['mentions']) == 1
    mention = res.data['mentions'][0]
    assert mention['mentioned_username'] == 'bob'
    assert mention['entity_type'] == 'user'
