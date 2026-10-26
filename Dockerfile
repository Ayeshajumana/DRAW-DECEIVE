# Multi-stage production Dockerfile for DRAW & DECEIVE
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application source
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Run seed words
RUN python manage.py seed_words || true

EXPOSE 8000

# Run migrations, seed words, and start Daphne on dynamic PORT
CMD ["sh", "-c", "python manage.py migrate && python manage.py seed_words && daphne -b 0.0.0.0 -p ${PORT:-8000} config.asgi:application"]
