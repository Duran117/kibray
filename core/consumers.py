"""
WebSocket consumers for Kibray real-time features.

Uses Django Channels to handle WebSocket connections for:
- Real-time chat
- Live notifications
- Dashboard updates
- Project activity broadcast
"""

import json
from datetime import datetime
import logging

from channels.db import database_sync_to_async  # type: ignore
from channels.generic.websocket import AsyncWebsocketConsumer  # type: ignore
from django.core.cache import cache
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils import translation
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)


class RateLimitMixin:
    """
    Mixin to add rate limiting to WebSocket consumers.
    Prevents abuse by limiting messages per user per minute.
    """
    
    # Override these in consumer classes
    rate_limit_messages = 30  # messages per minute
    rate_limit_window = 60  # seconds
    
    def get_rate_limit_key(self):
        """Generate cache key for rate limiting"""
        user_id = getattr(self.user, 'id', 'anonymous')  # type: ignore[attr-defined]
        return f"websocket_rate_limit:{user_id}:{self.__class__.__name__}"
    
    async def check_rate_limit(self):
        """
        Check if user has exceeded rate limit.
        Returns True if allowed, False if rate limited.
        """
        key = self.get_rate_limit_key()
        
        # Get current count from cache
        count = cache.get(key, 0)
        
        if count >= self.rate_limit_messages:
            logger.warning(
                f"Rate limit exceeded for user {getattr(self.user, 'id', 'anonymous')} "  # type: ignore[attr-defined]
                f"in {self.__class__.__name__}: {count}/{self.rate_limit_messages} messages"
            )
            await self.send(  # type: ignore[attr-defined]
                text_data=json.dumps({
                    "type": "error",
                    "error": "rate_limit_exceeded",
                    "message": _("Rate limit exceeded. Maximum %(limit)s messages per minute.") % {"limit": self.rate_limit_messages},
                    "retry_after": self.rate_limit_window,
                })
            )
            return False
        
        # Increment counter
        cache.set(key, count + 1, self.rate_limit_window)
        return True
from django.contrib.auth.models import User


