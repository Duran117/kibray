"""
Django Settings - Production Environment
Secure settings for production deployment
"""

import os

import dj_database_url

from .base import *  # noqa: F403

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# HOTFIX: Disable template caching temporarily to force recompile
# This ensures the fixed template syntax is loaded immediately
TEMPLATES[0]["APP_DIRS"] = False  # noqa: F405
TEMPLATES[0]["OPTIONS"]["loaders"] = [  # noqa: F405
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]

# Add startup logging
print("=" * 60)
print("🚀 STARTING KIBRAY IN PRODUCTION MODE")
print("⚠️  TEMPLATE CACHING DISABLED (temporary hotfix)")
print("=" * 60)

# SECRET_KEY must be set in environment variables
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    print("❌ ERROR: DJANGO_SECRET_KEY not set!")
    raise ValueError("DJANGO_SECRET_KEY environment variable must be set in production!")
else:
    print(f"✅ SECRET_KEY loaded: {SECRET_KEY[:10]}...")

# Allowed hosts from environment
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")
if not ALLOWED_HOSTS or ALLOWED_HOSTS == [""]:
    # Fallback: Accept Railway domains and common cloud platforms
    ALLOWED_HOSTS = [
        "*.railway.app",
        "railway.app",
        "*.up.railway.app",
        "kibray.up.railway.app",
        "localhost",
        "127.0.0.1",
    ]
    print("⚠️ WARNING: Using default ALLOWED_HOSTS")
print(f"✅ ALLOWED_HOSTS: {ALLOWED_HOSTS}")

# Database - PostgreSQL via DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL not set!")
    raise ValueError("DATABASE_URL environment variable must be set in production!")
else:
    print("✅ DATABASE_URL configured")

DATABASES = {
    "default": dj_database_url.config(
        conn_max_age=60,  # Reduced from 600 - shorter lived connections save memory
        ssl_require=True,
        conn_health_checks=True,  # Enable health checks
    )
}

print(f"✅ Database configured: {DATABASES['default']['ENGINE']}")

# Static files - WhiteNoise with compression (no manifest for flexibility)
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

# Media files - AWS S3 or local storage with Railway volume
USE_S3 = os.getenv("USE_S3", "False") == "True"  # Default to False for Railway

if USE_S3:
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "us-east-1")
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
    AWS_DEFAULT_ACL = "public-read"
    AWS_QUERYSTRING_AUTH = False
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"
    print("✅ Using AWS S3 for media storage")
else:
    MEDIA_URL = "/media/"
    # Use Railway volume - check if we're on Railway and volume exists
    # Railway automatically mounts volumes at /data by default
    if os.path.exists("/data"):
        MEDIA_ROOT = "/data/media"
        # Create media directory if it doesn't exist
        os.makedirs(MEDIA_ROOT, exist_ok=True)
        # Also create floor_plans subdirectory
        os.makedirs(os.path.join(MEDIA_ROOT, "floor_plans"), exist_ok=True)
        print(f"✅ Using Railway Volume for media: {MEDIA_ROOT}")
        print("✅ Created subdirectories: floor_plans/")
    else:
        MEDIA_ROOT = BASE_DIR / "media"  # noqa: F405
        os.makedirs(MEDIA_ROOT, exist_ok=True)
        os.makedirs(os.path.join(MEDIA_ROOT, "floor_plans"), exist_ok=True)
        print("⚠️ Using local filesystem for media (not persistent!)")
        print(f"⚠️ MEDIA_ROOT: {MEDIA_ROOT}")

# Email - SMTP configuration required
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@kibray.com")

# CORS - Specific origins only
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ALLOWED_ORIGINS if origin.strip()]
CORS_ALLOW_CREDENTIALS = True

# CSRF - Handle both http and https for Railway (health checks use http)
_csrf_origins = os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in _csrf_origins if origin.strip()]

