---
phase: 09-platform-brief-containerization
plan: 03
subsystem: infra
tags: [docker-compose, github-actions, ghcr, ci-cd, container-orchestration, redis]

# Dependency graph
requires:
  - phase: 09-01
    provides: "Multi-stage Dockerfile for Python backend (API + worker)"
  - phase: 09-02
    provides: "Health check endpoints (/api/health, /api/health/ready)"
provides:
  - "Docker Compose with dev/prod profile separation"
  - "Production service orchestration (api, worker, redis) with health checks"
  - "GitHub Actions CI pipeline for Docker image publishing to ghcr.io"
  - "Redis production config (AOF, 256MB limit, LRU eviction)"
affects: [09-04, 10-platform-integration, deployment]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dev/prod profile separation in Docker Compose (no version key, V2 format)"
    - "Prod services with no port mappings (internal-only networking)"
    - "GHA cache for Docker layer caching in CI"
    - "OCI artifact attestation for supply chain security"

key-files:
  created:
    - ".github/workflows/docker-publish.yml"
  modified:
    - "docker-compose.yml"

key-decisions:
  - "DOCK-NETWORK: Standard bridge network (no internal:true) -- prod services need outbound for OpenAI API and external PostgreSQL"
  - "DOCK-ISOLATION: Port omission on prod services provides host isolation without blocking outbound traffic"
  - "DOCK-CI-CACHE: GHA layer cache (type=gha,mode=max) for fast CI rebuilds"
  - "DOCK-CI-TAGS: SHA + latest tags on main branch pushes"

patterns-established:
  - "Profile pattern: dev for local tooling (postgres, pgadmin), prod for deployed services (api, worker)"
  - "Shared services: No profiles key means service starts with any profile"
  - "Container naming: cg-{service} prefix for all containers"
  - "CI: Build on push to main, publish to ghcr.io with attestation"

# Metrics
duration: 5min
completed: 2026-01-30
---

# Phase 9 Plan 3: Docker Compose & CI Pipeline Summary

**Docker Compose with dev/prod profiles (no port exposure on prod) and GitHub Actions CI for ghcr.io image publishing with GHA layer caching**

## Performance

- **Duration:** 5 min
- **Started:** 2026-01-30T07:03:12Z
- **Completed:** 2026-01-30T07:08:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Docker Compose rewritten from V1 to V2 with dev/prod profile separation
- Production services (api, worker) have no port mappings -- only reachable within Docker network
- Redis configured for production (AOF persistence, 256MB memory limit, LRU eviction)
- GitHub Actions CI pipeline builds and pushes Docker images to ghcr.io on every push to main
- Full health check coverage: Redis (redis-cli ping), API (curl /api/health), Worker (arq --check)
- Dependency ordering ensures Redis is healthy before api/worker start

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite docker-compose.yml with dev/prod profiles** - `c3322fa` (feat)
2. **Task 2: Create GitHub Actions CI workflow for Docker image publishing** - `7a7b227` (feat)

## Files Created/Modified
- `docker-compose.yml` - Service orchestration with 5 services (redis, postgres, pgadmin, api, worker), dev/prod profiles, health checks, dependency ordering
- `.github/workflows/docker-publish.yml` - CI pipeline: checkout, buildx, login, metadata, build+push, attestation

## Decisions Made

1. **Standard bridge network (not internal:true)** -- `internal: true` blocks ALL outbound traffic. API and worker need outbound access for OpenAI API calls and external PostgreSQL connections. Isolation is achieved by omitting `ports:` on prod services (not reachable from host).

2. **SHA + latest tags** -- Every push to main gets a unique SHA tag for traceability plus `latest` for convenience. No semver tags yet (can be added when release workflow is needed).

3. **GHA layer caching (mode=max)** -- Uses GitHub Actions cache for Docker layers. `mode=max` caches all intermediate layers, not just final, for maximum cache hit rate on rebuilds.

4. **Artifact attestation** -- Uses `actions/attest-build-provenance@v2` for SLSA supply chain attestation, establishing provenance for container images.

## Deviations from Plan

None -- plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None -- no external service configuration required. GitHub Actions will automatically use `GITHUB_TOKEN` for ghcr.io authentication when the workflow runs.

## Next Phase Readiness
- Docker Compose ready for deployment orchestration
- CI pipeline will activate on first push to main with this workflow
- Platform integration (Phase 10) can reference the ghcr.io image URL
- Remaining: 09-04 (Platform Brief) will document deployment architecture

---
*Phase: 09-platform-brief-containerization*
*Completed: 2026-01-30*
