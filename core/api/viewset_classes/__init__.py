"""
ViewSets for Kibray API
"""
from .user_viewsets import UserViewSet
from .project_viewsets import ProjectViewSet
from .task_viewsets import TaskViewSet
from .changeorder_viewsets import ChangeOrderViewSet
from .analytics_viewsets import AnalyticsViewSet

__all__ = [
    'UserViewSet',
    'ProjectViewSet',
    'TaskViewSet',
    'ChangeOrderViewSet',
    'AnalyticsViewSet',
]
