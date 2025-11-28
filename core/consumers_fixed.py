"""
WebSocket consumers for Kibray real-time features.

Uses Django Channels to handle WebSocket connections for:
- Real-time chat
- Live notifications
- Dashboard updates
- Project activity broadcast
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer  # type: ignore
from channels.db import database_sync_to_async  # type: ignore
from django.contrib.auth.models import User
from datetime import datetime


class ProjectChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for project-specific chat rooms.

    Features:
    - Real-time message delivery
    - Read receipts
    - Typing indicators
    - File attachment notifications
    - @mentions
    """

    async def connect(self):
        """Accept WebSocket connection and join project chat group"""
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
        from core.models import ChatMessage, ChatChannel, Project

        project = Project.objects.get(id=project_id)

        # Get or create project channel
        channel, _ = ChatChannel.objects.get_or_create(project=project, defaults={"name": f"Project: {project.name}"})

        # Create message
        message = ChatMessage.objects.create(
            channel=channel,
            user=user,
            content=content,
        )

        return message.id

    @database_sync_to_async
    def mark_message_read(self, message_id, user):
        """Mark message as read by user"""
        from core.models import ChatMessage

        try:
            message = ChatMessage.objects.get(id=message_id)
            # Add read tracking logic here (create MessageRead model if needed)
            return True
        except ChatMessage.DoesNotExist:
            return False


class DirectChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for direct messages between two users"""

    async def connect(self):
        """Accept WebSocket connection for direct chat"""
        self.other_user_id = self.scope["url_route"]["kwargs"]["user_id"]  # type: ignore[typeddict-item]
        self.user = self.scope["user"]  # type: ignore[typeddict-item]

        # Create unique room name (sorted user IDs for consistency)
        user_ids = sorted([int(self.user.id), int(self.other_user_id)])  # type: ignore[union-attr]
        self.room_group_name = f"direct_chat_{user_ids[0]}_{user_ids[1]}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        """Leave direct chat group"""
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """Receive and broadcast direct message"""
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
        from core.models import ChatMessage, ChatChannel

        # Get or create direct message channel
        to_user = User.objects.get(id=to_user_id)
        user_ids = sorted([int(from_user.id), int(to_user.id)])  # type: ignore[attr-defined]

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


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications.

    Sends live updates for:
    - New tasks assigned
    - Invoice status changes
    - Project updates
    - Chat mentions
    - System alerts
    """

    async def connect(self):
        """Connect to user's notification channel"""
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
