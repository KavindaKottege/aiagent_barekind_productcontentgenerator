# ==============================================================================
# Multi-stage Docker image for Python backend (API + Worker)
#
# Single image, dual entrypoint pattern:
#   API:    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
#   Worker: arq app.workers.worker_settings.WorkerSettings
#
# Build from repo root:
#   docker build -f backend/Dockerfile -t cg-backend .
#
# No CMD is set -- docker-compose provides the command for each service.
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Builder -- install Python dependencies in a virtual environment
# ------------------------------------------------------------------------------
FROM python:3.13-slim-bookworm AS builder

# Install build dependencies for C extensions (asyncpg, pandas, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Install Python dependencies (cached unless requirements.txt changes)
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# ------------------------------------------------------------------------------
# Stage 2: Runtime -- lean image with only what's needed to run
# ------------------------------------------------------------------------------
FROM python:3.13-slim-bookworm AS runtime

# Install only runtime system dependencies
#   libpq5: PostgreSQL client library (required by asyncpg)
#   curl:   Used for container health checks
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage (owned by appuser)
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code (owned by appuser)
COPY --chown=appuser:appuser backend/app /app/app

# Copy Alembic migrations and config (owned by appuser)
COPY --chown=appuser:appuser backend/alembic /app/alembic
COPY --chown=appuser:appuser backend/alembic.ini /app/alembic.ini

# Create uploads directory for file processing (owned by appuser)
RUN mkdir -p /app/uploads && chown appuser:appuser /app/uploads

# Switch to non-root user
USER appuser

# Document the port (informational only, does not publish)
EXPOSE 8000

# No CMD -- docker-compose provides the command:
#   API:    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
#   Worker: arq app.workers.worker_settings.WorkerSettings
