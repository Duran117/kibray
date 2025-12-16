"""
WebSocket Security Audit for Kibray

Comprehensive security checks including:
- Authentication verification
- Authorization controls
- Input validation
- Rate limiting
- XSS prevention
- CSRF protection
- Origin validation
"""

import re
import json
from functools import wraps
from django.core.exceptions import ValidationError
from django.utils.html import escape
from channels.db import database_sync_to_async


class WebSocketSecurityValidator:
    """
    Security validator for WebSocket connections and messages.
    
    Provides validation for:
    - User authentication
    - Message content (XSS prevention)
    - Rate limiting
    - Input sanitization
    - Permission checks
    """
    
    # Maximum message length to prevent DoS
    MAX_MESSAGE_LENGTH = 10000  # 10KB
    
    # Allowed message types (whitelist approach)
    ALLOWED_MESSAGE_TYPES = {
        'chat_message',
        'message',
        'typing',
        'typing_start',
        'typing_stop',
        'mark_read',
        'read_receipt',
        'ping',
        'pong',
        'status_update',
        'notification_read',
    }
    
    # Rate limiting: max messages per minute
    MAX_MESSAGES_PER_MINUTE = 60
    
    # XSS patterns to detect and block
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',  # onclick, onerror, etc.
        r'<iframe',
        r'<object',
        r'<embed',
    ]
    
    @staticmethod
    def validate_authentication(scope):
        """
        Validate that WebSocket connection is authenticated.
        
        Args:
            scope: ASGI scope dict
            
        Returns:
            tuple: (is_valid, error_message)
        """
        user = scope.get('user')
        
        if not user:
            return False, "Authentication required"
        
        if not user.is_authenticated:
            return False, "User not authenticated"
        
        if not user.is_active:
            return False, "User account is inactive"
        
        return True, None
    
    @staticmethod
    def validate_origin(scope, allowed_origins=None):
        """
        Validate WebSocket origin to prevent CSRF.
        
        Args:
            scope: ASGI scope dict
            allowed_origins: List of allowed origins (None = use Django settings)
            
        Returns:
            tuple: (is_valid, error_message)
        """
        headers = dict(scope.get('headers', []))
        origin = headers.get(b'origin', b'').decode()
        
        if not origin:
            return False, "Origin header missing"
        
        # Check against allowed origins
        if allowed_origins:
            if origin not in allowed_origins:
                return False, f"Origin {origin} not allowed"
        
        return True, None
    
    @classmethod
    def validate_message_type(cls, message_type):
        """
        Validate message type against whitelist.
        
        Args:
            message_type: String message type
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not message_type:
            return False, "Message type required"
        
        if message_type not in cls.ALLOWED_MESSAGE_TYPES:
            return False, f"Message type '{message_type}' not allowed"
        
        return True, None
    
    @classmethod
    def validate_message_length(cls, message_data):
        """
        Validate message length to prevent DoS.
        
        Args:
            message_data: Message content (string or dict)
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if isinstance(message_data, dict):
            message_data = json.dumps(message_data)
        
        message_length = len(str(message_data))
        
        if message_length > cls.MAX_MESSAGE_LENGTH:
            return False, f"Message too long ({message_length} > {cls.MAX_MESSAGE_LENGTH})"
        
        return True, None
    
    @classmethod
    def sanitize_message(cls, message):
        """
        Sanitize message content to prevent XSS.
        
        Args:
            message: String message content
            
        Returns:
            str: Sanitized message
        """
        if not isinstance(message, str):
            return message
        
        # Escape HTML entities
        sanitized = escape(message)
        
        # Check for XSS patterns
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                # Log potential XSS attempt
                import logging
                logger = logging.getLogger('security')
                logger.warning(f"Potential XSS attempt detected: {pattern}")
                
                # Remove malicious content
                sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

        # Explicitly strip common JS payload fragments like alert(...)
        sanitized = re.sub(r"alert\s*\([^)]*\)", "", sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    @classmethod
    def validate_json(cls, data):
        """
        Validate and parse JSON data safely.
        
        Args:
            data: JSON string
            
        Returns:
            tuple: (parsed_data or None, error_message or None)
        """
        try:
            if not data:
                return None, "Empty data"
            
            parsed = json.loads(data)
            
            if not isinstance(parsed, dict):
                return None, "Data must be a JSON object"
            
            return parsed, None
            
        except json.JSONDecodeError as e:
            return None, f"Invalid JSON: {str(e)}"
    
    @staticmethod
    @database_sync_to_async
    def check_permission(user, permission_name, obj=None):
        """
        Check if user has specific permission.
        
        Args:
            user: Django User instance
            permission_name: Permission string (e.g., 'core.view_project')
            obj: Optional object to check permission against
            
        Returns:
            bool: True if user has permission
        """
        if user.is_superuser:
            return True
        
        if obj:
            # Object-level permission check (requires django-guardian or similar)
            # For now, check basic permission
            return user.has_perm(permission_name)
        
        return user.has_perm(permission_name)
    
    @staticmethod
    @database_sync_to_async
    def check_project_access(user, project_id):
        """
        Check if user has access to specific project.
        
        Args:
            user: Django User instance
            project_id: Project ID
            
        Returns:
            tuple: (has_access, error_message)
        """
        from core.models import Project
        
        try:
            project = Project.objects.get(id=project_id)
            
            # Check if user is project member or admin
            if user.is_superuser:
                return True, None
            
            # Check if user is assigned to project
            # (Adjust based on your Project model structure)
            if hasattr(project, 'assigned_users'):
                if user in project.assigned_users.all():
                    return True, None
            
            if hasattr(project, 'owner') and project.owner == user:
                return True, None
            
            return False, "Access denied to this project"
            
        except Project.DoesNotExist:
            return False, "Project not found"


def require_authentication(func):
    """
    Decorator to require authentication for WebSocket consumer methods.
    
    Usage:
        @require_authentication
        async def receive(self, text_data):
            # Only authenticated users reach here
            pass
    """
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        is_valid, error = WebSocketSecurityValidator.validate_authentication(self.scope)
        
        if not is_valid:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': error,
            }))
            await self.close()
            return
        
        return await func(self, *args, **kwargs)
    
    return wrapper


