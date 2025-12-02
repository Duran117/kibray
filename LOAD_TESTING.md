# Load Testing Guide

## Overview

Kibray uses [Locust](https://locust.io/) for load testing and performance analysis.

## Installation

Locust is already in `requirements.txt`:
```bash
pip install locust==2.32.4
```

## Running Load Tests

### Basic Test

```bash
# Start Locust with web UI
locust -f locustfile.py --host=http://localhost:8000

# Open browser at http://localhost:8089
# Configure:
# - Number of users: 100
# - Spawn rate: 10 users/second
# - Host: http://localhost:8000 (or production URL)
```

### Headless Mode (CI/CD)

```bash
# Run without web UI
locust -f locustfile.py \
    --host=https://api.kibray.com \
    --users=100 \
    --spawn-rate=10 \
    --run-time=5m \
    --headless \
    --html=load-test-report.html
```

### Production Load Test

```bash
# Gradual ramp-up for production
locust -f locustfile.py \
    --host=https://api.kibray.com \
    --users=500 \
    --spawn-rate=5 \
    --run-time=10m \
    --headless \
    --csv=results/prod-test \
    --html=results/prod-test.html
```

## Test Scenarios

### 1. KibrayUser (Regular User)
- **Weight**: 10 (most common)
- **Tasks**:
  - View dashboard (3x)
  - List projects (5x)
  - View project detail (2x)
  - List tasks (4x)
  - Create task (1x)
  - View time entries (2x)
  - Create time entry (1x)
  - View schedule (2x)
  - Search (1x)
  - View analytics (1x)

### 2. AdminUser (Administrator)
- **Weight**: 1 (1 admin per 10 users)
- **Tasks**:
  - View admin dashboard (2x)
  - Export data (1x) - heavy
  - View detailed analytics (1x)
  - Bulk operations (1x)

### 3. APIOnlyUser (Mobile/Integration)
- **Weight**: 2 (2 API users per 10 users)
- **Tasks**:
  - Sync data (5x)
  - Push updates (3x)
  - Upload photo (1x) - heavy

## Performance Targets

### Response Times (95th percentile)
- **List endpoints**: < 200ms
- **Detail endpoints**: < 150ms
- **Create/Update**: < 300ms
- **Heavy operations** (exports, bulk): < 2000ms
- **Health check**: < 50ms

### Throughput
- **Target**: 100 requests/second sustained
- **Peak**: 200 requests/second for 1 minute
- **Users**: Support 500 concurrent users

### Error Rate
- **Target**: < 0.1% error rate
- **Acceptable**: < 1% under peak load

## Interpreting Results

### Locust Web UI Metrics

1. **RPS (Requests Per Second)**
   - Current throughput
   - Should be stable, not declining

2. **Response Times**
   - Median (50th percentile)
   - 95th percentile - most important
   - 99th percentile - catch outliers

3. **Number of Users**
   - Active virtual users
   - Ramp up gradually

4. **Failures**
   - Failed requests count
   - Should be < 1%

### Statistics Tab

```
Name                            # reqs    # fails    Avg    Min    Max  Median  req/s
GET /api/v1/projects/            1250        2     145     45    823    150    12.5
POST /api/v1/tasks/               250        0     287     98   1203    280     2.5
```

**Key metrics**:
- **# fails**: Should be very low
- **Avg**: Average response time
- **Median**: 50th percentile (typical user experience)
- **req/s**: Throughput per endpoint

### Failures Tab

Shows failed requests with reasons:
- **Connection errors**: Server crashed or overloaded
- **HTTP 500**: Application errors (check Sentry)
- **HTTP 429**: Rate limiting (expected if enabled)
- **Timeouts**: Response > 30 seconds

## Monitoring During Load Tests

### 1. Server Metrics (Railway/Render Dashboard)

Monitor:
- **CPU usage**: Should stay < 80%
- **Memory usage**: Should stay < 90%
- **Network I/O**: Track bandwidth
- **Database connections**: Should not max out

### 2. Database (PostgreSQL)

```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

-- Slow queries (> 100ms)
SELECT query, mean_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Database size
SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database;
```

### 3. Redis (Cache)

```bash
# Connect to Redis
redis-cli

# Monitor commands in real-time
MONITOR

# Get stats
INFO stats
INFO memory

# Check connected clients
CLIENT LIST
```

### 4. Application Logs

```bash
# Tail logs during load test
tail -f logs/django.log

# Filter errors only
grep ERROR logs/django.log | tail -20

# Count error types
grep ERROR logs/django.log | cut -d' ' -f5 | sort | uniq -c
```

## Common Performance Issues

### 1. Database N+1 Queries

**Symptom**: Slow list endpoints (> 500ms)

**Fix**: Use `select_related()` and `prefetch_related()`:
```python
# Bad
projects = Project.objects.all()

# Good
projects = Project.objects.select_related('owner').prefetch_related('tasks')
```

### 2. Missing Indexes

**Symptom**: Slow filtering/ordering queries

**Fix**: Add database indexes (see `DATABASE_OPTIMIZATION.md`)

### 3. Large Serializer Responses

**Symptom**: High response times despite fast queries

**Fix**: Use field limiting:
```python
# In serializer Meta
fields = ['id', 'title', 'status']  # Only return needed fields
```

### 4. Memory Leaks

**Symptom**: Memory usage increases over time

**Fix**: 
- Enable `max_requests` in Gunicorn (already set to 1000)
- Check for queryset caching issues
- Review Celery task cleanup

### 5. Connection Pool Exhaustion

**Symptom**: Database connection errors under load

**Fix**: Adjust connection pool size in `production.py`:
```python
DATABASES = {
    'default': {
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',  # 30 seconds
        }
    }
}
```

## Optimization Strategies

### 1. Caching (Already Implemented)

```python
from django.core.cache import cache

# Cache expensive queries
projects = cache.get('all_projects')
if not projects:
    projects = Project.objects.select_related('owner').all()
    cache.set('all_projects', projects, 300)  # 5 minutes
```

### 2. Pagination (Already Implemented)

```python
# REST Framework pagination in settings
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
```

### 3. Database Connection Pooling (Already Implemented)

- PostgreSQL: `conn_max_age=600` (10 minutes)
- Redis: Connection pool with 50 max connections

### 4. Static File Optimization (Already Implemented)

- WhiteNoise with compression
- Gzip compression for text files
- CDN for static assets (optional)

### 5. Async Tasks (Already Implemented)

- Celery for background jobs
- Email sending asynchronous
- Report generation async

## Load Testing Schedule

### Before Launch
- [ ] Run 100 users for 10 minutes
- [ ] Run 500 users for 5 minutes
- [ ] Identify and fix bottlenecks

### Weekly (Staging)
- [ ] Automated load test in CI/CD
- [ ] Compare results to baseline
- [ ] Alert if performance degrades > 20%

### Monthly (Production)
- [ ] Off-peak load test
- [ ] Review and optimize slow endpoints
- [ ] Update capacity planning

### After Major Releases
- [ ] Load test new features
- [ ] Compare to previous version
- [ ] Ensure no performance regression

## CI/CD Integration

Add to `.github/workflows/ci-cd.yml`:

```yaml
jobs:
  load-test:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    steps:
      - uses: actions/checkout@v4
      
      - name: Install Locust
        run: pip install locust==2.32.4
      
      - name: Run Load Test
        run: |
          locust -f locustfile.py \
            --host=${{ secrets.STAGING_URL }} \
            --users=50 \
            --spawn-rate=5 \
            --run-time=2m \
            --headless \
            --html=load-test-report.html
      
      - name: Upload Results
        uses: actions/upload-artifact@v4
        with:
          name: load-test-results
          path: load-test-report.html
      
      - name: Check Performance
        run: |
          # Fail if 95th percentile > 500ms
          python scripts/check_performance.py load-test-report.html
```

## Resources

- [Locust Documentation](https://docs.locust.io/)
- [Load Testing Best Practices](https://www.nginx.com/blog/load-testing-best-practices/)
- [Performance Testing Checklist](https://github.com/aliesbelik/awesome-performance-testing)

## Example Commands

```bash
# Quick test (local)
locust -f locustfile.py --host=http://localhost:8000 --users=10 --spawn-rate=2 --run-time=1m --headless

# Staging test
locust -f locustfile.py --host=https://staging.kibray.com --users=100 --spawn-rate=10 --run-time=5m --headless --html=staging-report.html

# Production smoke test (low load)
locust -f locustfile.py --host=https://kibray.com --users=50 --spawn-rate=5 --run-time=3m --headless --html=prod-smoke.html

# Peak load test (high load)
locust -f locustfile.py --host=https://kibray.com --users=500 --spawn-rate=10 --run-time=10m --headless --html=prod-peak.html --csv=prod-peak
```
