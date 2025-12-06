#!/bin/bash
set -e

echo "🔄 Starting Kibray application..."

# Run migrations
echo "📦 Running database migrations..."
python manage.py migrate --noinput

echo "✅ Migrations complete"

# Start Gunicorn
echo "🚀 Starting Gunicorn on port ${PORT:-8000}..."
exec gunicorn kibray_backend.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 3 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --worker-class sync
