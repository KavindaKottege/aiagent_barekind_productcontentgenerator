# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-22)

**Core value:** Generate professional, on-brand product content at scale with minimal friction - agencies can confidently use this with clients without worrying about workflow bottlenecks or unprofessional UX
**Current focus:** ALL PHASES COMPLETE — v1 milestone ready for audit

## Current Position

Phase: 7 of 7 (Export & Polish) - COMPLETE
Plan: 5 of 5 (07-05 E2E verification checkpoint passed)
Status: All 7 phases complete — 40 plans executed
Last activity: 2026-01-29 — Phase 7 complete, export verified by user

Progress: [██████████] 100% (40 of 40 plans complete)

## Performance Metrics

**Velocity:**
- Total plans completed: 26
- Average duration: 3.4 minutes
- Total execution time: ~1.6 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 5 | 20 min | 4 min |
| 02 | 5 | 22 min | 4.4 min |
| 03 | 5 | 17 min | 3.4 min |
| 04 | 6 | 20.9 min | 3.5 min |
| 05 | 6 | ~31 min | ~5.2 min |

**Recent Trend:**
- 05-01 completed in 4.9 minutes
- 05-02 completed in 2 minutes
- 05-03 completed in TBD minutes
- 05-04 completed in 5 minutes
- 05-05 completed in 4 minutes
- 05-06 completed in ~15 minutes (with checkpoint)
- 05-07 completed in 2 minutes (gap closure)
- Trend: Phase 5 complete in 7 plans (including gap closure)

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Rebuild frontend in Next.js instead of enhancing Streamlit for full design control and professional UI
- Separate frontend/backend architecture for better separation of concerns and scalability
- PostgreSQL for persistence with industry standard support for complex queries
- Keep existing AI logic/prompts and optimize dynamically rather than rebuild from scratch
- Team-only auth for v1 to simplify scope (client access deferred to future)

**From 01-01 execution:**
- Use port 5433 for PostgreSQL (5432 occupied by other project)
- Async-only SQLAlchemy (no sync fallback)
- Pydantic Settings for centralized configuration
- expire_on_commit=False for async SQLAlchemy sessions

**From 01-02 execution:**
- Use Argon2 for password hashing (more secure than bcrypt)
- Implement Row-Level Security at database layer for defense-in-depth
- First user automatically becomes admin (simplifies initial setup)
- JWT tokens with 7-day expiration (balances security and UX)
- OAuth2 password flow for standard authentication pattern
- Two RLS policies: user_isolation_policy + user_signup_policy for auth-less signup

**From 01-03 execution:**
- Use jose library for JWT operations (Next.js compatible, ESM-native)
- Server Actions with useActionState pattern for form handling
- React cache() for Data Access Layer request deduplication
- 7-day session cookie expiration with httpOnly and sameSite=lax
- OAuth2PasswordRequestForm format for login (username field = email)
- Optimistic middleware + Server Component verification pattern

**From 01-04 execution:**
- Singleton pattern for app_settings table (single row with id=1)
- Public endpoint for has-api-key check (enables frontend setup flow)
- API key stored plaintext for v1 (encryption deferred to future)
- Idempotent seed script that skips existing data
- getAdmin() DAL function redirects non-admins to dashboard with error

**From 01-05 execution:**
- Dual-cookie architecture: session cookie for frontend userId lookup, access_token cookie for backend API authorization
- Decode JWT without verification in auth actions (safe since just received from trusted backend)
- Both cookies use identical security settings (httpOnly, secure in prod, sameSite lax, 7 days)
- DAL uses getAccessToken() to send backend JWT in Authorization header

**From 02-01 execution:**
- Migration 004 for clients table (003 already existed for default prompts)
- Computed has_custom_prompts field pattern using from_orm_with_computed() classmethod
- Users can create/read/update clients but only admins can delete
- User-scoped queries pattern for data isolation in multi-tenant setup

