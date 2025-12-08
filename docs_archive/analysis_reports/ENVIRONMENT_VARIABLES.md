# Environment Variables Management Guide

## Overview

This guide documents all required environment variables for Kibray deployment across different environments.

## Environment Variables Checklist

### ✅ Required for All Environments

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `DJANGO_ENV` | Environment name | `development`, `staging`, `production` | Yes |
| `SECRET_KEY` | Django secret key (50+ chars) | `django-insecure-xxx...` | Yes |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` | Yes (prod/staging) |

### 🔐 Security & Authentication

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `kibray.com,www.kibray.com` | Yes (prod) |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated trusted origins | `https://kibray.com` | Yes (prod) |
| `CORS_ALLOWED_ORIGINS` | Comma-separated CORS origins | `https://app.kibray.com` | Yes (prod) |

### 💾 Database & Cache

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL URL | See above | Yes |
| `REDIS_URL` | Redis connection string | `redis://user:pass@host:6379/0` | Yes (prod) |
| `REDIS_PASSWORD` | Redis password (if required) | `secure_password` | Recommended |

### 📦 Static & Media Files

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `AWS_ACCESS_KEY_ID` | AWS access key | `AKIAXXXXX` | Yes (prod) |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `xxxxx` | Yes (prod) |
| `AWS_STORAGE_BUCKET_NAME` | S3 bucket name | `kibray-media` | Yes (prod) |
| `AWS_S3_REGION_NAME` | AWS region | `us-east-1` | Yes (prod) |
| `AWS_S3_CUSTOM_DOMAIN` | CloudFront domain (optional) | `cdn.kibray.com` | No |

### 📧 Email Configuration

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `EMAIL_HOST` | SMTP server | `smtp.gmail.com` | Yes (prod) |
| `EMAIL_PORT` | SMTP port | `587` | Yes (prod) |
| `EMAIL_HOST_USER` | SMTP username | `noreply@kibray.com` | Yes (prod) |
| `EMAIL_HOST_PASSWORD` | SMTP password | `app_password` | Yes (prod) |
| `EMAIL_USE_TLS` | Use TLS | `True` | Yes (prod) |
| `DEFAULT_FROM_EMAIL` | Default sender | `Kibray <noreply@kibray.com>` | Yes (prod) |

### 🔔 Push Notifications (Firebase)

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `FIREBASE_CREDENTIALS_PATH` | Path to service account JSON | `/app/firebase-creds.json` | Yes (for push) |
| `VITE_FIREBASE_API_KEY` | Firebase API key | `AIzaSyXXXX` | Yes (for push) |
| `VITE_FIREBASE_PROJECT_ID` | Firebase project ID | `kibray-prod` | Yes (for push) |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | Firebase sender ID | `123456789` | Yes (for push) |
| `VITE_FIREBASE_APP_ID` | Firebase app ID | `1:123:web:xxx` | Yes (for push) |
| `VITE_FIREBASE_VAPID_KEY` | VAPID key for web push | `BG7XXX...` | Yes (for push) |

### 📊 Monitoring & Logging

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `SENTRY_DSN` | Sentry project DSN | `https://xxx@sentry.io/xxx` | Recommended |
| `LOG_LEVEL` | Logging level | `INFO`, `DEBUG`, `WARNING` | No |

### ⚙️ Application Settings

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `API_BASE_URL` | Backend API URL | `https://api.kibray.com` | Yes (frontend) |
| `WEB_CONCURRENCY` | Gunicorn workers | `4` | No (auto-calculated) |
| `PORT` | Server port | `8000` | No (platform-provided) |

### 📈 Business Intelligence

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `BI_LOW_MARGIN_THRESHOLD` | Low margin threshold (%) | `15` | No |
| `BI_HIGH_MARGIN_THRESHOLD` | High margin threshold (%) | `30` | No |

### 🔄 Celery (Background Tasks)

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `CELERY_BROKER_URL` | Celery broker (Redis) | `redis://host:6379/0` | Yes (if using Celery) |
| `CELERY_RESULT_BACKEND` | Result backend | `redis://host:6379/0` | Yes (if using Celery) |

## Platform-Specific Configuration

### Railway

Set variables in Railway dashboard:
```bash
railway variables set DJANGO_ENV=production
railway variables set SECRET_KEY="your-secret-key"
railway variables set DATABASE_URL="postgresql://..."
```

