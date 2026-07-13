FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Seed the database on build if it doesn't already exist.
# (For a persistent DB, mount a volume and run `python seed.py` once instead.)
RUN python seed.py || true

EXPOSE 8000

# $PORT is provided by most hosts (Render, Railway…); default to 8000 locally.
CMD gunicorn wsgi:app --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 60
