---
phase: 09-platform-brief-containerization
plan: 01
subsystem: containerization
tags: [docker, dockerfile, multi-stage, python, backend]
depends_on: []
provides:
  - "Production Docker image for Python backend (API + worker)"
  - "Build context exclusions via .dockerignore"
affects:
  - "09-02 (Frontend Dockerfile)"
  - "09-03 (docker-compose orchestration)"
  - "09-04 (CI/CD pipeline)"
tech_stack:
  added:
    - "Docker multi-stage build"
    - "python:3.13-slim-bookworm"
  patterns:
    - "Single image, dual entrypoint (API vs worker via command)"
    - "COPY --chown to avoid duplicate chown layer"
    - "Non-root user (appuser) for runtime security"
key_files:
  created:
    - ".dockerignore"
    - "backend/Dockerfile"
  modified: []
decisions:
  - id: "DOCK-IMAGE-PATTERN"
    decision: "Single multi-stage image serves both API and worker"
    rationale: "Same dependencies, different entrypoint commands. Reduces build time and image management."
  - id: "DOCK-BASE-IMAGE"
    decision: "python:3.13-slim-bookworm (not Alpine)"
    rationale: "Project uses pandas, asyncpg, openpyxl with C extensions. musl libc (Alpine) causes build issues with these packages."
  - id: "DOCK-CHOWN-STRATEGY"
    decision: "Use COPY --chown instead of RUN chown -R"
    rationale: "RUN chown -R duplicates entire venv layer (354MB). COPY --chown sets ownership during copy, saving 40% image size (1.11GB -> 661MB)."
  - id: "DOCK-NO-CMD"
    decision: "No CMD in Dockerfile"
    rationale: "docker-compose provides the command per service: uvicorn for API, arq for worker."
metrics:
  duration: "3m 3s"
  completed: "2026-01-30"
---

# Phase 9 Plan 1: Backend Dockerfile Summary

Multi-stage Docker image for Python backend with .dockerignore, building from repo root with non-root user and COPY --chown optimization (661MB final image).

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Create .dockerignore for backend build context | 76b42a0 | .dockerignore |
| 2 | Create multi-stage production Dockerfile | 2d01933 | backend/Dockerfile |

## What Was Built

### .dockerignore (repo root)
Comprehensive exclusion file for Docker build context. Prevents secrets (.env), frontend code, Python caches, virtual environments, planning docs, data files (*.xlsx), and dev tooling from entering the build context. Placed at repo root since `docker build` context is `.` (repo root).

### backend/Dockerfile (multi-stage)
Two-stage production Dockerfile:

**Stage 1 (builder):** Installs gcc + libpq-dev for C extension compilation, creates virtual environment at `/app/.venv`, installs all Python requirements.

**Stage 2 (runtime):** Installs only runtime deps (libpq5, curl), creates non-root `appuser`, copies venv and app code with `--chown=appuser:appuser`, exposes port 8000. No CMD -- docker-compose provides the entrypoint command.

**Key commands:**
- API: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2`
- Worker: `arq app.workers.worker_settings.WorkerSettings`

## Verification Results

| Check | Result |
|-------|--------|
| Docker build completes | Pass |
| Python version | 3.13.11 |
| Non-root user (whoami) | appuser |
| /app/app/main.py exists | Pass |
| /app/alembic.ini exists | Pass |
| Key packages installed | fastapi, SQLAlchemy, arq, langchain-openai |
| Image size | 661MB |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed image size bloat from RUN chown -R**
- **Found during:** Task 2 verification
- **Issue:** `RUN chown -R appuser:appuser /app` created a 354MB duplicate layer (copying entire venv to change ownership), inflating image from ~660MB to 1.11GB
- **Fix:** Replaced with `COPY --chown=appuser:appuser` on each COPY instruction, which sets ownership during copy without creating an extra layer
- **Files modified:** backend/Dockerfile
- **Commit:** 2d01933

**2. [Deviation] .dockerignore placed at repo root instead of backend/**
- **Plan correction applied:** The plan originally specified `backend/.dockerignore` in frontmatter but later corrected itself to repo root since Docker build context is the repo root (`.`). Followed the corrected instruction.

## Image Size Analysis

661MB is above the plan's ideal 200-400MB range but reasonable for this dependency set:
- Base python:3.13-slim-bookworm: ~55MB
- System libs (libpq5, curl): ~7MB
- Python venv: ~337MB (pandas 10.4MB, numpy 14.4MB, langchain, tiktoken, etc.)
- App code + alembic: ~1.3MB

The venv dominates at 337MB due to ML/NLP dependencies (pandas, numpy, tiktoken, langchain). This is expected and cannot be reduced without removing functionality.

## Next Phase Readiness

Plan 09-01 provides the backend Docker image that Plan 09-03 (docker-compose) needs to orchestrate. No blockers for subsequent plans.
