# Kibray REST API v1 Documentation

## 🎯 Overview

Complete REST API for the Kibray construction management system, designed for mobile apps (iOS/Android via Capacitor) and third-party integrations.

**Base URL**: `/api/v1/`

## 🔐 Authentication

### JWT Token-Based Authentication

All endpoints (except login) require a valid JWT access token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

### 1. Login (Get Token)

**Endpoint**: `POST /api/v1/auth/login/`

**Request Body**:
```json
{
  "username": "user@example.com",
  "password": "your_password"
}
```

**Response** (200 OK):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Token Lifetimes**:
- Access token: **24 hours**
- Refresh token: **7 days**

### 2. Refresh Access Token

**Endpoint**: `POST /api/v1/auth/refresh/`

**Request Body**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response** (200 OK):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."  // New refresh token (rotation enabled)
}
```

### Example: Using curl

```bash
# 1. Login and get tokens
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "pass"}'

# 2. Use access token for API calls
curl -X GET http://localhost:8000/api/v1/notifications/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."

# 3. Refresh when access token expires
curl -X POST http://localhost:8000/api/v1/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."}'
```

---

## 📱 API Endpoints

### Notifications

#### List Notifications
**GET** `/api/v1/notifications/`

**Query Parameters**:
- `page` (int): Page number (default: 1, page size: 50)

**Response**:
```json
{
  "count": 42,
  "next": "http://localhost:8000/api/v1/notifications/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "message": "New task assigned",
      "is_read": false,
      "created_at": "2025-01-15T10:30:00Z",
      "project_name": "Downtown Office Renovation",
      "link": "/projects/5/tasks/"
    }
  ]
}
```

#### Mark All Read
**POST** `/api/v1/notifications/mark_all_read/`

**Response**: `{"status": "ok"}`

#### Mark Single Notification Read
**POST** `/api/v1/notifications/{id}/mark_read/`

**Response**: `{"status": "ok"}`

#### Count Unread
**GET** `/api/v1/notifications/count_unread/`

**Response**: `{"count": 5}`

---

### Chat

#### List Chat Channels (for current user)
**GET** `/api/v1/chat/channels/`

**Response**:
```json
[
  {
    "id": 1,
    "name": "General Discussion",
    "project_name": "Downtown Office Renovation",
    "created_at": "2025-01-10T14:00:00Z"
  }
]
```

#### List Messages in Channel
**GET** `/api/v1/chat/messages/?channel={channel_id}`

**Query Parameters**:
- `channel` (int, required): Channel ID

**Response**:
```json
[
  {
    "id": 42,
    "channel": 1,
    "user": 3,
    "user_name": "John Smith",
    "content": "The drywall is complete.",
    "created_at": "2025-01-15T09:45:00Z",
    "attachment": null
  }
]
```

#### Send Message
**POST** `/api/v1/chat/messages/`

**Request Body**:
```json
{
  "channel": 1,
  "content": "All clear on floor 2"
}
```

**Response**: `201 Created` with created message object

---

### Site Photos (Visual & Collaboration)

#### Upload Site Photo
**POST** `/api/v1/site-photos/`

Supports `multipart/form-data` or JSON. Fields: `project` (id), `image` (file), optional `caption`, `location_lat`, `location_lng`, `location_accuracy_m`, `damage_report` (id), `photo_type`.

#### List Site Photos
**GET** `/api/v1/site-photos/?project={id}&damage_report={id}&photo_type=before|progress|after|defect|reference&start=YYYY-MM-DD&end=YYYY-MM-DD`

Response: array of photos. Pagination disabled for simplicity.

---

### Tasks


#### List Tasks
**GET** `/api/v1/tasks/`

**Query Parameters**:
- `touchup=true` - Filter only touch-up tasks (uses `is_touchup` flag)
- `assigned_to_me=true` - Filter tasks assigned to current user
- `is_touchup=true|false` - Direct filter for touch-up tasks (for advanced queries)

**Response**:
```json
[
  {
    "id": 15,
    "title": "Paint touch-up in lobby",
    "description": "Fix paint chips near entrance",
    "assigned_to": 4,
    "assigned_to_name": "Maria Garcia",
    "status": "Pendiente",
    "priority": "high",
    "is_touchup": true,
    "project": 2,
    "project_name": "Downtown Office Renovation",
    "due_date": "2025-01-20",
    "created_at": "2025-01-14T08:00:00Z",
    "started_at": null,
    "time_tracked_seconds": 0,
    "time_tracked_hours": 0.0,
    "total_hours": 0.0,
    "dependencies_ids": [12, 13],
    "reopen_events_count": 1
  }
]
```

#### Touch-Up Kanban Board
**GET** `/api/v1/tasks/touchup_board/?project={id}`

Returns a kanban-style board of touch-up tasks grouped by status and priority for a project (or all projects if not specified).

**Response**:
```json
{
  "columns": {
    "Pendiente": [ ... ],
    "En Progreso": [ ... ],
    "Completada": [ ... ],
    "Cancelada": [ ... ]
  },
  "total": 7
}
```

#### Update Task Status
**POST** `/api/v1/tasks/{id}/update_status/`

**Request Body**:
```json
{
  "status": "completed"
}
```

**Valid Statuses**: `Pendiente`, `En Progreso`, `Completada`, `Cancelada`

**Response**: Updated task object

#### Create/Update Task (writable fields)

Tasks are managed via standard REST endpoints:
- `POST /api/v1/tasks/` to create
- `PATCH /api/v1/tasks/{id}/` to update

Writable fields include:
- `title`, `description`, `project`, `assigned_to`,
- `priority` one of: `low`, `medium`, `high`, `urgent`
- `due_date` (YYYY-MM-DD or null)
- `dependencies` (list of task IDs to set ManyToMany)

Example (PATCH):
```json
{
  "priority": "urgent",
  "due_date": "2025-01-30",
  "dependencies": [10, 11]
}
```

Notes:
- `dependencies` sets the full dependency list; use actions below to add/remove individually.
- Circular/self dependencies are validated and will return 400.

#### Reopen Task
**POST** `/api/v1/tasks/{id}/reopen/`

Body:
```json
{ "notes": "Client requested changes" }
```

Response:
```json
{ "status": "ok", "new_status": "En Progreso", "reopen_events_count": 2 }
```

#### Start/Stop Time Tracking
- **POST** `/api/v1/tasks/{id}/start_tracking/` → `{ "status": "ok", "started_at": "..." }`
- **POST** `/api/v1/tasks/{id}/stop_tracking/` → `{ "status": "ok", "elapsed_seconds": 354, "total_hours": 2.1 }`

Rules:
- `start_tracking` requires all dependencies completed and task not marked as touch-up.

#### Time Summary
**GET** `/api/v1/tasks/{id}/time_summary/`

Response:
```json
{
  "task_id": 123,
  "task_title": "Fix door frame",
  "internal_tracking_hours": 1.5,
  "time_entry_hours": 2.0,
  "total_hours": 3.5,
  "employee_breakdown": [
    {"employee_id": 7, "employee_name": "Ana", "hours": 2.0}
  ],
  "is_tracking_active": false,
  "reopen_count": 1
}
```

#### Manage Dependencies
- **POST** `/api/v1/tasks/{id}/add_dependency/` → `{ "dependency_id": 99 }`
- **POST** `/api/v1/tasks/{id}/remove_dependency/` → `{ "dependency_id": 99 }`

#### Add Task Image (Touch-ups)
**POST** `/api/v1/tasks/{id}/add_image/` (multipart)

Form fields: `image` (file), optional `caption`

Response: `{ "status": "ok", "image_id": 55, "version": 2 }`

#### Touch-up Kanban Board
**GET** `/api/v1/tasks/touchup_board/?project={id}&status=Pendiente,En%20Progreso&priority=high,urgent&assigned_to_me=true`

Response: `{ columns: [...], totals: { ... } }`

#### Gantt Data
**GET** `/api/v1/tasks/gantt/?project={id}` → `{ tasks: [...], dependencies: [...] }`

---

### Damage Reports

#### List Damage Reports
**GET** `/api/v1/damage-reports/?project={id}&status=open|in_progress|resolved&severity=low|medium|high|critical&category=...`

**Response**:
```json
[
  {
    "id": 8,
    "project": 2,
    "project_name": "Harbor View Apartments",
    "reported_by": 5,
    "reported_by_name": "Tom Anderson",
    "title": "Cracked tile in bathroom 3B",
    "description": "Large crack in floor tile",
  "category": "cosmetic",
  "status": "open",
  "severity": "medium",
  "reported_at": "2025-01-14T11:30:00Z",
  "in_progress_at": null,
  "resolved_at": null,
  "auto_task": 123,
  "photos": []
  }
]
```

#### Create Damage Report
**POST** `/api/v1/damage-reports/` (multipart or JSON)

Fields: `project` (id), `title`, optional `description`, `category`, `severity`, optional `assigned_to`, `location_detail`, `estimated_cost`.

#### Add Evidence Photo
**POST** `/api/v1/damage-reports/{id}/add_photo/`

`multipart/form-data` with `image` (file) and optional `notes`.

#### Analytics
**GET** `/api/v1/damage-reports/analytics/?project={id}` → `{ severity, status, category, total }`

---

### Floor Plans

#### List Floor Plans
**GET** `/api/v1/floor-plans/`

**Query Parameters**:
- `project` (int): Filter by project ID

**Response**:
```json
[
  {
    "id": 3,
    "project": 1,
    "project_name": "Downtown Office Renovation",
    "name": "Ground Floor",
    "version": "v2",
    "file": "https://s3.amazonaws.com/kibray-media/plans/floor1_v2.pdf",
    "uploaded_at": "2025-01-12T10:00:00Z",
    "pins": [
      {
        "id": 12,
        "title": "Paint Selection",
        "x_percent": 45.2,
        "y_percent": 67.8,
        "type": "color",
        "color": "#3B82F6"
      }
    ]
  }
]
```

#### List Plan Pins (for a specific plan)
**GET** `/api/v1/plan-pins/?plan={plan_id}&pin_type=note|touchup|color|alert|damage`

**Response**: Array of pin objects (see nested structure above)

#### Comment on Pin
**POST** `/api/v1/plan-pins/{id}/comment/`

Body: `{ "comment": "Please fix ASAP" }`

---

### Color Samples

#### List Color Samples
**GET** `/api/v1/color-samples/`

**Query Parameters**:
- `project` (int): Filter by project ID
- `status` (string): Filter by status (`pending`, `approved`, `rejected`)

**Response**:
```json
[
  {
    "id": 7,
    "project": 1,
    "project_name": "Downtown Office Renovation",
    "name": "Lobby Wall - Option A",
    "color_code": "#E5E7EB",
    "location": "Main Lobby",
    "photo": "https://s3.amazonaws.com/kibray-media/colors/sample7.jpg",
    "status": "proposed",
    "sample_number": "ACMEM10001",
    "approved_by": null,
    "approved_at": null
  }
]
```

#### Approve Sample
**POST** `/api/v1/color-samples/{id}/approve/`

Body: `{ "signature_ip": "203.0.113.10" }` (optional)

#### Reject Sample
**POST** `/api/v1/color-samples/{id}/reject/`

Body: `{ "reason": "Does not match spec" }`

---

### Projects

#### List Projects (Read-Only)
**GET** `/api/v1/projects/`

**Response**:
```json
[
  {
    "id": 1,
    "name": "Downtown Office Renovation",
    "address": "123 Main St, Downtown",
    "start_date": "2024-12-01",
    "end_date": "2025-06-30",
    "status": "active"
  }
]
```

#### Project Manager Assignments

- `GET /api/v1/project-manager-assignments/` — list assignments
- `POST /api/v1/project-manager-assignments/` — create assignment (body: `{ project, pm }`)
- `POST /api/v1/project-manager-assignments/assign/` — convenience action to create assignment; triggers notifications to PM and admins

Notes:
- Notifications are generated via a post-save signal; duplicates are avoided by unique constraints where applicable.

#### Color Approvals

- `GET /api/v1/color-approvals/` — list color approvals
- `POST /api/v1/color-approvals/` — create approval request (fields: `project`, `requested_by`, `color_name`, `color_code`, `brand`, `location`)
- `POST /api/v1/color-approvals/{id}/approve` — approve with optional multipart file `client_signature`
- `POST /api/v1/color-approvals/{id}/reject` — reject with JSON body `{ reason: string }`

Filtering & Search:
- Filter: `project`, `status`, `color_name`, `brand`
- Search: `color_name`, `color_code`, `brand`, `location`

Auth:
- Requires JWT authentication; obtain tokens via `/api/v1/auth/login/` and include `Authorization: Bearer <token>`

---

## 🚨 Error Responses

### 401 Unauthorized
```json
{
  "detail": "Given token not valid for any token type",
  "code": "token_not_valid",
  "messages": [
    {
      "token_class": "AccessToken",
      "token_type": "access",
      "message": "Token is invalid or expired"
    }
  ]
}
```

**Solution**: Refresh your access token using the refresh endpoint.

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**Solution**: Ensure user has required role/permissions for the resource.

### 400 Bad Request
```json
{
  "field_name": [
    "This field is required."
  ]
}
```

**Solution**: Check request body matches expected format.

---

## 🔧 Configuration

### Environment Variables (Production)

```bash
# Required for production deployment
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=False
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# AWS S3 Storage (for media files)
USE_S3=True
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=kibray-media
AWS_S3_REGION_NAME=us-east-1