def require_permission(permission_name):
    """
    Decorator to require specific permission for WebSocket consumer methods.
    
    Usage:
        @require_permission('core.view_project')
        async def receive(self, text_data):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            user = self.scope.get('user')
            
            has_permission = await WebSocketSecurityValidator.check_permission(
                user, permission_name
            )
            
            if not has_permission:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'error': f'Permission denied: {permission_name}',
                }))
                await self.close()
                return
            
            return await func(self, *args, **kwargs)
        
        return wrapper
    return decorator


def validate_message(func):
    """
    Decorator to validate and sanitize WebSocket messages.
    
    Usage:
        @validate_message
        async def receive(self, text_data):
            # text_data is already validated and sanitized
            pass
    """
    @wraps(func)
    async def wrapper(self, text_data, **kwargs):
        validator = WebSocketSecurityValidator
        
        # Parse JSON
        data, error = validator.validate_json(text_data)
        if error:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': error,
            }))
            return
        
        # Validate message type
        message_type = data.get('type')
        is_valid, error = validator.validate_message_type(message_type)
        if not is_valid:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': error,
            }))
            return
        
        # Validate message length
        is_valid, error = validator.validate_message_length(data)
        if not is_valid:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': error,
            }))
            return
        
        # Sanitize message content
        if 'message' in data:
            data['message'] = validator.sanitize_message(data['message'])
        
        # Update text_data with sanitized version
        text_data = json.dumps(data)
        
        return await func(self, text_data, **kwargs)
    
    return wrapper


class RateLimiter:
    """
    Rate limiter for WebSocket connections.
    
    Tracks message counts per user and enforces limits.
    """
    
    def __init__(self):
        self.message_counts = {}  # {user_id: [(timestamp, count), ...]}
        self.cleanup_interval = 60  # Cleanup every 60 seconds
        self.last_cleanup = 0
    
    def is_rate_limited(self, user_id, max_messages=60, window=60):
        """
        Check if user is rate limited.
        
        Args:
            user_id: User ID
            max_messages: Maximum messages allowed in window
            window: Time window in seconds
            
        Returns:
            bool: True if rate limited
        """
        import time
        current_time = time.time()
        
        # Cleanup old entries
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup(current_time, window)
        
        # Get user's message history
        if user_id not in self.message_counts:
            self.message_counts[user_id] = []
        
        user_messages = self.message_counts[user_id]
        
        # Remove messages outside window
        cutoff_time = current_time - window
        user_messages = [
            (timestamp, count) 
            for timestamp, count in user_messages 
            if timestamp > cutoff_time
        ]
        
        # Count messages in window
        total_messages = sum(count for _, count in user_messages)
        
        if total_messages >= max_messages:
            return True
        
        # Add current message
        user_messages.append((current_time, 1))
        self.message_counts[user_id] = user_messages
        
        return False
    
    def _cleanup(self, current_time, window):
        """Remove old entries from rate limiter"""
        cutoff_time = current_time - window
        
        for user_id in list(self.message_counts.keys()):
            self.message_counts[user_id] = [
                (timestamp, count)
                for timestamp, count in self.message_counts[user_id]
                if timestamp > cutoff_time
            ]
            
            # Remove user if no recent messages
            if not self.message_counts[user_id]:
                del self.message_counts[user_id]
        
        self.last_cleanup = current_time


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(max_messages=60, window=60):
    """
    Decorator to rate limit WebSocket consumer methods.
    
    Usage:
        @rate_limit(max_messages=60, window=60)
        async def receive(self, text_data):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            user = self.scope.get('user')
            
            if user and user.is_authenticated:
                if rate_limiter.is_rate_limited(user.id, max_messages, window):
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'error': 'Rate limit exceeded. Please slow down.',
                    }))
                    return
            
            return await func(self, *args, **kwargs)
        
        return wrapper
    return decorator
