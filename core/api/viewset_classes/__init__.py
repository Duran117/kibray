"""
ViewSets for Kibray API
"""
from .analytics_viewsets import AnalyticsViewSet
from .changeorder_viewsets import ChangeOrderViewSet
from .project_viewsets import ProjectViewSet
from .task_viewsets import TaskViewSet
from .user_viewsets import UserViewSet

__all__ = [
    'UserViewSet',
    'ProjectViewSet',
    'TaskViewSet',
    'ChangeOrderViewSet',
    'AnalyticsViewSet',
]
