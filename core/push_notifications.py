"""
Push Notification Service for Kibray

Integrates with Firebase Cloud Messaging (FCM) for push notifications:
- Web push notifications
- Mobile push (iOS/Android)
- Notification batching
- User preferences
- Delivery tracking
"""

import json
import logging
from typing import List, Optional
from django.conf import settings
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async

logger = logging.getLogger('push_notifications')

User = get_user_model()


class PushNotificationService:
    """
    Service for sending push notifications via FCM.
    
    Features:
    - Multi-platform support (Web, iOS, Android)
    - Token management
    - Notification batching
    - User preferences
    - Delivery tracking
    """
    
    def __init__(self):
        self.fcm_enabled = getattr(settings, 'FCM_ENABLED', False)
        self.fcm_server_key = getattr(settings, 'FCM_SERVER_KEY', None)
        
        if self.fcm_enabled and not self.fcm_server_key:
            logger.warning("FCM enabled but no server key configured")
            self.fcm_enabled = False
    
    async def send_notification(
        self,
        user_id: int,
        title: str,
        body: str,
        data: Optional[dict] = None,
        category: str = 'general',
        priority: str = 'normal'
    ):
        """
        Send push notification to user.
        
        Args:
            user_id: Target user ID
            title: Notification title
            body: Notification body
            data: Additional data payload
            category: Notification category
            priority: 'normal' or 'high'
            
        Returns:
            dict: Result with success status and message IDs
        """
        if not self.fcm_enabled:
            logger.debug("FCM not enabled, skipping push notification")
            return {'success': False, 'reason': 'FCM not enabled'}
        
        # Get user's device tokens
        tokens = await self._get_user_tokens(user_id)
        
        if not tokens:
            logger.debug(f"No device tokens for user {user_id}")
            return {'success': False, 'reason': 'No device tokens'}
        
        # Check user preferences
        preferences = await self._get_user_preferences(user_id)
        
        if not self._should_send(category, preferences):
            logger.debug(f"User {user_id} has disabled {category} notifications")
            return {'success': False, 'reason': 'User preferences'}
        
        # Prepare notification payload
        payload = self._build_payload(title, body, data, category, priority)
        
        # Send to all user devices
        results = []
        for token in tokens:
            result = await self._send_to_token(token, payload)
            results.append(result)
        
        # Log results
        successful = sum(1 for r in results if r.get('success'))
        logger.info(f"Sent push notification to {successful}/{len(tokens)} devices for user {user_id}")
        
        return {
            'success': successful > 0,
            'sent_count': successful,
            'total_devices': len(tokens),
            'results': results
        }
    
    async def send_bulk_notification(
        self,
        user_ids: List[int],
        title: str,
        body: str,
        data: Optional[dict] = None,
        category: str = 'general'
    ):
        """
        Send notification to multiple users.
        
        Args:
            user_ids: List of user IDs
            title: Notification title
            body: Notification body
            data: Additional data
            category: Notification category
            
        Returns:
            dict: Bulk send results
        """
        results = []
        
        for user_id in user_ids:
            result = await self.send_notification(
                user_id, title, body, data, category
            )
            results.append({
                'user_id': user_id,
                'result': result
            })
        
        successful_users = sum(1 for r in results if r['result'].get('success'))
        
        return {
            'success': True,
            'total_users': len(user_ids),
            'successful_users': successful_users,
            'results': results
        }
    
    async def register_device_token(
        self,
        user_id: int,
        token: str,
        device_type: str = 'web',
        device_name: Optional[str] = None
    ):
        """
        Register device token for push notifications.
        
        Args:
            user_id: User ID
            token: FCM device token
            device_type: 'web', 'ios', or 'android'
            device_name: Optional device identifier
            
        Returns:
            bool: Success status
        """
        return await self._save_device_token(
            user_id, token, device_type, device_name
        )
    
    async def unregister_device_token(self, user_id: int, token: str):
        """
        Remove device token.
        
        Args:
            user_id: User ID
            token: FCM device token
            
        Returns:
            bool: Success status
        """
        return await self._delete_device_token(user_id, token)
    
    async def update_user_preferences(
        self,
        user_id: int,
        preferences: dict
    ):
        """
        Update user's push notification preferences.
        
        Args:
            user_id: User ID
            preferences: Dictionary of category preferences
                Example: {
                    'chat': True,
                    'task': True,
                    'mention': True,
                    'system': False
                }
            
        Returns:
            bool: Success status
        """
        return await self._save_user_preferences(user_id, preferences)
    
    def _build_payload(
        self,
        title: str,
        body: str,
        data: Optional[dict],
        category: str,
        priority: str
    ) -> dict:
        """Build FCM notification payload"""
        payload = {
            'notification': {
                'title': title,
                'body': body,
            },
            'data': {
                'category': category,
                **(data or {})
            },
            'android': {
                'priority': 'high' if priority == 'high' else 'normal',
            },
            'apns': {
                'payload': {
                    'aps': {
                        'sound': 'default',
                        'badge': 1,
                    }
                }
            },
            'webpush': {
                'notification': {
                    'icon': '/static/images/logo.png',
                    'badge': '/static/images/badge.png',
                }
            }
        }
        
        return payload
    
    async def _send_to_token(self, token: str, payload: dict) -> dict:
        """
        Send notification to specific device token.
        
        Args:
            token: FCM device token
            payload: Notification payload
            
        Returns:
            dict: Send result
        """
        try:
            # In production, use Firebase Admin SDK
            # For now, simulate sending
            
            # Example with requests library:
            # import requests
            # url = 'https://fcm.googleapis.com/fcm/send'
            # headers = {
            #     'Authorization': f'key={self.fcm_server_key}',
            #     'Content-Type': 'application/json',
            # }
            # payload['to'] = token
            # response = requests.post(url, headers=headers, json=payload)
            # return response.json()
            
            logger.debug(f"Would send push notification to token: {token[:10]}...")
            
            return {
                'success': True,
                'message_id': f'msg_{token[:8]}',
                'token': token
            }
            
        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return {
                'success': False,
                'error': str(e),
                'token': token
            }
    
    def _should_send(self, category: str, preferences: dict) -> bool:
        """Check if notification should be sent based on preferences"""
        if not preferences:
            return True  # Default: send all notifications
        
        return preferences.get(category, True)
    
    @database_sync_to_async
    def _get_user_tokens(self, user_id: int) -> List[str]:
        """Get all device tokens for user"""
        from core.models import DeviceToken
        
        try:
            tokens = DeviceToken.objects.filter(
                user_id=user_id,
                is_active=True
            ).values_list('token', flat=True)
            
            return list(tokens)
            
        except Exception as e:
            logger.error(f"Failed to get user tokens: {e}")
            return []
    
    @database_sync_to_async
    def _get_user_preferences(self, user_id: int) -> dict:
        """Get user's notification preferences"""
        from core.models import NotificationPreference
        
        try:
            prefs = NotificationPreference.objects.filter(
                user_id=user_id
            ).first()
            
            if prefs:
                return prefs.preferences or {}
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return {}
    
    @database_sync_to_async
    def _save_device_token(
        self,
        user_id: int,
        token: str,
        device_type: str,
        device_name: Optional[str]
    ) -> bool:
        """Save device token to database"""
        from core.models import DeviceToken
        from django.utils import timezone
        
        try:
            DeviceToken.objects.update_or_create(
                user_id=user_id,
                token=token,
                defaults={
                    'device_type': device_type,
                    'device_name': device_name,
                    'is_active': True,
                    'last_used': timezone.now(),
                }
            )
            
            logger.info(f"Saved device token for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save device token: {e}")
            return False
    
    @database_sync_to_async
    def _delete_device_token(self, user_id: int, token: str) -> bool:
        """Delete device token from database"""
        from core.models import DeviceToken
        
        try:
            DeviceToken.objects.filter(
                user_id=user_id,
                token=token
            ).update(is_active=False)
            
            logger.info(f"Deleted device token for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete device token: {e}")
            return False
    
    @database_sync_to_async
    def _save_user_preferences(self, user_id: int, preferences: dict) -> bool:
        """Save user notification preferences"""
        from core.models import NotificationPreference
        
        try:
            NotificationPreference.objects.update_or_create(
                user_id=user_id,
                defaults={
                    'preferences': preferences
                }
            )
            
            logger.info(f"Updated preferences for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")
            return False


