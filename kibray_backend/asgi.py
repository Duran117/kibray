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
from channels.auth import AuthMiddlewareStack  # type: ignore  # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # type: ignore  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # type: ignore  # noqa: E402

# Import WebSocket routing and compression middleware
try:
    from core.routing import websocket_urlpatterns
    from core.websocket_middleware import WebSocketCompressionMiddleware
except ImportError:
    websocket_urlpatterns = []
    WebSocketCompressionMiddleware = None

# ASGI application with WebSocket support
# Middleware stack (outer to inner):
# 1. WebSocketCompressionMiddleware - Enable permessage-deflate compression
# 2. AllowedHostsOriginValidator - Validate WebSocket origin
# 3. AuthMiddlewareStack - Django authentication
# 4. URLRouter - Route to appropriate consumer
if WebSocketCompressionMiddleware:
    websocket_app = WebSocketCompressionMiddleware(
        AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter(websocket_urlpatterns)
            )
        )
    )
else:
    # Fallback without compression
    websocket_app = AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    )

application = ProtocolTypeRouter(
    {
        # Django's ASGI application to handle traditional HTTP requests
        "http": django_asgi_app,
        # WebSocket handler with compression, authentication, and routing
        "websocket": websocket_app,
    }
)
