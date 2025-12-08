# Sentry Error Tracking Setup

## Overview

Sentry is configured for production error tracking, performance monitoring, and alerting.

## Configuration

Sentry is already integrated in `kibray_backend/settings/production.py`:

```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[
        DjangoIntegration(),
        RedisIntegration(),
        CeleryIntegration(),
    ],
    traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
    send_default_pii=False,  # Don't send personally identifiable information
    environment=os.getenv("DJANGO_ENV", "production"),
)
```

## Setup Steps

### 1. Create Sentry Project

1. Go to https://sentry.io/
2. Sign up or log in
3. Create a new project:
   - Platform: **Django**
   - Alert frequency: **On every new issue**
   - Name: **kibray-backend**

### 2. Get DSN

After creating the project:
1. Go to **Settings → Projects → kibray-backend → Client Keys (DSN)**
2. Copy the DSN (looks like: `https://xxxxx@sentry.io/xxxxx`)

### 3. Configure Environment Variables

Add to your production environment (Railway/Render):

```bash
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
DJANGO_ENV=production
```

For staging:
```bash
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
DJANGO_ENV=staging
```

### 4. Test Sentry Integration

Create a test view to trigger an error:

```python
# In any view file
def trigger_error(request):
    1 / 0  # This will trigger a ZeroDivisionError
```

Or use Django shell:
```python
python manage.py shell
>>> from sentry_sdk import capture_message
>>> capture_message("Test message from Kibray", level="info")
```

### 5. Configure Source Maps (Frontend)

For better error tracking in React/Vite frontend:

1. Install Sentry Vite plugin:
```bash
cd frontend
npm install @sentry/vite-plugin --save-dev
```

2. Update `vite.config.ts`:
```typescript
import { sentryVitePlugin } from "@sentry/vite-plugin";

export default defineConfig({
  plugins: [
    react(),
    sentryVitePlugin({
      org: "your-org-slug",
      project: "kibray-frontend",
      authToken: process.env.SENTRY_AUTH_TOKEN,
    }),
  ],
  build: {
    sourcemap: true, // Enable source maps
  },
});
```

3. Add to frontend environment:
```bash
VITE_SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
SENTRY_AUTH_TOKEN=your_auth_token
```

## Alert Configuration

### Email Alerts

1. Go to **Settings → Projects → kibray-backend → Alerts**
2. Create alert rule:
   - **When**: An event is seen
   - **If**: First seen
   - **Then**: Send notification via Email

### Slack Integration

1. Go to **Settings → Integrations → Slack**
2. Click **Add to Slack**
3. Choose channel for notifications
4. Configure alert rules to use Slack

### PagerDuty (Critical Issues)

For production incidents:
1. Go to **Settings → Integrations → PagerDuty**
2. Connect PagerDuty account
3. Create alert rule for critical errors

## Performance Monitoring

Current configuration tracks 10% of transactions (`traces_sample_rate=0.1`).

### View Performance Data

1. Go to **Performance** tab in Sentry
2. See transaction durations, database queries, external API calls
3. Identify slow endpoints

### Increase Sampling for Specific Transactions

```python
import sentry_sdk

def traces_sampler(sampling_context):
    # Sample 100% of /api/v1/projects/ endpoints
    if sampling_context["wsgi_environ"]["PATH_INFO"].startswith("/api/v1/projects/"):
        return 1.0
    # Sample 10% of everything else
    return 0.1

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sampler=traces_sampler,
)
```

## Custom Context

Add custom data to error reports:

```python
from sentry_sdk import set_user, set_context, capture_exception

# Set user context
set_user({"id": user.id, "email": user.email, "username": user.username})

# Set custom context
set_context("business_context", {
    "project_id": project.id,
    "project_name": project.name,
    "action": "invoice_generation",
})

# Capture exception with extra data
try:
    generate_invoice(project)
except Exception as e:
    capture_exception(e)
```

## Release Tracking

Track which code version caused errors:

```bash
# Install Sentry CLI
curl -sL https://sentry.io/get-cli/ | bash

# Create release
sentry-cli releases new $(git describe --always)
sentry-cli releases set-commits --auto $(git describe --always)
sentry-cli releases finalize $(git describe --always)

# Associate with deployment
sentry-cli releases deploys $(git describe --always) new -e production
```

Add to CI/CD workflow (`.github/workflows/ci-cd.yml`):

```yaml
- name: Create Sentry Release
  env:
    SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
    SENTRY_ORG: your-org
    SENTRY_PROJECT: kibray-backend
  run: |
    curl -sL https://sentry.io/get-cli/ | bash
    export SENTRY_RELEASE=$(git describe --always)
    sentry-cli releases new $SENTRY_RELEASE
    sentry-cli releases set-commits --auto $SENTRY_RELEASE
    sentry-cli releases finalize $SENTRY_RELEASE
```

## Issue Management

### Resolve Issues

1. Click **Resolve** in issue detail
2. Sentry will reopen if error occurs again

### Ignore Issues

For known non-critical issues:
1. Click **Ignore** → **Until this affects more users**
2. Or permanently ignore

### Assign Issues

1. Click **Assign to** → Team member
2. Receive notification when assigned

## Metrics Dashboard

View key metrics:
- **Error rate**: Errors per minute
- **APDEX score**: Application performance index
- **Throughput**: Requests per minute
- **P50/P75/P95**: Response time percentiles

## Best Practices

1. **Don't send PII**: `send_default_pii=False` is set
2. **Sample appropriately**: 10% sampling reduces Sentry costs
3. **Add context**: Use `set_context()` for business logic context
4. **Tag errors**: Use tags for filtering (environment, feature, user_type)
5. **Create breadcrumbs**: Add breadcrumbs for debugging flow

Example breadcrumbs:
```python
from sentry_sdk import add_breadcrumb

add_breadcrumb(
    category="project",
    message="User created new project",
    level="info",
    data={"project_id": project.id}
)
```

## Cost Optimization

- Free tier: 5,000 errors/month, 10,000 transactions/month
- Adjust `traces_sample_rate` based on traffic
- Use `before_send` to filter out noisy errors:

```python
def before_send(event, hint):
    # Don't send 404 errors
    if event.get('logger') == 'django.security.DisallowedHost':
        return None
    return event

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    before_send=before_send,
)
```

## Production Checklist

- [x] Sentry SDK installed (`sentry-sdk==2.18.0`)
- [x] Integration configured in `production.py`
- [ ] SENTRY_DSN environment variable set
- [ ] Test error captured successfully
- [ ] Email alerts configured
- [ ] Slack notifications set up (optional)
- [ ] Performance monitoring reviewed
- [ ] Release tracking configured in CI/CD
- [ ] Source maps uploaded for frontend
- [ ] Team members invited to Sentry project

## Support

- Documentation: https://docs.sentry.io/platforms/python/guides/django/
- Status page: https://status.sentry.io/
- Community: https://discord.gg/sentry
