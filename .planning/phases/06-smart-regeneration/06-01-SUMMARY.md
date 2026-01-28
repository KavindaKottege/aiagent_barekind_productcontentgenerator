---
phase: "06-smart-regeneration"
plan: "01"
subsystem: "backend-review"
tags: ["rejection-feedback", "regeneration", "JSONB", "pydantic", "api"]

dependency_graph:
  requires: ["05-01"]  # Review system model (ProductGroup review fields)
  provides: ["rejection-feedback-capture", "regeneration-count-tracking", "reject-with-reasons-endpoint"]
  affects: ["06-02", "06-03", "06-04"]  # Regeneration service, batch regen, UI will consume these fields

tech_stack:
  added: []
  patterns:
    - "Literal type for enum-like validation in Pydantic"
    - "JSONB array for flexible structured rejection feedback"
    - "Predefined rejection reasons pattern (no free text)"

key_files:
  created:
    - "backend/alembic/versions/022_add_regeneration_fields.py"
    - "backend/app/schemas/regeneration.py"
  modified:
    - "backend/app/models/product_group.py"
    - "backend/app/routers/review.py"
    - "backend/app/schemas/__init__.py"

decisions:
  - id: "06-01-D1"
    decision: "Use UUID for product_group_id in RejectWithReasonsRequest (not str)"
    rationale: "Consistency with existing ReviewActionRequest pattern and type-safe UUID comparison with ProductGroup.id"

metrics:
  duration: "2.2 minutes"
  completed: "2026-01-29"
---

# Phase 6 Plan 01: Rejection Feedback Capture Summary

**One-liner:** JSONB rejection_reasons field on ProductGroup with Literal-validated reject-with-reasons endpoint for structured regeneration feedback

## What Was Done

### Task 1: Extend ProductGroup model with regeneration fields
- Added `rejection_reasons` (JSONB, nullable, default `[]`) for storing structured rejection feedback
- Added `regeneration_count` (Integer, not null, default 0) for tracking regeneration cycles
- Created migration 022 with index on `regeneration_count` for efficient filtering
- **Commit:** `a89e6dc`

### Task 2: Create regeneration Pydantic schemas
- Created `RejectionReasonType` Literal with 4 predefined values: `off_brand_tone`, `generic_boring`, `factually_wrong`, `seo_issues`
- Created `REJECTION_REASON_LABELS` dict for frontend display mapping
- Created `RejectWithReasonsRequest` model with UUID `product_group_id` and optional `rejection_reasons` list
- Exported from `app.schemas.__init__`
- **Commit:** `2a07448`

### Task 3: Add reject-with-reasons API endpoint
- Added `POST /api/review/reject-with-reasons` endpoint to review router
- Validates rejection reasons against `RejectionReasonType` Literal (rejects invalid values)
- Stores reasons as JSONB array, sets `review_status="rejected"`, records timestamp
- Returns `next_product_id` for auto-advance workflow (same pattern as existing reject)
- Verifies user ownership before allowing rejection
- **Commit:** `c73c22a`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Changed product_group_id from str to UUID**
- **Found during:** Task 3
- **Issue:** Plan specified `product_group_id: str` in `RejectWithReasonsRequest`, but existing `ReviewActionRequest` uses `UUID` and `ProductGroup.id` is a UUID column. Using `str` would cause type mismatch in SQLAlchemy queries.
- **Fix:** Changed to `UUID` type with proper import from `uuid` module
- **Files modified:** `backend/app/schemas/regeneration.py`
- **Commit:** `c73c22a`

## Verification Results

| Check | Result |
|-------|--------|
| ProductGroup has rejection_reasons field | PASS |
| ProductGroup has regeneration_count field | PASS |
| Migration 022 applies successfully | PASS |
| Schema validates against predefined reasons | PASS |
| Invalid reasons rejected with ValidationError | PASS |
| Endpoint exists at /review/reject-with-reasons | PASS |

## Decisions Made

| ID | Decision | Rationale |
|----|----------|-----------|
| 06-01-D1 | UUID for product_group_id (not str) | Type consistency with existing patterns and safe UUID comparison |

## Next Phase Readiness

- Rejection feedback capture is ready for consumption by regeneration service (06-02)
- `rejection_reasons` JSONB field can be read by prompt enhancement logic (06-03)
- `regeneration_count` field ready for increment on each regeneration cycle
- No blockers for subsequent plans
