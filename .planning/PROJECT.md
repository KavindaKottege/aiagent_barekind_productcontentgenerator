# Candid Founders Content Generator

## What This Is

A professional AI-powered product content generator deployed on the MadeByKav platform. Tenants upload raw product Excel files (Faire format), select which product fields to use, and generate optimized titles and descriptions using client-specific brand guidelines and prompts. The app handles client profiles, smart regeneration with feedback, and multi-mode review (manual, AI-assisted, or auto). Each tenant gets their own isolated workspace at `tenantname.madebykav.com/app/content-generator`.

## Core Value

Generate professional, on-brand product content at scale with minimal friction - agencies can confidently use this with clients without worrying about workflow bottlenecks or unprofessional UX.

## Current Milestone: v2.0 Platform Deployment

**Goal:** Deploy the Content Generator to the MadeByKav platform without losing any functionality or reliability, using platform SDKs for auth, database, and UI.

**Target features:**
- Migrate auth to @madebykav/auth (platform-managed users and sessions)
- Migrate database to shared platform PostgreSQL with tenant isolation
- Migrate UI components to @madebykav/ui
- Containerize Python backend (FastAPI + ARQ worker + Redis) for platform hosting
- Build Next.js → Python backend proxy layer for authenticated internal requests
- Per-tenant OpenAI API key support
- Platform infrastructure brief documenting what needs to be set up

## Requirements

### Validated

<!-- Shipped and confirmed in v1.0 -->

- ✓ Next.js frontend with modern, professional UI — v1.0
- ✓ Python/FastAPI backend API (separation from UI) — v1.0
- ✓ PostgreSQL database for persistent storage — v1.0
- ✓ Team authentication and user management — v1.0
- ✓ Client profile creation and management — v1.0
- ✓ Store client-specific prompts, brand guidelines, tone, and language — v1.0
- ✓ Switch between client profiles easily — v1.0
- ✓ Client profile selection persists across sessions — v1.0
- ✓ Upload raw Faire Excel files without pre-formatting — v1.0
- ✓ Automatic column detection and mapping — v1.0
- ✓ User selects which product fields feed into AI — v1.0
- ✓ Product status filtering — v1.0
- ✓ Dynamic prompt building based on available fields — v1.0
- ✓ Warn user in review if selected fields were missing — v1.0
- ✓ Progress tracking during batch generation — v1.0
- ✓ Handle missing fields gracefully — v1.0
- ✓ Three review modes: Manual, AI-assisted, AI-auto — v1.0
- ✓ Keyboard shortcuts for rapid review — v1.0
- ✓ Auto-advance to next product after approve/reject — v1.0
- ✓ Undo/redo functionality during review — v1.0
- ✓ Track rejection reasons per product — v1.0
- ✓ Store previous generation attempts — v1.0
- ✓ Include AI review feedback in regeneration context — v1.0
- ✓ Regenerate only rejected products with enhanced prompts — v1.0
- ✓ Download original Excel with updated columns — v1.0
- ✓ Preserve all other Excel columns and formatting — v1.0
- ✓ Only include approved products in output — v1.0
- ✓ Clean, modern SaaS-style dashboard — v1.0
- ✓ Robust error handling with clear user feedback — v1.0
- ✓ Admin debug mode showing AI prompts — v1.0

### Active

<!-- v2.0 Platform Deployment -->

**Auth Migration**
- [ ] Replace custom JWT auth with @madebykav/auth SDK
- [ ] Remove standalone login/signup pages (platform handles user accounts)
- [ ] All data access scoped by tenant_id from platform session
- [ ] Python backend validates requests via internal headers from Next.js

**Database Migration**
- [ ] All tables use tenant_id column for platform multi-tenancy
- [ ] Drizzle ORM schema for Next.js data access layer
- [ ] SQLAlchemy models adapted for tenant_id and shared database
- [ ] Database migration strategy from dedicated to shared PostgreSQL
- [ ] RLS policies using platform's set_config pattern

**UI Migration**
- [ ] Switch from local shadcn/ui to @madebykav/ui components
- [ ] Remove auth pages (login, signup, logout handled by platform)
- [ ] Adapt layout for platform embedding (tenant subdomain context)

**Backend Containerization**
- [ ] Production Dockerfile for FastAPI backend
- [ ] Production Dockerfile for ARQ worker
- [ ] Redis service configuration
- [ ] Docker Compose for all backend services
- [ ] Internal-only networking (not publicly exposed)

