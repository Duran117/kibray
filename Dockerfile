FROM python:3.11-slim

# System dependencies (including cairo dev headers for pycairo compilation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libpq-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-dev \
    libffi-dev \
    shared-mime-info \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY . .

# Make start scripts executable
RUN chmod +x start.sh start_worker.sh

# Collect static assets at build time
# Use a dummy secret key and skip DB-dependent settings for collectstatic
RUN DJANGO_SECRET_KEY=build-placeholder \
    DATABASE_URL=sqlite:///tmp/dummy.db \
    REDIS_URL=redis://localhost:6379/0 \
    DJANGO_ENV=production \
    python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000

# Start using script
CMD ["./start.sh"]