class ProjectChatConsumer(RateLimitMixin, AsyncWebsocketConsumer):
    """
    WebSocket consumer for project-specific chat rooms.

    Features:
    - Real-time message delivery
    - Read receipts
    - Typing indicators
    - File attachment notifications
    - @mentions
    - Rate limiting (30 messages/min)
    """
    
    # Rate limiting config
    rate_limit_messages = 30
    rate_limit_window = 60

    async def connect(self):
        """Accept WebSocket connection and join project chat group"""
        # Activate language from querystring
        try:
            query = parse_qs(self.scope.get("query_string", b"").decode())  # type: ignore[typeddict-item]
            lang = (query.get("lang", [None])[0] or "").split('-')[0]
            if lang:
                translation.activate(lang)
                self.lang = lang
        except Exception:
            self.lang = None
        self.project_id = self.scope["url_route"]["kwargs"]["project_id"]  # type: ignore[typeddict-item]
        self.room_group_name = f"chat_project_{self.project_id}"
        self.user = self.scope["user"]  # type: ignore[typeddict-item]

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        # Notify others user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_joined",
                "user_id": self.user.id,  # type: ignore[union-attr]
                "username": self.user.username,  # type: ignore[union-attr]
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def disconnect(self, close_code):
        """Leave chat group when WebSocket closes"""
        # Notify others user left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_left",
                "user_id": self.user.id,  # type: ignore[union-attr]
                "username": self.user.username,  # type: ignore[union-attr]
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """Receive message from WebSocket and broadcast to group"""
        # Check rate limit first
        if not await self.check_rate_limit():
            return  # Rate limit exceeded, error already sent
        
        data = json.loads(text_data)
        message_type = data.get("type", "message")

        if message_type == "message":
            # Save message to database
            message_id = await self.save_message(
                project_id=self.project_id,
                user=self.user,
                content=data["message"],
                attachments=data.get("attachments", []),
            )

            # Broadcast to chat group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message_id": message_id,
                    "message": data["message"],
                    "user_id": self.user.id,  # type: ignore[union-attr]
                    "username": self.user.username,  # type: ignore[union-attr]
                    "timestamp": datetime.now().isoformat(),
                    "attachments": data.get("attachments", []),
                },
            )

        elif message_type == "typing":
            # Broadcast typing indicator
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_indicator",
                    "user_id": self.user.id,  # type: ignore[union-attr]
                    "username": self.user.username,  # type: ignore[union-attr]
                    "is_typing": data.get("is_typing", True),
                },
            )

        elif message_type == "read_receipt":
            # Mark message as read
            await self.mark_message_read(message_id=data["message_id"], user=self.user)

            # Broadcast read receipt
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "read_receipt",
                    "message_id": data["message_id"],
                    "user_id": self.user.id,  # type: ignore[union-attr]
                    "timestamp": datetime.now().isoformat(),
                },
            )

    # Handlers for different message types from group
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "message",
                    "message_id": event["message_id"],
                    "message": event["message"],
                    "user_id": event["user_id"],
                    "username": event["username"],
                    "timestamp": event["timestamp"],
                    "attachments": event.get("attachments", []),
                }
            )
        )

    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        # Don't send to the user who is typing
        if event["user_id"] != self.user.id:  # type: ignore[union-attr]
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "typing",
                        "user_id": event["user_id"],
                        "username": event["username"],
                        "is_typing": event["is_typing"],
                    }
                )
            )

    async def user_joined(self, event):
        """Notify when user joins"""
        if event["user_id"] != self.user.id:  # type: ignore[union-attr]
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "user_joined",
                        "user_id": event["user_id"],
                        "username": event["username"],
                        "timestamp": event["timestamp"],
                    }
                )
            )

    async def user_left(self, event):
        """Notify when user leaves"""
        if event["user_id"] != self.user.id:  # type: ignore[union-attr]
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "user_left",
                        "user_id": event["user_id"],
                        "username": event["username"],
                        "timestamp": event["timestamp"],
                    }
                )
            )

    async def read_receipt(self, event):
        """Send read receipt to WebSocket"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "read_receipt",
                    "message_id": event["message_id"],
                    "user_id": event["user_id"],
                    "timestamp": event["timestamp"],
                }
            )
        )

    @database_sync_to_async
    def save_message(self, project_id, user, content, attachments):
        """Save chat message to database"""
        from core.models import ChatChannel, ChatMessage, Project

        project = Project.objects.get(id=project_id)

        # Get or create project channel
        channel, _ = ChatChannel.objects.get_or_create(project=project, defaults={"name": f"Project: {project.name}"})

        # Create message
        message = ChatMessage.objects.create(
            channel=channel,
            user=user,
            message=content,  # Changed from content to message
        )

        return message.id

    @database_sync_to_async
    def mark_message_read(self, message_id, user):
        """Mark message as read by user"""
        from core.models import ChatMessage

        try:
            message = ChatMessage.objects.get(id=message_id)
            message.mark_as_read(user)  # Use the new method
            return True
        except ChatMessage.DoesNotExist:
            return False


class DirectChatConsumer(RateLimitMixin, AsyncWebsocketConsumer):
    """
    WebSocket consumer for direct messages between two users.
    Rate limited to 30 messages per minute.
    """
    
    rate_limit_messages = 30
    rate_limit_window = 60

    async def connect(self):
        """Accept WebSocket connection for direct chat"""
        try:
            query = parse_qs(self.scope.get("query_string", b"").decode())  # type: ignore[typeddict-item]
            lang = (query.get("lang", [None])[0] or "").split('-')[0]
            if lang:
                translation.activate(lang)
                self.lang = lang
        except Exception:
            self.lang = None
        self.other_user_id = self.scope["url_route"]["kwargs"]["user_id"]  # type: ignore[typeddict-item]
        self.user = self.scope["user"]  # type: ignore[typeddict-item]

        # Create unique room name (sorted user IDs for consistency)
        user_ids = sorted([self.user.id, int(self.other_user_id)])  # type: ignore[union-attr]
        self.room_group_name = f"direct_chat_{user_ids[0]}_{user_ids[1]}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        """Leave direct chat group"""
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """Receive and broadcast direct message"""
        # Rate limit check
        if not await self.check_rate_limit():
            return
        data = json.loads(text_data)

        # Save message to database
        message_id = await self.save_direct_message(
            from_user=self.user, to_user_id=self.other_user_id, content=data["message"]
        )

        # Broadcast to both users
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "direct_message",
                "message_id": message_id,
                "message": data["message"],
                "from_user_id": self.user.id,  # type: ignore[union-attr]
                "from_username": self.user.username,  # type: ignore[union-attr]
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def direct_message(self, event):
        """Send direct message to WebSocket"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "message",
                    "message_id": event["message_id"],
                    "message": event["message"],
                    "from_user_id": event["from_user_id"],
                    "from_username": event["from_username"],
                    "timestamp": event["timestamp"],
                }
            )
        )

    @database_sync_to_async
    def save_direct_message(self, from_user, to_user_id, content):
        """Save direct message to database"""
        from core.models import ChatChannel, ChatMessage

        # Get or create direct message channel
        to_user = User.objects.get(id=to_user_id)
        user_ids = sorted([from_user.id, to_user.id])  # type: ignore[attr-defined]

        channel, _ = ChatChannel.objects.get_or_create(
            name=f"DM_{user_ids[0]}_{user_ids[1]}", defaults={"is_direct": True}
        )

        # Add participants if needed
        channel.participants.add(from_user, to_user)

        # Create message
        message = ChatMessage.objects.create(
            channel=channel,
            user=from_user,
            content=content,
        )

        return message.id


