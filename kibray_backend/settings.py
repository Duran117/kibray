# Celery: run tasks eagerly during tests to avoid broker requirement
import os as _os

if _os.getenv("PYTEST_CURRENT_TEST") or _os.getenv("RUN_TESTS") == "1":
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

# 🔐 Seguridad: usar variable en producción
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-secret-key-change-me"  # solo para DEV
    else:
        raise Exception("DJANGO_SECRET_KEY environment variable not set!")

# 🔁 Modo debug (False en producción)
DEBUG = os.getenv("DEBUG", "False") == "False"

# 🌍 Hosts permitidos
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "kibray-backend.onrender.com", "testserver"]

# 📦 Aplicaciones instaladas
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    "django_filters",
    "storages",
    "core",
    "signatures",
    "reports",
]

# ⚙️ Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# 🔗 URLs
ROOT_URLCONF = "kibray_backend.urls"

# 🧱 Plantillas
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "core" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.company",
                "core.context_processors.notification_badges",
            ],
        },
    },
]

# 🔥 WSGI
WSGI_APPLICATION = "kibray_backend.wsgi.application"

# 🛢 Base de datos: PostgreSQL en producción, SQLite local
DATABASES = {
    "default": dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}', conn_max_age=600, ssl_require=not DEBUG
    )
}

# 🔐 Validación de contraseñas
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# 🌐 Internacionalización
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Denver"
USE_I18N = True
USE_TZ = True

# Django 6.0 URLField default scheme change – opt-in now to silence warning
FORMS_URLFIELD_ASSUME_HTTPS = True

# Idiomas soportados
LANGUAGES = [
    ("en", "English"),
    ("es", "Español"),
]

# Ruta para los archivos de traducción (si más adelante agregas .po/.mo)
LOCALE_PATHS = [BASE_DIR / "locale"]

# 📁 Archivos estáticos
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "core", "static"),
    os.path.join(BASE_DIR, "static"),  # Navigation and Gantt builds
    os.path.join(BASE_DIR, "staticfiles"),  # For Vite built assets
]
STATIC_ROOT = os.path.join(BASE_DIR, "static_collected")
if DEBUG:
    # Simpler storage in development/test to avoid manifest hash lookups
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
else:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# 📁 Media: S3 en producción, local en desarrollo
USE_S3 = os.getenv("USE_S3", "False") == "True"

if USE_S3:
    # AWS S3 settings
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
else:
    # Local filesystem
    MEDIA_URL = "/media/"
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Custom settings
# Feature flags
# Disable legacy TouchUpPin UI by default; consolidate touch-ups via Task(is_touchup=True)
TOUCHUP_PIN_ENABLED = False
# 🔑 ID por defecto
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# 🔐 Redirección login/logout
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/login/"
LOGIN_URL = "/login/"

# 🛡 Seguridad en producción
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = "DENY"

# 🔐 Django REST Framework + JWT
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S.%fZ",
    "DATE_FORMAT": "%Y-%m-%d",
    "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}

# 🌐 CORS para app móvil y frontend
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
CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
]
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# 📧 Email para digest y notificaciones (configurar en producción)
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@kibray.com")

# ============================================================================
# Module 21: Business Intelligence Configuration
# ============================================================================

# Alert Thresholds for BI Dashboard
BI_LOW_MARGIN_THRESHOLD = float(os.getenv("BI_LOW_MARGIN_THRESHOLD", "15.0"))  # Projects below 15% margin flagged as red
BI_HIGH_MARGIN_THRESHOLD = float(os.getenv("BI_HIGH_MARGIN_THRESHOLD", "30.0"))  # Projects above 30% considered high performers
BI_CACHE_TTL = int(os.getenv("BI_CACHE_TTL", "300"))  # Cache timeout in seconds (default: 5 minutes)
BI_CASH_FLOW_DAYS = int(os.getenv("BI_CASH_FLOW_DAYS", "30"))  # Default projection horizon
BI_TOP_PERFORMERS_LIMIT = int(os.getenv("BI_TOP_PERFORMERS_LIMIT", "5"))  # Number of top employees to show

# ============================================================================
# DRF Spectacular - OpenAPI 3 Documentation
# ============================================================================

SPECTACULAR_SETTINGS = {
    "TITLE": "Kibray Construction Management API",
    "DESCRIPTION": "Comprehensive REST API for construction project management including projects, tasks, change orders, files, users, analytics and real-time features",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "/api/v1/",
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_OPERATIONS": True,
    "SERVERS": [
        {"url": "http://localhost:8000", "description": "Development server"},
    ],
}
