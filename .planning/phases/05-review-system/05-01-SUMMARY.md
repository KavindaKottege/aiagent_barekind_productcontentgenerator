---
phase: 05-review-system
plan: 01
subsystem: api
tags: [fastapi, sqlalchemy, pydantic, alembic, postgresql, review-api]

# Dependency graph
requires:
  - phase: 04-ai-generation-core
    provides: ProductGroup model with generated content fields
provides:
  - Review status tracking fields on ProductGroup model
  - ReviewJob model for batch AI review tracking
  - Review Pydantic schemas for API validation
  - Complete review API (approve/reject/edit/undo/stats)
affects: [05-02-review-ui, 05-03-ai-review-service, 06-smart-regeneration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Separate edited_* fields pattern for tracking user edits alongside generated content"
    - "Dual review status pattern (manual review_status + AI ai_review_status)"
    - "Auto-advance pattern returning next_product_id after approve/reject"
    - "JSONB array for ai_review_safety_flags field"

key-files:
  created:
    - backend/app/models/review_job.py
    - backend/app/schemas/review.py
    - backend/app/routers/review.py
    - backend/alembic/versions/009_add_review_fields.py
  modified:
    - backend/app/models/product_group.py
    - backend/app/models/__init__.py
    - backend/app/schemas/__init__.py
    - backend/app/routers/__init__.py
    - backend/app/main.py

key-decisions:
  - "Store edited content in separate fields (edited_title, edited_description) to preserve original generated content"
  - "Use JSONB array for ai_review_safety_flags for flexible safety concern tracking"
  - "Auto-advance returns next_product_id after approve/reject for smooth review workflow"
  - "Character limit validation in Pydantic schema (30-60 title, 2000-3000 description)"
  - "Edit action sets review_status='edited', requires explicit approval after editing"

patterns-established:
  - "Review status state machine: null → approved/rejected/edited"
  - "Auto-advance pattern: API returns next_product_id for seamless queue progression"
  - "Dual content pattern: generated_* fields preserved, edited_* fields for user changes"
  - "Safety flags array pattern: JSONB array for extensible AI safety concerns"

# Metrics
duration: 4.9min
completed: 2026-01-23
---

# Phase 5 Plan 1: Review Backend API Summary

**Review status tracking fields and complete CRUD API for manual approve/reject/edit workflow**

## Performance

- **Duration:** 4.9 min
- **Started:** 2026-01-23T16:28:43Z
- **Completed:** 2026-01-23T16:33:34Z
- **Tasks:** 3
- **Files modified:** 9

## Accomplishments
- Extended ProductGroup model with 8 review fields (review_status, edited_title, edited_description, ai_review_status, ai_review_reason, ai_review_safety_flags, reviewed_at, ai_reviewed_at)
- Created ReviewJob model for batch AI review job tracking (follows GenerationJob pattern)
- Implemented complete review API with 8 endpoints for full CRUD workflow
- Auto-advance feature returns next unreviewed product_group_id after approve/reject

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend ProductGroup model with review fields** - `901aee0` (feat)
2. **Task 2: Create review Pydantic schemas** - `c68013c` (feat)
3. **Task 3: Create review API router** - `0beeebb` (feat)

## Files Created/Modified
- `backend/app/models/product_group.py` - Added 8 review status fields (review_status, ai_review_status, ai_review_reason, ai_review_safety_flags, edited_title, edited_description, reviewed_at, ai_reviewed_at)
- `backend/app/models/review_job.py` - ReviewJob model for batch AI review tracking with status, progress, cost tracking
- `backend/alembic/versions/009_add_review_fields.py` - Migration adds 8 columns to product_groups, creates review_jobs table, adds indexes
- `backend/app/schemas/review.py` - Pydantic schemas (ProductGroupReview, ReviewActionRequest, EditContentRequest, ReviewActionResponse, ReviewStatsResponse, UndoReviewRequest)
- `backend/app/routers/review.py` - Review API router with 8 endpoints (GET products list, GET single product, POST approve, POST reject, POST edit, POST undo, GET stats, GET next-unreviewed)
- `backend/app/models/__init__.py` - Export ReviewJob
- `backend/app/schemas/__init__.py` - Export review schemas
- `backend/app/routers/__init__.py` - Export review_router
- `backend/app/main.py` - Register review_router with /api prefix

## Decisions Made

**Separate edited content fields:**
- Store edited_title and edited_description separately from generated_title and generated_description
- Preserves original AI output for comparison and audit trail
- Enables fallback to generated content if user clears edits

**Dual review status pattern:**
- review_status for manual review (approved, rejected, edited)
- ai_review_status for AI review recommendations (ai_approved, ai_rejected)
- Enables future workflows where AI pre-reviews and human makes final decision

**JSONB array for safety flags:**
- ai_review_safety_flags as JSONB array instead of comma-separated string
- Allows flexible addition of safety concerns without schema changes
- PostgreSQL JSONB provides efficient querying and indexing

**Character limit validation in Pydantic:**
- EditContentRequest validates 30-60 chars for title, 2000-3000 for description
- Matches generation constraints from Phase 4 for consistency
- Frontend can show real-time validation based on API constraints

**Edit workflow requires explicit approval:**
- POST /api/review/edit sets review_status='edited' but does not approve
- User must click Approve after editing to finalize
- Prevents accidental approval of quick edits without review

**Auto-advance for smooth workflow:**
- approve and reject endpoints return next_product_id
- Frontend can automatically navigate to next unreviewed product
- Orders by row_index for consistent queue progression

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all tasks completed smoothly.

## Next Phase Readiness

**Backend review API complete.** Ready for:
- Phase 5 Plan 2: Review UI frontend components
- Phase 5 Plan 3: AI Review Service for automated safety checks
- Phase 6: Smart Regeneration (can read review_status to identify rejected content)

**Review workflow state machine established:**
- Generated products start with review_status=null
- Manual actions: approve, reject, edit (requires subsequent approve)
- AI actions: ai_approved, ai_rejected (recommendations only, don't affect manual review_status)
- Undo action clears review_status and reviewed_at

**API provides all data needed for review UI:**
- ProductGroupReview schema includes images from first product
- original_data dict for collapsible panel (description, product_type, option_name, country_of_origin, made_to_order)
- ReviewStatsResponse provides counts for status badges

---
*Phase: 05-review-system*
*Completed: 2026-01-23*
