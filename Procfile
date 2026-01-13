release: python manage.py migrate --noinput
web: gunicorn kibray_backend.wsgi:application --config gunicorn.conf.py
worker: celery -A kibray_backend worker --loglevel=info --concurrency=2 --max-tasks-per-child=200
beat: celery -A kibray_backend beat --loglevel=info
