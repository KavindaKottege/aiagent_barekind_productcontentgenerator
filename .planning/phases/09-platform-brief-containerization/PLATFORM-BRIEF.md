# Platform Infrastructure Brief: Content Generator

**App name:** Content Generator
**App slug:** `content-generator`
**URL pattern:** `{tenant}.madebykav.com/app/content-generator`
**Brief version:** 1.0
**Date:** 2026-01-30
**Source repo:** `madebykav_SEOContentGenerator`

---

## 1. App Overview

The Content Generator is an AI-powered product content generation tool for marketing agencies. Users upload product data (via Excel), configure brand voice and generation parameters per client, then batch-generate SEO-optimized product descriptions using OpenAI. Generated content goes through a review workflow before export.

**Architecture summary:** Next.js frontend (platform-hosted) + Python backend (Docker containers: FastAPI API + ARQ background worker + Redis job queue). PostgreSQL is platform-provided.

**This is the first platform app with a Python backend.** All previous apps are Node.js-only. This brief defines the infrastructure pattern for apps that need non-standard backend services.

---

## 2. Service Architecture

```
                         PUBLIC
                           |
                    +------v------+
                    |   Browser   |
                    +------+------+
                           |
                           | HTTPS
                           |
              +------------v------------+
              |     Next.js Frontend    |  <-- Platform-hosted (standard app)
              |  (Auth, UI, API proxy)  |
              +-----+----------+-------+
                    |          |
      Tenant headers|          | Drizzle ORM
      (internal)    |          | (direct DB access for
                    |          |  reads/simple writes)
           +--------v--------+ |
           |  FastAPI API    | |
           |  (port 8000)    | |
           |  [app-provided] | |
           +---+----+----+--+ |
               |    |    |     |
               |    |    |     |
          +----v-+  |  +-v-----v---------+
          | Redis|  |  |   PostgreSQL    |
          | queue|  |  | [platform-      |
          | [app-|  |  |  provided]      |
          | prov]|  |  +---------^-------+
          +--+---+  |            |
             |      |            |
             | jobs |            | DB read/write
             |      |            |
          +--v------v---+       |
          |  ARQ Worker  |------+
          | [app-provided]|
          |               |----> OpenAI API (external, HTTPS)
          +---------------+
```

### Service Ownership

| Service | Owner | Notes |
|---------|-------|-------|
| Next.js Frontend | Platform | Standard platform app deployment |
| PostgreSQL | Platform | Shared database, app uses tenant isolation |
| FastAPI API | App (this brief) | Docker container, internal only |
| ARQ Worker | App (this brief) | Docker container, no ports |
| Redis | App (this brief) | Docker container, job queue + results cache |

---

## 3. Services to Provision

### 3.1 Platform-Provided (already exists)

**PostgreSQL Database**
- Shared platform database
- App uses Row-Level Security (RLS) with `set_config('app.current_tenant_id', tenantId)` for tenant isolation
- Alembic manages migrations (run on container startup)
- Tables: `users`, `clients`, `products`, `product_groups`, `generation_jobs`, `generation_audits`, `review_jobs`, `app_settings`

**Next.js Frontend**
- Standard platform app deployment (same as all other platform apps)
- Acts as API gateway: proxies requests to FastAPI with tenant context headers
- Also accesses PostgreSQL directly via Drizzle ORM for reads and simple writes

### 3.2 App-Provided (must be hosted)

All three services below run from Docker containers. The API and Worker share a single Docker image.

#### FastAPI API Container

| Property | Value |
|----------|-------|
| Image | `ghcr.io/kavindakottege/madebykav_seocontentgenerator:latest` |
| Command | `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2` |
| Internal port | 8000 |
| Public port | **None** -- must NOT be exposed to public internet |
| Volumes | `/app/uploads` -- persistent storage for uploaded Excel files |
| Restart policy | `unless-stopped` |
| Depends on | Redis (must be healthy before API starts) |

**Health checks:**

| Probe | Endpoint | Method | Expected Response | Interval | Timeout | Retries | Start Period |
|-------|----------|--------|-------------------|----------|---------|---------|--------------|
| Liveness | `http://localhost:8000/api/health` | GET | 200 `{"status": "healthy"}` | 30s | 10s | 3 | 15s |
| Readiness | `http://localhost:8000/api/health/ready` | GET | 200 `{"status": "ready", "checks": {"database": "ok", "redis": "ok"}}` | 30s | 10s | 3 | 15s |

