# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-22)

**Core value:** Generate professional, on-brand product content at scale with minimal friction - agencies can confidently use this with clients without worrying about workflow bottlenecks or unprofessional UX
**Current focus:** Phase 3 - Excel Processing

## Current Position

Phase: 3 of 7 (Excel Processing)
Plan: 5 of 5 (complete)
Status: Phase verified and complete ✓
Last activity: 2026-01-22 — Phase 3 verification passed (8/8 success criteria)

Progress: [██████░░░░] 54% (Phase 3 complete)

## Performance Metrics

**Velocity:**
- Total plans completed: 14
- Average duration: 3.7 minutes
- Total execution time: 0.9 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 5 | 20 min | 4 min |
| 02 | 5 | 22 min | 4.4 min |
| 03 | 5 | 17 min | 3.4 min |

**Recent Trend:**
- 03-01 completed in 3 minutes
- 03-02 completed in 3 minutes
- 03-03 completed in 3.2 minutes
- 03-04 completed in 3.4 minutes
- 03-05 completed in 4 minutes
- Trend: Strong velocity (avg 3.3 min/plan Phase 3)

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

### Pending Todos

None yet.

### Blockers/Concerns

**Phase 4 (AI Generation):** May need research for LangChain prompt engineering patterns specific to product content domain and OpenAI model selection for quality/cost optimization.

**Phase 6 (Smart Regeneration):** May need research for feedback learning techniques and refinement loop implementations.

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

**Phase 4 (AI Generation Core) ready to plan:**
- Excel processing foundation complete and verified
- Product and field selection data available for prompt building
- Client-specific prompts and guidelines stored
- Variant grouping ready for bulk generation
- Ready for LangChain integration, cost tracking, and batch generation

## Session Continuity

Last session: 2026-01-22 (current)
Stopped at: Completed Phase 3 verification
Resume file: None
Next: Begin Phase 4 - AI Generation Core (research, planning, execution)

---
*State initialized: 2026-01-22*
*Last updated: 2026-01-22*
