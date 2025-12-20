"""
Django Settings Package
Auto-loads the correct settings module based on DJANGO_SETTINGS_MODULE environment variable
"""
import os

# Default to development settings
ENVIRONMENT = os.getenv("DJANGO_ENV", "development")

if ENVIRONMENT == "production":
    from .production import *  # noqa: F403
elif ENVIRONMENT == "staging":
    from .staging import *  # noqa: F403
else:
    from .development import *  # noqa: F403
