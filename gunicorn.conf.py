"""
Gunicorn configuration file for Kibray production deployment
Optimized for Railway's memory constraints
"""

import os

# Server Socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 512  # Reduced for memory savings

# Worker Processes - OPTIMIZED FOR RAILWAY
# Railway free tier has ~512MB RAM, Pro has ~8GB
# Each Django worker can use 150-300MB
# Use WEB_CONCURRENCY env var for control, default to 2 workers
workers = int(os.getenv("WEB_CONCURRENCY", 2))  # Fixed 2 workers by default
worker_class = "sync"  # Sync is more memory efficient than gevent/eventlet
threads = 1  # Reduce threads per worker
worker_connections = 100  # Reduced from 1000
max_requests = 500  # More aggressive restart to prevent memory leaks
max_requests_jitter = 50  # Randomize to avoid simultaneous restarts
timeout = 30  # Workers silent for more than this many seconds are killed
graceful_timeout = 30
keepalive = 2

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Logging
accesslog = os.getenv("GUNICORN_ACCESS_LOG", "-")  # '-' means stdout
errorlog = os.getenv("GUNICORN_ERROR_LOG", "-")  # '-' means stderr
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")  # debug, info, warning, error, critical
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process Naming
proc_name = "kibray"

# Server Mechanics
daemon = False  # Don't daemonize (required for Docker/Railway/Render)
pidfile = None  # Don't create a PID file
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Preload app to save RAM resources
preload_app = True


# Hooks
def on_starting(server):
    """Called just before the master process is initialized.
    NOTE: Migrations, collectstatic, and superuser creation are handled by start.sh
    before gunicorn starts. No need to duplicate them here.
    """
    print("🚀 Gunicorn master starting")


def when_ready(server):
    """Called just after the server is started."""
    print(f"✅ Gunicorn ready - {workers} workers on {bind}")


def on_exit(server):
    """Called just before exiting Gunicorn."""
    print("👋 Gunicorn shutting down")


def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    print(f"⚠️  Worker {worker.pid} interrupted")


def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    print(f"🔧 Worker {worker.pid} spawned")


def pre_exec(server):
    """Called just before a new master process is forked."""
    print("🔄 Gunicorn restarting")


def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    print(f"❌ Worker {worker.pid} aborted")
