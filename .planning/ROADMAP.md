# Roadmap: Candid Founders Content Generator

## Overview

Transform a working Streamlit prototype into a commercial-grade SaaS platform for marketing agencies. The journey establishes modern Next.js + FastAPI architecture with multi-tenant isolation, then builds the core workflow (client management -> Excel upload -> AI generation -> review -> export) with cost controls and quality safeguards throughout. Each phase delivers a verifiable capability that moves agencies from manual product content creation to AI-powered bulk generation at scale.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation & Authentication** - Modern architecture with secure multi-tenant auth
- [x] **Phase 2: Client Management** - Client profiles with brand voice and prompt configuration
- [x] **Phase 3: Excel Processing** - Upload and map Faire Excel with variant grouping
- [x] **Phase 4: AI Generation Core** - LangChain + OpenAI with cost controls and progress tracking
- [x] **Phase 5: Review System** - Manual review workflow with keyboard shortcuts
- [x] **Phase 6: Smart Regeneration** - Learning from rejections with enhanced prompts
- [x] **Phase 7: Export & Polish** - Download approved content and final UX refinements
- [x] **Phase 8: Admin Debug Mode** - Debug window showing exact prompts sent to AI model

## Phase Details

### Phase 1: Foundation & Authentication
**Goal**: Establish production-ready architecture with secure user authentication and multi-tenant data isolation
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05
**Success Criteria** (what must be TRUE):
  1. User can sign up with email and password
  2. User can log in and remain authenticated across browser sessions
  3. User can log out from any page
  4. Authentication persists across browser refresh without re-login
  5. OpenAI API key is configured and stored securely per application instance
  6. Database enforces row-level security to prevent cross-tenant data access
**Plans**: 5 plans in 3 waves (includes 1 gap closure plan)
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
**Success Criteria** (what must be TRUE):
  1. User can create new client profile with name
  2. User can edit client profile to include brand name, story, tone, language, and guidelines
  3. User can configure AI prompts per client (system prompt, task1, task2)
  4. User can delete client profile when no longer needed
  5. User can switch between client profiles in the UI
  6. Selected client profile persists across sessions
  7. User can view list of all client profiles in their account
**Plans**: 5 plans in 2 waves
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
**Success Criteria** (what must be TRUE):
  1. User can upload Faire Excel template without manual pre-formatting
  2. App automatically detects and maps Faire columns to product fields
  3. User can select which product fields to use as AI inputs during generation
  4. User can filter which product statuses to generate content for
  5. App handles missing product fields gracefully without crashing
  6. App processes large Excel files (5,000+ products) without memory errors
  7. App detects product option variants (identical Name, Token, SKU) and groups them for single generation
  8. Grouped products display as single item in UI (not duplicated per option)
**Plans**: 5 plans in 4 waves
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
**Success Criteria** (what must be TRUE):
  1. User can generate content for 5-10,000 products per upload
  2. System builds prompts dynamically based on available product fields
  3. Generated titles meet character limits (30-60 chars) and descriptions meet limits (2000-3000 chars)
  4. System automatically retries generations that violate character limits
  5. User sees real-time progress showing X of Y products completed and current cost total
  6. System tracks OpenAI API costs per generation batch with running total displayed
  7. System handles OpenAI rate limits automatically with exponential backoff
  8. Failed generations retry automatically without user intervention
  9. Long-running generations execute in background without blocking UI
  10. User can pause generation in progress
  11. User can resume paused or interrupted generation from where it stopped
  12. System enforces $500 soft cap per batch and prompts user to explicitly continue or stop
**Plans**: 6 plans in 4 waves
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
**Success Criteria** (what must be TRUE):
  1. User can manually review each product with approve/reject/edit actions
  2. User can navigate products using keyboard shortcuts
  3. UI auto-advances to next product after approve or reject action
  4. User can choose AI-assisted review mode to get GPT-5.2 recommendations
  5. User can choose AI-auto review mode for automatic approval with optional manual review
  6. User can undo and redo review decisions during active session
  7. Review UI displays warnings when products are missing selected fields
  8. User can start reviewing completed products while generation is still running
  9. Review UI updates in real-time as new products complete generation
**Plans**: 7 plans in 3 waves (includes 1 gap closure plan)
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
**Success Criteria** (what must be TRUE):
  1. User can provide rejection reason when rejecting a product
  2. System stores previous generation attempts per product
  3. System includes AI review feedback in regeneration prompts when available
  4. User can regenerate only rejected products without re-running entire batch
**Plans**: 7 plans in 3 waves
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
**Success Criteria** (what must be TRUE):
  1. User can download original Excel file with updated Product Name and Description columns
  2. Downloaded Excel preserves all other columns and formatting from original upload
  3. Downloaded Excel only includes approved products (rejected products excluded)
  4. For grouped option variants, generated title and description are copied to all original rows
  5. Overall application has clean, modern SaaS-style dashboard interface
  6. Application provides robust error handling with clear user feedback messages
  7. Application is responsive across different screen sizes
**Plans**: 5 plans in 3 waves
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
**Success Criteria** (what must be TRUE):
  1. Admin can toggle debug mode on/off from the settings page
  2. When enabled, a debug frame appears at the bottom of the screen
  3. Debug frame shows the exact system prompt, user prompt, and model parameters sent to OpenAI for each generation
  4. Debug frame updates in real-time as products are generated
  5. Debug mode persists across page navigation within the session
  6. Debug frame is only visible to admin users
**Plans**: 2 plans in 2 waves
**Status**: Complete
**Completed**: 2026-01-29

Plans:
- [x] 08-01-PLAN.md — Backend: Debug API endpoint and frontend server action
- [x] 08-02-PLAN.md — Frontend: Debug context, collapsible panel, settings toggle, layout integration

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Authentication | 5/5 | Complete | 2026-01-22 |
| 2. Client Management | 5/5 | Complete | 2026-01-22 |
| 3. Excel Processing | 5/5 | Complete | 2026-01-22 |
| 4. AI Generation Core | 6/6 | Complete | 2026-01-23 |
| 5. Review System | 7/7 | Complete | 2026-01-29 |
| 6. Smart Regeneration | 7/7 | Complete | 2026-01-29 |
| 7. Export & Polish | 5/5 | Complete | 2026-01-29 |
| 8. Admin Debug Mode | 2/2 | Complete | 2026-01-29 |

---
*Roadmap created: 2026-01-22*
*Last updated: 2026-01-29 (Phase 8 complete — all 8 phases done)*