# Email (optional, for notifications)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password

# CORS (already configured for Capacitor)
# Default origins: capacitor://localhost, ionic://localhost, http://localhost:8100
```

### Local Development

For local development, API works with default settings:
- SQLite database (db.sqlite3)
- Local media storage (media/)
- Console email backend
- CORS enabled for localhost

**Start server**:
```bash
python manage.py runserver
```

**API available at**: `http://localhost:8000/api/v1/`

---

## 📱 Mobile App Integration (Capacitor/iOS)

### Recommended Setup

1. **Install Capacitor** in your iOS project:
```bash
npm install @capacitor/core @capacitor/ios
npx cap init
npx cap add ios
```

2. **Configure server URL** in `capacitor.config.json`:
```json
{
  "server": {
    "url": "https://kibray-backend.onrender.com",
    "cleartext": false
  }
}
```

3. **Install native plugins** for advanced features:
```bash
npm install @capacitor/camera @capacitor/push-notifications @capacitor/filesystem
```

4. **Example: Login and API call** (JavaScript/TypeScript):
```javascript
// Login
const response = await fetch('https://kibray-backend.onrender.com/api/v1/auth/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'user', password: 'pass' })
});
const { access, refresh } = await response.json();
localStorage.setItem('access_token', access);
localStorage.setItem('refresh_token', refresh);

// API call with token
const notifs = await fetch('https://kibray-backend.onrender.com/api/v1/notifications/', {
  headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
});
const data = await notifs.json();
```