The readiness endpoint returns HTTP 503 with `{"status": "not_ready", "checks": {...}}` when either PostgreSQL or Redis is unreachable. Each dependency check has a 5-second internal timeout.

**Entrypoint behavior:**
The container entrypoint script runs `alembic upgrade head` (database migrations) before starting uvicorn. Migrations are idempotent -- Alembic tracks applied versions, so running from multiple containers is safe.

#### ARQ Worker Container

| Property | Value |
|----------|-------|
| Image | `ghcr.io/kavindakottege/madebykav_seocontentgenerator:latest` (same image as API) |
| Command | `arq app.workers.worker_settings.WorkerSettings` |
| Internal port | **None** -- no network ports |
| Public port | **None** |
| Volumes | None |
| Restart policy | `unless-stopped` |
| Depends on | Redis (must be healthy before worker starts) |

**Health check:**

| Probe | Command | Expected | Interval | Timeout | Retries | Start Period |
|-------|---------|----------|----------|---------|---------|--------------|
| Liveness | `arq app.workers.worker_settings.WorkerSettings --check` | Exit code 0 | 30s | 10s | 3 | 15s |

The `arq --check` command verifies the worker process is alive and connected to Redis. It reports healthy if the worker has sent a heartbeat within the last 30 seconds (`health_check_interval = 30`).

**Entrypoint behavior:**
Same entrypoint script as API. Runs `alembic upgrade head` before starting the worker. Idempotent -- safe to run from both API and worker containers simultaneously.

**Worker configuration:**
- Max concurrent jobs: 5
- Job timeout: 7200s (2 hours, for large batch generation)
- Result retention: 3600s (1 hour)
- Redis poll interval: 500ms

#### Redis Container

| Property | Value |
|----------|-------|
| Image | `redis:7-alpine` |
| Command | `redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru` |
| Internal port | 6379 |
| Public port | **None** |
| Volumes | `/data` -- persistent AOF storage |
| Restart policy | `unless-stopped` |

**Health check:**

| Probe | Command | Expected | Interval | Timeout | Retries |
|-------|---------|----------|----------|---------|---------|
| Liveness | `redis-cli ping` | `PONG` (exit code 0) | 10s | 5s | 5 |

**Redis configuration notes:**
- AOF (Append-Only File) enabled for durability across restarts
- 256MB memory limit with LRU eviction prevents unbounded growth
- Redis is used for ARQ job queue and job results -- not for caching
- Data loss on Redis restart is tolerable (jobs can be re-enqueued) but AOF minimizes this

---

## 4. Networking Requirements

### Internal Communication

| From | To | Protocol | Port | Purpose |
|------|----|----------|------|---------|
| Next.js | FastAPI API | HTTP | 8000 | API proxy (tenant-authenticated requests) |
| FastAPI API | Redis | TCP | 6379 | Job enqueue, results fetch |
| FastAPI API | PostgreSQL | TCP | 5432 | Database queries |
| ARQ Worker | Redis | TCP | 6379 | Job dequeue, results store, health heartbeat |
| ARQ Worker | PostgreSQL | TCP | 5432 | Database queries during job execution |
| ARQ Worker | OpenAI API | HTTPS | 443 | AI content generation (api.openai.com) |
| FastAPI API | OpenAI API | HTTPS | 443 | AI content generation (api.openai.com) |

### Network Rules

1. **No public internet exposure for API, Worker, or Redis.** The FastAPI API listens on port 8000 but this port must NOT be mapped to the host or exposed to the public internet. Only the Next.js frontend (platform reverse proxy) routes traffic to the API.

2. **Outbound internet required.** Both the API and Worker containers must be able to reach `api.openai.com` (HTTPS/443) for AI generation. Standard bridge networking (not `internal: true`) is required.

3. **Internal DNS resolution.** All app-provided services (API, Worker, Redis) must be able to resolve each other by service name within the Docker network. The `REDIS_URL` environment variable uses the service name (`redis://redis:6379`).

