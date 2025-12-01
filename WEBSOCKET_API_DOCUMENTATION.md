# WebSocket System - Complete API Documentation

**Phase 6 - Real-time Communication System**

Version: 1.0.0  
Last Updated: 2024

## 📚 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Getting Started](#getting-started)
4. [WebSocket Consumers](#websocket-consumers)
5. [Message Types](#message-types)
6. [Authentication](#authentication)
7. [Rate Limiting](#rate-limiting)
8. [Security](#security)
9. [Error Handling](#error-handling)
10. [Best Practices](#best-practices)
11. [Deployment](#deployment)
12. [Troubleshooting](#troubleshooting)

---

## Overview

The Kibray WebSocket system provides real-time communication capabilities for:
- **Chat Messaging**: Instant messaging between team members
- **Live Notifications**: Real-time alerts and updates
- **User Status**: Online/offline/typing indicators
- **File Sharing**: Real-time file upload progress and sharing
- **Collaborative Features**: Multi-user editing and updates

### Key Features

✅ **Real-time Communication**: Instant message delivery  
✅ **Offline Support**: Queue messages when disconnected  
✅ **File Attachments**: Send files with chunked upload  
✅ **Push Notifications**: FCM integration for mobile/web  
✅ **Compression**: permessage-deflate for bandwidth optimization  
✅ **Security**: XSS prevention, rate limiting, authentication  
✅ **Metrics**: Real-time monitoring dashboard  
✅ **Scalability**: Redis backing for horizontal scaling  

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Client (Browser/App)                  │
│  - WebSocket Client                                          │
│  - Offline Queue                                             │
│  - Connection Manager                                        │
└─────────────────────────────────────────────────────────────┘
                              ↓ WSS://
┌─────────────────────────────────────────────────────────────┐
│                     Load Balancer (Optional)                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       Django Channels                        │
│  - ASGI Server (Daphne/Uvicorn)                             │
│  - WebSocket Consumers                                       │
│  - Channel Layer (Redis)                                     │
│  - Rate Limiting                                             │
│  - Authentication                                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                         Backends                             │
│  - PostgreSQL (Messages, Users, etc.)                        │
│  - Redis (Channel Layer, Cache, Rate Limits)                 │
│  - Celery (Background Tasks)                                 │
│  - File Storage (S3/Local)                                   │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Backend**: Django 4.2+, Django Channels 4.0+
- **ASGI Server**: Daphne or Uvicorn
- **Channel Layer**: Redis 6.0+
- **Database**: PostgreSQL 13+
- **Cache**: Redis
- **Task Queue**: Celery
- **Frontend**: React 18+, WebSocket API

---

## Getting Started

### Prerequisites

```bash
# Python 3.9+
python --version

# Redis 6.0+
redis-cli --version

# PostgreSQL 13+
psql --version
```

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Key WebSocket packages
pip install channels==4.0.0
pip install channels-redis==4.1.0
pip install daphne==4.0.0
```

### Configuration

#### settings.py

```python
# ASGI Application
ASGI_APPLICATION = 'kibray_backend.asgi.application'

# Channel Layers
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
            'capacity': 1500,
            'expiry': 10,
        },
    },
}

# WebSocket Settings
WEBSOCKET_RATE_LIMIT = 60  # messages per minute
WEBSOCKET_MESSAGE_MAX_SIZE = 1024 * 1024  # 1 MB
WEBSOCKET_CONNECTION_TIMEOUT = 3600  # 1 hour
```

#### asgi.py

```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from core.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kibray_backend.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
```

### Running the Server

#### Development

```bash
# Start Django (HTTP)
python manage.py runserver

# Start Daphne (WebSocket)
daphne -b 0.0.0.0 -p 8001 kibray_backend.asgi:application
```

#### Production

```bash
# Start with supervisor or systemd
daphne -b 127.0.0.1 -p 8001 \
  --proxy-headers \
  kibray_backend.asgi:application
```

---

## WebSocket Consumers

### Available Endpoints

| Endpoint | Consumer | Purpose |
|----------|----------|---------|
| `/ws/chat/<room_name>/` | ChatConsumer | Chat messaging |
| `/ws/notifications/` | NotificationConsumer | Real-time notifications |
| `/ws/status/` | StatusConsumer | User online status |

### ChatConsumer

**Endpoint**: `/ws/chat/<room_name>/`

**Features**:
- Send/receive messages
- Typing indicators
- Read receipts
- File attachments
- Message editing/deletion

#### Connection

```javascript
const socket = new WebSocket(
  `wss://your-domain.com/ws/chat/${roomName}/`
);

socket.onopen = () => {
  console.log('Connected to chat');
};

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  handleMessage(data);
};

socket.onerror = (error) => {
  console.error('WebSocket error:', error);
};

socket.onclose = (event) => {
  console.log('Disconnected:', event.code, event.reason);
};
```

#### Send Message

```javascript
socket.send(JSON.stringify({
  type: 'chat_message',
  message: 'Hello, world!',
  channel_id: 123,
}));
```

#### Receive Message

```javascript
{
  "type": "chat_message",
  "message": {
    "id": 456,
    "content": "Hello, world!",
    "author": {
      "id": 1,
      "username": "john",
      "avatar": "/media/avatars/john.jpg"
    },
    "timestamp": "2024-01-01T12:00:00Z",
    "channel_id": 123
  }
}
```

### NotificationConsumer

**Endpoint**: `/ws/notifications/`

**Features**:
- Real-time notifications
- Notification acknowledgment
- Unread count updates

#### Connection

```javascript
const socket = new WebSocket(
  'wss://your-domain.com/ws/notifications/'
);
```

#### Receive Notification

```javascript
{
  "type": "notification",
  "notification": {
    "id": 789,
    "title": "New Task Assigned",
    "message": "You've been assigned a new task",
    "category": "task",
    "url": "/tasks/123",
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

#### Mark as Read

```javascript
socket.send(JSON.stringify({
  type: 'mark_read',
  notification_id: 789,
}));
```

### StatusConsumer

**Endpoint**: `/ws/status/`

**Features**:
- User online/offline status
- Typing indicators
- Last seen timestamps

#### Set Status

```javascript
socket.send(JSON.stringify({
  type: 'status_update',
  status: 'online',  // online, away, busy, offline
}));
```

#### Typing Indicator

```javascript
socket.send(JSON.stringify({
  type: 'typing',
  channel_id: 123,
  is_typing: true,
}));
```

---

## Message Types

### Chat Messages

#### chat_message
```javascript
// Send
{
  "type": "chat_message",
  "message": "Hello, world!",
  "channel_id": 123,
  "reply_to": 456,  // optional
}

// Receive
{
  "type": "chat_message",
  "message": {
    "id": 789,
    "content": "Hello, world!",
    "author": {...},
    "timestamp": "2024-01-01T12:00:00Z",
    "channel_id": 123,
    "reply_to": null,
    "attachments": []
  }
}
```

#### edit_message
```javascript
{
  "type": "edit_message",
  "message_id": 789,
  "new_content": "Updated message",
}
```

#### delete_message
```javascript
{
  "type": "delete_message",
  "message_id": 789,
}
```

#### typing_indicator
```javascript
{
  "type": "typing",
  "channel_id": 123,
  "is_typing": true,
}
```

### File Attachments

#### upload_file
```javascript
{
  "type": "upload_file",
  "file_name": "document.pdf",
  "file_size": 1024000,
  "file_type": "application/pdf",
  "channel_id": 123,
}
```

#### upload_chunk
```javascript
{
  "type": "upload_chunk",
  "upload_id": "abc123",
  "chunk_index": 0,
  "chunk_data": "base64_encoded_data",
}
```

### Notifications

#### notification
```javascript
{
  "type": "notification",
  "notification": {
    "id": 789,
    "title": "New Message",
    "message": "You have a new message",
    "category": "chat",
    "url": "/chat/123",
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

#### mark_read
```javascript
{
  "type": "mark_read",
  "notification_id": 789,
}
```

### Status Updates

#### status_update
```javascript
{
  "type": "status_update",
  "status": "online",  // online, away, busy, offline
}
```

#### user_status
```javascript
// Receive
{
  "type": "user_status",
  "user_id": 1,
  "status": "online",
  "last_seen": "2024-01-01T12:00:00Z"
}
```

---

## Authentication

### Token-Based Authentication

#### Get Token

```bash
curl -X POST http://your-domain.com/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOi...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOi..."
}
```

#### Connect with Token

```javascript
const token = localStorage.getItem('access_token');
const socket = new WebSocket(
  `wss://your-domain.com/ws/chat/room/?token=${token}`
);
```

### Session Authentication

```javascript
// Uses Django session cookie automatically
const socket = new WebSocket(
  'wss://your-domain.com/ws/chat/room/'
);
```

---

## Rate Limiting

### Configuration

```python
# settings.py
WEBSOCKET_RATE_LIMIT = 60  # messages per minute per connection
```

### Implementation

Rate limiting is applied per connection:
- **Limit**: 60 messages per minute (default)
- **Window**: Rolling 60-second window
- **Response**: Error message when exceeded

### Rate Limit Response

```javascript
{
  "type": "error",
  "error": "Rate limit exceeded. Please slow down.",
  "code": "RATE_LIMIT_EXCEEDED"
}
```

### Best Practices

- Implement client-side throttling
- Show user feedback when rate limited
- Use exponential backoff for retries
- Batch messages when possible

---

## Security

### XSS Prevention

All messages are sanitized before storage and display:

```python
# 7 XSS patterns blocked
DANGEROUS_PATTERNS = [
    r'<script[^>]*>.*?</script>',
    r'javascript:',
    r'onerror\s*=',
    r'onclick\s*=',
    r'onload\s*=',
    r'<iframe[^>]*>',
    r'eval\(',
]
```

### CSRF Protection

WebSocket connections use:
- Token authentication
- Origin validation
- Secure cookies

### Origin Validation

```python
# settings.py
ALLOWED_HOSTS = ['your-domain.com']
CSRF_TRUSTED_ORIGINS = ['https://your-domain.com']
```

### SSL/TLS

Always use WSS (WebSocket Secure) in production:

```javascript
// Good
const socket = new WebSocket('wss://your-domain.com/ws/chat/room/');

// Bad (development only)
const socket = new WebSocket('ws://localhost:8001/ws/chat/room/');
```

---

## Error Handling

### Error Types

```javascript
{
  "type": "error",
  "error": "Error message",
  "code": "ERROR_CODE"
}
```

### Common Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| `AUTHENTICATION_FAILED` | Invalid credentials | Re-authenticate |
| `RATE_LIMIT_EXCEEDED` | Too many messages | Slow down |
| `INVALID_MESSAGE` | Malformed message | Check format |
| `PERMISSION_DENIED` | No access | Check permissions |
| `CHANNEL_NOT_FOUND` | Invalid channel | Verify channel ID |
| `MESSAGE_TOO_LARGE` | Message exceeds limit | Reduce size |

### Client-Side Error Handling

```javascript
socket.onerror = (error) => {
  console.error('WebSocket error:', error);
  // Show user-friendly message
  showNotification('Connection error. Retrying...', 'error');
  // Attempt reconnection
  reconnectWithBackoff();
};

socket.onclose = (event) => {
  if (event.code === 1006) {
    // Abnormal closure - retry
    reconnectWithBackoff();
  } else if (event.code === 1000) {
    // Normal closure - don't retry
    console.log('Connection closed normally');
  }
};
```

---

## Best Practices

### Connection Management

```javascript
class WebSocketManager {
  constructor(url) {
    this.url = url;
    this.socket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }
  
  connect() {
    this.socket = new WebSocket(this.url);
    
    this.socket.onopen = () => {
      this.reconnectAttempts = 0;
      console.log('Connected');
    };
    
    this.socket.onclose = () => {
      this.reconnect();
    };
  }
  
  reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }
    
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;
    
    setTimeout(() => {
      console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);
      this.connect();
    }, delay);
  }
  
  send(data) {
    if (this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    } else {
      console.warn('Socket not open. Queueing message...');
      // Queue for later
    }
  }
}
```

### Message Queueing

```javascript
class OfflineQueue {
  constructor() {
    this.queue = this.loadQueue();
  }
  
  enqueue(message) {
    this.queue.push({
      ...message,
      timestamp: Date.now(),
    });
    this.saveQueue();
  }
  
  dequeueAll(socket) {
    while (this.queue.length > 0) {
      const message = this.queue.shift();
      socket.send(JSON.stringify(message));
    }
    this.saveQueue();
  }
  
  loadQueue() {
    const stored = localStorage.getItem('offline_queue');
    return stored ? JSON.parse(stored) : [];
  }
  
  saveQueue() {
    localStorage.setItem('offline_queue', JSON.stringify(this.queue));
  }
}
```

### Performance Optimization

```javascript
// Batch multiple updates
const updates = [];
const BATCH_DELAY = 100; // ms

function queueUpdate(update) {
  updates.push(update);
  
  if (updates.length === 1) {
    setTimeout(() => {
      socket.send(JSON.stringify({
        type: 'batch_update',
        updates: updates.splice(0),
      }));
    }, BATCH_DELAY);
  }
}

// Throttle typing indicators
const sendTypingIndicator = throttle(() => {
  socket.send(JSON.stringify({
    type: 'typing',
    channel_id: currentChannel,
    is_typing: true,
  }));
}, 1000);
```

---

## Deployment

### Production Checklist

- [ ] Use WSS (WebSocket Secure)
- [ ] Configure SSL certificates
- [ ] Set up Redis with persistence
- [ ] Configure proper ALLOWED_HOSTS
- [ ] Enable compression
- [ ] Set up monitoring
- [ ] Configure log aggregation
- [ ] Set up auto-scaling
- [ ] Test failover scenarios
- [ ] Document runbooks

### Nginx Configuration

```nginx
upstream daphne {
    server 127.0.0.1:8001;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location /ws/ {
        proxy_pass http://daphne;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_read_timeout 86400;
    }
}
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["daphne", "-b", "0.0.0.0", "-p", "8001", "kibray_backend.asgi:application"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8001:8001"
    depends_on:
      - redis
      - postgres
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://user:pass@postgres:5432/kibray
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
  
  postgres:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=kibray
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass

volumes:
  redis_data:
  postgres_data:
```

### Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: websocket-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: websocket
  template:
    metadata:
      labels:
        app: websocket
    spec:
      containers:
      - name: daphne
        image: your-registry/kibray-websocket:latest
        ports:
        - containerPort: 8001
        env:
        - name: REDIS_URL
          value: redis://redis-service:6379
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

### Monitoring

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram

websocket_connections = Counter(
    'websocket_connections_total',
    'Total WebSocket connections'
)

websocket_messages = Counter(
    'websocket_messages_total',
    'Total WebSocket messages',
    ['type']
)

websocket_latency = Histogram(
    'websocket_message_latency_seconds',
    'WebSocket message latency'
)
```

---

## Troubleshooting

### Connection Issues

**Problem**: Can't connect to WebSocket  
**Solutions**:
- Check Daphne is running
- Verify Redis is accessible
- Check firewall rules
- Verify SSL certificates
- Check browser console for errors

**Problem**: Frequent disconnections  
**Solutions**:
- Increase timeout settings
- Check network stability
- Review server logs
- Monitor server resources
- Check for rate limiting

### Performance Issues

**Problem**: High latency  
**Solutions**:
- Enable compression
- Optimize message size
- Check Redis performance
- Review database queries
- Use connection pooling

**Problem**: High memory usage  
**Solutions**:
- Limit channel layer capacity
- Reduce message expiry time
- Clear old cache entries
- Monitor Redis memory
- Optimize consumer code

### Debugging

```python
# Enable debug logging
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'channels': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'daphne': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

```javascript
// Client-side debugging
socket.addEventListener('message', (event) => {
  console.log('Received:', event.data);
});

socket.addEventListener('error', (error) => {
  console.error('Error:', error);
});

socket.addEventListener('open', () => {
  console.log('Connection opened');
});

socket.addEventListener('close', (event) => {
  console.log('Connection closed:', event.code, event.reason);
});
```

---

## Support & Resources

### Documentation
- [Django Channels Docs](https://channels.readthedocs.io/)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Redis Documentation](https://redis.io/documentation)

### Community
- Django Channels GitHub: https://github.com/django/channels
- Stack Overflow: #django-channels
- Django Forum: https://forum.djangoproject.com/

### Internal Resources
- WebSocket Security Guide: WEBSOCKET_SECURITY_AUDIT.md
- Load Testing Guide: WEBSOCKET_LOAD_TESTING_GUIDE.md
- Metrics Dashboard: WEBSOCKET_METRICS_DASHBOARD.md
- Push Notifications: PUSH_NOTIFICATIONS_IMPLEMENTATION.md

---

**Phase 6 WebSocket System - Complete API Documentation**  
Version 1.0.0 | Production Ready ✅
