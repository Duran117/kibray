#!/bin/bash
set -e

echo "🔄 Starting Kibray Celery Worker..."

# Run migrations (in case worker starts before web)
echo "📦 Running database migrations..."
python manage.py migrate --noinput
echo "✅ Migrations complete"

# Start Celery worker
echo "🚀 Starting Celery worker..."
exec celery -A kibray_backend worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=200 \
    --without-heartbeat \
    --without-mingle \
    --without-gossip
