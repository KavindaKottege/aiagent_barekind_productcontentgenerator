# Phase 9: Platform Brief & Containerization - Research

**Researched:** 2026-01-30
**Domain:** Docker containerization, Docker Compose orchestration, CI/CD image publishing, health checks, platform infrastructure documentation
**Confidence:** HIGH

## Summary

Phase 9 produces two deliverables: (1) production-ready Docker containers for the Python backend services (FastAPI API + ARQ worker + Redis) and (2) a standalone platform brief document that tells another Claude Code GSD instance exactly what to provision.

The standard approach is a single multi-stage Dockerfile using `python:3.13-slim-bookworm` that produces one image serving dual roles (API server via `uvicorn` and ARQ worker via `arq` CLI) controlled by the entrypoint command. Redis uses the official `redis:7-alpine` image. A single `docker-compose.yml` with profiles separates dev and prod configurations. Services communicate on an internal-only Docker network (`internal: true`). GitHub Actions builds and pushes the image to `ghcr.io` on every push to `main`.

The existing codebase already has a basic health check endpoint (`GET /api/health`) and a dev-only `docker-compose.yml` with PostgreSQL, Redis, and pgAdmin. ARQ already has a built-in Redis health key with a CLI check command (`arq --check`). The phase transforms these into production-grade configurations.

**Primary recommendation:** Build a single Python Docker image with multi-stage build (builder + runtime), use Docker Compose profiles to separate dev/prod in one file, implement both liveness and readiness health checks for FastAPI, use ARQ's built-in `--check` CLI for worker health, and push images to `ghcr.io` via GitHub Actions with GHA layer caching.

## Standard Stack

### Core

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| Docker (multi-stage build) | Buildkit | Single image for API + worker | Standard pattern for web+worker apps (Django+Celery, Rails+Sidekiq) |
| `python:3.13-slim-bookworm` | 3.13 | Base image for Python services | Slim variant is ~130MB vs ~1GB full; bookworm pins Debian release for reproducibility; project uses Python 3.13 |
| `redis:7-alpine` | 7.x | Redis for ARQ job queue | Official image, Alpine variant (~5MB base), already used in dev compose |
| Docker Compose | V2 (no version key) | Service orchestration | Single file with profiles for dev/prod; `version` key is obsolete in Compose V2 |
| GitHub Actions | N/A | CI/CD pipeline | Builds image on push to main, pushes to ghcr.io |
| `docker/build-push-action` | v6 | GitHub Actions Docker build | Official Docker action for building and pushing images |
| `docker/metadata-action` | v5 | Image tagging | Automatic tag generation from Git metadata |
| `docker/login-action` | v3 | Registry auth | Authenticates to ghcr.io using GITHUB_TOKEN |

### Supporting

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| `docker/setup-buildx-action` | v3 | Docker Buildx setup | Required for multi-stage builds and caching in CI |
| `actions/checkout` | v5 | Repository checkout | First step in every CI workflow |
| uvicorn | >= 0.30.0 | ASGI server | Already a project dependency; runs FastAPI in production |
| arq CLI | >= 0.26.0 | Worker runner + health check | Already a project dependency; `arq --check` provides Docker HEALTHCHECK |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `python:3.13-slim-bookworm` | `python:3.13-alpine` | Alpine is smaller but musl libc can break wheels (pandas, asyncpg compilation); slim is safer for this project's dependency set |
| GHA cache (`type=gha`) | Registry cache (`type=registry`) | Registry cache has no 10GB limit but needs separate cache image; GHA is simpler for this project's modest image size |
| Hand-rolled health checks | `fastapi-healthchecks` library | Library is inactive (no releases in 12 months); simple hand-rolled endpoints are sufficient and have zero maintenance burden |
| Gunicorn + uvicorn workers | uvicorn standalone with `--workers` | Gunicorn adds complexity; uvicorn `--workers` is sufficient since this is a single-tenant internal API |

## Architecture Patterns

### Recommended Project Structure

