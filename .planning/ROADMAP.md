# Roadmap: Candid Founders Content Generator

## Milestones

- v1.0 MVP - Phases 1-8 (shipped 2026-01-29)
- v2.0 Platform Deployment - Phases 9-14 (in progress)

## Phases

<details>
<summary>v1.0 MVP (Phases 1-8) - SHIPPED 2026-01-29</summary>

- [x] **Phase 1: Foundation & Authentication** - Modern architecture with secure multi-tenant auth
- [x] **Phase 2: Client Management** - Client profiles with brand voice and prompt configuration
- [x] **Phase 3: Excel Processing** - Upload and map Faire Excel with variant grouping
- [x] **Phase 4: AI Generation Core** - LangChain + OpenAI with cost controls and progress tracking
- [x] **Phase 5: Review System** - Manual review workflow with keyboard shortcuts
- [x] **Phase 6: Smart Regeneration** - Learning from rejections with enhanced prompts
- [x] **Phase 7: Export & Polish** - Download approved content and final UX refinements
- [x] **Phase 8: Admin Debug Mode** - Debug window showing exact prompts sent to AI model

### Phase 1: Foundation & Authentication
**Goal**: Establish production-ready architecture with secure user authentication and multi-tenant data isolation
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05
**Status**: Complete
**Completed**: 2026-01-22

Plans:
- [x] 01-01-PLAN.md — Docker + Next.js + FastAPI scaffolding
- [x] 01-02-PLAN.md — Backend: User model, migrations, auth API
- [x] 01-03-PLAN.md — Frontend: Auth pages, Server Actions, session management
- [x] 01-04-PLAN.md — Admin settings page + dev environment seeding
- [x] 01-05-PLAN.md — Gap closure: Fix frontend-backend JWT integration

### Phase 2: Client Management
**Goal**: Users can create and manage client profiles with brand-specific prompts and guidelines
**Depends on**: Phase 1
**Requirements**: CLNT-01, CLNT-02, CLNT-03, CLNT-04, CLNT-05, CLNT-06, CLNT-07
**Status**: Complete
**Completed**: 2026-01-22

Plans:
- [x] 02-01-PLAN.md — Backend: Client model, migration, CRUD API endpoints
- [x] 02-02-PLAN.md — Backend: Add default prompts to AppSettings
- [x] 02-03-PLAN.md — Frontend: Client list, create/edit pages, Server Actions
- [x] 02-04-PLAN.md — Frontend: Client selector dropdown with localStorage persistence
- [x] 02-05-PLAN.md — Frontend: Admin Prompt Settings page

### Phase 3: Excel Processing
**Goal**: Users can upload raw Faire Excel files and configure product field mapping for AI generation
**Depends on**: Phase 2
**Requirements**: EXCL-01, EXCL-02, EXCL-03, EXCL-04, EXCL-05, EXCL-06, EXCL-07, EXCL-08, EXCL-09, EXCL-10, EXCL-11, EXCL-12
**Status**: Complete
**Completed**: 2026-01-22

Plans:
- [x] 03-01-PLAN.md — Backend: Product and ProductGroup models, migration
- [x] 03-02-PLAN.md — Backend: Excel parser, column mapper, variant grouper, upload endpoint
- [x] 03-03-PLAN.md — Frontend: Upload modal with progress and Server Action
- [x] 03-04-PLAN.md — Frontend: Products list with variant grouping display
- [x] 03-05-PLAN.md — Field selection panel persisted per client

### Phase 4: AI Generation Core
**Goal**: Users can generate optimized product titles and descriptions at scale with real-time cost and progress tracking
**Depends on**: Phase 3
**Requirements**: GEN-01, GEN-02, GEN-03, GEN-04, GEN-05, GEN-06, GEN-07, GEN-08, GEN-09, GEN-10, GEN-11, GEN-12, GEN-14, GEN-15
**Status**: Complete
**Completed**: 2026-01-23

Plans:
- [x] 04-01-PLAN.md — Backend: Dependencies, GenerationJob/Audit models, migration
- [x] 04-02-PLAN.md — Backend: LangChain AI service, cost tracker, structured output
- [x] 04-03-PLAN.md — Backend: ARQ worker setup, job manager, Redis integration
- [x] 04-04-PLAN.md — Backend: Generation API endpoints with SSE progress streaming
- [x] 04-05-PLAN.md — Frontend: Generate button, progress UI, soft cap dialog
- [x] 04-06-PLAN.md — Admin: Generation settings (model, temperature, soft cap)

### Phase 5: Review System
**Goal**: Users can efficiently review generated content with keyboard-driven workflow
**Depends on**: Phase 4
**Requirements**: REV-01, REV-02, REV-03, REV-04, REV-05, REV-06, REV-07, REV-08, REV-09
**Status**: Complete
**Completed**: 2026-01-29