**API Proxy Layer**
- [ ] Next.js API routes forward to Python backend
- [ ] Tenant context (tenant_id, user_id) passed via internal headers
- [ ] SSE stream proxying for generation progress
- [ ] File upload proxying for Excel files

**Per-Tenant Configuration**
- [ ] OpenAI API key stored and managed per tenant
- [ ] Settings UI for tenant to configure their API key
- [ ] Python backend reads tenant's key for AI generation

**Platform Brief**
- [ ] Infrastructure requirements document for platform setup
- [ ] Docker container hosting specifications
- [ ] Internal networking between Next.js and Python services
- [ ] Environment variable configuration guide

### Out of Scope

- Multi-language content generation — English only for now
- Alternative LLM providers — OpenAI only
- Custom Excel templates beyond Faire format — Faire only
- Bulk prompt testing/A-B testing — defer to future
- Analytics dashboard — defer to future
- Real-time collaboration — single-user workflow per tenant
- Using @madebykav/ai SDK for generation — app needs LangChain structured output, direct OpenAI API access required
- Database migration tooling (automated data transfer from dev to production) — manual initial setup

## Context

**Current State:**
- Complete v1.0 app: 8 phases, 42 plans executed
- Full workflow working: upload → client management → field selection → AI generation → review → regeneration → export
- Running locally with Docker Compose (PostgreSQL, Redis, pgAdmin)
- No production deployment yet

**Target Platform:**
- MadeByKav.com — multi-tenant SaaS platform
- URL: `tenantname.madebykav.com/app/content-generator`
- Platform provides: auth (@madebykav/auth), database (@madebykav/db), UI (@madebykav/ui)
- Platform uses session-based auth (mbk_session cookie, sessions table in PostgreSQL)
- Platform passes x-tenant-id and x-app-slug headers to apps
- Auth context: { tenantId, appSlug, userId }
- Tenant isolation via PostgreSQL RLS with set_config('app.current_tenant_id', tenantId, true)

**Architecture:**
- Next.js handles all public traffic, auth, and serves as API gateway
- Python backend (FastAPI + ARQ worker) runs as internal Docker service
- Redis runs alongside Python services for job queue
- Next.js proxies requests to Python backend with tenant context headers
- Both Next.js (Drizzle) and Python (SQLAlchemy) access shared PostgreSQL

**Known Challenges:**
- Dual ORM setup: Drizzle (Next.js) + SQLAlchemy (Python) on same database
- SSE proxy through Next.js for real-time generation progress
- File upload proxy for large Excel files (10MB+)
- Replacing user_id with tenant_id across all tables and queries
- Keeping all existing functionality working through the migration

## Constraints

- **Platform**: MadeByKav.com — must use platform SDKs (@madebykav/auth, @madebykav/db, @madebykav/ui)
- **Auth**: Platform-managed sessions — no custom auth system
- **Database**: Shared platform PostgreSQL — tenant isolation via RLS
- **Backend**: Docker containers — FastAPI + ARQ + Redis as internal services
- **UI**: @madebykav/ui components — platform consistency
- **LLM Provider**: OpenAI only — direct API access via LangChain (not platform AI gateway)
- **No Functionality Loss**: Every v1.0 feature must work identically after migration

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Rebuild frontend in Next.js instead of enhancing Streamlit | Need full design control for professional UI | ✓ Good |
| Separate frontend/backend architecture | Better separation of concerns, independent deployment | ✓ Good |
| PostgreSQL for persistence | Industry standard, supports RLS for multi-tenancy | ✓ Good |
| Keep existing AI logic/prompts | Core generation logic works; optimize dynamically | ✓ Good |
| Deploy to MadeByKav platform | Existing platform infrastructure, shared services, tenant management | — Pending |
| Use @madebykav/auth instead of custom JWT | Platform handles user management, sessions, tenant isolation | — Pending |
| Python backend as internal Docker service | Can't port LangChain/openpyxl/pandas to Node.js; Next.js proxies requests | — Pending |
| Dual ORM (Drizzle + SQLAlchemy) on shared DB | Each runtime needs native ORM; Drizzle for Next.js, SQLAlchemy for Python | — Pending |
| Per-tenant OpenAI API key | Platform manages keys per-app at tenant level | — Pending |

---
*Last updated: 2026-01-30 after v2.0 milestone start*
