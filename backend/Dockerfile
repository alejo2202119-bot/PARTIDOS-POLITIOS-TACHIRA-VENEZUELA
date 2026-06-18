# ============================================================================
#  VPID backend image — python:3.11-slim, non-root, exposes 8000
# ============================================================================
FROM python:3.11-slim AS base

# Runtime hardening / sane Python defaults
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System deps: build tools for asyncpg/bcrypt wheels, curl for healthcheck,
# and the minimal libs reportlab/matplotlib need at runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libpq5 \
        libfreetype6 \
        libjpeg62-turbo \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Non-root user; owns the app dir and the mounted storage volume target
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/storage/reports \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Lightweight container healthcheck hitting the API /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Default: API server. The ETL service overrides this with
# `python -m app.etl.scheduler` (see docker-compose.yml).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
