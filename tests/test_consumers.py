"""
Unit tests for WebSocket consumers.
Tests real-time features including chat, notifications, and status.

Run with: pytest tests/test_consumers.py -v
"""

import pytest
import json
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.test import TestCase

from kibray_backend.asgi import application
from core.models import ChatChannel, ChatMessage, Project, UserStatus, NotificationLog

User = get_user_model()

pytestmark = pytest.mark.django_db(transaction=True)


@database_sync_to_async
def create_user(username="testuser", password="testpass123"):
    """Helper to create a test user"""
    return User.objects.create_user(username=username, password=password)


@database_sync_to_async
def create_project(name="Test Project"):
    """Helper to create a test project"""
    return Project.objects.create(name=name)


@database_sync_to_async
def get_chat_channel(project):
    """Helper to get or create chat channel"""
    channel, _ = ChatChannel.objects.get_or_create(
        project=project,
        defaults={"name": f"Project: {project.name}"}
    )
    return channel


@database_sync_to_async
def get_message_count(channel):
    """Helper to count messages in a channel"""
    return ChatMessage.objects.filter(channel=channel).count()


@database_sync_to_async
def get_user_status(user):
    """Helper to get user status"""
    return UserStatus.objects.filter(user=user).first()


class TestProjectChatConsumer:
    """Tests for ProjectChatConsumer"""
    
    @pytest.mark.asyncio
    async def test_connect_to_project_chat(self):
        """Test connecting to project chat room"""
        user = await create_user()
        project = await create_project()
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/project/{project.id}/",
        )
        communicator.scope["user"] = user
        
        connected, _ = await communicator.connect()
        assert connected
        
        # Should receive user_joined message
        response = await communicator.receive_json_from()
        assert response["type"] == "user_joined"
        
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_send_chat_message(self):
        """Test sending a chat message"""
        user = await create_user()
        project = await create_project()
        channel = await get_chat_channel(project)
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/project/{project.id}/",
        )
        communicator.scope["user"] = user
        
        await communicator.connect()
        await communicator.receive_json_from()  # user_joined
        
        # Send a message
        await communicator.send_json_to({
            "type": "message",
            "message": "Hello from test!",
            "attachments": []
        })
        
        # Should receive the broadcast message
        response = await communicator.receive_json_from()
        assert response["type"] == "message"
        assert response["message"] == "Hello from test!"
        assert response["username"] == user.username
        
        # Verify message was saved to database
        message_count = await get_message_count(channel)
        assert message_count == 1
        
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_typing_indicator(self):
        """Test typing indicator broadcast"""
        user = await create_user()
        project = await create_project()
        
        # Connect two users
        communicator1 = WebsocketCommunicator(
            application,
            f"/ws/chat/project/{project.id}/",
        )
        communicator1.scope["user"] = user
        
        user2 = await create_user(username="user2")
        communicator2 = WebsocketCommunicator(
            application,
            f"/ws/chat/project/{project.id}/",
        )
        communicator2.scope["user"] = user2
        
        await communicator1.connect()
        await communicator1.receive_json_from()  # user_joined
        
        await communicator2.connect()
        await communicator2.receive_json_from()  # user_joined
        await communicator1.receive_json_from()  # user2 joined
        
        # User1 starts typing
        await communicator1.send_json_to({
            "type": "typing",
            "is_typing": True
        })
        
        # User2 should receive typing indicator
        response = await communicator2.receive_json_from()
        assert response["type"] == "typing"
        assert response["username"] == user.username
        assert response["is_typing"] is True
        
        await communicator1.disconnect()
        await communicator2.disconnect()
    
    @pytest.mark.asyncio
    async def test_read_receipt(self):
        """Test read receipt functionality"""
        user = await create_user()
        project = await create_project()
        channel = await get_chat_channel(project)
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/project/{project.id}/",
        )
        communicator.scope["user"] = user
        
        await communicator.connect()
        await communicator.receive_json_from()  # user_joined
        
        # Send a message
        await communicator.send_json_to({
            "type": "message",
            "message": "Test message",
            "attachments": []
        })
        
        response = await communicator.receive_json_from()
        message_id = response["message_id"]
        
        # Send read receipt
        await communicator.send_json_to({
            "type": "read_receipt",
            "message_id": message_id
        })
        
        # Should receive read receipt broadcast
        response = await communicator.receive_json_from()
        assert response["type"] == "read_receipt"
        assert response["message_id"] == message_id
        
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting prevents spam"""
        user = await create_user()
        project = await create_project()
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/project/{project.id}/",
        )
        communicator.scope["user"] = user
        
        await communicator.connect()
        await communicator.receive_json_from()  # user_joined
        
        # Send messages rapidly (31 messages, limit is 30)
        for i in range(31):
            await communicator.send_json_to({
                "type": "message",
                "message": f"Message {i}",
                "attachments": []
            })
            
            # Receive first 30 messages
            if i < 30:
                response = await communicator.receive_json_from()
                assert response["type"] == "message"
        
        # 31st message should trigger rate limit error
        response = await communicator.receive_json_from()
        assert response["type"] == "error"
        assert response["error"] == "rate_limit_exceeded"
        
        await communicator.disconnect()


class TestStatusConsumer:
    """Tests for StatusConsumer"""
    
    @pytest.mark.asyncio
    async def test_connect_marks_user_online(self):
        """Test connecting marks user as online"""
        user = await create_user()
        
        communicator = WebsocketCommunicator(
            application,
            "/ws/status/",
        )
        communicator.scope["user"] = user
        
        connected, _ = await communicator.connect()
        assert connected
        
        # Should receive connection_established
        response = await communicator.receive_json_from()
        assert response["type"] == "connection_established"
        assert "online_users" in response
        
        # Verify user status was created and marked online
        status = await get_user_status(user)
        assert status is not None
        assert status.is_online is True
        
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_heartbeat_updates_timestamp(self):
        """Test heartbeat updates last_heartbeat"""
        user = await create_user()
        
        communicator = WebsocketCommunicator(
            application,
            "/ws/status/",
        )
        communicator.scope["user"] = user
        
        await communicator.connect()
        await communicator.receive_json_from()  # connection_established
        
        # Send heartbeat
        await communicator.send_json_to({
            "action": "heartbeat"
        })
        
        # Should receive heartbeat_ack
        response = await communicator.receive_json_from()
        assert response["type"] == "heartbeat_ack"
        
        # Verify heartbeat timestamp was updated
        status = await get_user_status(user)
        assert status.last_heartbeat is not None
        
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_disconnect_marks_user_offline(self):
        """Test disconnecting marks user as offline"""
        user = await create_user()
        
        communicator = WebsocketCommunicator(
            application,
            "/ws/status/",
        )
        communicator.scope["user"] = user
        
        await communicator.connect()
        await communicator.receive_json_from()  # connection_established
        
        # Disconnect
        await communicator.disconnect()
        
        # Verify user was marked offline
        status = await get_user_status(user)
        assert status.is_online is False
    
    @pytest.mark.asyncio
    async def test_status_broadcast_to_other_users(self):
        """Test status changes broadcast to other connected users"""
        user1 = await create_user(username="user1")
        user2 = await create_user(username="user2")
        
        # Connect user1
        comm1 = WebsocketCommunicator(application, "/ws/status/")
        comm1.scope["user"] = user1
        await comm1.connect()
        await comm1.receive_json_from()  # connection_established
        
        # Connect user2
        comm2 = WebsocketCommunicator(application, "/ws/status/")
        comm2.scope["user"] = user2
        await comm2.connect()
        await comm2.receive_json_from()  # connection_established
        
        # User1 should receive user2's online status
        response = await comm1.receive_json_from()
        assert response["type"] == "user_status_changed"
        assert response["status"] == "online"
        
        await comm1.disconnect()
        await comm2.disconnect()


class TestNotificationConsumer:
    """Tests for NotificationConsumer"""
    
    @pytest.mark.asyncio
    async def test_connect_receives_unread_count(self):
        """Test connecting receives unread notification count"""
        user = await create_user()
        
        communicator = WebsocketCommunicator(
            application,
            "/ws/notifications/",
        )
        communicator.scope["user"] = user
        
        connected, _ = await communicator.connect()
        assert connected
        
        # Should receive unread count
        response = await communicator.receive_json_from()
        assert response["type"] == "unread_count"
        assert "count" in response
        
        await communicator.disconnect()


class TestTaskConsumer:
    """Tests for TaskConsumer"""
    
    @pytest.mark.asyncio
    async def test_connect_to_task_updates(self):
        """Test connecting to task updates for a project"""
        user = await create_user()
        project = await create_project()
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/tasks/{project.id}/",
        )
        communicator.scope["user"] = user
        
        connected, _ = await communicator.connect()
        assert connected
        
        # Should receive connection confirmation
        response = await communicator.receive_json_from()
        assert response["type"] == "connection_established"
        assert response["project_id"] == str(project.id)
        
        await communicator.disconnect()


# Integration Tests
class TestWebSocketIntegration(TestCase):
    """Integration tests for WebSocket system"""
    
    def test_user_status_cleanup_task(self):
        """Test Celery task cleans up stale online status"""
        from core.tasks import cleanup_stale_user_status
        from django.utils import timezone
        from datetime import timedelta
        
        # Create user with stale heartbeat
        user = User.objects.create_user(username="staleuser", password="test123")
        status = UserStatus.objects.create(
            user=user,
            is_online=True,
            last_heartbeat=timezone.now() - timedelta(minutes=10)
        )
        
        # Run cleanup task
        result = cleanup_stale_user_status(threshold_minutes=5)
        
        # Verify status was updated
        status.refresh_from_db()
        assert status.is_online is False
        assert result["status"] == "success"
        assert result["users_marked_offline"] == 1
    
    def test_notification_log_creation(self):
        """Test notification log is created correctly"""
        user = User.objects.create_user(username="notifyuser", password="test123")
        
        notification = NotificationLog.objects.create(
            user=user,
            title="Test Notification",
            message="This is a test",
            category="info"
        )
        
        assert notification.read is False
        assert notification.delivered_via_websocket is False
        
        # Mark as delivered
        notification.mark_as_delivered()
        assert notification.delivered_via_websocket is True
        assert notification.delivered_at is not None
        
        # Mark as read
        notification.mark_as_read()
        assert notification.read is True
        assert notification.read_at is not None
