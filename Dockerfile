# Multi-language build: Python + Node
FROM python:3.11-slim AS base

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Frontend build
COPY frontend/package.json frontend/package-lock.json* ./frontend/
RUN cd frontend && npm ci && npm run build

# Copy project source
COPY . .

# Collect static assets (Django)
RUN python manage.py collectstatic --noinput || true

# Expose gunicorn port (Railway provides $PORT)
ENV PORT=8000

CMD ["bash", "-c", "gunicorn kibray_backend.wsgi:application --workers=3 --threads=2 --timeout=120 --bind 0.0.0.0:${PORT:-8000}"]
