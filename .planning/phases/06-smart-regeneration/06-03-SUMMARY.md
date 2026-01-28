---
phase: 06-smart-regeneration
plan: 03
subsystem: ai
tags: [langchain, openai, regeneration, prompt-engineering, pydantic]

# Dependency graph
requires:
  - phase: 06-01
    provides: "JSONB rejection_reasons, regeneration_count fields, RejectionReasonType"
provides:
  - "RegenerationContext schema for carrying rejection feedback"
  - "get_positive_guidance() helper for converting reasons to constructive prompts"
  - "_build_feedback_section() method for assembling regeneration prompt sections"
  - "regeneration_context parameter on build_title_prompt, build_description_prompt, generate_title, generate_description"
affects: [06-05, 06-06, 06-07]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Regeneration feedback injection pattern: feedback only injected when regeneration_count > 0"
    - "Positive guidance mapping: rejection reasons converted to constructive focus areas"
    - "Description truncation at 500 chars to prevent token explosion in prompts"

key-files:
  created: []
  modified:
    - "backend/app/schemas/regeneration.py"
    - "backend/app/schemas/__init__.py"
    - "backend/app/services/ai_generation.py"

key-decisions:
  - "Feedback only injected when regeneration_count > 0 to avoid impacting initial generation"
  - "Previous description truncated at 500 chars to prevent prompt token explosion"
  - "Positive guidance derived from rejection reasons via static mapping"

patterns-established:
  - "Regeneration feedback pattern: _build_feedback_section builds multi-section feedback string"
  - "Dual guidance pattern: negative (DO NOT REUSE) + positive (FOCUS ON) for balanced regeneration"

# Metrics
duration: 3min
completed: 2026-01-29
---

# Phase 6 Plan 3: Smart Regeneration Prompt Context Summary

**RegenerationContext schema and feedback injection into AIGenerationService prompt builders for rejection-aware regeneration**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-28T22:59:49Z
- **Completed:** 2026-01-28T23:03:14Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- RegenerationContext Pydantic model carries previous content, rejection reasons, AI review flags, and regeneration count
- REASON_TO_POSITIVE_GUIDANCE mapping converts rejection reasons to constructive focus areas for the AI
- _build_feedback_section helper builds multi-line feedback with negative guidance (DO NOT REUSE), rejection reasons, AI flags, and positive guidance
- build_title_prompt and build_description_prompt accept optional regeneration_context and inject feedback section
- generate_title and generate_description pass regeneration_context through to prompt builders

## Task Commits

Each task was committed atomically:

1. **Task 1: Add RegenerationContext schema** - `40f770d` (feat)
2. **Task 2: Add regeneration context support to AIGenerationService** - `0123cf6` (feat)

## Files Created/Modified
- `backend/app/schemas/regeneration.py` - Added RegenerationContext model, REASON_TO_POSITIVE_GUIDANCE mapping, get_positive_guidance() helper
- `backend/app/schemas/__init__.py` - Added exports for RegenerationContext, get_positive_guidance, REASON_TO_POSITIVE_GUIDANCE
- `backend/app/services/ai_generation.py` - Added _build_feedback_section, regeneration_context param to prompt builders and generators

## Decisions Made
- Feedback only injected when regeneration_count > 0 so initial generation is completely unaffected
- Previous description truncated to 500 characters to prevent token explosion in prompts
- Positive guidance uses static mapping from rejection reasons (no AI inference needed)
- Reason labels use human-readable lowercase phrases ("off-brand tone" not "off_brand_tone") for clarity in prompts

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- RegenerationContext ready to be constructed from ProductGroup fields (rejection_reasons, ai_review_safety_flags, regeneration_count, generated_title, generated_description)
- generate_title and generate_description ready to receive regeneration_context from the regeneration worker (06-05/06-06)
- Existing callers unaffected since regeneration_context defaults to None

---
*Phase: 06-smart-regeneration*
*Completed: 2026-01-29*