4. **Platform PostgreSQL access.** API and Worker containers receive `DATABASE_URL` pointing to the platform's PostgreSQL instance. This must be reachable from within the Docker network.

---

## 5. Environment Variables

### Complete Variable Reference

| Variable | Service(s) | Required | Default | Format | Description |
|----------|-----------|----------|---------|--------|-------------|
| `DATABASE_URL` | API, Worker | **Yes** | None (dev: `postgresql+asyncpg://devuser:devpassword@localhost:5433/saas_dev`) | `postgresql+asyncpg://{user}:{pass}@{host}:{port}/{db}` | PostgreSQL connection string. **MUST use `postgresql+asyncpg://` scheme** (not `postgres://` or `postgresql://`). The async driver is required. |
| `REDIS_URL` | API, Worker | **Yes** | `redis://localhost:6379` | `redis://{host}:{port}` | Redis connection string. In Docker: `redis://redis:6379` (uses service name). |
| `SECRET_KEY` | API | **Yes** | None (dev: `dev-secret-key-change-in-production-32chars`) | String, min 32 characters | JWT signing key for authentication tokens. Must be cryptographically random in production. |
| `ALGORITHM` | API | No | `HS256` | String | JWT signing algorithm. No need to change. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | API | No | `10080` (7 days) | Integer | JWT token expiration in minutes. |
| `FRONTEND_URL` | API | **Yes** | `http://localhost:3000` | URL | Frontend origin for CORS configuration. Must match the tenant URL pattern (e.g., `https://{tenant}.madebykav.com`). |
| `ENVIRONMENT` | API, Worker | **Yes** | `development` | `development` or `production` | Controls logging verbosity and debug features. Set to `production` in deployment. |
| `AI_MODEL` | API, Worker | No | `gpt-4o` | String | OpenAI model identifier for content generation. |
| `AI_TEMPERATURE` | API, Worker | No | `0.7` | Float (0.0-2.0) | OpenAI generation temperature (creativity level). |
| `GENERATION_SOFT_CAP` | API, Worker | No | `500.0` | Float (USD) | Cost soft cap for AI generation spending. Warns when exceeded. |

### Important Notes

1. **OpenAI API key is NOT an environment variable.** It is stored in the `app_settings` database table per tenant and read at runtime. No `OPENAI_API_KEY` env var is needed.

2. **DATABASE_URL dialect requirement.** The URL MUST use the `postgresql+asyncpg://` scheme. The application uses SQLAlchemy's async engine with the `asyncpg` driver. Using `postgres://` or `postgresql://` (without `+asyncpg`) will cause a startup error.

3. **REDIS_URL in Docker.** When running in Docker with the compose configuration, set `REDIS_URL=redis://redis:6379`. The hostname `redis` resolves to the Redis container via Docker DNS.

4. **FRONTEND_URL for CORS.** This must exactly match the origin of incoming requests. If the tenant URL is `https://acme.madebykav.com`, then `FRONTEND_URL=https://acme.madebykav.com`. Wildcard CORS is not supported.

5. **SECRET_KEY generation.** Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"` or equivalent.

---

## 6. Database Requirements

### Schema Management

- **ORM:** SQLAlchemy 2.0 (async) with Alembic for migrations
- **Migration runner:** `alembic upgrade head` runs automatically on container startup (entrypoint script)
- **Migration location:** `/app/alembic/` directory inside the container
- **Config file:** `/app/alembic.ini` inside the container

### Tables

| Table | Purpose |
|-------|---------|
| `users` | App users (linked to platform tenant) |
| `clients` | Marketing agency clients (brand profiles) |
| `products` | Individual product records with generated content |
| `product_groups` | Logical groupings of products (by upload batch) |
| `generation_jobs` | Async AI generation job tracking |
| `generation_audits` | Generation cost and usage tracking |
| `review_jobs` | Async AI review job tracking |
| `app_settings` | Per-tenant settings (OpenAI API key, preferences) |

### Tenant Isolation

- Row-Level Security (RLS) with `set_config('app.current_tenant_id', tenantId)` pattern
- Next.js frontend passes tenant context to the API via headers
- All queries are scoped to the current tenant
- Table prefixing with app slug will be addressed in Phase 10 (platform integration)