Or use Railway CLI:
```bash
railway link
railway variables set --environment production
```

### Render

Set in Render dashboard under **Environment**:
- Auto-generated: `DATABASE_URL`, `PORT`
- Manual: All other variables from `.env.example`

Or use `render.yaml`:
```yaml
envVars:
  - key: DJANGO_ENV
    value: production
  - key: SECRET_KEY
    generateValue: true
```

### Heroku

Set with Heroku CLI:
```bash
heroku config:set DJANGO_ENV=production
heroku config:set SECRET_KEY="your-secret-key"
```

Add DATABASE_URL via addon:
```bash
heroku addons:create heroku-postgresql:mini
```

## Security Best Practices

### 1. Never Commit Secrets

- Add `.env` to `.gitignore` (already done)
- Use `.env.example` with dummy values only
- Use platform secret management (Railway/Render/Heroku)

### 2. Rotate Secrets Regularly

- `SECRET_KEY`: Change every 90 days
- Database passwords: Change every 90 days
- API keys: Rotate when team members leave
- JWT secrets: Rotate on security incidents

### 3. Use Strong Values

Generate `SECRET_KEY`:
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Generate random password:
```bash
openssl rand -base64 32
```

### 4. Separate by Environment

Use different values for:
- Development: Less restrictive, test APIs
- Staging: Production-like, staging APIs
- Production: Strict security, production APIs

### 5. Principle of Least Privilege

- AWS IAM: Only S3 access, not EC2
- Database: Application user can't DROP tables
- Redis: Use password authentication

## Validation Script

Create `scripts/validate_env.py`:

```python
#!/usr/bin/env python
"""Validate required environment variables"""
import os
import sys

REQUIRED_VARS = {
    "production": [
        "DJANGO_ENV",
        "SECRET_KEY",
        "ALLOWED_HOSTS",
        "DATABASE_URL",
        "REDIS_URL",
        "EMAIL_HOST",
        "EMAIL_HOST_USER",
        "EMAIL_HOST_PASSWORD",
    ],
    "staging": [
        "DJANGO_ENV",
        "SECRET_KEY",
        "DATABASE_URL",
        "REDIS_URL",
    ],
    "development": [
        "SECRET_KEY",
    ],
}

def validate_env(environment="production"):
    missing = []
    required = REQUIRED_VARS.get(environment, [])
    
    for var in required:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing required environment variables for {environment}:")
        for var in missing:
            print(f"  - {var}")
        sys.exit(1)
    else:
        print(f"✅ All required environment variables for {environment} are set")

if __name__ == "__main__":
    env = os.getenv("DJANGO_ENV", "development")
    validate_env(env)
```

Run before deployment:
```bash
python scripts/validate_env.py
```

## Troubleshooting

### "SECRET_KEY must be set"

```bash
export SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
```

### "DATABASE_URL not found"

Check format:
```
postgresql://username:password@hostname:5432/database_name
```

For Railway/Render, this is auto-generated.

### Redis connection refused

Check `REDIS_URL` format:
```
redis://username:password@hostname:6379/0
```

For Railway/Render, add Redis service.

### AWS S3 access denied

1. Verify `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
2. Check IAM permissions (S3 PutObject, GetObject, DeleteObject)
3. Verify bucket name and region

### Email sending fails

1. Check SMTP credentials
2. For Gmail: Use App Password, not regular password
3. Check firewall allows port 587 (TLS) or 465 (SSL)

## Environment Files

### `.env.example` (template)
```bash
# Copy this to .env and fill in real values
# DO NOT commit .env to version control

DJANGO_ENV=development
SECRET_KEY=change-me-in-production
DATABASE_URL=postgresql://user:pass@localhost:5432/kibray
...
```

### `.env` (local development - gitignored)
```bash
DJANGO_ENV=development
SECRET_KEY=local-dev-key-not-secure
DATABASE_URL=sqlite:///db.sqlite3
DEBUG=True
```

### Platform Environment (production)
Set in Railway/Render/Heroku dashboard - never in code.

## References

- [Django Settings Best Practices](https://docs.djangoproject.com/en/5.0/topics/settings/)
- [12-Factor App Config](https://12factor.net/config)
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
