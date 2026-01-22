---
phase: 03-excel-processing
plan: 02
subsystem: api
tags: [openpyxl, pandas, rapidfuzz, fastapi, excel, fuzzy-matching, streaming]

# Dependency graph
requires:
  - phase: 03-01
    provides: Product and ProductGroup database models with JSONB unmapped_data
provides:
  - Streaming Excel parser using openpyxl read_only mode (memory efficient)
  - Fuzzy column mapper with RapidFuzz for automatic Faire column detection
  - Variant grouper using pandas groupby for product clustering
  - POST /products/upload endpoint with file validation and bulk insert
  - GET /products/groups and GET /products/groups/{id} for product retrieval
affects: [03-03-field-selection, 04-ai-generation, 07-excel-export]

# Tech tracking
tech-stack:
  added: [openpyxl, pandas, rapidfuzz]
  patterns: [streaming parser with batch processing, fuzzy matching with confidence scoring, bulk insert pattern with SQLAlchemy, temp file handling for uploads]

key-files:
  created:
    - backend/app/services/__init__.py
    - backend/app/services/excel_parser.py
    - backend/app/services/column_mapper.py
    - backend/app/services/variant_grouper.py
    - backend/app/routers/products.py
  modified:
    - backend/requirements.txt
    - backend/app/main.py

key-decisions:
  - "Use streaming Excel parser with 500-row batches for memory efficiency on large files"
  - "75% fuzzy match threshold for column mapping (balance between flexibility and accuracy)"
  - "Replace existing products on re-upload (idempotent upload for client)"
  - "Formula injection sanitization by prefixing with apostrophe"
  - "Return mapping confidence score (HIGH/MEDIUM/LOW) for user awareness"

patterns-established:
  - "Service class pattern: separate concerns into ExcelParser, FuzzyColumnMapper, VariantGrouper"
  - "Temp file handling: use tempfile.NamedTemporaryFile for upload processing, cleanup in finally block"
  - "Bulk insert pattern: build list of dicts, use SQLAlchemy insert() for performance"
  - "Two-phase insert: groups first (for FK), then products referencing group IDs"

# Metrics
duration: 3min
completed: 2026-01-22
---

# Phase 3 Plan 2: Excel Processing Pipeline Summary

**Streaming Excel parser with fuzzy column auto-mapping and variant grouping using openpyxl, RapidFuzz, and pandas**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-22T23:57:39Z
- **Completed:** 2026-01-22T24:00:53Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Streaming Excel parser handles large files without memory exhaustion (500-row batches)
- Fuzzy column mapper auto-detects Faire columns with 75% similarity threshold
- Variant grouper clusters products by Name/Token/SKU using pandas groupby
- Upload endpoint orchestrates parse → map → group → bulk insert pipeline
- Four product endpoints: upload, list groups, get group details, delete client products

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Excel processing dependencies and create service classes** - `6546481` (feat)
   - Added openpyxl, pandas, rapidfuzz dependencies
   - Created ExcelParser with streaming read_only mode
   - Created FuzzyColumnMapper with RapidFuzz for auto-mapping
   - Created VariantGrouper with pandas groupby

2. **Task 2: Create products router with upload endpoint** - `3114adc` (feat)
   - POST /products/upload with full pipeline
   - GET /products/groups for listing
   - GET /products/groups/{id} with variants
   - DELETE /products/client/{id} for cleanup

## Files Created/Modified

**Services:**
- `backend/app/services/__init__.py` - Service exports
- `backend/app/services/excel_parser.py` - Streaming Excel parser with openpyxl read_only mode
- `backend/app/services/column_mapper.py` - Fuzzy matcher with RapidFuzz (75% threshold)
- `backend/app/services/variant_grouper.py` - Pandas-based variant grouping by Name/Token/SKU

**API:**
- `backend/app/routers/products.py` - Four product endpoints with bulk operations
- `backend/app/main.py` - Added products router registration

**Config:**
- `backend/requirements.txt` - Added openpyxl, pandas, rapidfuzz

## Decisions Made

**1. Streaming parser with 500-row batches**
- Rationale: Large Excel files (10k+ rows) would exhaust memory if loaded entirely
- Implementation: openpyxl read_only=True mode with generator pattern
- Trade-off: Slightly more complex code for significant memory savings

**2. 75% fuzzy match threshold**
- Rationale: Balance between flexibility (catching typos, variations) and accuracy (avoiding false matches)
- Tested against: Faire column naming patterns from research phase
- Result: HIGH confidence when 5+ fields matched, MEDIUM when 3-4, LOW when missing required fields

**3. Idempotent upload (replace existing products)**
- Rationale: Re-uploading same file should replace old data, not duplicate
- Implementation: Delete all products/groups for client_id before insert
- Benefit: Simple UX - users don't worry about duplicates

**4. Formula injection sanitization**
- Rationale: Excel formulas in CSV exports can execute on open (security risk)
- Implementation: Prefix cells starting with =, +, -, @ with apostrophe
- Standard: OWASP CSV Injection prevention

**5. Return mapping confidence score**
- Rationale: Users should know if column detection was successful
- Levels: HIGH (5+ mapped), MEDIUM (3-4 mapped), LOW (missing required)
- UX: Enables frontend to show warning if confidence is MEDIUM/LOW

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all services and endpoints implemented as designed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for 03-03 (Field Selection UI):**
- ✅ Upload endpoint returns mapped_columns dict for UI display
- ✅ Upload endpoint returns unmapped_columns list for user awareness
- ✅ Upload endpoint returns mapping_confidence for warning display
- ✅ Product groups stored with variant_count for UI badges
- ✅ Products preserve row_index for correct export ordering in Phase 7

**Next steps:**
- 03-03: Build field selection UI for users to choose which columns feed AI prompts
- 03-04: Create dynamic prompt builder that adapts to selected fields
- 03-05: Build product status filtering for selective generation

**No blockers:** Excel processing pipeline complete and verified.

---
*Phase: 03-excel-processing*
*Completed: 2026-01-22*
