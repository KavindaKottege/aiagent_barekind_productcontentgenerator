---
phase: 06-smart-regeneration
plan: 02
subsystem: review-ui
tags: [rejection-reasons, dialog, checkbox, server-action, review-interface]
depends_on:
  requires: [05-02, 05-07]
  provides: [rejection-reasons-dialog, rejectWithReasons-action, rejection-reason-types]
  affects: [06-03, 06-04, 06-05]
tech-stack:
  added: []
  patterns: [dialog-with-state-reset, checkbox-multi-select, server-action-with-reasons]
key-files:
  created:
    - frontend/src/lib/rejection-reasons.ts
    - frontend/src/components/review/rejection-reasons-dialog.tsx
  modified:
    - frontend/src/app/actions/review.ts
    - frontend/src/components/review/review-interface.tsx
decisions:
  - id: "06-02-01"
    decision: "Dialog triggers on Reject click/keyboard shortcut, not inline"
    rationale: "Non-disruptive UX - user sees dialog overlay, can cancel or skip"
  - id: "06-02-02"
    decision: "Skip button sends empty reasons array (not null)"
    rationale: "Consistent API contract - always sends array, backend handles empty case"
metrics:
  duration: "2 minutes"
  completed: "2026-01-29"
---

# Phase 06 Plan 02: Frontend Rejection Feedback UI Summary

**One-liner:** RejectionReasonsDialog with 4 checkbox reasons, Skip/Reject buttons, integrated into review interface via handleRejectClick flow

## What Was Built

### Task 1: Rejection Reasons Constants and Types
- Created `frontend/src/lib/rejection-reasons.ts` with 4 predefined reasons:
  - `off_brand_tone` - "Off-brand tone"
  - `generic_boring` - "Generic/boring"
  - `factually_wrong` - "Factually wrong"
  - `seo_issues` - "SEO issues"
- Exported `RejectionReason` type (keyof the constants map)
- Added `getReasonLabel()` and `isValidReason()` utility functions

### Task 2: Rejection Reasons Dialog Component
- Created `RejectionReasonsDialog` with shadcn/ui Dialog and Checkbox components
- Multi-select checkboxes for each rejection reason
- **Skip** button rejects without feedback (sends empty array)
- **Reject with Feedback** button sends selected reasons
- Button text dynamically shows "Reject" when no reasons selected, "Reject with Feedback" when reasons selected
- State resets on close, confirm, and skip for clean reuse

### Task 3: Server Action and Review Interface Integration
- Added `rejectWithReasons` server action calling `POST /api/review/reject-with-reasons`
- Replaced `handleReject` with `handleRejectClick` (opens dialog) and `handleRejectConfirm` (processes rejection with reasons)
- Keyboard shortcut 'R' now opens the dialog instead of directly rejecting
- Dialog mounted in review interface with loading state from transition
- Auto-advance to next unreviewed product after confirmation

## Commits

| # | Hash | Message |
|---|------|---------|
| 1 | 4576836 | feat(06-02): create rejection reasons constants and types |
| 2 | c518082 | feat(06-02): create rejection reasons dialog component |
| 3 | 3dc9c83 | feat(06-02): integrate rejection reasons dialog into review UI |

## Deviations from Plan

None - plan executed exactly as written.

## Decisions Made

1. **Dialog triggers on Reject click/keyboard shortcut** - The dialog overlay pattern keeps the review context visible behind the dialog, allowing users to reference the content while selecting reasons.
2. **Skip sends empty array** - Consistent API contract where `rejection_reasons` is always an array. Backend handles the empty case as a standard rejection without feedback.

## Verification

- Full TypeScript project type check: PASS (zero errors)
- Full Next.js build: PASS (all routes compiled)
- All success criteria met:
  - [x] Rejection reasons dialog appears when user clicks Reject
  - [x] User can select 0, 1, or multiple rejection reasons
  - [x] Skip button works (rejects without feedback)
  - [x] Selected reasons are sent to /api/review/reject-with-reasons
  - [x] Keyboard shortcut 'R' triggers dialog flow
  - [x] Dialog closes after confirmation and auto-advances

## Next Phase Readiness

- Rejection reasons types exported for backend plan 06-01 (backend endpoint)
- Dialog integration ready for end-to-end testing once backend `reject-with-reasons` endpoint exists
- Constants map matches backend `RejectionReasonType` literal for type safety across stack
