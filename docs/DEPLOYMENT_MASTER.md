# DEPLOYMENT MASTER
**System:** Kibray ERP  
**Last Updated:** December 8, 2025  
**Status:** Official Master Document  
**Owner Authorization:** Approved via Owner Decision Questionnaire

---

## TABLE OF CONTENTS

1. [Deployment Overview](#deployment-overview)
2. [Infrastructure](#infrastructure)
3. [Deployment Workflow](#deployment-workflow)
4. [Environment Configuration](#environment-configuration)
5. [Pre-Deployment Validation](#pre-deployment-validation)
6. [Deployment Procedures](#deployment-procedures)
7. [Post-Deployment Verification](#post-deployment-verification)
8. [Rollback Procedures](#rollback-procedures)
9. [Monitoring & Alerts](#monitoring--alerts)
10. [Troubleshooting](#troubleshooting)

---

## DEPLOYMENT OVERVIEW

### Deployment Strategy
**Continuous Deployment** via Railway platform

**Workflow:**
```
Push to main branch
    ↓
GitHub Actions run tests
    ↓
Tests pass
    ↓
Railway auto-deploys
    ↓
Migrations run automatically
    ↓
Health checks validate
    ↓
Production live
```

### Deployment Frequency
- **Development:** On every commit to `develop` branch
- **Staging:** On every commit to `staging` branch
- **Production:** On every commit to `main` branch (after validation)

### Deployment Principles
1. **Automated:** No manual deployment steps
2. **Tested:** All tests must pass before deploy
3. **Reversible:** Quick rollback capability
4. **Monitored:** Real-time health monitoring
5. **Documented:** Every deploy logged

---

## INFRASTRUCTURE

### Platform: Railway

**Why Railway:**
- Auto-deploy on git push
- Built-in PostgreSQL and Redis
- Environment variable management
- SSL certificates auto-managed
- Zero-downtime deployments
- Easy rollback
- Monitoring included

### Architecture

```
┌─────────────────────────────────────────────┐
│            CloudFlare CDN                    │
│         (DDoS protection, caching)           │
└───────────────────┬─────────────────────────┘
                    │
                    │ HTTPS
                    ↓
┌─────────────────────────────────────────────┐
│          Railway Load Balancer               │
└───────────────────┬─────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ↓                       ↓
┌───────────────┐       ┌───────────────┐
│  Django App   │       │  Django App   │
│  Instance 1   │       │  Instance 2   │
└───────┬───────┘       └───────┬───────┘
        │                       │
        └───────────┬───────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ↓                       ↓
┌───────────────┐       ┌───────────────┐
│  PostgreSQL   │       │     Redis     │
│   Database    │       │     Cache     │
└───────────────┘       └───────────────┘
        │                       │
        └───────────┬───────────┘
                    ↓
            ┌───────────────┐
            │   AWS S3      │
            │ Media Storage │
            └───────────────┘
```

### Resource Allocation

#### Production
- **App Instances:** 2 (auto-scaling up to 4)
- **Memory:** 2 GB per instance
- **CPU:** 2 vCPU per instance
- **Database:** PostgreSQL 15 - 4 GB RAM, 50 GB storage
- **Redis:** 1 GB RAM
- **Storage:** AWS S3 (unlimited)

#### Staging
- **App Instances:** 1
- **Memory:** 1 GB
- **CPU:** 1 vCPU
- **Database:** PostgreSQL 15 - 2 GB RAM, 20 GB storage
- **Redis:** 512 MB

---

## DEPLOYMENT WORKFLOW

### Automated Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          python manage.py test
      
      - name: Run security checks
        run: |
          safety check
          bandit -r . -ll
      
      - name: Check migrations
        run: |
          python manage.py makemigrations --check --dry-run

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: success()
    steps:
      - name: Trigger Railway Deploy
        run: |
          curl -X POST ${{ secrets.RAILWAY_WEBHOOK_URL }}
```

### Railway Configuration

**railway.json:**
```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt && python manage.py collectstatic --noinput"
  },
  "deploy": {
    "startCommand": "gunicorn config.wsgi:application --bind 0.0.0.0:$PORT",
    "healthcheckPath": "/health/",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

---

## ENVIRONMENT CONFIGURATION

### Environment Variables

#### Required for All Environments
```bash
# Django Core
SECRET_KEY=...                    # Django secret key
DEBUG=False                       # NEVER True in production
ALLOWED_HOSTS=kibray.up.railway.app,kibray.com

# Database
DATABASE_URL=postgresql://...     # Railway auto-provides

# Redis
REDIS_URL=redis://...            # Railway auto-provides

# Static/Media
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=kibray-media
AWS_S3_REGION_NAME=us-east-1

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...

# Encryption
FIELD_ENCRYPTION_KEY=...         # For encrypted fields

# External APIs
OPENAI_API_KEY=...
GOOGLE_CALENDAR_CLIENT_ID=...
GOOGLE_CALENDAR_CLIENT_SECRET=...

# Monitoring
SENTRY_DSN=...
```

#### Production-Specific
```bash
# Performance
DJANGO_SETTINGS_MODULE=config.settings.production
CONN_MAX_AGE=600                 # Database connection pooling
GUNICORN_WORKERS=4
GUNICORN_THREADS=2

# Security
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Caching
CACHE_TTL=3600
```

### Configuration Management

**settings/production.py:**
```python
from .base import *

DEBUG = False

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# Database with connection pooling
DATABASES['default']['CONN_MAX_AGE'] = 600

# Redis cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {'max_connections': 50}
        }
    }
}

# Security
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'sentry_sdk.integrations.logging.EventHandler',
        },
    },
    'root': {
        'handlers': ['console', 'sentry'],
        'level': 'INFO',
    },
}
```

---

## PRE-DEPLOYMENT VALIDATION

### Validation Checklist

**Required before EVERY deployment:**

#### 1. Unit Tests
```bash
python manage.py test --verbosity=2
```
- All tests must pass
- No skipped tests without justification
- Coverage > 80%

#### 2. Integration Tests
```bash
python manage.py test core.tests.test_integration --verbosity=2
```
- API endpoint tests
- Database integration tests
- External service mocks

#### 3. Permission Tests
```bash
python manage.py test core.tests.test_permissions --verbosity=2
```
- All 7 roles validated
- Permission matrix verified
- API access control tested

#### 4. Financial Tests
```bash
python manage.py test financials.tests --verbosity=2
```
- Calculation accuracy
- Invoice generation
- Profitability reports

#### 5. Calendar Tests
```bash
python manage.py test calendar.tests --verbosity=2
```
- Event creation
- Conflict detection
- External sync
- Drag & drop

#### 6. Startup Checks
```bash
python manage.py check --deploy
```
- Configuration validation
- Security checks
- Database connectivity

#### 7. Migrations
```bash
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
```
- No pending migrations
- Migration plan reviewed

#### 8. Static Files
```bash
python manage.py collectstatic --noinput --dry-run
```
- All static files collected
- No missing files

#### 9. AI Readiness
```bash
python manage.py test ai_assistant.tests --verbosity=2
```
- OpenAI API connectivity
- Model loading
- Risk detection

#### 10. Documentation Integrity
```bash
# Validate all master documents exist
ls -1 *.md | grep -E "(ARCHITECTURE|REQUIREMENTS|MODULES|ROLE|API|CALENDAR|SECURITY|DEPLOYMENT|PHASE)"
```
- All 9 master documents present
- No broken links
- Current version info

---

## DEPLOYMENT PROCEDURES

### Standard Deployment

#### Step 1: Pre-Deployment
```bash
# Run full validation suite
./scripts/pre_deploy_check.sh

# Expected output: ALL CHECKS PASSED
```

#### Step 2: Merge to Main
```bash
git checkout main
git pull origin main
git merge develop
git push origin main
```

#### Step 3: Monitor GitHub Actions
- Watch test execution
- Verify all tests pass
- Check for warnings

#### Step 4: Railway Auto-Deploys
- Build starts automatically
- Migrations run
- Static files collected
- Health check validates

#### Step 5: Smoke Tests
```bash
# API health
curl https://kibray.up.railway.app/health/

# Database connectivity
curl https://kibray.up.railway.app/api/health/db/

# Redis connectivity
curl https://kibray.up.railway.app/api/health/redis/

# Authentication
curl -X POST https://kibray.up.railway.app/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'
```

### Emergency Deployment (Hotfix)

#### For Critical Issues Only

1. Create hotfix branch from main
   ```bash
   git checkout main
   git checkout -b hotfix/critical-issue
   ```

2. Make minimal changes
   - Only fix the critical issue
   - No feature additions
   - No refactoring

3. Test thoroughly
   ```bash
   python manage.py test
   ```

4. Fast-track merge
   ```bash
   git checkout main
   git merge hotfix/critical-issue
   git push origin main
   ```

5. Monitor closely
   - Watch deploy in Railway dashboard
   - Monitor Sentry for errors
   - Verify fix in production

---

## POST-DEPLOYMENT VERIFICATION

### Automated Checks

**Health Check Endpoint:**
```python
# /health/ endpoint
def health_check(request):
    checks = {
        'database': check_database(),
        'redis': check_redis(),
        'storage': check_s3(),
        'migrations': check_migrations(),
    }
    
    all_healthy = all(checks.values())
    status = 200 if all_healthy else 503
    
    return JsonResponse({
        'status': 'healthy' if all_healthy else 'unhealthy',
        'checks': checks,
        'timestamp': timezone.now().isoformat()
    }, status=status)
```

### Manual Verification

**Dashboard Smoke Test:**
1. Log in as Admin
2. Navigate to main dashboard
3. Verify all widgets load
4. Check for JavaScript errors
5. Verify WebSocket connection

**Core Functionality Test:**
1. Create a test project
2. Add a calendar event
3. Create a task
4. Upload a photo
5. Generate an invoice (draft)
6. Delete test data

### Performance Verification

**Response Time Benchmarks:**
- Homepage: < 500ms
- API endpoints: < 200ms
- Dashboard: < 1s
- Reports: < 5s

**Monitor:**
```bash
# Average response time
curl -w "@curl-format.txt" -o /dev/null -s https://kibray.up.railway.app/

# Database query time
# Check Railway metrics
```

---

## ROLLBACK PROCEDURES

### Automatic Rollback

Railway automatically rolls back if:
- Health check fails
- App crashes repeatedly
- Startup timeout

### Manual Rollback

#### Option 1: Railway Dashboard
1. Go to Railway dashboard
2. Select project
3. Click "Deployments"
4. Find last stable deployment
5. Click "Rollback"

#### Option 2: Git Revert
```bash
# Revert last commit
git revert HEAD
git push origin main

# Railway auto-deploys reverted code
```

#### Option 3: Re-deploy Previous Version
```bash
# Find last stable commit
git log --oneline

# Reset to that commit
git reset --hard <commit-hash>
git push origin main --force

# WARNING: Only use in emergencies
```

### Post-Rollback

1. **Investigate Issue**
   - Check Sentry errors
   - Review deploy logs
   - Identify root cause

2. **Fix in Development**
   - Create fix branch
   - Test thoroughly
   - Code review

3. **Re-deploy Fix**
   - Merge to main
   - Monitor closely

---

## MONITORING & ALERTS

### Monitoring Tools

#### 1. Sentry (Error Tracking)
- Real-time error reports
- Stack traces
- User context
- Performance monitoring

**Alert Thresholds:**
- Error rate > 10/minute → Alert admins
- Same error > 100 times → Page on-call
- Performance regression > 50% → Investigate

#### 2. Railway Metrics
- CPU usage
- Memory usage
- Request rate
- Response time
- Database connections

**Alert Thresholds:**
- CPU > 80% for 5min → Scale up
- Memory > 90% → Investigate
- Response time > 2s avg → Performance issue

#### 3. Custom Alerts

```python
# Custom monitoring
class SystemMonitor:
    def check_critical_services(self):
        alerts = []
        
        # Database connections
        active_conns = self.get_db_connections()
        if active_conns > 80:
            alerts.append('High database connection count')
        
        # Redis memory
        redis_mem = self.get_redis_memory()
        if redis_mem > 0.9:
            alerts.append('Redis near memory limit')
        
        # Celery queue
        queue_size = self.get_celery_queue_size()
        if queue_size > 1000:
            alerts.append('Celery queue backing up')
        
        return alerts
```

### Alert Channels
- **Email:** Immediate for critical issues
- **Slack:** Real-time for all alerts
- **SMS:** Critical only (P0 incidents)
- **Dashboard:** All alerts visible

---

## TROUBLESHOOTING

### Common Issues

#### Issue: Deploy Fails with Migration Error

**Symptoms:**
```
django.db.utils.OperationalError: no such table: core_project
```

**Solution:**
```bash
# Railway CLI
railway run python manage.py migrate --fake-initial

# Or via Railway dashboard: Run Command
python manage.py migrate
```

#### Issue: Static Files Not Loading

**Symptoms:**
- CSS not applied
- Images missing
- 404 on static files

**Solution:**
```bash
# Verify S3 credentials
python manage.py check

# Re-collect static files
railway run python manage.py collectstatic --noinput --clear
```

#### Issue: Database Connection Errors

**Symptoms:**
```
FATAL: too many connections
```

**Solution:**
```python
# Increase CONN_MAX_AGE
DATABASES['default']['CONN_MAX_AGE'] = 0  # Temporary fix

# Then investigate connection leaks
# Add to middleware for monitoring
```

#### Issue: High Memory Usage

**Symptoms:**
- App crashes
- Slow performance
- Out of memory errors

**Solution:**
```bash
# Check for memory leaks
# Profile with memory_profiler

# Reduce Gunicorn workers temporarily
GUNICORN_WORKERS=2  # Down from 4

# Scale up Railway instance
```

#### Issue: WebSocket Disconnects

**Symptoms:**
- Real-time updates stop
- Users report stale data

**Solution:**
```python
# Check Redis connection
redis-cli -u $REDIS_URL ping

# Verify channel layer
python manage.py shell
>>> from channels.layers import get_channel_layer
>>> channel_layer = get_channel_layer()
>>> await channel_layer.send("test", {"type": "test.message"})

# Restart app if needed
```

---

## DEPLOYMENT HISTORY

### Recent Deployments
Track in `/docs/deployment_log.md`

**Format:**
```markdown
## Deployment YYYY-MM-DD HH:MM

- **Commit:** abc123def
- **Deployed By:** Jane Smith
- **Changes:**
  - Feature: Added AI risk detection
  - Fix: Resolved calendar sync issue
  - Migration: 0097_add_risk_fields
- **Tests:** 740 passing
- **Status:** ✅ Success
- **Rollback:** No issues
```

---

## CROSS-REFERENCES

- See **SECURITY_COMPREHENSIVE.md** for security deployment requirements
- See **ARCHITECTURE_UNIFIED.md** for system architecture
- See **REQUIREMENTS_OVERVIEW.md** for deployment requirements

---

**Document Control:**
- Version: 1.0
- Status: Official Master Document #8 of 9
- Owner Approved: December 8, 2025
- Last Updated: December 8, 2025
- Next Review: March 8, 2026