```
backend/
  Dockerfile                  # Multi-stage: builder + runtime
  .dockerignore               # Exclude venv, __pycache__, .env, tests, uploads
  app/
    main.py                   # FastAPI app (already exists)
    workers/
      worker_settings.py      # ARQ WorkerSettings (already exists)

docker-compose.yml            # Single file, profiles for dev/prod (replaces existing)

.github/
  workflows/
    docker-publish.yml        # CI pipeline: build + push to ghcr.io

# Delivered separately (not in repo):
PLATFORM-BRIEF.md             # Handoff document for platform GSD
```

### Pattern 1: Single Image, Dual Entrypoint

**What:** One Docker image runs as either FastAPI API or ARQ worker depending on the `command` in docker-compose.yml.

**When to use:** When API and worker share the same codebase and dependencies (which this project does).

**Example:**

```dockerfile
# Dockerfile (final stage)
FROM python:3.13-slim-bookworm AS runtime

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY backend/app /app/app
COPY backend/alembic /app/alembic
COPY backend/alembic.ini /app/alembic.ini

ENV PATH="/app/.venv/bin:$PATH"

# No CMD -- docker-compose provides the command
# API: uvicorn app.main:app --host 0.0.0.0 --port 8000
# Worker: arq app.workers.worker_settings.WorkerSettings
```

```yaml
# docker-compose.yml (prod profile excerpt)
services:
  api:
    image: ghcr.io/owner/repo:latest
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
    profiles: ["prod"]

  worker:
    image: ghcr.io/owner/repo:latest
    command: ["arq", "app.workers.worker_settings.WorkerSettings"]
    profiles: ["prod"]
```

### Pattern 2: Docker Compose Profiles (Dev + Prod in One File)

**What:** Services without a `profiles` key start with every profile. Services tagged with `profiles: ["dev"]` or `profiles: ["prod"]` only start when that profile is activated.

**When to use:** When you want a single compose file that serves both local development and production.

**Example:**

```yaml
services:
  redis:
    image: redis:7-alpine
    # No profiles key = starts with ALL profiles

  postgres:
    image: postgres:16
    profiles: ["dev"]     # Only in dev (platform provides DB in prod)

  api:
    build:
      context: .
      dockerfile: backend/Dockerfile
    profiles: ["dev"]     # Dev builds locally

  api-prod:
    image: ghcr.io/owner/repo:latest
    profiles: ["prod"]    # Prod pulls pre-built image
```

```bash
# Development
docker compose --profile dev up

# Production
docker compose --profile prod up
```

### Pattern 3: Internal-Only Network

**What:** Backend services run on a Docker network marked `internal: true`, preventing outbound internet access and ensuring they are not reachable from outside the Docker host.

**When to use:** When backend services should only be accessible through a reverse proxy or API gateway (which Phase 12 provides).

**Example:**

```yaml
networks:
  backend:
    internal: true    # No external connectivity
    driver: bridge

services:
  api:
    networks:
      - backend
  worker:
    networks:
      - backend
  redis:
    networks:
      - backend
```

### Pattern 4: Dependency Ordering with Health Checks

**What:** Use `depends_on` with `condition: service_healthy` to ensure services start in correct order.

**When to use:** Always in production compose files to prevent race conditions.

**Example:**

```yaml
services:
  redis:
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    depends_on:
      redis:
        condition: service_healthy

  worker:
    depends_on:
      redis:
        condition: service_healthy
```

### Anti-Patterns to Avoid

- **Shell form CMD:** `CMD uvicorn app.main:app` prevents graceful shutdown and lifespan event triggering. Always use exec form: `CMD ["uvicorn", "app.main:app", ...]`
- **`version` key in docker-compose.yml:** Obsolete in Compose V2 (produces warnings). Remove entirely.
- **Separate Dockerfiles for API and worker:** When they share the same codebase and dependencies, one image with different commands is cleaner and reduces build time/storage.
- **Exposing backend ports to host in production:** Backend services should only be on the internal network. Port mapping (`ports:`) is for dev only; prod uses Docker networking.
- **Alpine for this project:** The dependency set includes pandas, asyncpg, and openpyxl which rely on C extensions. Slim-bookworm avoids musl compilation issues.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ARQ worker health monitoring | Custom Redis key check script | ARQ built-in `arq --check` CLI | Returns exit 0/1, integrates directly with Docker HEALTHCHECK; already checks the Redis health key that ARQ writes every `health_check_interval` seconds |
| Docker image tagging | Manual tag logic in workflow | `docker/metadata-action@v5` | Automatically generates tags from Git context (branch, SHA, semver tags) |
| Wait-for-it scripts | Shell scripts to wait for dependencies | Docker Compose `depends_on: condition: service_healthy` | Native Docker Compose feature; more reliable than polling scripts |
| Multi-platform builds | Custom build scripts | `docker/setup-buildx-action@v3` | Handles QEMU + Buildx setup for multi-arch if needed later |
| Layer cache management | Manual cache directory management | `cache-from: type=gha` / `cache-to: type=gha,mode=max` | GitHub Actions native cache backend; zero configuration needed |

