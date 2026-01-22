---
phase: 03-excel-processing
plan: 05
subsystem: ui
tags: [nextjs, react, checkbox, shadcn, client-state, jsonb, alembic]

# Dependency graph
requires:
  - phase: 03-01
    provides: Client model and database schema
  - phase: 03-04
    provides: Products page structure for integration
provides:
  - Client model extended with ai_input_fields JSONB column
  - FieldSelectionPanel component for AI input field selection
  - Field selection persists per client
  - UI prepares for Phase 5 (Review System) to detect missing fields
affects: [04-ai-generation, 05-review-system]

# Tech tracking
tech-stack:
  added: [shadcn checkbox component]
  patterns: [JSONB for dynamic field lists, required field UI pattern]

key-files:
  created:
    - backend/alembic/versions/006_add_ai_field_selection_to_clients.py
    - frontend/src/components/field-selection-panel.tsx
    - frontend/src/components/ui/checkbox.tsx
  modified:
    - backend/app/models/client.py
    - backend/app/schemas/client.py
    - frontend/src/app/actions/clients.ts
    - frontend/src/app/(dashboard)/products/page.tsx
    - frontend/src/components/products-page-content.tsx

key-decisions:
  - "JSONB column for ai_input_fields stores list of field names as JSON array"
  - "Default value None means use all available fields (explicit opt-in pattern)"
  - "Required fields (product_name) cannot be deselected for AI generation quality"
  - "Field selection panel only shows when products exist for client"
  - "8 available fields: product_name (required), description, product_type, option_name, country_of_origin, made_to_order, sku, images"
  - "Save indicator shows for 2 seconds after successful update"

patterns-established:
  - "Required field pattern: Checkbox disabled with visual indicator and gray label"
  - "Field selection persistence: Store as JSONB array in client table"
  - "Conditional panel display: Only show field selection when products uploaded"
  - "Parallel data fetching: Products and client data fetched together for efficiency"

# Metrics
duration: 4min
completed: 2026-01-22
---

# Phase 3 Plan 5: Field Selection UI Summary

**JSONB field selection persists per client with 8 configurable AI input fields and required product_name constraint**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-22T14:02:51Z
- **Completed:** 2026-01-22T14:06:47Z
- **Tasks:** 3
- **Files modified:** 9

## Accomplishments
- Client model extended with ai_input_fields JSONB column via migration 006
- FieldSelectionPanel component with checkbox grid for 8 product fields
- Field selection persists per client and displays on products page
- Required fields visually indicated and cannot be deselected
- Preparation for Phase 5 to warn about missing data during review

## Task Commits

Each task was committed atomically:

1. **Task 1: Add ai_input_fields to Client model** - `10400d3` (feat)
2. **Task 2: Create field selection panel component** - `fc6961a` (feat)
3. **Task 3: Integrate field selection panel into products page** - `e23979e` (feat)

## Files Created/Modified
- `backend/app/models/client.py` - Added ai_input_fields JSONB column with JSON import
- `backend/app/schemas/client.py` - Added ai_input_fields to ClientUpdate and ClientPublic schemas
- `backend/alembic/versions/006_add_ai_field_selection_to_clients.py` - Migration to add column to database
- `frontend/src/components/field-selection-panel.tsx` - Checkbox panel with 8 fields and required field handling
- `frontend/src/components/ui/checkbox.tsx` - Shadcn checkbox component
- `frontend/src/app/actions/clients.ts` - Added updateClientFieldSelection action and updated Client interface
- `frontend/src/app/(dashboard)/products/page.tsx` - Fetch client data in parallel with products
- `frontend/src/components/products-page-content.tsx` - Integrated FieldSelectionPanel with conditional display

## Decisions Made

**1. JSONB for dynamic field lists**
- Rationale: Flexible storage for variable-length array of field names without schema changes

**2. Default value None means "use all fields"**
- Rationale: Explicit opt-in pattern - users must save selection to customize, otherwise all fields used

**3. Required fields cannot be deselected**
- Rationale: Product name is essential for AI generation quality - prevent user error

**4. 8 available fields with descriptions**
- Rationale: Clear labels help users understand what each field provides to AI prompts

**5. Panel only shows when products exist**
- Rationale: Field selection is irrelevant without products - reduces cognitive load on empty state

**6. Page refresh on selection change**
- Rationale: Simple state sync - router.refresh() reloads server component with updated client data

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**1. TypeScript type error with REQUIRED_FIELDS.includes()**
- **Problem:** REQUIRED_FIELDS inferred as readonly array of literal types, fieldId was string
- **Resolution:** Added explicit `string[]` type annotation to REQUIRED_FIELDS constant
- **Impact:** Build succeeded after type annotation

## Next Phase Readiness

**Phase 4 (AI Generation) ready:**
- ai_input_fields available on Client model for prompt construction
- Selected fields can be used to build context for AI prompts
- Default behavior (None) means use all available fields

**Phase 5 (Review System) prepared:**
- ai_input_fields stored per client enables missing data detection
- Product.unmapped_data JSONB (from 03-01) preserves all columns
- Review UI can warn when selected fields are missing in uploaded data
- EXCL-06 requirement foundation complete (actual warning UI is Phase 5 task)

**No blockers identified.**

---
*Phase: 03-excel-processing*
*Completed: 2026-01-22*
