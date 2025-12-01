"""
Tests for chat message cursor-based pagination

Phase 6 - Improvement #9: Message Pagination
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import ChatChannel, ChatMessage, Project

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass123")


@pytest.fixture
def project(db):
    from datetime import date
    return Project.objects.create(
        name="Test Project",
        budget_labor=50000.00,
        budget_materials=30000.00,
        budget_total=80000.00,
        start_date=date(2024, 1, 1),
    )


@pytest.fixture
def channel(db, project):
    return ChatChannel.objects.create(
        name="general",
        project=project,
    )


@pytest.fixture
def messages(db, user, channel):
    """Create 75 messages for pagination testing"""
    messages = []
    for i in range(75):
        msg = ChatMessage.objects.create(
            channel=channel,
            user=user,
            message=f"Test message {i+1}",
        )
        messages.append(msg)
    return messages


@pytest.mark.django_db
class TestChatMessagePagination:
    """Test cursor-based pagination for chat messages"""

    def test_paginated_endpoint_exists(self, api_client, user, channel, messages):
        """Test that paginated endpoint is accessible"""
        api_client.force_authenticate(user=user)
        url = reverse("chat-message-paginated-messages")
        response = api_client.get(url, {"channel": channel.id})
        
        assert response.status_code == status.HTTP_200_OK

    def test_returns_50_messages_by_default(self, api_client, user, channel, messages):
        """Test default page size is 50"""
        api_client.force_authenticate(user=user)
        url = reverse("chat-message-paginated-messages")
        response = api_client.get(url, {"channel": channel.id})
        
        assert len(response.data["results"]) == 50

    def test_has_pagination_metadata(self, api_client, user, channel, messages):
        """Test response includes pagination metadata"""
        api_client.force_authenticate(user=user)
        url = reverse("chat-message-paginated-messages")
        response = api_client.get(url, {"channel": channel.id})
        
        data = response.data
        assert "results" in data
        assert "next" in data
        assert "previous" in data
        assert "has_more" in data
        assert "has_previous" in data

    def test_has_more_is_true_when_messages_remain(self, api_client, user, channel, messages):
        """Test has_more flag is True when more messages exist"""
        api_client.force_authenticate(user=user)
        url = reverse("chat-message-paginated-messages")
        response = api_client.get(url, {"channel": channel.id})
        
        # 75 messages total, 50 on first page = 25 remaining
        assert response.data["has_more"] is True

    def test_cursor_loads_next_page(self, api_client, user, channel, messages):
        """Test cursor parameter loads next page of results"""
        api_client.force_authenticate(user=user)
        url = reverse("chat-message-paginated-messages")
        
        # First page
        response1 = api_client.get(url, {"channel": channel.id})
        assert len(response1.data["results"]) == 50
        
        # Extract cursor from 'previous' link (older messages)
        previous_link = response1.data["previous"]
        assert previous_link is not None
        
        cursor_match = previous_link.split("cursor=")[-1].split("&")[0]
        
        # Second page
        response2 = api_client.get(url, {"channel": channel.id, "cursor": cursor_match})
        assert len(response2.data["results"]) == 25  # Remaining messages

    def test_messages_ordered_by_created_at_desc(self, api_client, user, channel, messages):
        """Test messages are ordered newest first"""
        api_client.force_authenticate(user=user)
        url = reverse("chat-message-paginated-messages")
        response = api_client.get(url, {"channel": channel.id})
        
        results = response.data["results"]
        # First message should be the newest (message 75)
        assert "Test message 75" in results[0]["message"]
        # Last message on page should be older
        assert "Test message" in results[-1]["message"]

    def test_requires_channel_parameter(self, api_client, user, channel):
        """Test endpoint requires channel parameter"""
        api_client.force_authenticate(user=user)
        url = reverse("chat-message-paginated-messages")
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "channel parameter is required" in str(response.data)

    def test_includes_read_by_count(self, api_client, user, channel, messages):
        """Test serializer includes read_by_count field"""
        api_client.force_authenticate(user=user)
        
        # Mark first 3 messages as read
        for msg in messages[:3]:
            msg.read_by.add(user)
        
        url = reverse("chat-message-paginated-messages")
        response = api_client.get(url, {"channel": channel.id})
        
        # Check that read_by_count field exists
        assert "read_by_count" in response.data["results"][0]

    def test_custom_page_size(self, api_client, user, channel, messages):
        """Test page_size query parameter"""
        api_client.force_authenticate(user=user)
        url = reverse("chat-message-paginated-messages")
        response = api_client.get(url, {"channel": channel.id, "page_size": "25"})
        
        assert len(response.data["results"]) == 25

    def test_no_duplicate_messages_across_pages(self, api_client, user, channel, messages):
        """Test that messages don't appear on multiple pages"""
        api_client.force_authenticate(user=user)
        url = reverse("chat-message-paginated-messages")
        
        # First page
        response1 = api_client.get(url, {"channel": channel.id})
        page1_ids = {msg["id"] for msg in response1.data["results"]}
        
        # Second page
        previous_link = response1.data["previous"]
        if previous_link:
            cursor = previous_link.split("cursor=")[-1].split("&")[0]
            response2 = api_client.get(url, {"channel": channel.id, "cursor": cursor})
            page2_ids = {msg["id"] for msg in response2.data["results"]}
            
            # No overlap
            assert page1_ids.isdisjoint(page2_ids)
