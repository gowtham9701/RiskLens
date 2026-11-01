FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for psycopg/reportlab
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Install the analytics engine first (separate layer for caching)
COPY analytics /app/analytics
RUN pip install --no-cache-dir -e /app/analytics

# Backend deps
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# App code + sample data
COPY backend /app/backend
COPY data /app/data

EXPOSE 8000

# Seed on first boot (idempotent) then serve. Override in compose if desired.
CMD ["sh", "-c", "python -m backend.app.seed || true; uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]
