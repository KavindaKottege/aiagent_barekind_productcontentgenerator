# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-30)

**Core value:** Generate professional, on-brand product content at scale with minimal friction - agencies can confidently use this with clients without worrying about workflow bottlenecks or unprofessional UX
**Current focus:** Milestone v2.0 — Platform Deployment (defining requirements)

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements for v2.0
Last activity: 2026-01-30 — Milestone v2.0 started

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Deploy to MadeByKav platform (tenantname.madebykav.com/app/content-generator)
- Use @madebykav/auth SDK instead of custom JWT auth
- Use @madebykav/db SDK with Drizzle ORM for Next.js data access
- Use @madebykav/ui SDK for UI components
- Python backend as internal Docker service (not publicly exposed)
- Next.js acts as API gateway, proxies to Python backend with tenant context
- Dual ORM: Drizzle (Next.js) + SQLAlchemy (Python) on shared PostgreSQL
- Per-tenant OpenAI API key managed at platform level
- Session-based auth (mbk_session cookie, sessions table in PostgreSQL)
- Platform passes x-tenant-id and x-app-slug headers to apps
- Tenant isolation via PostgreSQL RLS with set_config('app.current_tenant_id', tenantId, true)

### From v1.0 (carried forward)

Key architectural decisions that affect v2.0 migration:

- Async-only SQLAlchemy with asyncpg (no sync fallback)
- ARQ + Redis for background job processing
- SSE for real-time progress streaming (500ms polling)
- LangChain with structured output for AI generation
- Tiktoken for token counting and cost tracking
- 3 retries max for character limit violations
- JSONB columns for flexible data (unmapped_data, rejection_reasons, ai_input_fields)
- Generation audit trail (GenerationAudit model)
- Dual review status pattern (manual + AI review status)

### Roadmap Evolution

- v1.0 complete: 8 phases, 42 plans executed
- v2.0 started: Platform Deployment milestone

### Pending Todos

None yet.

### Blockers/Concerns

- Platform needs Docker container hosting capability for Python services
- Need to verify @madebykav/ui component compatibility with current UI patterns
- Dual ORM on shared database needs careful migration coordination
- SSE proxying through Next.js needs testing for reliability

### Next Phase Readiness

**v1.0 COMPLETE**
- All 8 phases complete, all 51 v1 requirements met
- Full workflow: auth → clients → upload → generate → review → regenerate → export → debug

**v2.0 IN PROGRESS**
- Defining requirements and roadmap

## Session Continuity

Last session: 2026-01-30 (current)
Stopped at: Defining v2.0 milestone requirements
Resume file: None
Next: Complete requirements definition and roadmap creation

---
*State initialized: 2026-01-22*
*Last updated: 2026-01-30 (v2.0 milestone start)*
