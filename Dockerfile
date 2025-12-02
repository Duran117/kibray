FROM python:3.11-slim AS base

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

## (Node build removed) If frontend build is needed later, reintroduce Node install.

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

## Frontend build skipped (package.json not present in deployment context). Static assets assumed pre-built.

# Copy project source
COPY . .

# Collect static assets (Django)
RUN python manage.py collectstatic --noinput || true

# Expose gunicorn port (Railway provides $PORT)
ENV PORT=8000

# Run migrations, create superuser, and start gunicorn
CMD ["bash", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py create_initial_superuser --noinput && gunicorn kibray_backend.wsgi:application --workers=3 --threads=2 --timeout=120 --bind 0.0.0.0:${PORT:-8000}"]
