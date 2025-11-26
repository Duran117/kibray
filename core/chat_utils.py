"""
Utilities for Chat System - @mentions parsing and entity linking
"""
import re
from django.contrib.auth import get_user_model
from typing import List, Dict, Any

User = get_user_model()


def parse_mentions(message_text: str) -> List[Dict[str, Any]]:
    """
    Parse @mentions from message text.
    
    Supports:
    - @username - simple user mention
    - @task#123 - entity linking to task ID 123
    - @damage#45 - entity linking to damage report ID 45
    - @color#7 - entity linking to color sample ID 7
    
    Returns list of mention dictionaries with keys:
    - mention_type: 'user' or entity type ('task', 'damage', etc.)
    - raw_text: original mention string
    - username: (if user mention)
    - entity_type: (if entity mention)
    - entity_id: (if entity mention)
    """
    mentions = []
    
    # Pattern 1: Entity mentions like @task#123, @damage#45
    entity_pattern = r'@(task|damage|color_sample|floor_plan|material|change_order)#(\d+)'
    for match in re.finditer(entity_pattern, message_text, re.IGNORECASE):
        entity_type = match.group(1).lower()
        entity_id = int(match.group(2))
        mentions.append({
            'mention_type': 'entity',
            'raw_text': match.group(0),
            'entity_type': entity_type,
            'entity_id': entity_id,
        })
    
    # Pattern 2: Simple user mentions like @alice, @bob_smith
    user_pattern = r'@([a-zA-Z0-9_]{3,30})\b'
    for match in re.finditer(user_pattern, message_text):
        username = match.group(1)
        # Avoid duplicates if already captured as entity
        if not any(m.get('raw_text') == match.group(0) for m in mentions):
            mentions.append({
                'mention_type': 'user',
                'raw_text': match.group(0),
                'username': username,
            })
    
    return mentions


def create_mention_objects(message, mentions_data: List[Dict[str, Any]]) -> List['ChatMention']:
    """
    Create ChatMention objects for parsed mentions.
    
    Args:
        message: ChatMessage instance
        mentions_data: List of mention dicts from parse_mentions()
    
    Returns:
        List of created ChatMention instances
    """
    from core.models import ChatMention
    
    created = []
    for mention in mentions_data:
        if mention['mention_type'] == 'user':
            # Try to find user by username
            try:
                user = User.objects.get(username=mention['username'])
                mention_obj = ChatMention.objects.create(
                    message=message,
                    mentioned_user=user,
                    entity_type='user',
                )
                created.append(mention_obj)
            except User.DoesNotExist:
                # Skip if user not found
                pass
        
        elif mention['mention_type'] == 'entity':
            # Create entity link mention
            mention_obj = ChatMention.objects.create(
                message=message,
                entity_type=mention['entity_type'],
                entity_id=mention['entity_id'],
                entity_label=f"{mention['entity_type']} #{mention['entity_id']}",
            )
            created.append(mention_obj)
    
    return created


def create_mention_notifications(mention_objects: List['ChatMention']) -> None:
    """
    Create notifications for users mentioned in chat message.
    Only notifies direct @user mentions, not entity links.
    """
    from core.models import Notification
    
    for mention in mention_objects:
        if mention.mentioned_user and mention.entity_type == 'user':
            # Get message info
            message = mention.message
            sender = message.user
            channel = message.channel
            project = channel.project
            
            # Don't notify if user mentions themselves
            if sender == mention.mentioned_user:
                continue
            
            # Create notification
            Notification.objects.create(
                user=mention.mentioned_user,
                notification_type='chat_message',
                title=f'@{sender.username} mentioned you in {channel.name}',
                message=message.message[:200],  # Truncate long messages
                related_object_type='chat_message',
                related_object_id=message.id,
                link_url=f'/projects/{project.id}/chat/{channel.id}/',
            )


def get_entity_display_label(entity_type: str, entity_id: int) -> str:
    """
    Get human-readable label for entity reference.
    
    Returns string like "Task #45: Paint walls" or "Damage #12: Broken tile"
    """
    try:
        if entity_type == 'task':
            from core.models import Task
            obj = Task.objects.get(id=entity_id)
            return f"Task #{obj.id}: {obj.title[:50]}"
        
        elif entity_type == 'damage':
            from core.models import DamageReport
            obj = DamageReport.objects.get(id=entity_id)
            return f"Damage #{obj.id}: {obj.title[:50]}"
        
        elif entity_type == 'color_sample':
            from core.models import ColorSample
            obj = ColorSample.objects.get(id=entity_id)
            return f"Color #{obj.id}: {obj.room_name or 'Sample'}"
        
        elif entity_type == 'material':
            from core.models import Material
            obj = Material.objects.get(id=entity_id)
            return f"Material: {obj.name[:50]}"
        
        elif entity_type == 'change_order':
            from core.models import ChangeOrder
            obj = ChangeOrder.objects.get(id=entity_id)
            return f"CO #{obj.id}: {obj.description[:50]}"
        
        else:
            return f"{entity_type} #{entity_id}"
    
    except Exception:
        return f"{entity_type} #{entity_id}"


def enrich_mentions_with_labels(mention_objects: List['ChatMention']) -> None:
    """
    Update entity_label for all ChatMention objects with proper display labels.
    """
    for mention in mention_objects:
        if mention.entity_type != 'user' and mention.entity_id:
            label = get_entity_display_label(mention.entity_type, mention.entity_id)
            mention.entity_label = label
            mention.save(update_fields=['entity_label'])
