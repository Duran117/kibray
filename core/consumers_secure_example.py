"""
Secure WebSocket Consumer Example

Demonstrates security best practices:
- Authentication required
- Permission checks
- Message validation
- Rate limiting
- XSS prevention
"""

import json
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from core.websocket_security import (
    require_authentication,
    require_permission,
    validate_message,
    rate_limit,
    WebSocketSecurityValidator,
)


class SecureProjectChatConsumer(AsyncWebsocketConsumer):
    """
    Secure project chat consumer with full security validations.
    
    Security features:
    - Authentication required on connect
    - Project access verification
    - Message validation and sanitization
    - Rate limiting (60 messages/minute)
    - XSS prevention
    - Permission checks
    """
    
    @require_authentication
    async def connect(self):
        """
        Accept WebSocket connection with security checks.
        
        Validates:
        - User authentication
        - Project access permissions
        - Origin header (CSRF protection)
        """
        self.project_id = self.scope["url_route"]["kwargs"]["project_id"]
        self.room_group_name = f"chat_project_{self.project_id}"
        self.user = self.scope["user"]
        
        # Validate origin
        is_valid, error = WebSocketSecurityValidator.validate_origin(
            self.scope,
            allowed_origins=[
                'http://localhost:3000',
                'http://localhost:8000',
                'https://kibray.com',  # Add production domains
            ]
        )
        
        if not is_valid:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': error,
            }))
            await self.close()
            return
        
        # Check project access
        has_access, error = await WebSocketSecurityValidator.check_project_access(
            self.user, 
            self.project_id
        )
        
        if not has_access:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': error,
            }))
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        # Notify others user joined (safely)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': self.user.id,
                'username': self.user.username,
                'timestamp': datetime.now().isoformat(),
            }
        )
    
    async def disconnect(self, close_code):
        """Clean disconnect from chat group"""
        # Notify others user left
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'timestamp': datetime.now().isoformat(),
                }
            )
            
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name, 
                self.channel_name
            )
    
    @rate_limit(max_messages=60, window=60)
    @validate_message
    @require_permission('core.add_chatmessage')
    async def receive(self, text_data):
        """
        Receive and process messages with full security validation.
        
        Security checks (via decorators):
        1. Rate limiting - Max 60 messages/minute
        2. Message validation - Type, length, format
        3. Permission check - User can send messages
        4. XSS sanitization - Clean malicious content
        """
        data = json.loads(text_data)
        message_type = data.get('type')
        
        # Route to appropriate handler
        if message_type == 'chat_message':
            await self.handle_chat_message(data)
        elif message_type == 'typing_start':
            await self.handle_typing_start(data)
        elif message_type == 'typing_stop':
            await self.handle_typing_stop(data)
        elif message_type == 'mark_read':
            await self.handle_mark_read(data)
        else:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': f'Unknown message type: {message_type}',
            }))
    
    async def handle_chat_message(self, data):
        """
        Handle chat message (already validated and sanitized).
        
        Note: data['message'] is already XSS-sanitized by @validate_message
        """
        message_content = data.get('message', '').strip()
        
        if not message_content:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': 'Message cannot be empty',
            }))
            return
        
        # Save to database
        message_id = await self.save_message(
            user=self.user,
            content=message_content,
            project_id=self.project_id,
        )
        
        # Broadcast to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message_id': message_id,
                'message': message_content,
                'user_id': self.user.id,
                'username': self.user.username,
                'timestamp': datetime.now().isoformat(),
            }
        )
    
    async def handle_typing_start(self, data):
        """Broadcast typing indicator"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'username': self.user.username,
                'is_typing': True,
            }
        )
    
    async def handle_typing_stop(self, data):
        """Stop typing indicator"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'username': self.user.username,
                'is_typing': False,
            }
        )
    
    async def handle_mark_read(self, data):
        """Mark message as read"""
        message_id = data.get('message_id')
        
        if message_id:
            await self.mark_message_read(self.user.id, message_id)
            
            await self.send(text_data=json.dumps({
                'type': 'message_read_ack',
                'message_id': message_id,
            }))
    
    # Channel layer handlers (receive from group_send)
    
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message_id': event['message_id'],
            'message': event['message'],
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp'],
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        # Don't send own typing indicator back
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing'],
            }))
    
    async def user_joined(self, event):
        """Send user joined notification"""
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp'],
        }))
    
    async def user_left(self, event):
        """Send user left notification"""
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp'],
        }))
    
    # Database operations
    
    @database_sync_to_async
    def save_message(self, user, content, project_id):
        """Save message to database"""
        from core.models import ChatMessage, ChatChannel, Project
        
        try:
            project = Project.objects.get(id=project_id)
            channel, _ = ChatChannel.objects.get_or_create(
                name=f"project_{project_id}",
                defaults={'project': project}
            )
            
            message = ChatMessage.objects.create(
                channel=channel,
                user=user,
                content=content,
            )
            
            return message.id
            
        except Exception as e:
            import logging
            logger = logging.getLogger('websocket')
            logger.error(f"Failed to save message: {e}")
            return None
    
    @database_sync_to_async
    def mark_message_read(self, user_id, message_id):
        """Mark message as read by user"""
        from core.models import ChatMessage
        
        try:
            message = ChatMessage.objects.get(id=message_id)
            # Add to read_by if not already there
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
            message.read_by.add(user)
            message.save()
            
        except Exception as e:
            import logging
            logger = logging.getLogger('websocket')
            logger.error(f"Failed to mark message read: {e}")


class SecureNotificationConsumer(AsyncWebsocketConsumer):
    """
    Secure notification consumer with authentication.
    
    Security features:
    - Authentication required
    - User-specific channel (can only receive own notifications)
    - Rate limiting
    - Message validation
    """
    
    @require_authentication
    async def connect(self):
        """Connect to user's notification channel"""
        self.user = self.scope['user']
        self.room_group_name = f'notifications_{self.user.id}'
        
        # Validate origin
        is_valid, error = WebSocketSecurityValidator.validate_origin(self.scope)
        if not is_valid:
            await self.close()
            return
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        # Send unread count
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': unread_count,
        }))
    
    async def disconnect(self, close_code):
        """Disconnect from notification channel"""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    @rate_limit(max_messages=30, window=60)
    @validate_message
    async def receive(self, text_data):
        """Handle notification actions (mark as read, etc.)"""
        data = json.loads(text_data)
        
        if data.get('type') == 'mark_read':
            notification_id = data.get('notification_id')
            if notification_id:
                await self.mark_notification_read(notification_id)
    
    async def notification(self, event):
        """Send notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification'],
        }))
    
    @database_sync_to_async
    def get_unread_count(self):
        """Get unread notification count"""
        from core.models import NotificationLog
        return NotificationLog.objects.filter(
            user=self.user,
            is_read=False
        ).count()
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark notification as read"""
        from core.models import NotificationLog
        try:
            notification = NotificationLog.objects.get(
                id=notification_id,
                user=self.user  # Security: only mark own notifications
            )
            notification.is_read = True
            notification.save()
        except NotificationLog.DoesNotExist:
            pass