class NotificationConsumer(RateLimitMixin, AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications.

    Sends live updates for:
    - New tasks assigned
    - Invoice status changes
    - Project updates
    - Chat mentions
    - System alerts
    
    Rate limited to 100 messages per minute.
    """
    
    rate_limit_messages = 100
    rate_limit_window = 60

    async def connect(self):
        """Connect to user's notification channel"""
        try:
            query = parse_qs(self.scope.get("query_string", b"").decode())  # type: ignore[typeddict-item]
            lang = (query.get("lang", [None])[0] or "").split('-')[0]
            if lang:
                translation.activate(lang)
                self.lang = lang
        except Exception:
            self.lang = None
        self.user = self.scope["user"]  # type: ignore[typeddict-item]
        self.room_group_name = f"notifications_{self.user.id}"  # type: ignore[union-attr]

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        # Send unread notification count on connect
        unread_count = await self.get_unread_count()
        await self.send(
            text_data=json.dumps(
                {
                    "type": "unread_count",
                    "count": unread_count,
                }
            )
        )

    async def disconnect(self, close_code):
        """Disconnect from notification channel"""
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """Mark notification as read"""
        # Rate limit check
        if not await self.check_rate_limit():
            return
        
        data = json.loads(text_data)

        if data.get("type") == "mark_read":
            await self.mark_notification_read(data["notification_id"])

            # Send updated unread count
            unread_count = await self.get_unread_count()
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "unread_count",
                        "count": unread_count,
                    }
                )
            )

    async def notification(self, event):
        """Send notification to WebSocket"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "notification",
                    "id": event["notification_id"],
                    "title": event["title"],
                    "message": event["message"],
                    "notification_type": event["notification_type"],
                    "priority": event.get("priority", "normal"),
                    "url": event.get("url", ""),
                    "timestamp": event["timestamp"],
                }
            )
        )

    @database_sync_to_async
    def get_unread_count(self):
        """Get count of unread notifications"""
        from core.models import Notification

        return Notification.objects.filter(user=self.user, is_read=False).count()

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark notification as read"""
        from core.models import Notification

        Notification.objects.filter(id=notification_id, user=self.user).update(is_read=True)


class DashboardConsumer(AsyncWebsocketConsumer):
    """
    Real-time dashboard updates for project metrics.

    Sends live updates for:
    - Earned Value metrics
    - Time entries
    - Budget vs actual
    - Task completion
    - Quality scores
    """

    async def connect(self):
        """Connect to project dashboard channel"""
        self.project_id = self.scope["url_route"]["kwargs"]["project_id"]  # type: ignore[typeddict-item]
        self.room_group_name = f"dashboard_project_{self.project_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        # Send initial dashboard data
        dashboard_data = await self.get_dashboard_data()
        await self.send(text_data=json.dumps({"type": "dashboard_data", **dashboard_data}))

    async def disconnect(self, close_code):
        """Disconnect from dashboard channel"""
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def dashboard_update(self, event):
        """Send dashboard update to WebSocket"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "dashboard_update",
                    "metric": event["metric"],
                    "value": event["value"],
                    "timestamp": event["timestamp"],
                }
            )
        )

    @database_sync_to_async
    def get_dashboard_data(self):
        """Get current dashboard metrics"""
        from core.models import Project

        try:
            project = Project.objects.get(id=self.project_id)
            ev_data = project.earned_value_summary()

            return {
                "project_name": project.name,
                "earned_value": ev_data,
                "budget_total": float(project.budget_total),
                "total_expenses": float(project.total_expenses),
                "budget_remaining": float(project.budget_remaining),
                "profit": float(project.profit()),
            }
        except Project.DoesNotExist:
            return {}


class AdminDashboardConsumer(AsyncWebsocketConsumer):
    """Real-time admin dashboard with all projects overview"""

    async def connect(self):
        """Connect to admin dashboard channel"""
        # Security: Only admin/staff users can connect
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close()
            return
        if not (user.is_staff or user.is_superuser):
            await self.close()
            return
        
        self.room_group_name = "dashboard_admin"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        """Disconnect from admin dashboard"""
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def admin_update(self, event):
        """Send admin dashboard update"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "admin_update",
                    "data": event["data"],
                    "timestamp": event["timestamp"],
                }
            )
        )