**From 02-03 execution:**
- Two-tab form pattern for separating primary and advanced fields (Tabs component)
- Admin-only delete with AlertDialog confirmation prevents accidental deletion
- Badge indicators for visual quick-scan (custom prompts badge)
- Empty state with CTA button for first-time user experience
- Grid layout pattern: responsive 1/2/3 columns for entity lists

**From 02-04 execution:**
- React Context for global client state management
- ClientProvider wraps dashboard layout for shared context
- ClientSelector dropdown in header for quick client switching
- "All Clients" option for admin multi-client view

**From 02-05 execution:**
- Radix UI collapsible for expandable info sections
- Domain-specific prompt examples for product content generation
- Monospace font for prompt textareas (better for code-like text)
- Empty strings converted to null for clearing prompts

**From 03-01 execution:**
- JSONB unmapped_data column pattern preserves unmapped Excel columns for export
- ProductGroup model for variant grouping with generated content fields
- Images stored as JSONB array (PostgreSQL ARRAY type)
- Unique constraint on (client_id, product_name, product_token, sku) prevents duplicate groups
- Row_index field preserves original Excel ordering for export
- Composite index pattern (client_id, row_index) for export ordering

**From 03-02 execution:**
- Streaming Excel parser with 500-row batches for memory efficiency on large files
- 75% fuzzy match threshold for column mapping (balance flexibility and accuracy)
- Idempotent upload pattern: replace existing products for client on re-upload
- Formula injection sanitization by prefixing =, +, -, @ with apostrophe (OWASP CSV Injection prevention)
- Mapping confidence score (HIGH/MEDIUM/LOW) returned to frontend for user awareness
- Service class pattern: separate concerns into ExcelParser, FuzzyColumnMapper, VariantGrouper
- Bulk insert pattern with two-phase insert: groups first (for FK), then products

**From 03-03 execution:**
- Modal dialog pattern for non-disruptive upload workflow (stay on dashboard)
- 10MB Server Action body size limit for large Excel files
- Client validation blocks upload when no client selected
- Drag-and-drop file upload with useTransition for progress indication
- 1.5 second success delay shows stats before auto-redirect
- FormData forwarding pattern: Next.js Server Action → FastAPI backend
- Upload success displays total rows, product groups, variant groups, mapping confidence

**From 03-04 execution:**
- API route layer for client component data fetching (bypasses Server Action limitations)
- Status filter with 5 options: all, pending, generated, approved, rejected
- Lazy-loading variants only on expand to reduce initial page load
- URL sync pattern keeps selected client in URL params for shareability
- ProductGroupCard collapsible UI pattern with lazy-loaded variant details
- Status filter UI with count badges for each status

**From 03-05 execution:**
- JSONB column ai_input_fields stores list of field names for AI input
- Default value None means use all available fields (explicit opt-in pattern)
- Required fields pattern: product_name cannot be deselected for quality
- 8 available fields: product_name (required), description, product_type, option_name, country_of_origin, made_to_order, sku, images
- Field selection panel only shows when products exist for client
- Parallel data fetching: products and client data fetched together
- Prepares for Phase 5 (Review System) to detect missing selected fields in uploaded data

**From 04-01 execution:**
- Use ARQ for background job processing (native asyncio, 7x faster than Celery for short jobs)
- Decimal precision for cost tracking (Numeric 10,4 for job totals, 10,6 for per-product audit)
- Full audit trail pattern: track every generation attempt including retries
- Job status state machine: pending → running → paused/completed/failed/cancelled
- GenerationJob model tracks job status, progress counts, cost tracking
- GenerationAudit model stores per-product generation attempts with full audit trail
- Phase 4 dependencies installed: LangChain, OpenAI, ARQ, tiktoken, tenacity, sse-starlette
- Migration 007 creates generation tables with proper indexes

