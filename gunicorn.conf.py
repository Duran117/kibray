"""
Gunicorn configuration file for Kibray production deployment
"""
import multiprocessing
import os

# Server Socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker Processes
workers = int(os.getenv("WEB_CONCURRENCY", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"  # Use 'gthread' for threading support
threads = 2  # Threads per worker (only if worker_class='gthread')
worker_connections = 1000
max_requests = 1000  # Restart workers after this many requests (prevents memory leaks)
max_requests_jitter = 50  # Randomize max_requests to avoid all workers restarting simultaneously
timeout = 30  # Workers silent for more than this many seconds are killed and restarted
graceful_timeout = 30  # Timeout for graceful workers restart
keepalive = 2  # The number of seconds to wait for requests on a Keep-Alive connection

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
    """Called just before the master process is initialized."""
    import subprocess
    import sys
    
    print("🔄 Running database migrations...")
    try:
        subprocess.check_call([sys.executable, "manage.py", "migrate", "--noinput"])
        print("✅ Migrations complete")
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
    
    print("📦 Collecting static files...")
    try:
        subprocess.check_call([sys.executable, "manage.py", "collectstatic", "--noinput"])
        print("✅ Static files collected")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Static collection failed (non-fatal): {e}")
    
    print("👤 Creating initial superuser...")
    try:
        subprocess.check_call([sys.executable, "manage.py", "create_initial_superuser", "--noinput"])
        print("✅ Superuser setup complete")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Superuser creation failed (non-fatal): {e}")
    
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