---

## 7. Startup Order

Container startup must follow this sequence:

```
1. Redis
   |
   +-- (wait for healthy: redis-cli ping returns PONG)
   |
   +---> 2a. FastAPI API
   |          |
   |          +-- Run: alembic upgrade head (migrations)
   |          +-- Run: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
   |          +-- (wait for healthy: GET /api/health returns 200)
   |
   +---> 2b. ARQ Worker (can start in parallel with API)
              |
              +-- Run: alembic upgrade head (migrations, idempotent)
              +-- Run: arq app.workers.worker_settings.WorkerSettings
              +-- (wait for healthy: arq --check returns exit 0)
```

**Key points:**
- Redis must be healthy before API and Worker start (they connect to Redis on startup)
- API and Worker can start in parallel (both depend only on Redis being ready)
- PostgreSQL must be reachable when API/Worker start (for Alembic migrations and normal operation)
- Alembic migrations run from both containers but are idempotent (version tracking prevents duplicate application)

---

## 8. Monitoring and Health Checks

### Endpoint Summary

| Service | Probe Type | Check | Healthy Response | Unhealthy Response |
|---------|-----------|-------|------------------|-------------------|
| FastAPI API | Liveness | `GET http://localhost:8000/api/health` | 200 `{"status": "healthy"}` | Non-200 or timeout |
| FastAPI API | Readiness | `GET http://localhost:8000/api/health/ready` | 200 `{"status": "ready", "checks": {"database": "ok", "redis": "ok"}}` | 503 `{"status": "not_ready", "checks": {"database": "error: ...", "redis": "error: ..."}}` |
| ARQ Worker | Liveness | `arq app.workers.worker_settings.WorkerSettings --check` | Exit code 0 | Non-zero exit code |
| Redis | Liveness | `redis-cli ping` | `PONG` (exit code 0) | Non-zero exit code |

### Health Check Configuration (Docker Compose reference)

```yaml
# API
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 15s

# Worker
healthcheck:
  test: ["CMD", "arq", "app.workers.worker_settings.WorkerSettings", "--check"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 15s

# Redis
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 10s
  timeout: 5s
  retries: 5
```

### Readiness Probe Details

The API readiness endpoint (`/api/health/ready`) performs independent checks:

1. **Database check:** Executes `SELECT 1` against PostgreSQL with a 5-second async timeout
2. **Redis check:** Executes `PING` against Redis with a 5-second async timeout

Each check is isolated -- one failure does not prevent the other from being reported. The response body always includes both check results, making it easy to identify which dependency is down.

---

## 9. Volumes

| Volume | Container | Mount Path | Purpose | Persistence |
|--------|-----------|------------|---------|-------------|
| `uploads_data` | FastAPI API | `/app/uploads` | Uploaded Excel files for product import | Required -- user uploads must survive restarts |
| `redis_data` | Redis | `/data` | Redis AOF persistence file | Recommended -- preserves job queue across restarts |

**Volume provisioning notes:**
- Both volumes need persistent storage (not ephemeral)
- `uploads_data` size depends on usage; typical Excel files are 100KB-5MB each
- `redis_data` will be small (< 50MB) since Redis is used only for job queue, not caching
- No shared volumes between containers

---

## 10. Container Image Details

### Image Registry

| Property | Value |
|----------|-------|
| Registry | GitHub Container Registry (ghcr.io) |
| Image | `ghcr.io/kavindakottege/madebykav_seocontentgenerator` |
| Tags | `latest` (most recent main branch build), `sha-{commit}` (specific commit) |
| Build trigger | Push to `main` branch (GitHub Actions) |
| CI workflow | `.github/workflows/docker-publish.yml` |
| Attestation | SLSA build provenance via `actions/attest-build-provenance` |

### Image Specifications

| Property | Value |
|----------|-------|
| Base | `python:3.13-slim-bookworm` |
| Size | ~661MB |
| User | `appuser` (non-root, UID assigned by system) |
| Working dir | `/app` |
| Python version | 3.13 |
| Key packages | FastAPI, SQLAlchemy 2.0, asyncpg, ARQ, LangChain, pandas, openpyxl |

### Pulling the Image

