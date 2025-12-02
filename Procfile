release: python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py create_initial_superuser --noinput
web: gunicorn kibray_backend.wsgi:application --config gunicorn.conf.py
worker: celery -A kibray_backend worker --loglevel=info
beat: celery -A kibray_backend beat --loglevel=info
