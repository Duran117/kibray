"""
Django Settings - Staging Environment
Settings for staging/testing deployment (similar to production but with debug tools)
"""
from .production import *

# Allow DEBUG in staging for troubleshooting
DEBUG = os.getenv("DEBUG", "False") == "True"

# Less strict security for staging
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True") == "True"
SECURE_HSTS_SECONDS = 0  # Don't preload HSTS in staging

# Relaxed CORS for testing
CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL_ORIGINS", "False") == "True"

# Logging - More verbose in staging
LOGGING["root"]["level"] = "INFO"
LOGGING["loggers"]["django"]["level"] = "INFO"
LOGGING["loggers"]["core"]["level"] = "DEBUG"

# Sentry - Use staging environment tag
if SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment="staging",
        traces_sample_rate=0.5,  # Sample more transactions in staging
    )

print(f"🧪 Loaded STAGING settings (DEBUG={DEBUG})")
