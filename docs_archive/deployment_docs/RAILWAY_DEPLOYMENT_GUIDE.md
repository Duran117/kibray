# 🚂 RAILWAY DEPLOYMENT GUIDE - KIBRAY

**Quick Start**: Get Kibray running on Railway in 15 minutes

---

## 📋 PREREQUISITES

- [x] GitHub account with Kibray repository access
- [x] Railway account (sign up at https://railway.app)
- [x] Git installed locally
- [x] All code committed and pushed to GitHub

---

## 🚀 DEPLOYMENT STEPS

### 1. Create Railway Project (2 min)

1. Go to https://railway.app/dashboard
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose **`Duran117/kibray`**
5. Railway will auto-detect Python and start building

### 2. Add PostgreSQL Database (1 min)

1. In your Railway project, click **"New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway automatically creates `DATABASE_URL` variable
4. Done! ✅

### 3. Add Redis (1 min)

1. Click **"New"** again
2. Select **"Database"** → **"Redis"**
3. Railway automatically creates `REDIS_URL` variable
4. Done! ✅

### 4. Configure Environment Variables (5 min)

Click on your web service → **Variables** tab:

#### Required Variables
```bash
# Django Core
DJANGO_SETTINGS_MODULE=kibray_backend.settings.production
DJANGO_SECRET_KEY=<generate-below>
ALLOWED_HOSTS=*.railway.app

# Database (auto-created by Railway)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis (auto-created by Railway)
REDIS_URL=${{Redis.REDIS_URL}}

# Security
DEBUG=False
```

#### Generate SECRET_KEY
Run locally:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
Copy output and paste as `DJANGO_SECRET_KEY`

#### Optional: Email Configuration
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourcompany.com
```

#### Optional: AWS S3 (for media files)
```bash
USE_S3=True
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=kibray-media
AWS_S3_REGION_NAME=us-east-1
```

#### Optional: Sentry (error monitoring)
```bash
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
```

### 5. Deploy! (5 min)

1. Railway will automatically deploy after adding variables
2. Watch build logs in real-time
3. Deployment typically takes 3-5 minutes

#### Monitor Deployment
- **Build Logs**: Click "Deploy Logs" tab
- **Runtime Logs**: Click "Logs" tab after deployment
- **Health Check**: Railway will ping `/api/v1/health/`

### 6. Run Initial Setup (2 min)

Once deployed, open Railway CLI or use web terminal:

```bash
# Install Railway CLI (if not installed)
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Run migrations
railway run python manage.py migrate

# Create superuser
railway run python manage.py createsuperuser

# Optional: Load initial data
railway run python manage.py loaddata core/fixtures/initial_costcodes.json
```

---

## 🔍 VERIFICATION CHECKLIST

After deployment, verify these endpoints:

```bash
# Replace with your Railway URL
BASE_URL=https://your-app.railway.app

# Health check
curl $BASE_URL/api/v1/health/

# Admin panel
open $BASE_URL/admin/

# API root
open $BASE_URL/api/v1/

# Frontend
open $BASE_URL/
```

Expected responses:
- ✅ Health: `{"status": "healthy"}`
- ✅ Admin: Login page loads
- ✅ API: Browsable API interface
- ✅ Frontend: Dashboard loads (after login)

---

## 🎨 CONFIGURE CUSTOM DOMAIN (Optional)

### 1. Add Domain in Railway
1. Go to **Settings** → **Domains**
2. Click **"Generate Domain"** (free railway.app subdomain)
3. Or **"Custom Domain"** for your own domain

### 2. Update ALLOWED_HOSTS
```bash
# In Railway variables
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,*.railway.app
```

### 3. Configure DNS
Point your domain to Railway:
```
CNAME: yourdomain.com → your-app.railway.app
```

### 4. Enable HTTPS
Railway automatically provides SSL certificates via Let's Encrypt ✅

---

## ⚙️ POST-DEPLOYMENT CONFIGURATION

### Enable Celery Workers (Background Tasks)

1. In Railway project, click **"New"** → **"Empty Service"**
2. Name it **"celery-worker"**
3. Settings → Connect to same GitHub repo
4. Variables → Copy all environment variables from web service
5. Add start command override:
   ```bash
   celery -A kibray_backend worker --loglevel=info
   ```

### Enable Celery Beat (Scheduled Tasks)

1. Create another service: **"celery-beat"**
2. Same repo and variables
3. Start command:
   ```bash
   celery -A kibray_backend beat --loglevel=info
   ```

**Result**: You'll have 3 services:
- ✅ Web (Django/Gunicorn)
- ✅ Worker (Celery background tasks)
- ✅ Beat (Celery scheduler)

---

## 🔧 TROUBLESHOOTING

### Build Fails

**Check**:
1. `railway logs` - View detailed error
2. Verify Python version in `runtime.txt`
3. Check `requirements.txt` for missing packages

**Common Fix**:
```bash
# Ensure build command runs
railway up
```

### App Crashes on Start

**Check**:
1. Environment variables set correctly
2. `DATABASE_URL` exists
3. Migrations ran successfully

**Fix**:
```bash
railway run python manage.py migrate
railway logs  # Check for errors
```

### Static Files Not Loading

**Check**:
1. `STATIC_ROOT` configured
2. WhiteNoise middleware enabled

**Fix**:
```bash
railway run python manage.py collectstatic --noinput
```

### Database Connection Errors

**Check**:
1. PostgreSQL service running
2. `DATABASE_URL` variable set
3. SSL mode configured

**Fix**:
```python
# In production.py
DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600,
        ssl_require=True,  # ← Ensure this is True
    )
}
```

---

## 📊 MONITORING & LOGS

### View Logs
```bash
# All logs
railway logs

