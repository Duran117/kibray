# SECURITY COMPREHENSIVE
**System:** Kibray ERP  
**Last Updated:** December 8, 2025  
**Status:** Official Master Document  
**Owner Authorization:** Approved via Owner Decision Questionnaire

---

## TABLE OF CONTENTS

1. [Security Overview](#security-overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [Data Protection](#data-protection)
4. [Network Security](#network-security)
5. [Application Security](#application-security)
6. [Audit & Compliance](#audit--compliance)
7. [Secrets Management](#secrets-management)
8. [Incident Response](#incident-response)
9. [Security Best Practices](#security-best-practices)

---

## SECURITY OVERVIEW

### Security Posture
Kibray ERP implements **defense-in-depth** security with multiple layers of protection:

1. **Perimeter Security** - HTTPS, firewall, DDoS protection
2. **Authentication** - JWT tokens, session management
3. **Authorization** - Role-based access control (RBAC)
4. **Data Protection** - Encryption at rest and in transit
5. **Application Security** - Input validation, CSRF protection, SQL injection prevention
6. **Audit Logging** - Complete activity tracking
7. **Monitoring** - Real-time threat detection

### Security Principles
- **Least Privilege:** Users have minimum necessary access
- **Defense in Depth:** Multiple security layers
- **Fail Secure:** System defaults to deny access
- **Audit Everything:** All actions logged
- **Zero Trust:** Verify every request

---

## AUTHENTICATION & AUTHORIZATION

### Authentication Method
**JWT (JSON Web Token)** with refresh token rotation

#### Token Structure
```json
{
  "user_id": "uuid",
  "username": "user@example.com",
  "role": "project_manager_full",
  "permissions": ["can_send_external_emails", ...],
  "exp": 1641650400,
  "iat": 1641646800
}
```

#### Token Lifetimes
- **Access Token:** 1 hour
- **Refresh Token:** 7 days
- **Remember Me:** 30 days

### Authentication Flow

```
1. User enters credentials
   ↓
2. Server validates credentials
   ↓
3. Server generates JWT access + refresh tokens
   ↓
4. Client stores tokens (httpOnly cookie or localStorage)
   ↓
5. Client includes access token in Authorization header
   ↓
6. Server validates token on each request
   ↓
7. When access token expires, use refresh token
   ↓
8. Server issues new access token
```

### Password Security

#### Requirements
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character

#### Storage
```python
from django.contrib.auth.hashers import make_password

# Passwords hashed with PBKDF2-SHA256
password_hash = make_password(
    password,
    salt=None,  # Auto-generated
    hasher='pbkdf2_sha256'
)
# Iterations: 390,000 (Django 4.2+ default)
```

### Multi-Factor Authentication (2FA)

**Status:** Implemented for Admin and PM Full roles

**Methods:**
1. **TOTP (Time-based One-Time Password)** - Google Authenticator, Authy
2. **SMS (Optional)** - Text message codes
3. **Email (Backup)** - Email verification codes

**Implementation:**
```python
from django_otp.plugins.otp_totp.models import TOTPDevice

# Enable 2FA
device = TOTPDevice.objects.create(
    user=user,
    name='default',
    confirmed=True
)

# Verify code
device.verify_token(user_entered_code)
```

### Session Management

#### Session Security
- **HttpOnly cookies:** Prevent XSS access
- **Secure flag:** HTTPS only
- **SameSite:** Strict (CSRF protection)
- **Session timeout:** 30 minutes inactivity
- **Concurrent sessions:** Limited to 5 per user

#### Session Invalidation
- On logout
- On password change
- On role change
- On suspicious activity detection

---

## DATA PROTECTION

### Encryption at Rest

#### Database Encryption
- **PostgreSQL:** Encryption at storage level (Railway managed)
- **Sensitive Fields:** Additional application-level encryption

```python
from cryptography.fernet import Fernet
from django.conf import settings

class EncryptedTextField(models.TextField):
    """Encrypted text field for sensitive data"""
    
    def __init__(self, *args, **kwargs):
        self.cipher = Fernet(settings.FIELD_ENCRYPTION_KEY)
        super().__init__(*args, **kwargs)
    
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return self.cipher.decrypt(value.encode()).decode()
    
    def get_prep_value(self, value):
        if value is None:
            return value
        return self.cipher.encrypt(value.encode()).decode()
```

**Encrypted Fields:**
- Social Security Numbers
- Bank account numbers
- Credit card information (if stored)
- OAuth tokens
- API keys

#### File Storage Encryption
- **AWS S3:** Server-side encryption (SSE-S3)
- **Receipts/Invoices:** Encrypted before upload
- **Photos:** Standard S3 encryption

### Encryption in Transit

#### HTTPS/TLS
- **TLS Version:** 1.2 minimum, 1.3 preferred
- **Certificate:** Let's Encrypt auto-renewed
- **Cipher Suites:** Strong ciphers only
- **HSTS:** Enabled (max-age=31536000)

```python
# Django settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

#### API Communication
- All API endpoints require HTTPS
- WebSocket connections use WSS (WebSocket Secure)
- External API calls verify SSL certificates

### Data Sanitization

#### Input Validation
```python
from django.core.validators import validate_email, RegexValidator

class Project(models.Model):
    name = CharField(
        max_length=255,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s\-_]+$',
                message='Only alphanumeric, spaces, hyphens, and underscores allowed'
            )
        ]
    )
    
    email = EmailField(validators=[validate_email])
```

#### Output Encoding
- HTML escaping by default (Django templates)
- JSON encoding for API responses
- SQL parameterization (Django ORM)

---

## NETWORK SECURITY

### Firewall Rules
**Railway Platform:**
- Only ports 80 (HTTP) and 443 (HTTPS) exposed
- Internal services (Redis, PostgreSQL) not publicly accessible
- IP whitelisting for admin endpoints (optional)

### DDoS Protection
- **CloudFlare:** DDoS mitigation layer
- **Rate Limiting:** API endpoint throttling
- **Connection Limits:** Max connections per IP

### CORS (Cross-Origin Resource Sharing)
```python
# Django CORS settings
CORS_ALLOWED_ORIGINS = [
    "https://kibray.com",
    "https://www.kibray.com",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS'
]
```

---

## APPLICATION SECURITY

### CSRF Protection
**Django CSRF Middleware:** Enabled for all state-changing operations

```python
# CSRF token required for POST/PUT/DELETE
MIDDLEWARE = [
    ...
    'django.middleware.csrf.CsrfViewMiddleware',
    ...
]

# Cookie settings
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'Strict'
```

### SQL Injection Prevention
**Django ORM:** All queries parameterized

```python
# SAFE - Parameterized
Project.objects.filter(name=user_input)

# UNSAFE - Never do this
Project.objects.raw(f"SELECT * FROM projects WHERE name='{user_input}'")
```

### XSS (Cross-Site Scripting) Prevention

#### Template Auto-Escaping
```django
{# Django templates auto-escape by default #}
{{ user_input }}  {# Automatically escaped #}

{# Only use |safe if you trust the source #}
{{ admin_html_content|safe }}
```

#### Content Security Policy (CSP)
```python
# Django CSP settings
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://cdn.kibray.com")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
```

### File Upload Security

#### Validation
```python
from django.core.validators import FileExtensionValidator

class Document(models.Model):
    file = FileField(
        upload_to='documents/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
            )
        ],
        max_upload_size=10485760  # 10 MB
    )
    
    def save(self, *args, **kwargs):
        # Verify file type by content, not just extension
        file_type = magic.from_buffer(self.file.read(1024), mime=True)
        if file_type not in ALLOWED_MIME_TYPES:
            raise ValidationError('Invalid file type')
        
        # Sanitize filename
        self.file.name = secure_filename(self.file.name)
        
        super().save(*args, **kwargs)
```

#### Virus Scanning
```python
import clamd

def scan_file_for_viruses(file):
    cd = clamd.ClamdUnixSocket()
    scan_result = cd.scan(file.path)
    
    if scan_result[file.path][0] == 'FOUND':
        raise ValidationError(f'Virus detected: {scan_result[file.path][1]}')
```

### API Security

#### Rate Limiting
```python
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'expensive': '10/minute'  # For reports, AI analysis
    }
}
```

#### API Key Management
```python
class APIKey(models.Model):
    key = CharField(max_length=64, unique=True, db_index=True)
    user = ForeignKey(User, on_delete=CASCADE)
    name = CharField(max_length=100)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    last_used = DateTimeField(null=True)
    expires_at = DateTimeField(null=True)
    
    # IP whitelisting (optional)
    allowed_ips = JSONField(default=list)
    
    @classmethod
    def generate_key(cls):
        return secrets.token_urlsafe(48)
```

---

## AUDIT & COMPLIANCE

### Audit Logging

#### What Gets Logged
- All authentication attempts (success/failure)
- All authorization failures
- All data modifications (create/update/delete)
- All permission changes
- All role changes
- All sensitive data access
- All API calls
- All file uploads/downloads

#### Audit Log Model
```python
class AuditLog(models.Model):
    # Who
    user = ForeignKey(User, on_delete=SET_NULL, null=True)
    ip_address = GenericIPAddressField()
    user_agent = CharField(max_length=500)
    
    # What
    action = CharField(max_length=100)
    model = CharField(max_length=100)
    object_id = CharField(max_length=100)
    changes = JSONField(default=dict)
    
    # When
    timestamp = DateTimeField(auto_now_add=True)
    
    # Result
    success = BooleanField()
    error_message = TextField(blank=True)
    
    # Immutable
    class Meta:
        permissions = [
            ("view_audit_log", "Can view audit logs"),
        ]
    
    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionDenied("Audit logs are immutable")
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        raise PermissionDenied("Audit logs cannot be deleted")
```

#### Example Audit Entry
```json
{
  "user": "jane.smith@kibray.com",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "action": "update_project",
  "model": "Project",
  "object_id": "uuid-123",
  "changes": {
    "budget": {"old": "50000.00", "new": "55000.00"},
    "end_date": {"old": "2025-03-15", "new": "2025-03-20"}
  },
  "timestamp": "2025-12-08T10:30:00Z",
  "success": true
}
```

### Compliance

#### GDPR Compliance
- **Right to Access:** Users can export their data
- **Right to Erasure:** Data deletion process implemented
- **Data Portability:** Export in JSON format
- **Consent Management:** Explicit consent for data processing
- **Data Minimization:** Only collect necessary data

#### SOC 2 Readiness
- **Access Controls:** Role-based permissions
- **Audit Logging:** Complete activity trail
- **Encryption:** Data at rest and in transit
- **Incident Response:** Documented procedures
- **Monitoring:** Real-time alerting

---

## SECRETS MANAGEMENT

### Storage
**All secrets stored in Railway environment variables ONLY**

Never in:
- ❌ Source code
- ❌ Git repository
- ❌ Configuration files
- ❌ Database
- ❌ Client-side code

### Required Secrets
```bash
# Database
DATABASE_URL=postgresql://...

# Django
SECRET_KEY=...
FIELD_ENCRYPTION_KEY=...

# AWS S3
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=...

# Redis
REDIS_URL=redis://...

# Email
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...

# External APIs
GOOGLE_CALENDAR_CLIENT_ID=...
GOOGLE_CALENDAR_CLIENT_SECRET=...
OPENAI_API_KEY=...
SENTRY_DSN=...
```

### Secret Rotation
- **Database passwords:** Rotate every 90 days
- **API keys:** Rotate every 180 days
- **JWT secret:** Rotate annually
- **Encryption keys:** Rotate annually with key versioning

### Access Control
- Secrets accessible only to Admin role
- Railway environment variables require 2FA to view
- API keys logged on every use
- Suspicious access triggers alert

---

## INCIDENT RESPONSE

### Incident Severity Levels

| Level | Description | Response Time |
|-------|-------------|---------------|
| **P0 - Critical** | Data breach, system down | Immediate |
| **P1 - High** | Security vulnerability, partial outage | 1 hour |
| **P2 - Medium** | Performance degradation, minor issue | 4 hours |
| **P3 - Low** | Minor bug, cosmetic issue | 24 hours |

### Incident Response Plan

#### 1. Detection
- Automated alerts (Sentry, Railway)
- User reports
- Security scans
- Audit log analysis

#### 2. Containment
- Isolate affected systems
- Block malicious IPs
- Disable compromised accounts
- Take snapshots for forensics

#### 3. Eradication
- Patch vulnerabilities
- Remove malware
- Update credentials
- Close security gaps

#### 4. Recovery
- Restore from backups if needed
- Verify system integrity
- Re-enable services gradually
- Monitor closely

#### 5. Post-Incident
- Document incident
- Update procedures
- Notify affected users
- Implement preventive measures

### Emergency Contacts
```
Security Team Lead: security@kibray.com
System Admin: admin@kibray.com
Railway Support: Railway dashboard
Sentry Alerts: Sentry dashboard
```

---

## SECURITY BEST PRACTICES

### For Developers

1. **Never commit secrets** to Git
2. **Always use parameterized queries** (Django ORM)
3. **Validate all input** from users
4. **Escape all output** to prevent XSS
5. **Use HTTPS everywhere**
6. **Implement rate limiting** on sensitive endpoints
7. **Keep dependencies updated**
8. **Run security scans** before deploying
9. **Review code** for security issues
10. **Test with security mindset**

### For Administrators

1. **Enable 2FA** for all admin accounts
2. **Review audit logs** regularly
3. **Monitor failed login attempts**
4. **Rotate secrets** on schedule
5. **Keep system updated**
6. **Backup regularly** (automated)
7. **Test disaster recovery**
8. **Review user permissions** quarterly
9. **Train users** on security
10. **Report incidents** immediately

### For Users

1. **Use strong passwords** (8+ characters, mixed case, numbers, symbols)
2. **Enable 2FA** if available
3. **Don't share credentials**
4. **Lock screen** when away
5. **Verify email links** before clicking
6. **Report suspicious activity**
7. **Use secure networks** (avoid public WiFi for sensitive work)
8. **Keep browser updated**
9. **Log out** when done
10. **Don't reuse passwords**

---

## SECURITY MONITORING

### Real-Time Monitoring
- **Sentry:** Error and performance monitoring
- **Railway Metrics:** System health, resource usage
- **Custom Alerts:** Failed logins, permission denials, unusual activity

### Security Scans
- **Dependency scanning:** `safety check` (Python)
- **SAST:** Static Application Security Testing
- **DAST:** Dynamic Application Security Testing (staging)
- **Penetration testing:** Annually

### Metrics Tracked
- Failed login attempts per hour
- Permission denials per hour
- API rate limit hits
- Slow queries (potential DoS)
- Large file uploads (potential attack)
- Unusual access patterns

---

## CROSS-REFERENCES

- See **ROLE_PERMISSIONS_REFERENCE.md** for access control details
- See **DEPLOYMENT_MASTER.md** for secure deployment procedures
- See **API_ENDPOINTS_REFERENCE.md** for API security
- See **REQUIREMENTS_OVERVIEW.md** for security requirements

---

**Document Control:**
- Version: 1.0
- Status: Official Master Document #7 of 9
- Owner Approved: December 8, 2025
- Last Updated: December 8, 2025
- Next Security Review: March 8, 2026