# Add both http and https variants for Railway compatibility
_csrf_with_variants = []
for origin in CSRF_TRUSTED_ORIGINS:
    _csrf_with_variants.append(origin)
    # If origin is https://, also add http:// variant for Railway redirects
    if origin.startswith("https://"):
        _csrf_with_variants.append(origin.replace("https://", "http://"))
    # If origin is http://, also add https:// variant
    elif origin.startswith("http://"):
        _csrf_with_variants.append(origin.replace("http://", "https://"))

CSRF_TRUSTED_ORIGINS = list(set(_csrf_with_variants))  # Remove duplicates

# Security Settings
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# SSL Redirect
# Previously hard-coded to True which caused 301 redirects on platform health probes (e.g. Railway),
# preventing a direct 200 response for /api/v1/health/ and keeping the service in an unhealthy state.
# Now configurable via env var SECURE_SSL_REDIRECT (default False to allow initial health verification).
# Once deployment is stable, set SECURE_SSL_REDIRECT=True again to enforce HTTPS.
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "False") == "True"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Channel Layers - Redis with connection pooling
REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise ValueError("REDIS_URL environment variable must be set in production!")

# Ensure REDIS_URL has a database number for proper separation
# If URL doesn't end with /N, append /0 as default
if not REDIS_URL.rstrip('/').split('/')[-1].isdigit():
    REDIS_URL = REDIS_URL.rstrip('/') + '/0'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
            "capacity": 500,  # Reduced from 1500
            "expiry": 10,
            "symmetric_encryption_keys": [SECRET_KEY],
            "connection_kwargs": {
                "max_connections": 10,  # Reduced from 50
                "retry_on_timeout": True,
            },
            "group_expiry": 86400,
            "channel_capacity": {
                "chat.*": 500,  # Reduced from 2000
                "notifications.*": 200,  # Reduced from 500
            },
        },
    },
}

# Cache - Use local memory cache (Redis was causing timeouts and crashes)
# When Redis is stable again, can switch back to django_redis
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "kibray-cache",
        "TIMEOUT": 300,
        "OPTIONS": {
            "MAX_ENTRIES": 1000,
        },
    }
}

# ============================================
# CELERY CONFIGURATION FOR BACKGROUND TASKS
# ============================================
# Note: Celery requires Redis. If Redis is unavailable, tasks will run synchronously.
CELERY_BROKER_URL = REDIS_URL.replace("/0", "/2")  # Use database 2 for Celery broker
CELERY_RESULT_BACKEND = REDIS_URL.replace("/0", "/3")  # Use database 3 for results
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE  # noqa: F405
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes max per task
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Conservative for memory
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_RETRY = True  # Retry connecting to broker
CELERY_BROKER_CONNECTION_MAX_RETRIES = 3  # Reduced retries
CELERY_BROKER_CONNECTION_TIMEOUT = 5  # Reduced timeout
CELERY_REDIS_SOCKET_TIMEOUT = 5  # Socket timeout
CELERY_REDIS_SOCKET_CONNECT_TIMEOUT = 5  # Connect timeout
# Run tasks synchronously if broker unavailable (fallback mode)
CELERY_TASK_ALWAYS_EAGER = os.getenv("CELERY_TASK_ALWAYS_EAGER", "False") == "True"
print("✅ Celery configured with Redis broker")

# Logging - Structured logging for production
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "core": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# DRF Spectacular - Production server URL
SPECTACULAR_SETTINGS["SERVERS"] = [  # noqa: F405
    {
        "url": os.getenv("API_BASE_URL", "https://api.kibray.com"),
        "description": "Production server",
    },
]

# Sentry Integration (if configured)
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            RedisIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
        send_default_pii=False,  # Don't send personally identifiable information
        environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
    )

# WebSocket - Strict validation in production
WEBSOCKET_ACCEPT_ALL = False

print(f"🔒 Loaded PRODUCTION settings (DEBUG={DEBUG})")