5. **Photo upload** (using Capacitor Camera):
```javascript
import { Camera, CameraResultType } from '@capacitor/camera';

const photo = await Camera.getPhoto({
  resultType: CameraResultType.Uri,
  quality: 90
});

const formData = new FormData();
formData.append('project', '2');
formData.append('title', 'Damage report');
formData.append('photo', {
  uri: photo.path,
  name: 'damage.jpg',
  type: 'image/jpeg'
});

await fetch('https://kibray-backend.onrender.com/api/v1/damage-reports/', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
});
```

---

## 🔄 Real-Time Updates

### Current Strategy: Polling

For real-time features (chat, notifications), use **periodic polling**:

```javascript
// Poll notifications every 30 seconds
setInterval(async () => {
  const response = await fetch('/api/v1/notifications/count_unread/', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const { count } = await response.json();
  updateBadge(count);
}, 30000);
```

### Future Enhancement: WebSockets

For true real-time updates, Django Channels can be added:

1. Install: `pip install channels channels-redis`
2. Configure WebSocket consumers for chat/notifications
3. Mobile app connects via `wss://` protocol

This is **optional** and can be implemented as the user base scales.

---

## 📊 Rate Limiting & Performance

- **Pagination**: All list endpoints return max 50 items per page
- **Token expiry**: Access tokens expire after 24 hours
- **Refresh rotation**: New refresh token issued on each refresh (prevents token reuse)