Plans:
- [x] 05-01-PLAN.md — Backend: Review model fields, ReviewJob model, review API endpoints
- [x] 05-02-PLAN.md — Frontend: Dependencies, Server Actions, undo/redo context
- [x] 05-03-PLAN.md — Frontend: Review UI with keyboard navigation and image display
- [x] 05-04-PLAN.md — Backend: AI review service and batch review worker
- [x] 05-05-PLAN.md — Frontend: AI review panel and batch progress UI
- [x] 05-06-PLAN.md — Frontend: Missing fields warning and real-time updates
- [x] 05-07-PLAN.md — Gap closure: Wire undo to backend and add redo functionality

### Phase 6: Smart Regeneration
**Goal**: Users can regenerate rejected products with enhanced prompts that learn from rejection feedback
**Depends on**: Phase 5
**Requirements**: REGEN-01, REGEN-02, REGEN-03, REGEN-04
**Status**: Complete
**Completed**: 2026-01-29

Plans:
- [x] 06-01-PLAN.md — Backend: Extend ProductGroup model with rejection_reasons and regeneration_count fields
- [x] 06-02-PLAN.md — Frontend: Rejection reasons dialog and rejectWithReasons server action
- [x] 06-03-PLAN.md — Backend: Enhanced prompts with RegenerationContext support
- [x] 06-04-PLAN.md — Backend: Generation history and restore endpoints
- [x] 06-05-PLAN.md — Backend: Single and batch regeneration endpoints with worker integration
- [x] 06-06-PLAN.md — Frontend: History dialog, regenerate button, restore functionality
- [x] 06-07-PLAN.md — Frontend: Batch regenerate button on products and review pages

### Phase 7: Export & Polish
**Goal**: Users can download approved content in original Excel format with all columns preserved
**Depends on**: Phase 6
**Requirements**: EXP-01, EXP-02, EXP-03
**Status**: Complete
**Completed**: 2026-01-29

Plans:
- [x] 07-01-PLAN.md — Backend: Migration, ExcelExporter service, export API endpoints
- [x] 07-02-PLAN.md — Frontend: Sonner toasts, Skeleton components, error boundaries, loading pages
- [x] 07-03-PLAN.md — Frontend: Export button, confirmation dialog, file download
- [x] 07-04-PLAN.md — Frontend: Dashboard redesign with guided empty state and CSS polish
- [x] 07-05-PLAN.md — Checkpoint: End-to-end verification of export and polish

### Phase 8: Admin Debug Mode
**Goal**: Admin can enable a debug mode that shows the exact prompts and payloads sent to the AI model in a persistent bottom frame
**Depends on**: Phase 7
**Requirements**: None (developer/admin tooling)
**Status**: Complete
**Completed**: 2026-01-29

Plans:
- [x] 08-01-PLAN.md — Backend: Debug API endpoint and frontend server action
- [x] 08-02-PLAN.md — Frontend: Debug context, collapsible panel, settings toggle, layout integration

</details>

## v2.0 Platform Deployment (In Progress)

**Milestone Goal:** Deploy the Content Generator to the MadeByKav platform without losing any functionality or reliability, using platform SDKs for auth, database, and UI.