**From 04-02 execution:**
- LangChain with_structured_output(strict=True) guarantees JSON format via OpenAI function calling
- Tiktoken with o200k_base fallback for GPT-5.2 token counting (handles model evolution)
- ProductContent Pydantic schema validates character limits (30-60 title, 2000-3000 description)
- CostTracker uses tiktoken for accurate token counting and cost calculation
- 3 retries max (4 total attempts) for character limit violations
- Retry prompts inject previous error message for explicit correction
- Dynamic prompt building: client.ai_input_fields → brand context → prompts (client > app settings > defaults)
- AIGenerationService creates full audit trail for every generation attempt (success or failure)

**From 04-03 execution:**
- Redis 7-alpine service added to Docker Compose for ARQ job queue
- ARQ WorkerSettings with startup/shutdown hooks for database connection pooling
- generation_worker checks job status before each product for responsive pause/cancel
- Resume-as-new-job pattern preserves full audit trail for each pause/resume cycle
- Soft cap detection pauses job automatically, requires user acknowledgment to continue
- JobManager service handles job creation, enqueueing, and lifecycle operations
- Worker has separate database connection pool (pool_size=5, independent of FastAPI app)
- Progress calculation includes elapsed time, estimated remaining, projected cost

**From 04-04 execution:**
- POST /start blocks if active job exists for client (prevents concurrent generation)
- SSE progress endpoint polls every 500ms for responsive UI updates
- Resume creates new job (preserves audit trail, worker skips 'generated' products)
- Global /api prefix standardized for all routers
- Lifespan context manager for proper database connection cleanup
- SSE pattern: separate session per event generator for long-lived connections
- EventSourceResponse with asyncio.sleep(0.5) polling pattern

