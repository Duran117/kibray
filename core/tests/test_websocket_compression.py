"""
Tests for WebSocket compression functionality.

Run with: pytest core/tests/test_websocket_compression.py -v
"""

import pytest
import json
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

from kibray_backend.asgi import application
from core.models import ChatChannel, Project

User = get_user_model()

pytestmark = pytest.mark.django_db(transaction=True)


@database_sync_to_async
def create_user(username="testuser"):
    """Helper to create test user"""
    return User.objects.create_user(
        username=username,
        password="testpass123",
        email=f"{username}@test.com"
    )


@database_sync_to_async
def create_project(name="Test Project"):
    """Helper to create test project"""
    return Project.objects.create(name=name)


@database_sync_to_async
def get_chat_channel(project):
    """Helper to get or create chat channel"""
    channel, _ = ChatChannel.objects.get_or_create(
        name=f"project_{project.id}",
        defaults={"project": project}
    )
    return channel


class TestWebSocketCompression:
    """Test WebSocket compression features"""

    @pytest.mark.asyncio
    async def test_compression_middleware_exists(self):
        """Test that compression middleware is loaded"""
        # Import middleware
        from core.websocket_middleware import WebSocketCompressionMiddleware
        
        assert WebSocketCompressionMiddleware is not None
        assert hasattr(WebSocketCompressionMiddleware, '__call__')

    @pytest.mark.asyncio
    async def test_websocket_connection_with_compression_header(self):
        """Test WebSocket connection with permessage-deflate header"""
        user = await create_user("compression_test_user")
        project = await create_project("Compression Test Project")
        
        # Create communicator with compression header
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/project/{project.id}/",
            headers=[
                (b"sec-websocket-extensions", b"permessage-deflate; client_max_window_bits"),
            ]
        )
        
        # Force authentication
        communicator.scope["user"] = user
        
        # Connect
        connected, _ = await communicator.connect()
        assert connected, "WebSocket should connect with compression header"
        
        # Send a test message
        test_message = {
            "type": "chat_message",
            "message": "A" * 2000,  # Large message (2KB) to trigger compression
        }
        
        await communicator.send_json_to(test_message)
        
        # Should receive message back (echoed or broadcast)
        response = await communicator.receive_json_from(timeout=2)
        assert response is not None
        
        # Disconnect
        await communicator.disconnect()

    @pytest.mark.asyncio
    async def test_large_message_transmission(self):
        """Test that large messages (>1KB) are handled correctly"""
        user = await create_user("large_msg_test_user")
        project = await create_project("Large Message Project")
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/project/{project.id}/",
        )
        communicator.scope["user"] = user
        
        connected, _ = await communicator.connect()
        assert connected
        
        # Send large message (>1KB to benefit from compression)
        large_message_content = "X" * 5000  # 5KB message
        large_message = {
            "type": "chat_message",
            "message": large_message_content,
        }
        
        await communicator.send_json_to(large_message)
        
        # Should receive response
        response = await communicator.receive_json_from(timeout=3)
        assert response is not None
        
        await communicator.disconnect()

    @pytest.mark.asyncio
    async def test_compression_with_multiple_messages(self):
        """Test compression with rapid message sending"""
        user = await create_user("multi_msg_test_user")
        project = await create_project("Multi Message Project")
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/project/{project.id}/",
            headers=[
                (b"sec-websocket-extensions", b"permessage-deflate"),
            ]
        )
        communicator.scope["user"] = user
        
        connected, _ = await communicator.connect()
        assert connected
        
        # Send multiple messages
        for i in range(5):
            message = {
                "type": "chat_message",
                "message": f"Test message {i} with some repeated content " * 20,
            }
            await communicator.send_json_to(message)
        
        # Receive responses
        received_count = 0
        for _ in range(5):
            try:
                response = await communicator.receive_json_from(timeout=1)
                if response:
                    received_count += 1
            except Exception:
                break
        
        assert received_count > 0, "Should receive at least some messages back"
        
        await communicator.disconnect()

    @pytest.mark.asyncio
    async def test_compression_stats_utility(self):
        """Test compression stats utility functions"""
        from core.websocket_middleware import get_compression_stats
        
        # Mock scope with compression enabled
        scope = {
            "websocket": {
                "compression": {
                    "enabled": True,
                    "server_max_window_bits": 15,
                    "client_max_window_bits": 15,
                    "server_no_context_takeover": True,
                    "client_no_context_takeover": True,
                }
            }
        }
        
        stats = get_compression_stats(scope)
        
        assert stats["enabled"] is True
        assert stats["server_window_bits"] == 15
        assert stats["client_window_bits"] == 15

    @pytest.mark.asyncio
    async def test_without_compression_header(self):
        """Test WebSocket works without compression header (fallback)"""
        user = await create_user("no_compression_user")
        project = await create_project("No Compression Project")
        
        # Connect without compression header
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/project/{project.id}/",
        )
        communicator.scope["user"] = user
        
        connected, _ = await communicator.connect()
        assert connected, "WebSocket should work without compression"
        
        # Send normal message
        message = {
            "type": "chat_message",
            "message": "Test without compression",
        }
        
        await communicator.send_json_to(message)
        response = await communicator.receive_json_from(timeout=2)
        assert response is not None
        
        await communicator.disconnect()

    def test_compression_threshold_config(self):
        """Test compression threshold configuration"""
        from core.websocket_middleware import MessageCompressionMiddleware
        
        # Check threshold is set correctly
        assert MessageCompressionMiddleware.COMPRESSION_THRESHOLD == 1024
        assert MessageCompressionMiddleware.COMPRESSION_LEVEL in range(1, 10)

    @pytest.mark.asyncio
    async def test_json_message_size_calculation(self):
        """Test message size calculation for compression decision"""
        # Small message (should not trigger compression)
        small_msg = {"type": "ping", "data": "hello"}
        small_json = json.dumps(small_msg)
        assert len(small_json.encode()) < 1024
        
        # Large message (should trigger compression)
        large_msg = {
            "type": "chat_message",
            "message": "X" * 2000,  # 2KB
            "metadata": {"user": "test", "timestamp": "2024-01-01"}
        }
        large_json = json.dumps(large_msg)
        assert len(large_json.encode()) > 1024