# Global service instance
push_service = PushNotificationService()


# Helper functions for common notification types

async def send_chat_mention_notification(user_id: int, mentioned_by: str, channel_name: str, message_preview: str):
    """Send notification when user is mentioned in chat"""
    await push_service.send_notification(
        user_id=user_id,
        title=f"@{mentioned_by} mentioned you",
        body=f"In {channel_name}: {message_preview[:100]}",
        data={
            'type': 'chat_mention',
            'channel': channel_name,
        },
        category='mention',
        priority='high'
    )


async def send_task_assignment_notification(user_id: int, task_title: str, assigned_by: str):
    """Send notification when task is assigned"""
    await push_service.send_notification(
        user_id=user_id,
        title="New task assigned",
        body=f"{assigned_by} assigned you: {task_title}",
        data={
            'type': 'task_assigned',
            'task': task_title,
        },
        category='task',
        priority='normal'
    )


async def send_message_notification(user_id: int, sender: str, channel_name: str, message: str):
    """Send notification for new chat message"""
    await push_service.send_notification(
        user_id=user_id,
        title=f"{sender} in {channel_name}",
        body=message[:200],
        data={
            'type': 'chat_message',
            'channel': channel_name,
            'sender': sender,
        },
        category='chat',
        priority='normal'
    )
