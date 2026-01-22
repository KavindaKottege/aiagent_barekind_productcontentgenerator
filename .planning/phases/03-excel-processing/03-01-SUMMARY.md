---
phase: 03-excel-processing
plan: 01
subsystem: database
tags: [sqlalchemy, pydantic, postgresql, jsonb, alembic, migrations]

# Dependency graph
requires:
  - phase: 02-client-management
    provides: Client model and database foundation
provides:
  - Product and ProductGroup SQLAlchemy models with variant grouping
  - Pydantic schemas for product CRUD and upload responses
  - Database migration creating products and product_groups tables
  - JSONB column pattern for preserving unmapped Excel data
affects: [03-02-upload-endpoint, 04-ai-generation, 07-excel-export]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "JSONB column for unmapped Excel data preservation"
    - "Variant grouping via ProductGroup parent model"
    - "Unique constraint on grouping keys (client_id, product_name, product_token, sku)"
    - "Composite index on (client_id, row_index) for export ordering"

key-files:
  created:
    - backend/app/models/product_group.py
    - backend/app/models/product.py
    - backend/app/schemas/product.py
    - backend/alembic/versions/005_create_products_tables.py
  modified:
    - backend/app/models/__init__.py
    - backend/app/schemas/__init__.py
    - backend/app/models/client.py

key-decisions:
  - "JSONB unmapped_data column preserves all unmapped Excel columns for Phase 7 export"
  - "ProductGroup model represents variant groupings with generated_title/description fields for Phase 4"
  - "Images stored as JSONB array of strings (PostgreSQL ARRAY type)"
  - "Unique constraint on (client_id, product_name, product_token, sku) prevents duplicate groups"
  - "Row_index field preserves original Excel ordering for export"

patterns-established:
  - "Variant grouping: ProductGroup (1) -> Products (many) relationship"
  - "JSONB for flexible schema: unmapped_data stores columns not in model"
  - "Composite index pattern for ordering: (client_id, row_index)"

# Metrics
duration: 3min
completed: 2026-01-22
---

# Phase 3 Plan 1: Database Models for Product Storage Summary

**Product and ProductGroup SQLAlchemy models with JSONB for unmapped Excel data, migration 005 creates tables with variant grouping support**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-22T23:16:35Z
- **Completed:** 2026-01-22T23:19:44Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- ProductGroup model for variant grouping with generated content fields (title, description, status)
- Product model with all mapped Faire fields plus JSONB unmapped_data column
- Pydantic schemas for CRUD operations and upload response
- Migration 005 creates both tables with proper foreign keys and indexes
- CASCADE delete ensures orphan cleanup from clients down to products

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Product and ProductGroup SQLAlchemy models** - `921b100` (feat)
2. **Task 2: Create Pydantic schemas for Product** - `0011aca` (feat)
3. **Task 3: Create database migration for products tables** - `e02e7dc` (feat)

## Files Created/Modified
- `backend/app/models/product_group.py` - ProductGroup model for variant grouping with shared content
- `backend/app/models/product.py` - Product model with mapped Faire fields and JSONB unmapped_data
- `backend/app/schemas/product.py` - Pydantic schemas for Product, ProductGroup, and UploadResponse
- `backend/alembic/versions/005_create_products_tables.py` - Migration creating product_groups and products tables
- `backend/app/models/__init__.py` - Exports Product and ProductGroup models
- `backend/app/schemas/__init__.py` - Exports product schemas
- `backend/app/models/client.py` - Added products and product_groups relationships

## Decisions Made

**JSONB unmapped_data column pattern**
- Preserves all Excel columns not mapped to explicit model fields
- Enables Phase 7 export to reconstruct original Excel with generated content
- Default value '{}' ensures column always has valid JSON

**ProductGroup variant grouping model**
- Represents unique products (grouped by name + token + sku)
- Stores variant_count for UI display (e.g., "3 options")
- Contains generated_title and generated_description (filled by Phase 4)
- Status field tracks generation workflow: pending → generated → approved/rejected

**Images as JSONB array**
- PostgreSQL ARRAY(String) for image URLs
- JSONB for flexible storage (handles variable number of images)
- Nullable since not all products have images

**Row_index preservation**
- Integer field stores original Excel row number
- Composite index (client_id, row_index) enables export in original order
- Critical for Phase 7: users expect products in same order as uploaded

**Unique constraint on grouping keys**
- (client_id, product_name, product_token, sku) must be unique
- Prevents duplicate ProductGroups for same product
- Enables idempotent uploads (re-upload replaces existing products)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all models, schemas, and migration created without issues. Database tables verified with correct structure, indexes, and foreign key relationships.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Phase 03-02 (Upload Endpoint) ready to implement:**
- Product and ProductGroup models available for database operations
- Pydantic schemas ready for request/response validation
- UploadResponse schema defined for upload endpoint return value
- JSONB unmapped_data ready to store unmapped Excel columns
- Database tables created with proper indexes for performance

**Phase 04 (AI Generation) ready to receive:**
- ProductGroup.generated_title and generated_description fields ready
- ProductGroup.status field ready for workflow tracking
- Variant grouping structure in place for generating shared content

**Phase 07 (Excel Export) ready to receive:**
- Row_index field preserves original Excel ordering
- JSONB unmapped_data preserves all unmapped columns
- Composite index (client_id, row_index) enables efficient ordering query

---
*Phase: 03-excel-processing*
*Completed: 2026-01-22*
