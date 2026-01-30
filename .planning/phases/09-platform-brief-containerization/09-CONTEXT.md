# Phase 9: Platform Brief & Containerization - Context

**Gathered:** 2026-01-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Produce a standalone infrastructure brief for a platform GSD instance and production-ready Docker containers for all Python backend services (FastAPI, ARQ worker, Redis). The brief tells the platform operator exactly what to provision without reading source code. The Docker setup makes services startable, health-checkable, and internal-only.

</domain>

<decisions>
## Implementation Decisions

### Platform Brief — Audience & Format
- **Audience is another Claude Code GSD instance** that knows the MadeByKav platform but has no knowledge of the Content Generator app
- Brief is a **standalone handoff document** — not part of this repo, delivered separately to the platform GSD
- Format is Claude's discretion — optimized for an AI consumer (structured, parseable, actionable)
- Must include a **Mermaid/ASCII service architecture diagram** showing how Next.js, FastAPI, ARQ worker, Redis, and PostgreSQL connect
- Must include a **"Required Responses" section** — a checklist of what the platform GSD must provide back (DATABASE_URL, network config, base URL, ghcr.io access confirmation, etc.)
- No standard platform manifest format exists — this app is the first with a Python backend, so the brief defines its own structure

### Docker Topology
- **Single Docker image** for the Python app — runs as either FastAPI API or ARQ worker depending on the entrypoint command
- Redis uses the **official Redis image** — no custom build
- **PostgreSQL is platform-provided** — app containers receive DATABASE_URL, no database container in compose
- **Redis is app-provided** — Redis container is part of this app's Docker compose stack (platform does not provide Redis)
- **Single docker-compose.yml with profiles** for dev and prod — `docker compose --profile prod up`
- Backend services on **internal-only network** — not publicly reachable

### Health Check Design
- Claude's discretion on health check depth and implementation
- Health check endpoints and configuration should be documented in the platform brief so the platform GSD knows how to configure monitoring
- User-facing error handling when backend is down is a Phase 12 (API Proxy Layer) concern, not Phase 9

### Build & Deploy Workflow
- Images pushed to **GitHub Container Registry (ghcr.io)** — aligns with existing GitHub Packages setup for SDK packages
- **GitHub Actions CI pipeline** included — on push to main, builds image and pushes to ghcr.io
- Brief **lists all required environment variables** with descriptions, expected formats, and which service needs them — platform GSD decides injection method
- **Handoff timing: immediately after Phase 9** — platform GSD provisions while we develop Phases 10-13 locally; Phase 14 validates end-to-end on actual platform

### Claude's Discretion
- Platform brief format and section structure (optimized for AI consumer)
- Health check depth (shallow vs deep vs both liveness/readiness)
- ARQ worker health check approach (HTTP endpoint vs heartbeat file)
- Health check polling intervals and documentation detail
- Docker multi-stage build optimization
- GitHub Actions workflow specifics (caching, tagging strategy)

</decisions>

<specifics>
## Specific Ideas

- Brief audience is a GSD instance, not a human — structure for parseability and actionability
- Brief must include a "Required Responses" checklist so the user knows exactly what to collect from the platform GSD and bring back to later phases
- Single image with different entrypoints follows the standard web+worker pattern (like Django+Celery, Rails+Sidekiq)
- This is the first platform app with a Python backend — the brief sets a precedent for how apps declare non-standard infrastructure needs

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 09-platform-brief-containerization*
*Context gathered: 2026-01-30*