### Recommendations
- Cache user profile/project list on mobile app
- Use incremental sync (fetch only new data since last sync)
- Store tokens securely (iOS Keychain, Android Keystore)

---

## 🛠 Testing the API

### Using Postman

1. Import this collection structure:
   - **Auth** folder: Login, Refresh
   - **Notifications** folder: List, Mark Read, Count
   - **Chat** folder: Channels, Messages, Send
   - **Tasks** folder: List, Update Status
   - **Damage Reports** folder: List, Create (with file upload)

2. Set environment variable:
   - `base_url`: `http://localhost:8000` or `https://kibray-backend.onrender.com`
   - `access_token`: (populated from login response)

3. Use `{{base_url}}/api/v1/notifications/` in requests

### Using Django Shell

```python
# Test JWT auth
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User

user = User.objects.first()
refresh = RefreshToken.for_user(user)
print(f"Access: {refresh.access_token}")
print(f"Refresh: {refresh}")

# Test serializers
from core.api.serializers import NotificationSerializer
from core.models import Notification

notif = Notification.objects.first()
serializer = NotificationSerializer(notif)
print(serializer.data)
```

---

## 📞 Support & Next Steps

**API is production-ready** with:
- ✅ JWT authentication with refresh tokens
- ✅ Full CRUD for all core entities
- ✅ S3 media storage support
- ✅ CORS configured for Capacitor mobile apps
- ✅ PostgreSQL-ready (via dj_database_url)

**Next steps for mobile development**:
1. See `IOS_SETUP_GUIDE.md` for Xcode/Capacitor setup
2. Build SwiftUI or web-based mobile UI
3. Integrate Capacitor plugins (Camera, Push Notifications)
4. Submit to App Store

For questions or issues, check Django logs or open a support ticket.
