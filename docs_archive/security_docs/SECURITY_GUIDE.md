# Security & Audit Trail Guide

**Phase 9: Security Baseline**

This guide covers the security features implemented in Kibray, including role-based access control, comprehensive audit logging, and login attempt tracking.

---

## Table of Contents

1. [Overview](#overview)
2. [Permission Matrix (RBAC)](#permission-matrix-rbac)
3. [Audit Logging](#audit-logging)
4. [Login Attempt Tracking](#login-attempt-tracking)
5. [API Endpoints](#api-endpoints)
6. [Integration Guide](#integration-guide)
7. [Best Practices](#best-practices)

---

## Overview

The security baseline provides three key features:

- **Permission Matrix**: Fine-grained role-based access control (RBAC)
- **Audit Log**: Comprehensive tracking of all critical operations
- **Login Attempts**: Brute-force detection and rate limiting

All security features are automatically tracked via Django signals and middleware.

---

## Permission Matrix (RBAC)

### Model: `PermissionMatrix`

Defines granular permissions for users based on roles and entity types.

**Fields:**
- `user`: ForeignKey to User
- `role`: Choice field (admin, project_manager, contractor, client, viewer)
- `entity_type`: What the permission applies to (project, task, invoice, etc.)
- `can_view`, `can_create`, `can_edit`, `can_delete`, `can_approve`: Boolean flags
- `effective_from`, `effective_until`: Optional temporal access control
- `scope_project`: Optional project-specific scope (if null, applies globally)

### Creating Permissions

```python
from core.models import PermissionMatrix

# Grant project manager full task access
PermissionMatrix.objects.create(
    user=pm_user,
    role='project_manager',
    entity_type='task',
    can_view=True,
    can_create=True,
    can_edit=True,
    can_delete=False,
    can_approve=True
)

# Grant contractor time-limited invoice view access
from datetime import date, timedelta
PermissionMatrix.objects.create(
    user=contractor_user,
    role='contractor',
    entity_type='invoice',
    can_view=True,
    can_create=False,
    can_edit=False,
    effective_from=date.today(),
    effective_until=date.today() + timedelta(days=30)
)

# Grant project-scoped expense access
PermissionMatrix.objects.create(
    user=pm_user,
    role='project_manager',
    entity_type='expense',
    can_view=True,
    can_create=True,
    can_edit=True,
    scope_project=project_obj
)
```

### Checking Permissions

**Programmatic Check:**
```python
perms = PermissionMatrix.objects.filter(
    user=request.user,
    entity_type='invoice'
)

active_perms = [p for p in perms if p.is_active()]
can_edit = any(p.can_edit for p in active_perms)
```

**API Check:**
```bash
GET /api/v1/permissions/check_permission/?entity_type=invoice&action=edit&project_id=5

Response:
{
  "has_permission": true,
  "entity_type": "invoice",
  "action": "edit",
  "project_id": "5"
}
```

### Role Definitions

| Role | Typical Permissions |
|------|---------------------|
| **admin** | Full access to all entities |
| **project_manager** | View/edit/approve projects, tasks, invoices, expenses |
| **contractor** | View projects/tasks, create time entries, view own invoices |
| **client** | View project status, approve invoices/estimates |
| **viewer** | Read-only access to specified entities |

---

## Audit Logging

### Model: `AuditLog`

Tracks who did what, when, and from where.

**Fields:**
- `user`: ForeignKey to User (nullable if user deleted)
- `username`: Cached username
- `action`: create, update, delete, view, approve, reject, login, logout, etc.
- `entity_type`: project, task, invoice, user, etc.
- `entity_id`: Primary key of affected entity
- `entity_repr`: String representation
- `old_values`: JSON field with previous state (for updates/deletes)
- `new_values`: JSON field with new state (for creates/updates)
- `ip_address`, `user_agent`, `session_id`: Request context
- `request_path`, `request_method`: API endpoint info
- `notes`: Additional context
- `success`: Whether the action succeeded
- `error_message`: If failed, why
- `timestamp`: Auto-generated

### Automatic Logging

Audit logs are created automatically via:

1. **Django Signals** (for model changes)
2. **Authentication Signals** (for login/logout)
3. **API Middleware** (for HTTP requests)

**Example: Automatic Project Change Tracking**
```python
# When you update a project:
project.status = 'completed'
project.budget_total = Decimal('15000')
project.save()

# Audit log is automatically created with:
# - action: 'update'
# - old_values: {'status': 'active', 'budget': '10000'}
# - new_values: {'status': 'completed', 'budget': '15000'}
```

### Manual Logging

```python
from core.audit import log_audit_action

log_audit_action(
    user=request.user,
    action='approve',
    entity_type='invoice',
    entity_id=invoice.id,
    entity_repr=str(invoice),
    request=request,
    notes='Invoice approved by PM',
    success=True
)
```

### Querying Audit Logs

**Recent Activity:**
```python
from django.utils import timezone
from datetime import timedelta

cutoff = timezone.now() - timedelta(hours=24)
recent_logs = AuditLog.objects.filter(
    user=request.user,
    timestamp__gte=cutoff
).order_by('-timestamp')
```

**Entity History:**
```python
history = AuditLog.objects.filter(
    entity_type='project',
    entity_id=project.id
).order_by('-timestamp')

for log in history:
    print(f"{log.timestamp}: {log.username} {log.action}")
    if log.old_values and log.new_values:
        print(f"  Changed: {log.old_values} → {log.new_values}")
```

**API Endpoints:**
```bash
# Get recent activity (last 24 hours)
GET /api/v1/audit-logs/recent_activity/

# Get entity history
GET /api/v1/audit-logs/entity_history/?entity_type=project&entity_id=5
```

---

## Login Attempt Tracking

### Model: `LoginAttempt`

Tracks all login attempts (successful and failed) for security monitoring.

**Fields:**
- `username`: Username attempted
- `ip_address`: Source IP
- `user_agent`: Browser/client info
- `success`: Boolean
- `failure_reason`: invalid_password, user_not_found, rate_limited, etc.
- `timestamp`: When the attempt occurred
- `session_id`: Django session ID (if successful)
- `country_code`, `city`: Geolocation (optional future enhancement)

### Rate Limiting

**Check Rate Limit:**
```python
from core.models import LoginAttempt

is_blocked, attempt_count = LoginAttempt.check_rate_limit(
    username='testuser',
    ip_address='192.168.1.100',
    window_minutes=15,  # Default
    max_attempts=5      # Default
)

if is_blocked:
    return Response({'error': 'Too many failed attempts'}, status=429)
```

**Default Settings:**
- **Window**: 15 minutes
- **Threshold**: 5 failed attempts
- **Action**: Block further login attempts until window expires

### Manual Logging

```python
from core.models import LoginAttempt

# Log successful login
LoginAttempt.log_attempt(
    username='john_doe',
    ip_address='10.0.0.5',
    success=True,
    user_agent='Mozilla/5.0...',
    session_id='abc123xyz'
)

# Log failed login
LoginAttempt.log_attempt(
    username='john_doe',
    ip_address='10.0.0.5',
    success=False,
    failure_reason='invalid_password',
    user_agent='curl/7.68.0'
)
```

### Monitoring Suspicious Activity

**API Endpoint (Admin Only):**
```bash
GET /api/v1/login-attempts/suspicious_activity/

Response:
{
  "window": "1 hour",
  "threshold": 5,
  "suspicious_ips": [
    {"ip_address": "192.168.1.99", "failure_count": 12},
    {"ip_address": "10.0.0.42", "failure_count": 8}
  ]
}
```

**Programmatic Check:**
```python
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count

cutoff = timezone.now() - timedelta(hours=1)

suspicious_ips = LoginAttempt.objects.filter(
    success=False,
    timestamp__gte=cutoff
).values('ip_address').annotate(
    failure_count=Count('id')
).filter(failure_count__gte=5)
```

---

## API Endpoints

### Permission Matrix

**List Permissions:**
```bash
GET /api/v1/permissions/
GET /api/v1/permissions/?user=5
GET /api/v1/permissions/?role=project_manager
GET /api/v1/permissions/?entity_type=invoice
```

**Create Permission:**
```bash
POST /api/v1/permissions/
Content-Type: application/json

{
  "user": 5,
  "role": "contractor",
  "entity_type": "task",
  "can_view": true,
  "can_create": false,
  "can_edit": false,
  "effective_from": "2024-01-01",
  "effective_until": "2024-12-31"
}
```

**My Permissions (Grouped):**
```bash
GET /api/v1/permissions/my_permissions/

Response:
{
  "project": {
    "can_view": true,
    "can_create": true,
    "can_edit": true,
    "can_delete": false,
    "can_approve": true
  },
  "task": {
    "can_view": true,
    "can_create": true,
    "can_edit": true,
    "can_delete": false,
    "can_approve": false
  }
}
```

**Check Permission:**
```bash
GET /api/v1/permissions/check_permission/?entity_type=invoice&action=approve

Response:
{
  "has_permission": false,
  "entity_type": "invoice",
  "action": "approve"
}
```

### Audit Logs (Read-Only)

**List Logs:**
```bash
GET /api/v1/audit-logs/
GET /api/v1/audit-logs/?user=5
GET /api/v1/audit-logs/?action=delete
GET /api/v1/audit-logs/?entity_type=project&entity_id=10
```

**Recent Activity:**
```bash
GET /api/v1/audit-logs/recent_activity/

Response:
{
  "count": 15,
  "logs": [...]
}
```

**Entity History:**
```bash
GET /api/v1/audit-logs/entity_history/?entity_type=project&entity_id=5

Response:
{
  "entity_type": "project",
  "entity_id": "5",
  "history": [...]
}
```

### Login Attempts (Read-Only)

**List Attempts:**
```bash
GET /api/v1/login-attempts/
GET /api/v1/login-attempts/?username=john_doe
GET /api/v1/login-attempts/?success=false
```

**Recent Failures:**
```bash
GET /api/v1/login-attempts/recent_failures/

Response:
{
  "count": 3,
  "attempts": [...]
}
```

**Suspicious Activity (Admin Only):**
```bash
GET /api/v1/login-attempts/suspicious_activity/

Response:
{
  "window": "1 hour",
  "threshold": 5,
  "suspicious_ips": [...]
}
```

---

## Integration Guide

### Adding Audit Logging to Custom Views

```python
from core.audit import log_audit_action

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    # Perform approval
    invoice.status = 'approved'
    invoice.approved_by = request.user
    invoice.save()
    
    # Log the action
    log_audit_action(
        user=request.user,
        action='approve',
        entity_type='invoice',
        entity_id=invoice.id,
        entity_repr=f"Invoice #{invoice.id}",
        request=request,
        notes=f'Invoice approved for ${invoice.total_amount}',
        success=True
    )
    
    return Response({'status': 'approved'})
```

### Enforcing Permissions in Views

```python
from core.models import PermissionMatrix

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_expense(request, expense_id):
    # Check permission
    perms = PermissionMatrix.objects.filter(
        user=request.user,
        entity_type='expense'
    )
    active_perms = [p for p in perms if p.is_active()]
    
    if not any(p.can_delete for p in active_perms):
        return Response({'error': 'Permission denied'}, status=403)
    
    # Proceed with deletion
    expense = get_object_or_404(Expense, id=expense_id)
    expense.delete()
    
    return Response({'status': 'deleted'})
```

### Custom Login View with Rate Limiting

```python
from django.contrib.auth import authenticate, login
from core.models import LoginAttempt
from core.audit import get_client_ip

@api_view(['POST'])
def custom_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    ip = get_client_ip(request)
    
    # Check rate limit
    is_blocked, count = LoginAttempt.check_rate_limit(username, ip)
    if is_blocked:
        return Response({
            'error': 'Too many failed attempts. Try again in 15 minutes.'
        }, status=429)
    
    # Attempt authentication
    user = authenticate(request, username=username, password=password)
    
    if user:
        login(request, user)
        LoginAttempt.log_attempt(username, ip, True)
        return Response({'status': 'success'})
    else:
        LoginAttempt.log_attempt(username, ip, False, 'invalid_password')
        return Response({'error': 'Invalid credentials'}, status=401)
```

---

## Best Practices

### Permission Management

1. **Principle of Least Privilege**: Grant only necessary permissions
2. **Use Temporal Access**: Set `effective_until` for temporary access
3. **Scope to Projects**: Use `scope_project` when possible to limit exposure
4. **Regular Audits**: Review permissions quarterly, revoke unused ones
5. **Role-Based Assignment**: Prefer roles over individual permissions

### Audit Logging

1. **Log Critical Actions**: Focus on creates, updates, deletes, approvals
2. **Include Context**: Always log IP address, user agent, session ID
3. **Meaningful Notes**: Add human-readable descriptions
4. **Error Tracking**: Set `success=False` and `error_message` for failures
5. **Retention Policy**: Archive old logs (>1 year) to keep DB performant

### Login Security

1. **Monitor Failed Attempts**: Set up alerts for >10 failures/hour
2. **Geolocation Tracking**: Consider adding IP geolocation for anomaly detection
3. **Account Lockout**: Implement temporary account lockout after X failures
4. **Password Policies**: Enforce strong passwords, rotation policies
5. **Two-Factor Authentication**: Already implemented in `core.models.TwoFactorProfile`

### Performance Considerations

1. **Indexes**: All security models have appropriate DB indexes (timestamp, user, entity_type)
2. **Batch Queries**: Use `select_related` and `prefetch_related` for audit log queries
3. **Pagination**: Always paginate when displaying logs (use `StandardResultsSetPagination`)
4. **Async Logging**: Consider Celery tasks for heavy audit logging (future enhancement)
5. **Archival**: Move old audit logs to cold storage after 6-12 months

---

## Migration & Deployment

### Initial Setup

```bash
# Apply migrations
python manage.py migrate

# Create default permissions for admin users
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> from core.models import PermissionMatrix
>>> User = get_user_model()
>>> admin = User.objects.get(username='admin')
>>> 
>>> # Grant admin full access to all entities
>>> entities = ['project', 'task', 'invoice', 'expense', 'inventory']
>>> for entity in entities:
...     PermissionMatrix.objects.create(
...         user=admin,
...         role='admin',
...         entity_type=entity,
...         can_view=True,
...         can_create=True,
...         can_edit=True,
...         can_delete=True,
...         can_approve=True
...     )
```

### Middleware Configuration (Optional)

To enable automatic API request logging, add to `settings.py`:

```python
MIDDLEWARE = [
    # ... existing middleware
    'core.audit.AuditLogMiddleware',  # Add after authentication middleware
]
```

### Testing

```bash
# Run security tests
pytest tests/test_security.py -v

# Expected: 19 tests passing
# - 6 PermissionMatrix tests
# - 5 AuditLog tests
# - 7 LoginAttempt tests
# - 1 Integration test
```

---

## Troubleshooting

### Issue: Permissions not working

**Solution:**
1. Check `is_active()` - permissions may be expired or future-dated
2. Verify `scope_project` - project-scoped permissions don't apply to other projects
3. Check aggregation - multiple permissions are OR'd together (any True = True)

### Issue: Audit logs not being created

**Solution:**
1. Ensure Django signals are connected (check `apps.py`)
2. Verify middleware is installed (for API logging)
3. Check that model changes use `.save()` (bulk updates bypass signals)

### Issue: Rate limiting not working

**Solution:**
1. Verify `LoginAttempt.check_rate_limit()` is called before authentication
2. Check time window (default 15 minutes) - old attempts are ignored
3. Ensure IP address extraction is correct (`get_client_ip()`)

---

## Next Steps

- **Phase 10**: Extend permissions to frontend (role-based UI rendering)
- **Phase 11**: Advanced analytics (audit log dashboards, security reports)
- **Phase 12**: Compliance (GDPR data export, audit trail PDF generation)

---

## API Quick Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/permissions/` | GET | List permissions (filtered by user) |
| `/api/v1/permissions/` | POST | Create new permission |
| `/api/v1/permissions/my_permissions/` | GET | Get current user's aggregated permissions |
| `/api/v1/permissions/check_permission/` | GET | Check specific permission |
| `/api/v1/audit-logs/` | GET | List audit logs (read-only) |
| `/api/v1/audit-logs/recent_activity/` | GET | Last 24 hours of activity |
| `/api/v1/audit-logs/entity_history/` | GET | Full history for specific entity |
| `/api/v1/login-attempts/` | GET | List login attempts (read-only) |
| `/api/v1/login-attempts/recent_failures/` | GET | Failed attempts (last 7 days) |
| `/api/v1/login-attempts/suspicious_activity/` | GET | Detect brute-force patterns (admin only) |

---

**Documentation Version**: 1.0  
**Last Updated**: January 2025  
**Related Docs**: `AUTOMATION_GUIDE.md`, `API_README.md`
