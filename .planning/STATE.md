# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-22)

**Core value:** Generate professional, on-brand product content at scale with minimal friction - agencies can confidently use this with clients without worrying about workflow bottlenecks or unprofessional UX
**Current focus:** Phase 3 - Excel Processing

## Current Position

Phase: 3 of 7 (Excel Processing)
Plan: 2 of 5
Status: In progress
Last activity: 2026-01-22 — Completed 03-02-PLAN.md (Excel Processing Pipeline)

Progress: [████░░░░░░] 46% (12 of 26 plans complete)

## Performance Metrics

**Velocity:**
- Total plans completed: 12
- Average duration: 3.8 minutes
- Total execution time: 0.76 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 5 | 20 min | 4 min |
| 02 | 5 | 22 min | 4.4 min |
| 03 | 2 | 6 min | 3 min |

**Recent Trend:**
- 02-03 completed in 4 minutes
- 02-04 completed in 4 minutes
- 02-05 completed in 6 minutes
- 03-01 completed in 3 minutes
- 03-02 completed in 3 minutes
- Trend: Strong velocity (avg 3.8 min/plan)

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

**Phase 3 (Excel Processing) IN PROGRESS:**
- ✅ 03-01: Database models created (Product, ProductGroup)
- ✅ 03-02: Excel processing pipeline with streaming parser, fuzzy mapper, variant grouper
- Streaming Excel parser handles large files (500-row batches, memory efficient)
- Fuzzy column mapper auto-detects Faire columns (75% threshold, returns confidence)
- Variant grouper clusters products by Name/Token/SKU using pandas
- Upload endpoint orchestrates parse → map → group → bulk insert
- Four product endpoints: upload, list groups, get group details, delete
- Ready for field selection UI (03-03)

## Session Continuity

Last session: 2026-01-22 (current)
Stopped at: Completed 03-02-PLAN.md (Excel Processing Pipeline)
Resume file: None
Next: Continue Phase 3 - Excel Processing (plans 03-03 through 03-05)

---
*State initialized: 2026-01-22*
*Last updated: 2026-01-22*
