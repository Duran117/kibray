"""
Custom pagination classes for the Kibray API

iOS-optimized pagination with consistent response structure
"""

from collections import OrderedDict

from rest_framework.pagination import (
    CursorPagination,
    LimitOffsetPagination,
    PageNumberPagination,
)
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination for most list endpoints
    Default: 50 items per page (good for mobile)
    """

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("count", self.page.paginator.count),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("page_size", self.page_size),
                    ("total_pages", self.page.paginator.num_pages),
                    ("current_page", self.page.number),
                    ("results", data),
                ]
            )
        )


class LargeResultsSetPagination(PageNumberPagination):
    """
    Pagination for endpoints with many results (projects, time entries)
    Default: 100 items per page
    """

    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 500


class SmallResultsSetPagination(PageNumberPagination):
    """
    Pagination for detail-heavy endpoints (invoices with line items)
    Default: 25 items per page
    """

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


class MobileFriendlyPagination(LimitOffsetPagination):
    """
    Offset-based pagination for infinite scroll on mobile
    Better for iOS SwiftUI Lists with lazy loading
    """

    default_limit = 30
    max_limit = 100

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("count", self.count),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("limit", self.limit),
                    ("offset", self.offset),
                    ("results", data),
                ]
            )
        )


class ChatMessageCursorPagination(CursorPagination):
    """
    Cursor-based pagination optimized for chat message infinite scroll
    
    Advantages over offset pagination for chat:
    - O(1) performance regardless of scroll position
    - Stable pagination even when new messages arrive
    - No duplicate messages when real-time inserts occur
    - No skipped messages due to concurrent writes
    
    Usage:
        - Scrolling up (loading older messages): Use 'cursor' param from 'previous' link
        - Initial load: No cursor, returns newest 50 messages
        - Ordering: Newest first (-created_at)
    """

    page_size = 50
    ordering = "-created_at"  # Newest messages first
    cursor_query_param = "cursor"
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        """
        Enhanced response structure for infinite scroll UX
        
        Returns:
            {
                "next": "cursor_token_for_newer_messages",
                "previous": "cursor_token_for_older_messages",
                "has_more": bool,  # True if more older messages exist
                "has_previous": bool,  # True if newer messages exist
                "results": [...messages...]
            }
        """
        return Response(
            OrderedDict(
                [
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("has_more", self.get_previous_link() is not None),  # Older messages
                    ("has_previous", self.get_next_link() is not None),  # Newer messages
                    ("results", data),
                ]
            )
        )


class NotificationCursorPagination(CursorPagination):
    """
    Cursor-based pagination for notification feed
    
    Similar to ChatMessageCursorPagination but with smaller page size
    for faster initial load in notification dropdown
    """

    page_size = 30
    ordering = "-created_at"
    cursor_query_param = "cursor"
    page_size_query_param = "page_size"
    max_page_size = 50

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("has_more", self.get_previous_link() is not None),
                    ("has_previous", self.get_next_link() is not None),
                    ("results", data),
                ]
            )
        )

