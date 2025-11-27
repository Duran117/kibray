"""
Custom pagination classes for the Kibray API

iOS-optimized pagination with consistent response structure
"""

from collections import OrderedDict

from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
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
