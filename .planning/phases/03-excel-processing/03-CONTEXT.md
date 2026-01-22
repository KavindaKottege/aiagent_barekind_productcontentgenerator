# Phase 3: Excel Processing - Context

**Gathered:** 2026-01-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can upload raw Faire Excel files and the system automatically detects/maps columns to product fields, groups variant options together, and prepares products for AI generation. This phase handles data ingestion and preparation - NOT AI generation itself (that's Phase 4).

</domain>

<decisions>
## Implementation Decisions

### Upload workflow
- Upload triggered from modal/dialog on dashboard (not separate page)
- Immediate error message displayed in modal for invalid files (wrong format, corrupted, missing required columns)
- User stays in modal to retry upload on error
- New upload replaces existing products for that client (single active dataset per client)
- Required column validation before accepting file (ensure essential Faire columns exist: Name, Token, SKU, etc.)
- Progress bar shown while parsing/importing large Excel files
- Warn and require confirmation before replacing existing data (modal warning that upload will delete existing products/generations)
- After successful upload, user goes directly to products list view (mapping happens automatically in background)

### Column mapping
- Auto-detect Faire columns and hide mapping UI (no user interaction needed unless detection fails)
- If mapping fails or is ambiguous, show dropdown selectors for user to manually map Excel columns to product fields
- Store all Excel columns even if unmapped (preserve for export in Phase 7)
- Show preview of mapped data (first 5-10 sample rows with mapped fields visible) before confirming

### Variant grouping
- Products with identical Name, Token, and SKU are grouped as variants
- Display as single row with expand/collapse functionality in products list
- Collapsed row shows: Product name + variant count (e.g., "Blue Mug (4 options)")
- Expanded view shows: Option names for each variant (e.g., "Small - Red", "Medium - Blue")
- Variants always stay grouped (no ungroup option) - simplifies workflow
- Only one title/description generated per product group (applied to all variants on export)

### Field selection for AI
- User selects which product fields to use for AI generation before clicking "Generate" button
- Present available fields as checkbox list
- Certain fields are mandatory (e.g., Product Name always required)
- AI prompts adapt dynamically to missing fields - build optimized prompts with whatever data is available per product
- Field selection persists per client (saved in client profile, auto-applied on next upload)

### Claude's Discretion
- Specific file size limits (if needed)
- Exact validation error messages
- Progress bar implementation details
- Column detection algorithm specifics
- Visual design of expand/collapse UI
- Which fields are mandatory vs optional for AI generation

</decisions>

<specifics>
## Specific Ideas

- The upload modal should feel lightweight and quick - users shouldn't feel like they're navigating to a different workflow
- Products list after upload should immediately show the grouped data ready for generation
- Field selection should have sensible defaults checked (common fields agencies care about)

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 03-excel-processing*
*Context gathered: 2026-01-22*
