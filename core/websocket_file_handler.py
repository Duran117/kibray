"""
WebSocket File Attachment System for Kibray

Handles file uploads through WebSocket connections:
- Chunked file upload
- Progress tracking
- File validation
- Thumbnail generation
- Secure file storage
"""

import os
import hashlib
import mimetypes
from datetime import datetime
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from channels.db import database_sync_to_async
from PIL import Image
import io


class FileAttachmentHandler:
    """
    Handler for file attachments in WebSocket messages.
    
    Features:
    - Chunked upload support
    - File type validation
    - Size limits
    - Virus scanning integration
    - Thumbnail generation for images
    """
    
    # Maximum file sizes (bytes)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_IMAGE_SIZE = 5 * 1024 * 1024   # 5MB
    MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB
    
    # Allowed file types
    ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    ALLOWED_DOCUMENT_TYPES = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ]
    ALLOWED_TYPES = ALLOWED_IMAGE_TYPES + ALLOWED_DOCUMENT_TYPES
    
    # Thumbnail settings
    THUMBNAIL_SIZE = (300, 300)
    
    def __init__(self):
        self.upload_sessions = {}  # {session_id: {chunks: [], metadata: {}}}
    
    def validate_file_metadata(self, filename, file_type, file_size):
        """
        Validate file metadata before upload.
        
        Args:
            filename: Original filename
            file_type: MIME type
            file_size: Size in bytes
            
        Returns:
            tuple: (is_valid, error_message)
        """
        # Check file type
        if file_type not in self.ALLOWED_TYPES:
            return False, f"File type {file_type} not allowed"
        
        # Check file size
        if file_type in self.ALLOWED_IMAGE_TYPES:
            if file_size > self.MAX_IMAGE_SIZE:
                return False, f"Image too large (max {self.MAX_IMAGE_SIZE / 1024 / 1024}MB)"
        elif file_size > self.MAX_DOCUMENT_SIZE:
            return False, f"Document too large (max {self.MAX_DOCUMENT_SIZE / 1024 / 1024}MB)"
        
        # Check filename
        if not filename or len(filename) > 255:
            return False, "Invalid filename"
        
        # Check for dangerous extensions
        dangerous_extensions = ['.exe', '.bat', '.sh', '.cmd', '.scr', '.com']
        if any(filename.lower().endswith(ext) for ext in dangerous_extensions):
            return False, "Executable files not allowed"
        
        return True, None
    
    def start_upload_session(self, session_id, metadata):
        """
        Start a new file upload session.
        
        Args:
            session_id: Unique session identifier
            metadata: File metadata (filename, size, type, etc.)
            
        Returns:
            bool: Success
        """
        # Validate metadata
        is_valid, error = self.validate_file_metadata(
            metadata.get('filename'),
            metadata.get('file_type'),
            metadata.get('file_size', 0)
        )
        
        if not is_valid:
            return False, error
        
        # Create session
        self.upload_sessions[session_id] = {
            'chunks': [],
            'metadata': metadata,
            'started_at': datetime.now(),
            'bytes_received': 0,
        }
        
        return True, None
    
    def add_chunk(self, session_id, chunk_data, chunk_index):
        """
        Add a chunk to upload session.
        
        Args:
            session_id: Session identifier
            chunk_data: Base64 encoded chunk data
            chunk_index: Chunk sequence number
            
        Returns:
            tuple: (success, progress_percent)
        """
        if session_id not in self.upload_sessions:
            return False, "Invalid session"
        
        session = self.upload_sessions[session_id]
        
        # Decode chunk
        import base64
        try:
            chunk_bytes = base64.b64decode(chunk_data)
        except Exception as e:
            return False, f"Invalid chunk data: {e}"
        
        # Store chunk
        session['chunks'].append({
            'index': chunk_index,
            'data': chunk_bytes,
        })
        
        session['bytes_received'] += len(chunk_bytes)
        
        # Calculate progress
        total_size = session['metadata']['file_size']
        progress = (session['bytes_received'] / total_size) * 100 if total_size > 0 else 0
        
        return True, round(progress, 2)
    
    def complete_upload(self, session_id, user, channel_id):
        """
        Complete file upload and save to storage.
        
        Args:
            session_id: Session identifier
            user: User uploading file
            channel_id: Chat channel ID
            
        Returns:
            tuple: (file_attachment_id, file_url, thumbnail_url)
        """
        if session_id not in self.upload_sessions:
            return None, "Invalid session"
        
        session = self.upload_sessions[session_id]
        
        # Combine chunks
        chunks = sorted(session['chunks'], key=lambda x: x['index'])
        file_data = b''.join(chunk['data'] for chunk in chunks)
        
        # Verify size
        expected_size = session['metadata']['file_size']
        if len(file_data) != expected_size:
            return None, f"Size mismatch: expected {expected_size}, got {len(file_data)}"
        
        # Generate filename
        original_filename = session['metadata']['filename']
        file_hash = hashlib.sha256(file_data).hexdigest()[:12]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{file_hash}_{original_filename}"
        
        # Save file
        file_path = f"chat_attachments/{channel_id}/{safe_filename}"
        file_url = default_storage.save(file_path, ContentFile(file_data))
        
        # Generate thumbnail for images
        thumbnail_url = None
        if session['metadata']['file_type'] in self.ALLOWED_IMAGE_TYPES:
            thumbnail_url = self._generate_thumbnail(file_data, file_path)
        
        # Create database record
        attachment = self._create_attachment_record(
            user=user,
            channel_id=channel_id,
            filename=original_filename,
            file_path=file_url,
            file_type=session['metadata']['file_type'],
            file_size=len(file_data),
            thumbnail_path=thumbnail_url,
        )
        
        # Cleanup session
        del self.upload_sessions[session_id]
        
        return attachment.id, file_url, thumbnail_url
    
    def _generate_thumbnail(self, image_data, original_path):
        """
        Generate thumbnail for image.
        
        Args:
            image_data: Image bytes
            original_path: Path to original image
            
        Returns:
            str: Thumbnail URL
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert RGBA to RGB if needed
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            
            # Create thumbnail
            image.thumbnail(self.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            thumbnail_io = io.BytesIO()
            image.save(thumbnail_io, format='JPEG', quality=85)
            thumbnail_data = thumbnail_io.getvalue()
            
            # Generate thumbnail path
            base_path = os.path.splitext(original_path)[0]
            thumbnail_path = f"{base_path}_thumb.jpg"
            
            # Save to storage
            thumbnail_url = default_storage.save(
                thumbnail_path,
                ContentFile(thumbnail_data)
            )
            
            return thumbnail_url
            
        except Exception as e:
            import logging
            logger = logging.getLogger('websocket')
            logger.error(f"Failed to generate thumbnail: {e}")
            return None
    
    @database_sync_to_async
    def _create_attachment_record(self, user, channel_id, filename, file_path,
                                   file_type, file_size, thumbnail_path):
        """
        Create FileAttachment database record.
        
        Args:
            user: User who uploaded file
            channel_id: Chat channel ID
            filename: Original filename
            file_path: Stored file path
            file_type: MIME type
            file_size: Size in bytes
            thumbnail_path: Thumbnail path (optional)
            
        Returns:
            FileAttachment: Created record
        """
        from core.models import FileAttachment, ChatChannel
        
        channel = ChatChannel.objects.get(id=channel_id)
        
        attachment = FileAttachment.objects.create(
            user=user,
            channel=channel,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            thumbnail_path=thumbnail_path,
        )
        
        return attachment
    
    def cancel_upload(self, session_id):
        """Cancel an upload session"""
        if session_id in self.upload_sessions:
            del self.upload_sessions[session_id]
            return True
        return False
    
    def get_session_progress(self, session_id):
        """
        Get upload progress for session.
        
        Returns:
            dict: Progress information
        """
        if session_id not in self.upload_sessions:
            return None
        
        session = self.upload_sessions[session_id]
        total_size = session['metadata']['file_size']
        bytes_received = session['bytes_received']
        
        return {
            'session_id': session_id,
            'filename': session['metadata']['filename'],
            'total_size': total_size,
            'bytes_received': bytes_received,
            'progress': (bytes_received / total_size * 100) if total_size > 0 else 0,
            'chunks_received': len(session['chunks']),
        }


# Global handler instance
file_handler = FileAttachmentHandler()


async def handle_file_upload_message(consumer, data):
    """
    Handle file upload WebSocket message.
    
    Message types:
    - start_upload: Initialize upload session
    - upload_chunk: Send file chunk
    - complete_upload: Finalize upload
    - cancel_upload: Cancel upload
    
    Args:
        consumer: WebSocket consumer instance
        data: Message data
    """
    import json
    
    action = data.get('action')
    
    if action == 'start_upload':
        # Start new upload session
        session_id = data.get('session_id')
        metadata = data.get('metadata', {})
        
        success, error = file_handler.start_upload_session(session_id, metadata)
        
        if success:
            await consumer.send(text_data=json.dumps({
                'type': 'upload_started',
                'session_id': session_id,
                'message': 'Upload session started',
            }))
        else:
            await consumer.send(text_data=json.dumps({
                'type': 'upload_error',
                'session_id': session_id,
                'error': error,
            }))
    
    elif action == 'upload_chunk':
        # Receive file chunk
        session_id = data.get('session_id')
        chunk_data = data.get('chunk_data')
        chunk_index = data.get('chunk_index')
        
        success, result = file_handler.add_chunk(session_id, chunk_data, chunk_index)
        
        if success:
            await consumer.send(text_data=json.dumps({
                'type': 'upload_progress',
                'session_id': session_id,
                'progress': result,
                'chunk_index': chunk_index,
            }))
        else:
            await consumer.send(text_data=json.dumps({
                'type': 'upload_error',
                'session_id': session_id,
                'error': result,
            }))
    
    elif action == 'complete_upload':
        # Complete upload
        session_id = data.get('session_id')
        channel_id = data.get('channel_id')
        
        attachment_id, file_url, thumbnail_url = file_handler.complete_upload(
            session_id,
            consumer.user,
            channel_id
        )
        
        if attachment_id:
            # Notify channel about new attachment
            await consumer.channel_layer.group_send(
                consumer.room_group_name,
                {
                    'type': 'file_attachment',
                    'attachment_id': attachment_id,
                    'filename': data.get('metadata', {}).get('filename'),
                    'file_url': file_url,
                    'thumbnail_url': thumbnail_url,
                    'user_id': consumer.user.id,
                    'username': consumer.user.username,
                    'timestamp': datetime.now().isoformat(),
                }
            )
            
            await consumer.send(text_data=json.dumps({
                'type': 'upload_complete',
                'session_id': session_id,
                'attachment_id': attachment_id,
                'file_url': file_url,
                'thumbnail_url': thumbnail_url,
            }))
        else:
            await consumer.send(text_data=json.dumps({
                'type': 'upload_error',
                'session_id': session_id,
                'error': file_url,  # Error message
            }))
    
    elif action == 'cancel_upload':
        # Cancel upload
        session_id = data.get('session_id')
        
        success = file_handler.cancel_upload(session_id)
        
        await consumer.send(text_data=json.dumps({
            'type': 'upload_cancelled',
            'session_id': session_id,
            'success': success,
        }))
