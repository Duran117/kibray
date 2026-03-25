#!/bin/bash
set -e

echo "🔄 Starting Kibray application..."

# Run migrations
echo "📦 Running database migrations..."
python manage.py migrate --noinput

echo "✅ Migrations complete"

# NOTE: collectstatic is already run during Docker build (Dockerfile).
# Skipping here to speed up container startup and pass healthcheck faster.

# Create initial superuser if needed
echo "👤 Creating initial superuser..."
python manage.py create_initial_superuser --noinput 2>/dev/null || true

# Start Gunicorn using config file (gunicorn.conf.py)
echo "🚀 Starting Gunicorn on port ${PORT:-8000}..."
exec gunicorn kibray_backend.wsgi:application --config gunicorn.conf.py