**From 04-05 execution:**
- SSE authentication via query param token (EventSource doesn't support headers)
- Check for active job on mount and client changes for persistence
- Hide field selection panel during active generation to prevent conflicts
- Show generated badge in stats header for visibility
- EventSource pattern for SSE with progress/soft_cap/complete events
- Optimistic job state management with server sync on mount
- Completion callback pattern refreshes server data

**From 04-06 execution:**
- ai_temperature stored as Numeric(3,2) for 0.00-1.00 with 0.01 precision
- generation_soft_cap stored as Numeric(10,2) for dollar amounts with cent precision
- Generation settings GET endpoint requires authentication (any user), PATCH requires admin
- Temperature UI uses dual input: slider for quick adjustment, number input for precise control
- Default soft cap $500.00 prevents runaway costs while allowing large batches
- Settings domain separation: /api/settings/generation for generation-specific settings
- Cost estimation guidance provided inline for administrator context

**From 06-06 execution:**
- ScrollArea shadcn component added for generation history dialog scrolling
- History button always visible in review header (view history regardless of status)
- Regenerate button conditionally visible only for rejected products
- On regeneration start, navigate to products page for SSE progress view
- On history restore, router.refresh() reloads page to show restored content
- Fetch-on-open dialog pattern: useEffect fetches data when dialog open=true
- Server actions pattern follows review.ts for auth token handling

### Pending Todos

None yet.

### Blockers/Concerns

None - Phase 7 in progress. Toast, error boundaries, loading skeletons, frontend export UI, and dashboard redesign complete.

### Next Phase Readiness

**Phase 1 COMPLETE AND VERIFIED ✓**
- ✅ User can sign up with email and password
- ✅ User can log in and remain authenticated across browser sessions
- ✅ User can log out from any page
- ✅ Authentication persists across browser refresh without re-login
- ✅ OpenAI API key is configured and stored securely per application instance
- ✅ Database enforces row-level security to prevent cross-tenant data access
- Verification: 6/6 success criteria passed (100%)
- Dev environment fully automated with seed script
- Dual-cookie architecture working correctly

**Phase 2 (Client Management) COMPLETE AND VERIFIED ✓**
- ✅ User can create new client profile with name
- ✅ User can edit client profile to include brand name, story, tone, language, and guidelines
- ✅ User can configure AI prompts per client (system prompt, task1, task2)
- ✅ User can delete client profile when no longer needed
- ✅ User can switch between client profiles in the UI
- ✅ Selected client profile persists across sessions
- ✅ User can view list of all client profiles in their account
- Verification: 7/7 success criteria passed (100%)
- Full client management system with CRUD operations
- Client selector with persistent localStorage state
- Admin prompt configuration with collapsible examples

**Phase 3 (Excel Processing) COMPLETE AND VERIFIED ✓**
- ✅ User can upload Faire Excel template without manual pre-formatting
- ✅ App automatically detects and maps Faire columns to product fields
- ✅ User can select which product fields to use as AI inputs during generation
- ✅ User can filter which product statuses to generate content for
- ✅ App handles missing product fields gracefully without crashing
- ✅ App processes large Excel files (5,000+ products) without memory errors
- ✅ App detects product option variants (identical Name, Token, SKU) and groups them for single generation
- ✅ Grouped products display as single item in UI (not duplicated per option)
- Verification: 8/8 success criteria passed (100%)
- Streaming Excel parser (500-row batches, openpyxl read_only mode)
- Fuzzy column mapper (75% threshold, RapidFuzz)
- Variant grouper (pandas groupby on Name/Token/SKU)
- Upload modal with drag-drop, client validation, success stats
- Products list with expand/collapse, status filter, lazy-loaded variants
- AI input field selection persists per client (8 configurable fields)
- 9 of 12 EXCL requirements complete (3 deferred to later phases)

**Phase 4 (AI Generation Core) COMPLETE AND VERIFIED ✓**
- ✅ User can generate content for 5-10,000 products per upload
- ✅ System builds prompts dynamically based on available product fields
- ✅ Generated titles meet character limits (30-60 chars) and descriptions meet limits (2000-3000 chars)
- ✅ System automatically retries generations that violate character limits
- ✅ User sees real-time progress showing X of Y products completed and current cost total
- ✅ System tracks OpenAI API costs per generation batch with running total displayed
- ✅ System handles OpenAI rate limits automatically with exponential backoff
- ✅ Failed generations retry automatically without user intervention
- ✅ Long-running generations execute in background without blocking UI
- ✅ User can pause generation in progress
- ✅ User can resume paused or interrupted generation from where it stopped
- ✅ System enforces $500 soft cap per batch and prompts user to explicitly continue or stop
- Verification: 12/12 success criteria passed (100%)
- LangChain integration with structured output validation
- ARQ worker with Redis for background job processing
- Real-time SSE progress streaming every 500ms
- Tiktoken integration for accurate cost tracking
- Full audit trail with GenerationAudit model
- Admin-configurable settings (model, temperature, soft cap)

**Phase 4 Implementation Details:**
- ✅ Plan 04-01 complete: Dependencies and models foundation
- ✅ LangChain, OpenAI, ARQ, tiktoken, tenacity, sse-starlette installed
- ✅ GenerationJob and GenerationAudit models created
- ✅ Database migration 007 applied successfully
- ✅ Pydantic schemas ready for generation API
- ✅ Plan 04-02 complete: AI Generation Service Layer
- ✅ ProductContent schema with character limit validation (30-60 title, 2000-3000 description)
- ✅ CostTracker service with tiktoken integration for accurate token counting
- ✅ AIGenerationService with LangChain, dynamic prompt building, retry logic
- ✅ Plan 04-03 complete: ARQ worker infrastructure and job management
- ✅ Redis service running on port 6379 for ARQ job queue
- ✅ ARQ worker with generation_worker function for background processing
- ✅ Worker supports pause/cancel/resume with check-before-each-product pattern
- ✅ Soft cap detection pauses job automatically at $500 threshold
- ✅ JobManager service handles job creation, enqueueing, lifecycle operations
- ✅ Plan 04-04 complete: Generation API Endpoints
- ✅ 8 REST endpoints for job lifecycle (start, status, pause, cancel, resume, soft-cap, active-check)
- ✅ Server-Sent Events (SSE) streaming for real-time progress (500ms polling)
- ✅ Active job blocking prevents concurrent generation per client
- ✅ Global /api prefix standardized across all routers
- ✅ Plan 04-05 complete: Generation UI Frontend
- ✅ Generate button triggers generation for pending products
- ✅ Real-time progress UI with SSE (products, cost, ETA, success/failed)
- ✅ Pause/Cancel/Resume controls for user control
- ✅ Soft cap dialog prompts at $500 limit with continue/stop decision
- ✅ Active job persistence across page navigation
- ✅ Plan 04-06 complete: Generation Settings UI
- ✅ Admin settings page for AI model, temperature, cost soft cap configuration
- ✅ Migration 008 adds generation settings to app_settings table
- ✅ GET/PATCH /api/settings/generation endpoints for settings management
- ✅ GenerationSettingsForm with model dropdown, temperature slider, soft cap input
- ✅ Cost estimation guidance for administrators
- Phase 4 complete: Full AI generation system with UI, background processing, and admin controls
- ✅ Dual input pattern (slider + number) for temperature control
- Phase complete - ready for Phase 5 (Review System)

**Phase 5 (Review System) COMPLETE AND VERIFIED ✓**
- ✅ User can review generated content product-by-product
- ✅ User can approve/reject products with keyboard shortcuts (A/R)
- ✅ User can edit generated title/description inline
- ✅ User can undo/redo review actions during session
- ✅ AI-assisted review provides recommendations (single product or batch)
- ✅ AI-auto review mode for automatic approval workflow
- ✅ User sees real-time progress during batch AI review
- ✅ Missing fields warning alerts users to data quality issues
- ✅ Review list updates in real-time during generation
- Verification: 9/9 success criteria passed (100%)
- Migration 009 adds review fields to product_groups table
- ReviewJob model for tracking batch AI review jobs
- 8 Server Actions for review operations (approve, reject, edit, undo, stats, etc.)
- React Context for undo/redo history management
- react-hotkeys-hook and yet-another-react-lightbox dependencies installed

**From 05-01 execution:**
- Separate edited content fields (edited_title, edited_description) preserve original generated content
- Dual review status pattern: review_status (manual) and ai_review_status (AI recommendations)
- JSONB array for ai_review_safety_flags enables flexible safety concern tracking
- Character limit validation in Pydantic (30-60 title, 2000-3000 description) matches Phase 4 constraints
- Edit workflow requires explicit approval after editing (sets review_status='edited')
- Auto-advance pattern returns next_product_id after approve/reject for smooth workflow
- ReviewJob model follows GenerationJob pattern for batch AI review tracking

**From 05-02 execution:**
- Server Actions follow products.ts pattern for auth token handling
- Client-side character limit validation (30-60 title, 2000-3000 description)
- Session-only undo/redo history (clears on page refresh, simpler than persistent)
- Clear redo stack when new action recorded (standard undo/redo behavior)

**From 05-04 execution:**
- Temperature 0.3 for AI review (lower than generation 0.7) for more consistent evaluation
- Dual-mode AI review: AI-auto mode sets review_status directly, AI-assisted mode only sets ai_review_status
- Single product review is always AI-assisted mode (recommendations only)
- Resume can change auto_approve mode (flexibility for workflow adjustment)
- Safety checks in AI review prompts: quantity confusion, misleading expectations, misrepresentation

**From 05-05 execution:**
- AI-assisted mode is default for batch review (safer, prevents accidental auto-approvals)
- Single product review always AI-assisted (on-demand recommendations, never auto-approve)
- Auto-approved products show purple badge to distinguish from manual approvals
- User can override AI decisions at any time (maintain user control)
- Mode can change on resume for workflow flexibility
- Client wrapper pattern for server component with client-side state management
- SSE progress tracking for real-time batch AI review updates

**From 05-06 execution:**
- SSE proxy through Next.js API route for clean frontend EventSource consumption
- 2-second debounce for product list refresh to avoid API spam during generation
- Field checker function pattern for flexible missing field detection
- Collapsible warning banner for data quality awareness
- MissingFieldsWarning component alerts users when products lack selected AI input fields

**From 05-07 execution (gap closure):**
- Undo calls undoReview server action BEFORE navigating to persist status revert
- Redo re-applies undone action by calling approveProduct/rejectProduct
- Error recovery re-records action if undo fails to restore undo capability
- Ctrl+Shift+Z / Cmd+Shift+Z keyboard shortcut for redo

**From 06-01 execution:**
- JSONB rejection_reasons field on ProductGroup for structured rejection feedback
- regeneration_count integer field tracks regeneration cycles (starts at 0)
- Migration 022 adds both fields with index on regeneration_count
- RejectionReasonType Literal validates 4 predefined reasons: off_brand_tone, generic_boring, factually_wrong, seo_issues
- RejectWithReasonsRequest uses UUID product_group_id (fixed from plan's str type for consistency)
- POST /api/review/reject-with-reasons endpoint stores reasons as JSONB array
- Predefined rejection reasons only (no free text) per CONTEXT.md decision

**From 06-03 execution:**
- RegenerationContext Pydantic model carries previous_title, previous_description, rejection_reasons, ai_review_flags, regeneration_count
- REASON_TO_POSITIVE_GUIDANCE static mapping converts rejection reasons to constructive focus areas
- get_positive_guidance() helper returns comma-separated positive guidance string
- _build_feedback_section() builds multi-line feedback with negative (DO NOT REUSE) + positive (FOCUS ON) guidance
- Feedback only injected when regeneration_count > 0 (initial generation unaffected)
- Previous description truncated at 500 chars in feedback to prevent token explosion
- build_title_prompt, build_description_prompt, generate_title, generate_description all accept regeneration_context

**From 06-04 execution:**
- GET /api/regeneration/{product_group_id}/history returns successful generation audits
- POST /api/regeneration/{product_group_id}/restore/{audit_id} restores previous version
- is_current flag compares audit content to effective current content (edited or generated)
- Restore clears edited fields and resets review_status to None (pending re-review)
- Rejection reasons preserved on restore for context
- Regeneration router registered at /api/regeneration prefix in main.py

**From 06-05 execution:**
- RegenerateSingleRequest/RegenerateBatchRequest use UUID types for consistency
- RegenerationJobResponse includes is_regeneration flag for frontend differentiation
- RegenerationEstimate provides rejected_count and estimated_cost (~$0.02/product)
- POST /api/regeneration/regenerate-single creates single-product job with target_product_group_id
- POST /api/regeneration/{client_id}/regenerate-rejected creates batch job for all rejected products
- GET /api/regeneration/{client_id}/estimate returns cost estimate for batch regeneration
- Endpoints clear edited content on regeneration (restorable via 06-04 history/restore)
- Endpoints increment regeneration_count for feedback-enhanced prompts
- Worker builds RegenerationContext when regeneration_count > 0
- Worker passes regeneration_context to generate_title and generate_description
- Full pipeline: endpoint resets product -> ARQ job -> worker detects regen -> builds context -> AI service injects feedback

**From 06-07 execution:**
- BatchRegenerateButton shared component used on both products and review pages
- Estimate fetched lazily on dialog open (not on page mount) to minimize API calls
- Button hidden when no rejected products exist (conditional visibility pattern)
- History endpoint groups by job_id to handle split title/description audit records
- History dialog UX: compact rows with version numbering (v1=oldest), collapsible older versions, fixed 70vh modal with scroll
- Native overflow-y-auto preferred over ScrollArea for dialog scroll to avoid shadcn grid conflicts

**Phase 6 (Smart Regeneration) COMPLETE AND VERIFIED ✓**
- ✅ User can reject products with structured feedback reasons (checkboxes)
- ✅ System uses rejection feedback to improve regenerated content
- ✅ User can view generation history for any product
- ✅ User can restore previous versions from history
- ✅ User can regenerate a single rejected product
- ✅ User can batch regenerate all rejected products
- ✅ Batch regeneration shows count and estimated cost before confirmation
- ✅ Regenerated content is different from rejected version (feedback-enhanced)
- Verification: All success criteria passed via human-verify checkpoint
- 7 plans: rejection feedback, prompt enhancement, history/restore endpoints, regeneration endpoints, frontend UI, batch UI
- Full feedback loop: reject with reasons -> view history -> restore -> regenerate single/batch -> improved content

**Phase 7 (Export & Polish) IN PROGRESS**
- ✅ 07-01: Backend export system (migration, ExcelExporter, stats+download endpoints)
- ✅ 07-02: Sonner toast system, error boundaries (3 levels), skeleton loading pages (4 pages)
- ✅ 07-03: Frontend export UI (export button in header, confirmation dialog, client-side download)
- ✅ 07-04: Dashboard redesign with guided empty state + CSS transitions

**From 07-01 execution:**
- Migration 023 adds excel_column_order JSONB column to clients table
- Upload endpoint persists original Excel header order on client.excel_column_order
- ExcelExporter service reconstructs Excel with original column order and updated content
- REVERSE_MAP pattern: Excel header name -> field name from ExactColumnMapper.COLUMN_MAP
- Export router: GET /api/export/{client_id}/stats for dialog, GET /api/export/{client_id} for download
- Content substitution: approved/edited products use generated content; rejected/non-generated keep originals
- Variant rows inherit generated content from ProductGroup (same group = same content)
- include_pending query param controls whether pending-review products also get updated content
- Column order fallback: derive from COLUMN_MAP values + unmapped_data keys when excel_column_order not stored
- group_status key pattern avoids collision between Product.status and ProductGroup.status

**From 07-02 execution:**
- Sonner toast globally available via `import { toast } from 'sonner'`
- Toaster rendered in root layout with richColors and bottom-right position
- 3-level error boundary hierarchy: global-error.tsx (replaces root layout), error.tsx (root), (dashboard)/error.tsx (keeps header)
- 4 skeleton loading pages: products, review, clients, dashboard
- next-themes installed as Sonner dependency
- Error boundaries use 'use client' directive with reset() function for recovery
- Skeleton pages use Skeleton + Card components with space-y-6 wrapper pattern

**From 07-03 execution:**
- ExportButton in dashboard header next to UploadButtonWrapper
- Token passing pattern: getExportToken() server action returns access_token for client-side fetch to FastAPI download endpoint
- AlertDialog for export confirmation workflow (matches existing codebase patterns)
- Fetch + blob + createObjectURL + anchor click pattern for .xlsx file download
- Skeleton loading state in dialog while fetching export stats
- Warning state with link to review page when no approved products to export
- Local TooltipProvider wrapping (follows generation-progress.tsx pattern)

**From 07-04 execution:**
- New user detection via clients.length === 0 for guided onboarding
- 3-step onboarding: Create Client (active CTA), Upload Products (muted), Generate Content (muted)
- Returning user quick-action cards: Products, Review, Clients, Settings (admin only)
- card-hover CSS class for reusable hover lift effect (shadow + translateY)
- animate-fade-in CSS class for page entrance animation (opacity + translateY)
- 150ms smooth transitions on all buttons, links, role=button elements
- skeleton-pulse CSS class for consistent 1.5s loading animation timing

## Session Continuity

Last session: 2026-01-29 (current)
Stopped at: Completed 07-03-PLAN.md (frontend export UI)
Resume file: None
Next: 07-05 (final verification)

---
*State initialized: 2026-01-22*
*Last updated: 2026-01-29*
