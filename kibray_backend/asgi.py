"""
ASGI config for kibray_backend project.

Handles both HTTP and WebSocket connections using Django Channels.
WebSocket routes for real-time chat, notifications, and live dashboards.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Set Django settings before importing anything else
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kibray_backend.settings")

# Initialize Django ASGI application early to populate apps registry
django_asgi_app = get_asgi_application()

# Now import Channels components
from channels.auth import AuthMiddlewareStack  # type: ignore
from channels.routing import ProtocolTypeRouter, URLRouter  # type: ignore
from channels.security.websocket import AllowedHostsOriginValidator  # type: ignore

# Import WebSocket routing (will be created)
try:
    from core.routing import websocket_urlpatterns
except ImportError:
    websocket_urlpatterns = []

# ASGI application with WebSocket support
application = ProtocolTypeRouter(
    {
        # Django's ASGI application to handle traditional HTTP requests
        "http": django_asgi_app,
        # WebSocket chat handler with authentication and allowed hosts
        "websocket": AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter(websocket_urlpatterns))),
    }
)
