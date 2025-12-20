"""
Django Settings - Staging Environment
Settings for staging/testing deployment (similar to production but with debug tools)
"""

import os

from .production import *  # noqa: F403

# Allow DEBUG in staging for troubleshooting
DEBUG = os.getenv("DEBUG", "False") == "True"  # noqa: F405

# Less strict security for staging
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True") == "True"  # noqa: F405
SECURE_HSTS_SECONDS = 0  # Don't preload HSTS in staging

# Relaxed CORS for testing
CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL_ORIGINS", "False") == "True"  # noqa: F405

# Logging - More verbose in staging
LOGGING["root"]["level"] = "INFO"  # noqa: F405
LOGGING["loggers"]["django"]["level"] = "INFO"  # noqa: F405
LOGGING["loggers"]["core"]["level"] = "DEBUG"  # noqa: F405

# Sentry - Use staging environment tag
if SENTRY_DSN:  # noqa: F405
    import sentry_sdk
    sentry_sdk.init(
    dsn=SENTRY_DSN,  # noqa: F405
        environment="staging",
        traces_sample_rate=0.5,  # Sample more transactions in staging
    )

print(f"🧪 Loaded STAGING settings (DEBUG={DEBUG})")
