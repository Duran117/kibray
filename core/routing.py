"""
WebSocket URL routing for Kibray real-time features.

Handles:
- Real-time chat (project channels, direct messages)
- Live notifications
- Dashboard widgets (real-time metrics)
- Project updates broadcast
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Chat WebSocket - project-specific channels
    re_path(r'ws/chat/project/(?P<project_id>\d+)/$', consumers.ProjectChatConsumer.as_asgi()),  # type: ignore[arg-type]
    
    # Direct messages between users
    re_path(r'ws/chat/direct/(?P<user_id>\d+)/$', consumers.DirectChatConsumer.as_asgi()),  # type: ignore[arg-type]
    
    # Notifications WebSocket - user-specific
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),  # type: ignore[arg-type]
    
    # Real-time dashboard widgets
    re_path(r'ws/dashboard/project/(?P<project_id>\d+)/$', consumers.DashboardConsumer.as_asgi()),  # type: ignore[arg-type]
    
    # Global admin dashboard
    re_path(r'ws/dashboard/admin/$', consumers.AdminDashboardConsumer.as_asgi()),  # type: ignore[arg-type]
    
    # Daily plan updates for employees
    re_path(r'ws/daily-plan/(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})/$', consumers.DailyPlanConsumer.as_asgi()),  # type: ignore[arg-type]
    
    # Quality inspection live updates
    re_path(r'ws/quality/inspection/(?P<inspection_id>\d+)/$', consumers.QualityInspectionConsumer.as_asgi()),  # type: ignore[arg-type]
]
