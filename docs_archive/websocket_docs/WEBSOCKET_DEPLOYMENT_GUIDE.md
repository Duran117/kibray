# WebSocket System - Production Deployment Guide

**Phase 6 - Real-time Communication System**

Complete guide for deploying the Kibray WebSocket system to production.

## 🎯 Overview

This guide covers deploying a production-ready WebSocket system with:
- High availability
- Auto-scaling
- Monitoring and alerting
- Security best practices
- Performance optimization

## 📋 Prerequisites

### Infrastructure
- [ ] Linux server (Ubuntu 20.04+ or similar)
- [ ] 4+ GB RAM (8 GB recommended)
- [ ] 2+ CPU cores (4 cores recommended)
- [ ] 50+ GB disk space
- [ ] PostgreSQL 13+
- [ ] Redis 6.0+
- [ ] Domain name with SSL certificate

### Software
- [ ] Python 3.9+
- [ ] Node.js 16+ (for frontend)
- [ ] Nginx or similar reverse proxy
- [ ] Supervisor or systemd (process management)

### Accounts & Services
- [ ] Domain registrar access
- [ ] SSL certificate (Let's Encrypt or commercial)
- [ ] Firebase account (for push notifications)
- [ ] Email service (for notifications)
- [ ] Monitoring service (optional: DataDog, New Relic)

---

## 🚀 Deployment Steps

### Step 1: Server Setup

#### Update System

```bash
sudo apt update && sudo apt upgrade -y
```

#### Install Dependencies

```bash
# Python and build tools
sudo apt install -y python3.11 python3.11-venv python3-pip
sudo apt install -y build-essential libpq-dev python3-dev

# Redis
sudo apt install -y redis-server

# PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Nginx
sudo apt install -y nginx

# Process manager
sudo apt install -y supervisor
```

### Step 2: PostgreSQL Setup

```bash
# Create database and user
sudo -u postgres psql <<EOF
CREATE DATABASE kibray;
CREATE USER kibray_user WITH PASSWORD 'secure_password_here';
ALTER ROLE kibray_user SET client_encoding TO 'utf8';
ALTER ROLE kibray_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE kibray_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE kibray TO kibray_user;
EOF
```

#### Configure PostgreSQL

```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/13/main/postgresql.conf
```

Add/modify:
```
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
```

```bash
# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Step 3: Redis Setup

```bash
# Edit redis.conf
sudo nano /etc/redis/redis.conf
```

Configure:
```
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

```bash
# Enable and start Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### Step 4: Application Setup

#### Create Application User

```bash
sudo useradd -m -s /bin/bash kibray
sudo usermod -aG sudo kibray
```

#### Clone Repository

```bash
sudo -u kibray bash
cd /home/kibray
git clone https://github.com/your-org/kibray.git
cd kibray
```

#### Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
```

#### Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Environment Configuration

```bash
# Create .env file
nano .env
```

Add:
```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database
DATABASE_URL=postgresql://kibray_user:secure_password_here@localhost:5432/kibray

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# WebSocket
WEBSOCKET_RATE_LIMIT=60
WEBSOCKET_MESSAGE_MAX_SIZE=1048576

# Firebase (Push Notifications)
FCM_SERVER_KEY=your-fcm-server-key
FCM_VAPID_KEY=your-vapid-key

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Security
CSRF_TRUSTED_ORIGINS=https://your-domain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

#### Migrate Database

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

#### Create Superuser

```bash
python manage.py createsuperuser
```

### Step 5: Daphne (WebSocket Server) Setup

#### Create Systemd Service

```bash
sudo nano /etc/systemd/system/daphne.service
```

Add:
```ini
[Unit]
Description=Daphne WebSocket Server
After=network.target

[Service]
Type=simple
User=kibray
Group=kibray
WorkingDirectory=/home/kibray/kibray
Environment="PATH=/home/kibray/kibray/venv/bin"
ExecStart=/home/kibray/kibray/venv/bin/daphne \
    -b 127.0.0.1 \
    -p 8001 \
    --proxy-headers \
    kibray_backend.asgi:application

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable daphne
sudo systemctl start daphne
sudo systemctl status daphne
```

### Step 6: Gunicorn (HTTP Server) Setup

#### Create Systemd Service

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Add:
```ini
[Unit]
Description=Gunicorn HTTP Server
After=network.target

[Service]
Type=notify
User=kibray
Group=kibray
WorkingDirectory=/home/kibray/kibray
Environment="PATH=/home/kibray/kibray/venv/bin"
ExecStart=/home/kibray/kibray/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --timeout 60 \
    --access-logfile /var/log/gunicorn/access.log \
    --error-logfile /var/log/gunicorn/error.log \
    kibray_backend.wsgi:application

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# Create log directory
sudo mkdir -p /var/log/gunicorn
sudo chown kibray:kibray /var/log/gunicorn

# Enable and start service
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
sudo systemctl status gunicorn
```

### Step 7: Celery Setup

#### Create Worker Service

```bash
sudo nano /etc/systemd/system/celery.service
```

Add:
```ini
[Unit]
Description=Celery Worker
After=network.target

[Service]
Type=forking
User=kibray
Group=kibray
WorkingDirectory=/home/kibray/kibray
Environment="PATH=/home/kibray/kibray/venv/bin"
ExecStart=/home/kibray/kibray/venv/bin/celery -A kibray_backend worker \
    --loglevel=info \
    --concurrency=4 \
    --logfile=/var/log/celery/worker.log

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

#### Create Beat Service

```bash
sudo nano /etc/systemd/system/celerybeat.service
```

Add:
```ini
[Unit]
Description=Celery Beat Scheduler
After=network.target

[Service]
Type=simple
User=kibray
Group=kibray
WorkingDirectory=/home/kibray/kibray
Environment="PATH=/home/kibray/kibray/venv/bin"
ExecStart=/home/kibray/kibray/venv/bin/celery -A kibray_backend beat \
    --loglevel=info \
    --logfile=/var/log/celery/beat.log

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# Create log directory
sudo mkdir -p /var/log/celery
sudo chown kibray:kibray /var/log/celery

# Enable and start services
sudo systemctl enable celery celerybeat
sudo systemctl start celery celerybeat
sudo systemctl status celery celerybeat
```

### Step 8: Nginx Setup

#### SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

#### Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/kibray
```

Add:
```nginx
# Upstream servers
upstream gunicorn {
    server 127.0.0.1:8000;
}

upstream daphne {
    server 127.0.0.1:8001;
}

# HTTP -> HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$host$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Client max body size (for file uploads)
    client_max_body_size 100M;

    # Static files
    location /static/ {
        alias /home/kibray/kibray/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /home/kibray/kibray/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # WebSocket connections
    location /ws/ {
        proxy_pass http://daphne;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Long timeout for WebSocket
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    # API and main application
    location / {
        proxy_pass http://gunicorn;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/kibray /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

### Step 9: Frontend Build

```bash
cd /home/kibray/kibray/frontend/navigation
npm install
npm run build

# Copy build to static location
cp -r dist/* /home/kibray/kibray/staticfiles/
```

### Step 10: Monitoring Setup

#### Install Prometheus Node Exporter

```bash
wget https://github.com/prometheus/node_exporter/releases/download/v1.6.0/node_exporter-1.6.0.linux-amd64.tar.gz
tar xvfz node_exporter-1.6.0.linux-amd64.tar.gz
sudo mv node_exporter-1.6.0.linux-amd64/node_exporter /usr/local/bin/
rm -rf node_exporter-1.6.0.linux-amd64*
```

Create service:
```bash
sudo nano /etc/systemd/system/node_exporter.service
```

Add:
```ini
[Unit]
Description=Node Exporter
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable node_exporter
sudo systemctl start node_exporter
```

#### Configure Application Logging

```bash
sudo nano /home/kibray/kibray/kibray_backend/settings.py
```

Add logging configuration:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/kibray/django.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'websocket_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/kibray/websocket.log',
            'maxBytes': 10485760,
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'channels': {
            'handlers': ['websocket_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'daphne': {
            'handlers': ['websocket_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

```bash
# Create log directory
sudo mkdir -p /var/log/kibray
sudo chown kibray:kibray /var/log/kibray
```

### Step 11: Backups

#### Database Backup Script

```bash
sudo nano /usr/local/bin/backup-kibray-db.sh
```

Add:
```bash
#!/bin/bash
BACKUP_DIR="/home/kibray/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/kibray_db_$DATE.sql.gz"

mkdir -p $BACKUP_DIR

# Backup database
sudo -u postgres pg_dump kibray | gzip > $BACKUP_FILE

# Keep only last 30 days
find $BACKUP_DIR -name "kibray_db_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

```bash
sudo chmod +x /usr/local/bin/backup-kibray-db.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
```

Add:
```
0 2 * * * /usr/local/bin/backup-kibray-db.sh >> /var/log/kibray-backup.log 2>&1
```

---

## 🔒 Security Hardening

### Firewall Setup

```bash
# UFW firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### SSH Hardening

```bash
sudo nano /etc/ssh/sshd_config
```

Configure:
```
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
Port 2222  # Change default port
```

```bash
sudo systemctl restart sshd
```

### Fail2ban

```bash
sudo apt install -y fail2ban

# Configure
sudo nano /etc/fail2ban/jail.local
```

Add:
```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = 2222
```

```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## 📊 Monitoring & Alerts

### Health Check Endpoint

Add to Django:
```python
# urls.py
path('health/', lambda request: JsonResponse({'status': 'ok'})),
```

### Uptime Monitoring

Use services like:
- UptimeRobot
- Pingdom
- StatusCake

Configure to check:
- https://your-domain.com/health/
- Alert if down > 2 minutes

### Log Monitoring

```bash
# Install logwatch
sudo apt install -y logwatch

# Configure daily emails
sudo nano /etc/cron.daily/00logwatch
```

---

## 🚀 Scaling

### Horizontal Scaling

#### Multiple Daphne Instances

```nginx
# Nginx load balancing
upstream daphne {
    least_conn;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}
```

#### Redis Sentinel

For high availability:
```bash
# Setup Redis Sentinel for automatic failover
```

### Vertical Scaling

Increase resources:
- RAM: 16 GB+
- CPU: 8+ cores
- Storage: SSD recommended

---

## ✅ Post-Deployment Checklist

- [ ] All services running (Daphne, Gunicorn, Celery, Redis, PostgreSQL)
- [ ] SSL certificate installed and auto-renewal configured
- [ ] Firewall configured
- [ ] Backups scheduled and tested
- [ ] Monitoring configured
- [ ] Logs rotating properly
- [ ] WebSocket connections working
- [ ] Push notifications working
- [ ] Load testing completed
- [ ] Security scan completed
- [ ] Documentation updated
- [ ] Team trained on operations

---

## 🆘 Troubleshooting

### Service Not Starting

```bash
# Check logs
sudo journalctl -u daphne -n 50
sudo journalctl -u gunicorn -n 50
sudo journalctl -u celery -n 50

# Check status
sudo systemctl status daphne
sudo systemctl status gunicorn
sudo systemctl status celery
```

### WebSocket Not Connecting

1. Check Daphne is running
2. Verify Nginx WebSocket proxy configuration
3. Check firewall allows port 443
4. Test with: `wscat -c wss://your-domain.com/ws/test/`
5. Check browser console for errors

### High CPU Usage

```bash
# Check process usage
top

# Check connection count
redis-cli INFO clients

# Check WebSocket metrics
curl https://your-domain.com/api/websocket/metrics/ \
  -H "Authorization: Bearer TOKEN"
```

### Database Issues

```bash
# Check connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"

# Check slow queries
sudo -u postgres psql -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

---

## 📚 Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/)
- [Daphne Documentation](https://github.com/django/daphne)
- [Nginx WebSocket Proxying](https://nginx.org/en/docs/http/websocket.html)
- [Let's Encrypt](https://letsencrypt.org/)

---

**Production Deployment Complete** ✅

Your WebSocket system is now running in production with:
- High availability
- SSL/TLS encryption
- Automatic backups
- Monitoring and logging
- Security hardening
- Scalability options