# Follow logs (real-time)
railway logs --follow

# Specific service
railway logs --service web
```

### Metrics Dashboard
1. Railway dashboard → Your project
2. Click **"Metrics"** tab
3. View:
   - CPU usage
   - Memory usage
   - Network traffic
   - Request count

### Error Tracking (Sentry)

If configured:
1. Go to https://sentry.io
2. View errors by:
   - Frequency
   - User impact
   - Stack trace
   - Environment

---

## 💰 COST ESTIMATE

Railway Pricing (as of 2025):

### Hobby Plan (Free Trial)
- $5/month credit
- Good for testing

### Developer Plan ($5/month)
- Better for production
- Includes:
  - Web service: ~$5/month
  - PostgreSQL: ~$5/month
  - Redis: ~$3/month
  - Celery worker: ~$5/month (optional)

**Total**: $13-18/month for full stack

### Pro Plan ($20/month)
- Higher resource limits
- Priority support
- Better for scale

---

## 🔒 SECURITY CHECKLIST

Before going live:

- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` set
- [ ] `ALLOWED_HOSTS` configured
- [ ] HTTPS enabled (automatic on Railway)
- [ ] CSRF protection enabled (default)
- [ ] SQL injection protection (Django ORM handles this)
- [ ] XSS protection headers set
- [ ] Secure session cookies enabled
- [ ] Database backups configured
- [ ] Error monitoring (Sentry) set up
- [ ] Rate limiting configured

---

## 🚑 ROLLBACK PROCEDURE

If something goes wrong:

### Quick Rollback
```bash
# View deployments
railway status

# Rollback to previous
railway rollback
```

### Manual Rollback
1. Go to Railway dashboard
2. **Deployments** tab
3. Find last working deployment
4. Click **"Redeploy"**

### Database Rollback
```bash
# List backups
railway pg:backups

# Restore from backup
railway pg:backups:restore <backup-id>
```

---

## 📞 SUPPORT

### Railway Support
- **Docs**: https://docs.railway.app
- **Discord**: https://discord.gg/railway (fastest!)
- **Email**: team@railway.app
- **Status**: https://status.railway.app

### Django Support
- **Docs**: https://docs.djangoproject.com/en/4.2/
- **Forum**: https://forum.djangoproject.com/
- **IRC**: #django on Libera.Chat

---

## ✅ SUCCESS INDICATORS

Your deployment is successful when:

1. ✅ Health check returns `200 OK`
2. ✅ Admin panel loads and you can login
3. ✅ API endpoints respond correctly
4. ✅ Frontend loads without errors
5. ✅ Database queries work
6. ✅ Static files load (CSS, JS)
7. ✅ Background tasks run (if Celery enabled)
8. ✅ No errors in Railway logs

---

## 🎉 POST-DEPLOYMENT

Congratulations! Your app is live. Next steps:

1. **Monitor**: Check logs daily for first week
2. **Test**: Have users test all features
3. **Backup**: Ensure automated backups run
4. **Document**: Update docs with production URL
5. **Scale**: Add more resources if needed

---

## 📚 ADDITIONAL RESOURCES

- **Railway Docs**: https://docs.railway.app/guides/django
- **Django Deployment**: https://docs.djangoproject.com/en/4.2/howto/deployment/
- **Gunicorn Config**: https://docs.gunicorn.org/en/stable/settings.html
- **PostgreSQL on Railway**: https://docs.railway.app/databases/postgresql
- **Redis on Railway**: https://docs.railway.app/databases/redis

---

**Created by**: GitHub Copilot  
**Last Updated**: December 1, 2025  
**Version**: 1.0  
**Status**: Production-Ready ✅