```bash
# Requires authentication to ghcr.io
docker pull ghcr.io/kavindakottege/madebykav_seocontentgenerator:latest
```

Access requires read permission on the GitHub repository's packages. See Required Responses section for access confirmation.

---

## 11. Docker Compose Reference

The repository includes a complete `docker-compose.yml` with dev/prod profile separation. For production deployment:

```bash
docker compose --profile prod up -d
```

This starts: `redis`, `api`, `worker` (the `postgres` and `pgadmin` services are dev-only).

The compose file can be used as-is or adapted to the platform's container orchestration system. All configuration values (image names, commands, health checks, volumes, environment variables) documented above match the compose file exactly.

---

## 12. Required Responses

The platform operator must provide the following before deployment can proceed. Check each item when resolved.

### Infrastructure

- [ ] **DATABASE_URL** -- Full PostgreSQL connection string in `postgresql+asyncpg://{user}:{pass}@{host}:{port}/{db}` format. Must be reachable from the Docker network where app containers run.
- [ ] **Container hosting confirmation** -- Confirm the platform can host Docker containers (API + Worker + Redis) with the specifications in Section 3.2.
- [ ] **Redis hosting confirmation** -- Confirm Redis container can be provisioned as an app-provided service (or indicate if the platform provides a managed Redis instance instead).
- [ ] **Persistent volume provisioning** -- Confirm persistent volumes can be provisioned for:
  - `/app/uploads` on the API container (file storage)
  - `/data` on the Redis container (AOF persistence)

### Networking

- [ ] **Network configuration** -- Confirm internal networking between containers (API <-> Redis, Worker <-> Redis) and outbound internet access to `api.openai.com:443`.
- [ ] **DNS/routing** -- Confirm how Next.js frontend routes requests to the FastAPI API on port 8000. Expected pattern: internal service discovery or reverse proxy, NOT public internet routing.
- [ ] **No public exposure** -- Confirm the API container's port 8000 is not exposed to the public internet. Only the Next.js frontend (via platform routing) should reach the API.

### Secrets and Configuration

- [ ] **SECRET_KEY** -- A cryptographically random string (min 32 characters) for JWT token signing. Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] **FRONTEND_URL** -- The base URL for CORS configuration. Must match the tenant URL pattern (e.g., `https://{tenant}.madebykav.com` or a specific origin).
- [ ] **ENVIRONMENT** -- Set to `production` for the deployed environment.

### Image Access

- [ ] **ghcr.io access confirmation** -- Confirm the platform can pull from `ghcr.io/kavindakottege/madebykav_seocontentgenerator:latest`. This requires read access to the GitHub repository's packages.

### Response Format

For each item above, provide:
1. The value or configuration (for DATABASE_URL, SECRET_KEY, FRONTEND_URL, etc.)
2. Confirmation or alternative approach (for infrastructure items)
3. Any constraints or limitations that affect the specifications in this brief

---

## Appendix A: Quick Reference Commands

```bash
# Start production stack
docker compose --profile prod up -d

# Check all service health
docker compose --profile prod ps

# View API logs
docker logs cg-api --tail 100 -f

# View Worker logs
docker logs cg-worker --tail 100 -f

# View Redis logs
docker logs cg-redis --tail 100 -f

# Run migrations manually
docker exec cg-api alembic upgrade head

# Check worker health
docker exec cg-worker arq app.workers.worker_settings.WorkerSettings --check

# Check API readiness
curl http://localhost:8000/api/health/ready

# Enter API container shell
docker exec -it cg-api /bin/bash

# Redis CLI
docker exec -it cg-redis redis-cli
```

## Appendix B: Environment Variable Template

```env
# Required -- must be provided by platform
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
SECRET_KEY=<generate-with-secrets-token-urlsafe-32>
FRONTEND_URL=https://tenant.madebykav.com
ENVIRONMENT=production

# Required -- set by Docker networking (do not change in Docker deployment)
REDIS_URL=redis://redis:6379

# Optional -- defaults are suitable for production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
AI_MODEL=gpt-4o
AI_TEMPERATURE=0.7
GENERATION_SOFT_CAP=500.0
```

---

*Generated: 2026-01-30*
*Source: madebykav_SEOContentGenerator Phase 9 (Platform Brief & Containerization)*
