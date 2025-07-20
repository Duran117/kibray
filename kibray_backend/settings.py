import os
from pathlib import Path
import dj_database_url  # Asegúrate que está en requirements.txt

BASE_DIR = Path(__file__).resolve().parent.parent

# 🔐 ¡IMPORTANTE! Usa variables de entorno para seguridad en producción
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-nvh!d_lkeyq$*bk($53a2!gh&=5i351r6w2w_g052fgld-=w%6')

# 🔁 Detectar entorno: True para desarrollo, False para Render
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'kibray-backend.onrender.com']

# Aplicaciones
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

# Middleware (incluye WhiteNoise para servir archivos estáticos en Render)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # para producción estática
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'kibray_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'core', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'kibray_backend.wsgi.application'

# 🔄 Base de datos (usa PostgreSQL si DATABASE_URL está definida, si no usa SQLite)
DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600,
        ssl_require=not DEBUG  # Solo fuerza SSL en producción
    )
}

# Validación de contraseñas
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Configuración de idioma y zona horaria
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Archivos estáticos
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Archivos subidos por el usuario
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Campo por defecto para claves primarias
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Autenticación
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'
LOGIN_URL = '/login/'