**Phase Numbering:**
- Integer phases (9, 10, ...): Planned milestone work
- Decimal phases (9.1, 9.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 9: Platform Brief & Containerization** - Infrastructure docs and production Docker setup
- [ ] **Phase 10: Database Migration** - Tenant isolation with dual ORM on shared PostgreSQL
- [ ] **Phase 11: Auth & UI Migration** - Platform SDK auth and UI component swap
- [ ] **Phase 12: API Proxy Layer** - Next.js gateway proxying to internal Python backend
- [ ] **Phase 13: Per-Tenant Configuration** - Tenant-scoped OpenAI API keys and settings
- [ ] **Phase 14: Integration Verification** - End-to-end platform deployment validation

## Phase Details

### Phase 9: Platform Brief & Containerization
**Goal**: Platform operator has a complete infrastructure specification and production-ready Docker containers for all backend services
**Depends on**: Phase 8 (v1.0 complete)
**Requirements**: BRIEF-01, BRIEF-02, BRIEF-03, BRIEF-04, DOCK-01, DOCK-02, DOCK-03, DOCK-04, DOCK-05, DOCK-06
**Success Criteria** (what must be TRUE):
  1. A document exists that tells the platform operator exactly what services to provision, what ports to open, what volumes to mount, and what environment variables to set -- without needing to read any source code
  2. Running `docker compose up` starts FastAPI, ARQ worker, and Redis as healthy containers on an internal-only network
  3. Each container responds to a health check endpoint that container orchestration tools can poll
  4. Backend services are not reachable from the public internet (internal network only)
**Status**: Complete
**Completed**: 2026-01-30

Plans:
- [x] 09-01-PLAN.md -- Dockerfile + .dockerignore (multi-stage build, non-root user)
- [x] 09-02-PLAN.md -- Health check endpoints (liveness + readiness)
- [x] 09-03-PLAN.md -- Docker Compose profiles + GitHub Actions CI
- [x] 09-04-PLAN.md -- Platform infrastructure brief + entrypoint script

### Phase 10: Database Migration
**Goal**: All application data is tenant-isolated on a shared PostgreSQL database with both Drizzle and SQLAlchemy accessing the same schema
**Depends on**: Phase 9
**Requirements**: DB-01, DB-02, DB-03, DB-04, DB-05, DB-06, DB-07, DB-08
**Success Criteria** (what must be TRUE):
  1. Every app table has a tenant_id column and a table name prefixed with the app slug, so multiple apps share the database without collisions
  2. Drizzle ORM schema exists and can query all tables from Next.js server components and API routes using a withTenant() wrapper
  3. SQLAlchemy models use tenant_id (not user_id) and all queries go through set_config() RLS enforcement
  4. Running Alembic migrations on the shared database creates/updates all tables with RLS policies applied -- no manual SQL needed
  5. A query from tenant A cannot return data belonging to tenant B (RLS enforced at the database level)
**Plans**: TBD

### Phase 11: Auth & UI Migration
**Goal**: The app authenticates through the MadeByKav platform and uses platform UI components with no standalone auth pages
**Depends on**: Phase 10
**Requirements**: AUTH2-01, AUTH2-02, AUTH2-03, AUTH2-04, AUTH2-05, AUTH2-06, UI-01, UI-02, UI-03, UI-04
**Success Criteria** (what must be TRUE):
  1. Server components use getAuthContext() and API routes use requireAuth() from @madebykav/auth -- no custom JWT or session logic remains
  2. Visiting the app without a valid session redirects to the platform login page (not an in-app login page)
  3. All login, signup, and logout pages are removed from the app codebase
  4. All UI components render from @madebykav/ui -- no local shadcn/ui copies remain
  5. The app loads correctly at tenantname.madebykav.com/app/content-generator with platform header and navigation
**Plans**: TBD

### Phase 12: API Proxy Layer
**Goal**: The Next.js frontend seamlessly forwards all API requests to the internal Python backend with tenant context, including SSE streams and file uploads
**Depends on**: Phase 11
**Requirements**: PROXY-01, PROXY-02, PROXY-03, PROXY-04
**Success Criteria** (what must be TRUE):
  1. Frontend API calls go through Next.js API routes that inject x-tenant-id and x-user-id headers before forwarding to the Python backend
  2. SSE progress streams during AI generation flow from Python through Next.js to the browser without dropping events or stalling
  3. Uploading a 10MB Excel file through the proxy completes successfully and reaches the Python backend
  4. When the Python backend returns an error (4xx or 5xx), the frontend displays the correct error message to the user
**Plans**: TBD

### Phase 13: Per-Tenant Configuration
**Goal**: Each tenant manages their own OpenAI API key and the app gracefully handles tenants who have not yet configured one
**Depends on**: Phase 12
**Requirements**: CFG-01, CFG-02, CFG-03, CFG-04
**Success Criteria** (what must be TRUE):
  1. A settings page exists where the tenant can enter, update, and verify their OpenAI API key
  2. The Python backend uses the tenant's stored API key (not a global env var) when running AI generation
  3. A tenant without a configured API key sees a setup prompt and cannot start generation until a key is provided
**Plans**: TBD

### Phase 14: Integration Verification
**Goal**: The fully migrated app works end-to-end on the MadeByKav platform with no regressions from v1.0 functionality
**Depends on**: Phase 13
**Requirements**: (verification phase -- validates all v2.0 requirements together)
**Success Criteria** (what must be TRUE):
  1. A new tenant can access the app, configure their API key, create a client, upload an Excel file, generate content, review it, and export -- the complete v1.0 workflow works on the platform
  2. Two different tenants logged in simultaneously cannot see each other's clients, products, or generated content
  3. Stopping and restarting Docker containers does not lose any data or break in-progress generation jobs
  4. The debug panel from Phase 8 still works within the platform-embedded layout
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 9 -> 10 -> 11 -> 12 -> 13 -> 14

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation & Authentication | v1.0 | 5/5 | Complete | 2026-01-22 |
| 2. Client Management | v1.0 | 5/5 | Complete | 2026-01-22 |
| 3. Excel Processing | v1.0 | 5/5 | Complete | 2026-01-22 |
| 4. AI Generation Core | v1.0 | 6/6 | Complete | 2026-01-23 |
| 5. Review System | v1.0 | 7/7 | Complete | 2026-01-29 |
| 6. Smart Regeneration | v1.0 | 7/7 | Complete | 2026-01-29 |
| 7. Export & Polish | v1.0 | 5/5 | Complete | 2026-01-29 |
| 8. Admin Debug Mode | v1.0 | 2/2 | Complete | 2026-01-29 |
| 9. Platform Brief & Containerization | v2.0 | 4/4 | Complete | 2026-01-30 |
| 10. Database Migration | v2.0 | 0/TBD | Not started | - |
| 11. Auth & UI Migration | v2.0 | 0/TBD | Not started | - |
| 12. API Proxy Layer | v2.0 | 0/TBD | Not started | - |
| 13. Per-Tenant Configuration | v2.0 | 0/TBD | Not started | - |
| 14. Integration Verification | v2.0 | 0/TBD | Not started | - |

---
*Roadmap created: 2026-01-22*
*Last updated: 2026-01-30 (Phase 9 complete)*
