# Phase 7 Plan 1: Backend Export System Summary

**Completed:** 2026-01-29
**Duration:** 4 minutes
**Tasks:** 2/2

## One-liner

Excel export backend with column-order migration, ExcelExporter service, and stats+download API endpoints returning .xlsx with original structure preserved.

## What Was Built

### Task 1: Migration + Column Order Persistence
- Added `excel_column_order` JSON column to the Client model (after `ai_input_fields`)
- Created migration 023 adding nullable JSONB column to clients table
- Modified upload endpoint in `products.py` to persist original Excel header order on each upload
- Added Client model import and ownership validation in upload flow

### Task 2: ExcelExporter Service + Export API Endpoints
- **ExcelExporter service** (`backend/app/services/excel_exporter.py`):
  - Reverse-maps Excel header names to field names via `ExactColumnMapper.COLUMN_MAP`
  - `export()` method builds openpyxl Workbook with original column order
  - Content substitution rules: approved/edited products get generated content, rejected/non-generated keep originals
  - `include_pending` flag controls whether pending-review products also get updated content
  - Handles special types: images joined with space separator, booleans passed as-is

- **Export schemas** (`backend/app/schemas/export.py`):
  - `ExportStatsResponse` with total, not_generated, approved, pending, rejected counts

- **Export router** (`backend/app/routers/export.py`):
  - `GET /api/export/{client_id}/stats` -- returns product counts by status for dialog
  - `GET /api/export/{client_id}` -- downloads .xlsx file as StreamingResponse
  - Client ownership validation on both endpoints
  - Column order fallback: uses `client.excel_column_order` if available, otherwise derives from COLUMN_MAP + unmapped_data keys
  - Filename sanitization for Content-Disposition header
  - Blocks export with 400 if no approved products exist

- **Router registration** in `routers/__init__.py` and `main.py`

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Store column order on Client model (not separate table) | Simplest approach: one nullable JSON column, one migration, direct access during export |
| Separate group_status key in export data dict | Avoids collision between Product.status (product status) and ProductGroup.status (generation status) |
| Fallback column order from COLUMN_MAP + unmapped keys | Handles clients who uploaded before migration 023 was applied |
| Sanitized filename for Content-Disposition | Replaces special chars to prevent header injection and filesystem issues |
| Space separator for images on export | Matches Faire's space-separated URL format |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed group_status key collision**
- **Found during:** Task 2
- **Issue:** ExcelExporter's `_should_use_generated` checked `product.get("status")` which would return the Product's status field, not the ProductGroup's generation status. The router builds data with `group_status` key to avoid collision.
- **Fix:** Updated ExcelExporter to use `product.get("group_status")` instead of `product.get("status")`
- **Files modified:** `backend/app/services/excel_exporter.py`

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | b414890 | Migration + column order persistence |
| 2 | 6d5c914 | ExcelExporter service + export API endpoints |

## Key Files

### Created
- `backend/alembic/versions/023_add_excel_column_order.py` -- Migration adding excel_column_order to clients
- `backend/app/services/excel_exporter.py` -- ExcelExporter service class (130 lines)
- `backend/app/schemas/export.py` -- ExportStatsResponse schema
- `backend/app/routers/export.py` -- Export API endpoints (stats + download)

### Modified
- `backend/app/models/client.py` -- Added excel_column_order field
- `backend/app/routers/products.py` -- Persist column order on upload
- `backend/app/services/__init__.py` -- Export ExcelExporter
- `backend/app/schemas/__init__.py` -- Export ExportStatsResponse
- `backend/app/routers/__init__.py` -- Register export_router
- `backend/app/main.py` -- Include export_router with /api prefix

## Verification Results

- Migration 023 applied successfully (current head: 023)
- Upload endpoint persists column order to client.excel_column_order
- ExcelExporter produces valid .xlsx with correct headers and content
- Approved products receive generated title/description in export
- Rejected products keep original values unchanged
- Backend starts without import errors
- All export routes registered: GET /api/export/{client_id}/stats, GET /api/export/{client_id}

## Next Phase Readiness

Backend export system is complete and ready for frontend integration (Phase 7 Plan 2+):
- Stats endpoint ready for export confirmation dialog population
- Download endpoint ready for client-side fetch + blob download
- Column order stored on upload for reliable export reconstruction