**Key insight:** Docker and GitHub Actions ecosystems have mature, well-maintained official actions and patterns for every part of this pipeline. The only custom code needed is the Dockerfile, the health check endpoints, and the platform brief document.

## Common Pitfalls

### Pitfall 1: Stale `version` Key in docker-compose.yml

**What goes wrong:** Docker Compose V2 prints warnings when `version: '3.9'` is present (the current compose file has this).
**Why it happens:** The `version` key was deprecated in Compose V2 (fully obsolete since v2.25.0, March 2024).
**How to avoid:** Remove the `version` key entirely from docker-compose.yml. Compose V2 auto-detects the schema.
**Warning signs:** `level=warning msg="... the attribute version is obsolete"` in Docker output.

### Pitfall 2: Shell Form CMD Prevents Graceful Shutdown

**What goes wrong:** FastAPI lifespan events (database connection cleanup) never fire on container stop. Docker sends SIGTERM to the shell, not the Python process. Container takes 10 seconds to stop (Docker's kill timeout).
**Why it happens:** `CMD uvicorn ...` (shell form) wraps the command in `/bin/sh -c`, which doesn't forward signals.
**How to avoid:** Always use exec form: `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`.
**Warning signs:** Slow container shutdowns, database connection leaks.

### Pitfall 3: Missing .dockerignore

**What goes wrong:** Docker context includes `.venv/`, `__pycache__/`, `.env`, `node_modules/`, uploaded Excel files, and the frontend directory, inflating build time and potentially leaking secrets.
**Why it happens:** Without `.dockerignore`, Docker copies everything in the build context.
**How to avoid:** Create a comprehensive `.dockerignore` file before the Dockerfile.
**Warning signs:** Slow Docker builds, large image sizes, secrets in image layers.

### Pitfall 4: Running Containers as Root

**What goes wrong:** If the container is compromised, the attacker has root access to the container filesystem and potentially the host.
**Why it happens:** Docker runs processes as root by default.
**How to avoid:** Create a non-root user in the Dockerfile: `RUN groupadd -r appuser && useradd -r -g appuser appuser` then `USER appuser`.
**Warning signs:** `whoami` inside container returns `root`.

### Pitfall 5: ARQ Health Check Interval Default

**What goes wrong:** ARQ's default `health_check_interval` is 3600 seconds (1 hour). This means the Redis health key expires after 3601 seconds. Docker HEALTHCHECK may report the worker as unhealthy if checked during the gap.
**Why it happens:** The default is designed for long-running workers where frequent checks are unnecessary.
**How to avoid:** The project already sets `health_check_interval = 30` in `WorkerSettings`. Ensure the Docker HEALTHCHECK interval aligns (e.g., check every 30s, ARQ writes every 30s).
**Warning signs:** Intermittent "unhealthy" worker status.

### Pitfall 6: Database Connection String Scheme Mismatch

**What goes wrong:** The `DATABASE_URL` uses `postgresql+asyncpg://...` scheme, which is SQLAlchemy-specific. Alembic and the app engine both parse this. If the platform provides a standard `postgresql://` URL, it must be converted.
**Why it happens:** SQLAlchemy async requires the `+asyncpg` dialect prefix.
**How to avoid:** Document in the platform brief that `DATABASE_URL` must use the `postgresql+asyncpg://` scheme, not `postgresql://`.
**Warning signs:** `sqlalchemy.exc.ArgumentError` about unsupported dialect.

### Pitfall 7: GitHub Actions Cache API V2 Requirement

**What goes wrong:** Docker layer caching fails with "This legacy service is shutting down" error.
**Why it happens:** GitHub deprecated Cache API v1 effective April 15, 2025. Older Buildx versions used v1.
**How to avoid:** Use `docker/setup-buildx-action@v3` which installs the latest Buildx (v2-compatible).
**Warning signs:** Cache-related errors in CI builds.

### Pitfall 8: GITHUB_TOKEN Package Permissions

**What goes wrong:** Image push fails with 403/401 error.
**Why it happens:** By default, `GITHUB_TOKEN` has only read access to packages.
**How to avoid:** Set `permissions: packages: write` in the workflow job.
**Warning signs:** "permission denied" errors during `docker push`.

## Code Examples

### Multi-Stage Dockerfile for Python Backend

```dockerfile
# Source: FastAPI official docs + Docker Python best practices
# Stage 1: Builder — install dependencies
FROM python:3.13-slim-bookworm AS builder

WORKDIR /app

# Install build dependencies (some Python packages need gcc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment for clean copy to runtime
RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Install Python dependencies (cached layer)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime — lean production image
FROM python:3.13-slim-bookworm AS runtime

WORKDIR /app

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY backend/app /app/app
COPY backend/alembic /app/alembic
COPY backend/alembic.ini /app/alembic.ini

# Set ownership
RUN chown -R appuser:appuser /app

USER appuser

# Expose port (documentation only; compose controls actual exposure)
EXPOSE 8000

# No default CMD — docker-compose provides the command
# API: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# Worker: ["arq", "app.workers.worker_settings.WorkerSettings"]
```

### Docker Compose with Profiles (Dev + Prod)

```yaml
# Source: Docker Compose official docs, Docker profiles documentation
# No 'version' key — obsolete in Compose V2

services:
  # === Shared services (start with ALL profiles) ===
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - backend

  # === Dev-only services ===
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: devuser
      POSTGRES_PASSWORD: devpassword
      POSTGRES_DB: candidfounders_db
    ports:
      - "5433:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U devuser -d candidfounders_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    profiles: ["dev"]
    networks:
      - backend

  # === Prod services ===
  api:
    image: ghcr.io/kavindakottege/aiagent_barekind_productcontentgenerator:latest
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
    env_file: .env
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
    restart: unless-stopped
    profiles: ["prod"]
    networks:
      - backend

  worker:
    image: ghcr.io/kavindakottege/aiagent_barekind_productcontentgenerator:latest
    command: ["arq", "app.workers.worker_settings.WorkerSettings"]
    env_file: .env
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "arq", "app.workers.worker_settings.WorkerSettings", "--check"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
    restart: unless-stopped
    profiles: ["prod"]
    networks:
      - backend

networks:
  backend:
    internal: true
    driver: bridge

volumes:
  redis_data:
    driver: local
  postgres_data:
    driver: local
```

### FastAPI Health Check Endpoints (Liveness + Readiness)

```python
# Source: FastAPI health check best practices, Kubernetes probe patterns
import asyncio
from fastapi import APIRouter
from sqlalchemy import text
from app.database import async_session_maker
from app.config import settings
import redis.asyncio as aioredis

router = APIRouter(tags=["health"])

@router.get("/api/health")
async def liveness():
    """Liveness check — is the process alive and responding?"""
    return {"status": "healthy"}

@router.get("/api/health/ready")
async def readiness():
    """Readiness check — can the app handle traffic? Checks DB + Redis."""
    checks = {}

    # Check database
    try:
        async with async_session_maker() as session:
            await asyncio.wait_for(
                session.execute(text("SELECT 1")),
                timeout=5.0
            )
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"

    # Check Redis
    try:
        r = aioredis.from_url(settings.REDIS_URL)
        await asyncio.wait_for(r.ping(), timeout=5.0)
        await r.aclose()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"

    all_ok = all(v == "ok" for v in checks.values())
    status_code = 200 if all_ok else 503

    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if all_ok else "not_ready", "checks": checks}
    )
```

### GitHub Actions Workflow for ghcr.io

```yaml
# Source: GitHub official docs, docker/build-push-action docs
name: Build and Publish Docker Image

on:
  push:
    branches: ["main"]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      attestations: write
      id-token: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v5

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata (tags, labels)
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push Docker image
        id: push
        uses: docker/build-push-action@v6
        with:
          context: .
          file: backend/Dockerfile
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Generate artifact attestation
        uses: actions/attest-build-provenance@v3
        with:
          subject-name: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          subject-digest: ${{ steps.push.outputs.digest }}
          push-to-registry: true
```

### .dockerignore File

```
# Source: Docker best practices
# Python
__pycache__/
*.py[cod]
*.so
.Python
*.egg-info/
dist/
build/

# Virtual environments
.venv/
venv/
backend/.venv/
backend/venv/

# Environment files (secrets!)
.env
backend/.env

# Frontend (not needed for backend image)
frontend/

# IDE
.idea/
.vscode/
*.swp

# Git
.git/
.gitignore

# Planning docs
.planning/

# Data files
*.xlsx
backend/uploads/

# OS
.DS_Store
Thumbs.db

# Dev tooling
.dev-pids/
madebykav-app-template/
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `version: '3.x'` in docker-compose.yml | No version key (Compose V2 auto-detects) | March 2024 (Compose v2.25.0) | Must remove `version: '3.9'` from existing compose file |
| Gunicorn + uvicorn workers | uvicorn standalone with `--workers` flag | FastAPI 0.95+ / uvicorn 0.20+ | Simpler; fewer dependencies; FastAPI official docs recommend uvicorn directly |
| `tiangolo/uvicorn-gunicorn-fastapi` base image | Build from `python:3.x-slim` + install uvicorn | 2023 (deprecated by FastAPI creator) | Official docs say to build from scratch, not use pre-built images |
| Docker Compose V1 (`docker-compose`) | Docker Compose V2 (`docker compose`, no hyphen) | July 2023 (V1 end-of-life) | Commands use `docker compose` not `docker-compose` |
| GitHub Actions Cache API v1 | Cache API v2 required | April 2025 | Must use latest `docker/setup-buildx-action@v3` for GHA cache compatibility |
| Pin action SHAs | Pin by major version tag | Current best practice for non-critical pipelines | Use `@v5`, `@v6` etc. for readability; SHA pinning for high-security |

**Deprecated/outdated:**
- `tiangolo/uvicorn-gunicorn-fastapi` Docker image: Deprecated by the FastAPI creator; build from `python:3.x-slim` instead
- `docker-compose` CLI (V1): End-of-life since July 2023; use `docker compose` (V2, integrated into Docker CLI)
- `version` key in docker-compose.yml: Obsolete; remove entirely

## Open Questions

1. **Alembic Migrations in Production**
   - What we know: Alembic migrations need to run before the API starts. The dev script runs `alembic upgrade head` manually.
   - What's unclear: Should migrations run as a separate Docker entrypoint script, a Compose init service, or be triggered by the platform? The CONTEXT.md doesn't specify.
   - Recommendation: Include a `scripts/entrypoint.sh` that runs `alembic upgrade head` before starting uvicorn. Document this in the platform brief. This is a standard pattern (Django's `python manage.py migrate` in entrypoint).

2. **Upload Directory in Production**
   - What we know: The backend has a `backend/uploads/` directory for Excel file storage. In dev, this is a local directory.
   - What's unclear: Whether uploads need a Docker volume mount in production, or if this will be handled by a cloud storage solution in a later phase.
   - Recommendation: Mount a Docker volume at `/app/uploads` in the API container. Document in the platform brief.

3. **Redis Persistence Strategy**
   - What we know: Redis is used as a job queue (ARQ). Job results are kept for 1 hour (`keep_result = 3600`).
   - What's unclear: Whether Redis data loss on restart is acceptable (jobs would be lost) or if AOF persistence is required.
   - Recommendation: Enable AOF persistence (`--appendonly yes`) as a conservative default. Job data is transient but losing in-progress jobs would require manual re-triggering. Document in brief.

4. **Image Name Casing**
   - What we know: ghcr.io requires lowercase image names. The repository is `KavindaKottege/aiagent_barekind_productcontentgenerator` (capital K).
   - What's unclear: Whether `docker/metadata-action` auto-lowercases the image name.
   - Recommendation: Verify during implementation. The `${{ github.repository }}` context returns lowercase in most cases, but worth validating.

## Environment Variables Inventory

Complete inventory of environment variables needed by backend services (critical for the platform brief):

| Variable | Service | Required | Default | Format | Description |
|----------|---------|----------|---------|--------|-------------|
| `DATABASE_URL` | API, Worker | Yes | None | `postgresql+asyncpg://user:pass@host:port/dbname` | PostgreSQL connection (platform-provided) |
| `REDIS_URL` | API, Worker | Yes | `redis://localhost:6379` | `redis://host:port` | Redis connection (internal service name) |
| `SECRET_KEY` | API | Yes | None | 32+ character hex string | JWT signing key |
| `ALGORITHM` | API | No | `HS256` | String | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | API | No | `10080` | Integer | JWT token lifetime (7 days default) |
| `FRONTEND_URL` | API | Yes | None | URL | CORS allowed origin |
| `ENVIRONMENT` | API, Worker | No | `development` | `development` or `production` | Controls SQL echo logging |
| `AI_MODEL` | Worker | No | `gpt-4o` | String | OpenAI model name |
| `AI_TEMPERATURE` | Worker | No | `0.7` | Float 0-1 | Generation temperature |
| `GENERATION_SOFT_CAP` | Worker | No | `500.0` | Float | Cost soft cap in USD |

Note: `OPENAI_API_KEY` is stored in the database `app_settings` table, not as an environment variable.

## Sources

### Primary (HIGH confidence)
- [FastAPI Official Docker Docs](https://fastapi.tiangolo.com/deployment/docker/) - Dockerfile patterns, CMD exec form, layer caching
- [ARQ Official Docs](https://arq-docs.helpmanual.io/) - Health check mechanism, `--check` CLI, `health_check_interval`
- [GitHub Official Docs: Publishing Docker Images](https://docs.github.com/en/actions/use-cases-and-examples/publishing-packages/publishing-docker-images) - Complete workflow YAML, permissions, attestation
- [Docker Official Docs: GitHub Actions Cache](https://docs.docker.com/build/ci/github-actions/cache/) - GHA cache backend, `mode=max`
- [Docker Hub: Python Official Image](https://hub.docker.com/_/python) - Image variants, Alpine caveats
- [Docker Hub: Redis Official Image](https://hub.docker.com/_/redis) - Persistence configuration, Alpine variant

### Secondary (MEDIUM confidence)
- [Better Stack: FastAPI Docker Best Practices](https://betterstack.com/community/guides/scaling-python/fastapi-docker-best-practices/) - Multi-stage build strategy, security hardening
- [Collabnix: Docker Compose Profiles](https://collabnix.com/leveraging-compose-profiles-for-dev-prod-test-and-staging-environments/) - Profile patterns for environment separation
- [Blacksmith: Docker Layer Caching in GitHub Actions](https://www.blacksmith.sh/blog/cache-is-king-a-guide-for-docker-layer-caching-in-github-actions) - Cache backend comparison, Cache API v2 migration
- [Docker Forums: Version Key Obsolete](https://forums.docker.com/t/docker-compose-yml-version-is-obsolete/141313) - Compose V2 version key deprecation
- [Index.dev: FastAPI Health Check Best Practices](https://www.index.dev/blog/how-to-implement-health-check-in-python) - Liveness vs readiness patterns
- [BetterLink Blog: Redis Docker Deployment](https://eastondev.com/blog/en/posts/dev/20251217-docker-redis-deployment/) - Redis production persistence configuration

### Tertiary (LOW confidence)
- None. All findings verified with primary or secondary sources.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All tools are official Docker/GitHub recommendations verified against official documentation
- Architecture: HIGH - Patterns are well-documented standard practices (single image + dual entrypoint, Compose profiles, internal networks)
- Pitfalls: HIGH - All pitfalls verified against official docs and known issues
- Health checks: HIGH - ARQ built-in health check verified against ARQ official docs; FastAPI patterns verified against official deployment docs
- CI/CD: HIGH - GitHub Actions workflow verified against GitHub official documentation

**Research date:** 2026-01-30
**Valid until:** 2026-03-01 (stable domain; Docker and GitHub Actions patterns evolve slowly)
