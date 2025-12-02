web: bash entrypoint.sh
worker: celery -A kibray_backend worker --loglevel=info
beat: celery -A kibray_backend beat --loglevel=info
