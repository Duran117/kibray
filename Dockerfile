FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
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

# Make start script executable
RUN chmod +x start.sh

# Collect static assets (non-blocking if it fails)
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

# Start using script
CMD ["./start.sh"]
