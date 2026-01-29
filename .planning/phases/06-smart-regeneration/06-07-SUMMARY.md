---
phase: 06-smart-regeneration
plan: 07
subsystem: ui
tags: [react, nextjs, batch-regeneration, alert-dialog, products-page, review-page]

# Dependency graph
requires:
  - phase: 06-05
    provides: POST /regenerate-rejected endpoint and RegenerationEstimate schema
  - phase: 06-06
    provides: Server actions for regenerateRejected and getRegenerationEstimate
provides:
  - BatchRegenerateButton component with estimate dialog
  - Batch regeneration integrated into products page header
  - Batch regeneration integrated into review page header
  - Full smart regeneration workflow end-to-end
affects: [07-export-polish]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "BatchRegenerateButton with AlertDialog confirmation and cost estimate fetch"
    - "Conditional button visibility based on rejected product count"
    - "Shared component pattern across products and review pages"

key-files:
  created:
    - frontend/src/components/products/batch-regenerate-button.tsx
  modified:
    - frontend/src/components/products-page-content.tsx
    - frontend/src/app/(dashboard)/review/review-page-client.tsx
    - backend/app/routers/regeneration.py
    - frontend/src/components/review/generation-history-dialog.tsx

key-decisions:
  - "BatchRegenerateButton shared across both products and review pages (same component, different contexts)"
  - "Estimate fetched on dialog open (not on page load) to avoid unnecessary API calls"
  - "Button hidden when no rejected products exist to avoid dead-end clicks"
  - "History endpoint grouped by job_id to handle split title/description audit records"
  - "History dialog redesigned with compact table rows, version numbering, and collapsible older versions"

patterns-established:
  - "Shared action button component: reusable across multiple pages with context-specific callbacks"
  - "Estimate-on-open dialog: fetch cost estimate lazily when dialog opens, not on mount"

# Metrics
duration: ~5min (tasks) + checkpoint verification
completed: 2026-01-29
---

# Phase 6 Plan 07: Batch Regeneration UI Summary

**BatchRegenerateButton component with cost estimate dialog, integrated into products and review page headers, plus history endpoint and dialog UX fixes**

## Performance

- **Duration:** ~5 min (auto tasks) + checkpoint with orchestrator fixes
- **Started:** 2026-01-29T10:08:50+11:00
- **Completed:** 2026-01-29T15:05:30+11:00 (including checkpoint verification and fixes)
- **Tasks:** 3 auto tasks + 1 checkpoint (approved with fixes)
- **Files modified:** 5

## Accomplishments
- BatchRegenerateButton component with AlertDialog confirmation, estimate fetch, loading states, and error handling
- Integrated batch regeneration into products page header (visible when no active generation job)
- Integrated batch regeneration into review page header (visible when rejected products exist)
- History endpoint fixed to handle split title/description audit records by grouping by job_id
- History dialog UX redesigned: compact rows, v1/v2/v3 numbering, collapsible older versions, fixed modal height

## Task Commits

Each task was committed atomically:

1. **Task 1: Create batch regenerate button component** - `2134aaf` (feat)
2. **Task 2: Add batch regenerate button to products page** - `e532a7f` (feat)
3. **Task 3: Add batch regenerate button to review page** - `cb4adf7` (feat)

**Orchestrator fixes during checkpoint verification:**

4. **Fix history endpoint split audits** - `b0e28a5` (fix)
5. **Redesign history dialog UX** - `505cc5b` (fix)
6. **Fix dialog height constraint** - `d25a3d6` (fix)
7. **Fix dialog overflow with native scroll** - `1c38d0f` (fix)

## Files Created/Modified
- `frontend/src/components/products/batch-regenerate-button.tsx` - BatchRegenerateButton with AlertDialog confirmation and estimate fetch
- `frontend/src/components/products-page-content.tsx` - Added BatchRegenerateButton to products page stats header
- `frontend/src/app/(dashboard)/review/review-page-client.tsx` - Added BatchRegenerateButton to review page header
- `backend/app/routers/regeneration.py` - Fixed history endpoint to group split title/description audits by job_id
- `frontend/src/components/review/generation-history-dialog.tsx` - Redesigned with compact rows, version numbering, collapsible sections, fixed height

## Decisions Made
- BatchRegenerateButton is a shared component used identically on products and review pages with different callbacks
- Estimate is fetched lazily when dialog opens (not on page mount) to avoid unnecessary API calls on every page load
- Button is hidden entirely when rejectedCount is 0 (products page) or when manually_rejected is 0 (review page)
- On regeneration start, router.refresh() reloads page data to pick up status changes

## Deviations from Plan

### Orchestrator Fixes During Checkpoint

**1. [Rule 1 - Bug] History endpoint returned 0 results for split audit records**
- **Found during:** Checkpoint verification
- **Issue:** Generation creates separate audit records for title and description. The history query did not account for this, returning no combined results.
- **Fix:** Grouped audit records by job_id, combining title and description from the same generation run. Restore endpoint updated to find sibling audits from same job.
- **Files modified:** backend/app/routers/regeneration.py
- **Committed in:** b0e28a5

**2. [Rule 1 - Bug] History dialog UX was not production-ready**
- **Found during:** Checkpoint verification
- **Issue:** History dialog showed raw data without clear version numbering, no way to collapse older versions, and dialog overflowed on many versions.
- **Fix:** Redesigned with compact table rows, v1/v2/v3 version numbering (v1 = oldest), latest 3 versions always visible with older collapsed, click-to-expand for full content, fixed modal height at max-h-70vh with internal scroll.
- **Files modified:** frontend/src/components/review/generation-history-dialog.tsx
- **Committed in:** 505cc5b, d25a3d6, 1c38d0f

---

**Total deviations:** 2 issues fixed during checkpoint (1 backend bug, 1 UX redesign with 3 iterative commits)
**Impact on plan:** Both fixes necessary for correct and usable history functionality. No scope creep.

## Issues Encountered
None beyond the checkpoint fixes documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 6 (Smart Regeneration) is fully complete with all 7 plans executed
- Full regeneration workflow operational: reject with feedback -> view history -> restore versions -> regenerate single -> batch regenerate
- Ready for Phase 7 (Export & Polish) which depends on Phase 6
- All regeneration-related backend endpoints and frontend UI integrated and verified

---
*Phase: 06-smart-regeneration*
*Completed: 2026-01-29*
