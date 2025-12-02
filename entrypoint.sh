#!/bin/bash
set -e

echo "🔄 Running database migrations..."
python manage.py migrate --noinput

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

echo "👤 Creating initial superuser..."
python manage.py create_initial_superuser --noinput

echo "🚀 Starting Gunicorn web server..."
exec gunicorn kibray_backend.wsgi:application --config gunicorn.conf.py