class DailyPlanConsumer(AsyncWebsocketConsumer):
    """Real-time updates for daily plans"""

    async def connect(self):
        """Connect to daily plan channel"""
        self.date = self.scope["url_route"]["kwargs"]["date"]  # type: ignore[typeddict-item]
        self.room_group_name = f"daily_plan_{self.date}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        """Disconnect from daily plan channel"""
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def plan_update(self, event):
        """Send daily plan update"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "plan_update",
                    "plan_id": event["plan_id"],
                    "status": event["status"],
                    "timestamp": event["timestamp"],
                }
            )
        )


class QualityInspectionConsumer(AsyncWebsocketConsumer):
    """Real-time quality inspection updates"""

    async def connect(self):
        """Connect to quality inspection channel"""
        self.inspection_id = self.scope["url_route"]["kwargs"]["inspection_id"]  # type: ignore[typeddict-item]
        self.room_group_name = f"quality_inspection_{self.inspection_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        """Disconnect from quality inspection channel"""
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def inspection_update(self, event):
        """Send quality inspection update"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "inspection_update",
                    "defect_count": event["defect_count"],
                    "overall_score": event["overall_score"],
                    "timestamp": event["timestamp"],
                }
            )
        )


class TaskConsumer(RateLimitMixin, AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time task updates.
    Handles task creation, updates, deletion, and status changes.
    Rate limited to 60 messages per minute.
    """
    
    rate_limit_messages = 60
    rate_limit_window = 60

    async def connect(self):
        """Accept connection and join project task group"""
        try:
            query = parse_qs(self.scope.get("query_string", b"").decode())  # type: ignore[typeddict-item]
            lang = (query.get("lang", [None])[0] or "").split('-')[0]
            if lang:
                translation.activate(lang)
                self.lang = lang
        except Exception:
            self.lang = None
        self.project_id = self.scope["url_route"]["kwargs"]["project_id"]  # type: ignore[typeddict-item]
        self.task_group_name = f"tasks_project_{self.project_id}"
        self.user = self.scope["user"]  # type: ignore[typeddict-item]

        # Join task group
        await self.channel_layer.group_add(self.task_group_name, self.channel_name)
        await self.accept()

        # Send connection confirmation
        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection_established",
                    "message": _("Connected to task updates"),
                    "project_id": self.project_id,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        )

    async def disconnect(self, close_code):
        """Leave task group"""
        await self.channel_layer.group_discard(self.task_group_name, self.channel_name)

    async def receive(self, text_data):
        """Handle task-related actions"""
        # Rate limit check
        if not await self.check_rate_limit():
            return
        
        try:
            data = json.loads(text_data)
            action = data.get("action")

            if action == "subscribe_task":
                task_id = data.get("task_id")
                # Handle task subscription logic
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "task_subscribed",
                            "task_id": task_id,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                )
        except json.JSONDecodeError:
            await self.send(
                text_data=json.dumps(
                    {"type": "error", "message": "Invalid JSON format"}
                )
            )

    async def task_created(self, event):
        """Send task created notification"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "task_created",
                    "task_id": event.get("task_id"),
                    "task_data": event.get("task_data"),
                    "timestamp": event.get("timestamp"),
                }
            )
        )

    async def task_updated(self, event):
        """Send task updated notification"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "task_updated",
                    "task_id": event.get("task_id"),
                    "task_data": event.get("task_data"),
                    "changes": event.get("changes"),
                    "timestamp": event.get("timestamp"),
                }
            )
        )

    async def task_deleted(self, event):
        """Send task deleted notification"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "task_deleted",
                    "task_id": event.get("task_id"),
                    "timestamp": event.get("timestamp"),
                }
            )
        )

    async def task_status_changed(self, event):
        """Send task status change notification"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "task_status_changed",
                    "task_id": event.get("task_id"),
                    "old_status": event.get("old_status"),
                    "new_status": event.get("new_status"),
                    "timestamp": event.get("timestamp"),
                }
            )
        )


class StatusConsumer(RateLimitMixin, AsyncWebsocketConsumer):
    """
    WebSocket consumer for user online/offline status.
    Manages user presence and heartbeat.
    Higher rate limit (120/min) due to frequent heartbeats every 30s.
    """
    
    rate_limit_messages = 120  # Higher limit for heartbeats
    rate_limit_window = 60

    async def connect(self):
        """Accept connection and join status group"""
        self.user = self.scope["user"]  # type: ignore[typeddict-item]
        self.status_group_name = "user_status"

        # Join status group
        await self.channel_layer.group_add(self.status_group_name, self.channel_name)
        await self.accept()

        # Mark user as online and broadcast
        await self.set_user_online()
        await self.channel_layer.group_send(
            self.status_group_name,
            {
                "type": "user_status_changed",
                "user_id": self.user.id,  # type: ignore[union-attr]
                "username": self.user.username,  # type: ignore[union-attr]
                "status": "online",
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Send online users list
        online_users = await self.get_online_users()
        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection_established",
                    "message": "Connected to status updates",
                    "online_users": online_users,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        )

    async def disconnect(self, close_code):
        """Mark user as offline and leave status group"""
        if hasattr(self, "user") and hasattr(self.user, "is_authenticated"):  # type: ignore[union-attr]
            await self.set_user_offline()
            await self.channel_layer.group_send(
                self.status_group_name,
                {
                    "type": "user_status_changed",
                    "user_id": self.user.id,  # type: ignore[union-attr]
                    "username": self.user.username,  # type: ignore[union-attr]
                    "status": "offline",
                    "timestamp": datetime.now().isoformat(),
                },
            )
            await self.channel_layer.group_discard(self.status_group_name, self.channel_name)

    async def receive(self, text_data):
        """Handle status updates (heartbeat)"""
        # Rate limit check
        if not await self.check_rate_limit():
            return
        
        try:
            data = json.loads(text_data)
            action = data.get("action")

            if action == "heartbeat":
                await self.update_heartbeat()
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "heartbeat_ack",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                )
        except json.JSONDecodeError:
            pass

    async def user_status_changed(self, event):
        """Send user status change to WebSocket"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_status_changed",
                    "user_id": event["user_id"],
                    "username": event["username"],
                    "status": event["status"],
                    "timestamp": event["timestamp"],
                }
            )
        )

    @database_sync_to_async
    def set_user_online(self):
        """Mark user as online in database"""
        from core.models import UserStatus
        
        status, created = UserStatus.objects.get_or_create(user=self.user)  # type: ignore[union-attr]
        status.mark_online()

    @database_sync_to_async
    def set_user_offline(self):
        """Mark user as offline in database"""
        from core.models import UserStatus
        
        try:
            status = UserStatus.objects.get(user=self.user)  # type: ignore[union-attr]
            status.mark_offline()
        except UserStatus.DoesNotExist:
            pass

    @database_sync_to_async
    def update_heartbeat(self):
        """Update user's last seen timestamp"""
        from core.models import UserStatus
        
        try:
            status = UserStatus.objects.get(user=self.user)  # type: ignore[union-attr]
            status.update_heartbeat()
        except UserStatus.DoesNotExist:
            # Create if doesn't exist
            status = UserStatus.objects.create(user=self.user)  # type: ignore[union-attr]
            status.mark_online()

    @database_sync_to_async
    def get_online_users(self) -> list:
        """Get list of online users"""
        from core.models import UserStatus
        
        online_statuses = UserStatus.get_online_users()
        return [
            {
                "user_id": status.user.id,
                "username": status.user.username,
                "last_seen": status.last_seen.isoformat() if status.last_seen else None,
            }
            for status in online_statuses
        ]
