release: python manage.py migrate --noinput
web: python manage.py migrate --noinput && gunicorn kibray_backend.wsgi:application --config gunicorn.conf.py
worker: celery -A kibray_backend worker --loglevel=info
beat: celery -A kibray_backend beat --loglevel=info
