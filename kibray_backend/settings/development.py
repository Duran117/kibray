"""
Django Settings - Development Environment
Settings for local development
"""
import os
import sys
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver", "*"]

# Database - SQLite for development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Static files - Simple storage for development
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Media files - Local filesystem
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Email - Console backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@kibray.local"

# CORS - Allow all origins in development
CORS_ALLOWED_ORIGINS = [
    "capacitor://localhost",
    "ionic://localhost",
    "http://localhost",
    "http://localhost:8100",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # Set to True if needed

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Channel Layers / Cache
USE_IN_MEMORY_LAYERS = (
    os.getenv("PYTEST_CURRENT_TEST")
    or os.getenv("USE_IN_MEMORY_CHANNEL_LAYER") == "1"
    or any("pytest" in arg for arg in sys.argv)
)

if USE_IN_MEMORY_LAYERS:
    CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
    }
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-kibray-test-cache",
            "TIMEOUT": None,
        }
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [os.getenv("REDIS_URL", "redis://localhost:6379/0")],
                "capacity": 1500,
                "expiry": 10,
            },
        },
    }

    # Cache - Redis
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": os.getenv("REDIS_URL", "redis://localhost:6379/1"),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "IGNORE_EXCEPTIONS": True,
            },
            "KEY_PREFIX": "kibray_dev",
            "TIMEOUT": 300,
        }
    }

# Logging - Verbose in development
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "core": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# DRF Spectacular - Include localhost server
SPECTACULAR_SETTINGS["SERVERS"] = [
    {"url": "http://localhost:8000", "description": "Development server"},
]

# Security - Relaxed for development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "SAMEORIGIN"

# WebSocket - Accept all in dev
WEBSOCKET_ACCEPT_ALL = True

print(f"🚀 Loaded DEVELOPMENT settings (DEBUG={DEBUG})")
