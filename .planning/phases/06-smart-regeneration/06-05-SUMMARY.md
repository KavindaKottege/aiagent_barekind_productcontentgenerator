---
phase: "06"
plan: "05"
subsystem: "regeneration-api"
tags: [regeneration, api, endpoints, arq, worker, feedback-loop]
depends_on:
  requires: ["06-01", "06-03"]
  provides: ["regeneration-endpoints", "worker-regeneration-context"]
  affects: ["06-06", "06-07"]
tech_stack:
  added: []
  patterns: ["regeneration-context-passing", "feedback-enhanced-prompts", "single-vs-batch-regeneration"]
files:
  created: []
  modified:
    - "backend/app/schemas/regeneration.py"
    - "backend/app/schemas/__init__.py"
    - "backend/app/routers/regeneration.py"
    - "backend/app/workers/generation_worker.py"
decisions: []
metrics:
  duration: "4.6 minutes"
  completed: "2026-01-29"
---

# Phase 6 Plan 5: Regeneration API Endpoints and Worker Integration Summary

**One-liner:** Single/batch regeneration endpoints with ARQ job creation and RegenerationContext-aware worker loop

## What Was Done

### Task 1: Regeneration Request/Response Schemas
Added API-facing Pydantic schemas to `backend/app/schemas/regeneration.py`:
- `RegenerateSingleRequest` with UUID `product_group_id`
- `RegenerateBatchRequest` with UUID `client_id`
- `RegenerationJobResponse` with job_id, status, total_count, is_regeneration, message
- `RegenerationEstimate` with rejected_count and estimated_cost
- Updated `__init__.py` exports

### Task 2: Regeneration API Endpoints
Extended `backend/app/routers/regeneration.py` (created by 06-04) with three new endpoints:
- **GET `/{client_id}/estimate`** - Returns count of rejected products and estimated cost (~$0.02/product)
- **POST `/regenerate-single`** - Regenerates a single product: validates ownership/API key, checks no active job, resets status to pending, clears edits, increments regeneration_count, creates GenerationJob targeting single product, enqueues to ARQ
- **POST `/{client_id}/regenerate-rejected`** - Batch regenerates all rejected products for a client: same validation, resets all rejected products, creates batch GenerationJob, enqueues to ARQ without target

Key design decisions in endpoints:
- Edited content (edited_title, edited_description) intentionally cleared on regeneration -- previous versions preserved in GenerationAudit history and restorable via 06-04 restore endpoint
- Uses `target_product_group_id` on GenerationJob for single-product mode (worker skips to that product)
- Direct ARQ pool creation for enqueueing (matches generation router pattern)
- Active job conflict check prevents concurrent generation per client

### Task 3: Worker RegenerationContext Integration
Updated `backend/app/workers/generation_worker.py`:
- Added `RegenerationContext` import from regeneration schemas
- After loading primary_product, before title generation: builds `RegenerationContext` when `product_group.regeneration_count > 0`
- Context carries: previous_title, previous_description, rejection_reasons, ai_review_safety_flags, regeneration_count
- Passes `regeneration_context=regeneration_context` to both `generate_title()` and `generate_description()` calls
- 06-03 already added `_build_feedback_section()` method and prompt injection in AI service, so the full pipeline is wired

## Deviations from Plan

None - plan executed exactly as written. 06-03 and 06-04 had already completed their parallel work, so all dependencies were available.

## Key Technical Details

- **Regeneration flow:** Endpoint resets product -> creates job -> ARQ worker picks up -> detects regeneration_count > 0 -> builds RegenerationContext -> passes to AI service -> AI service injects feedback into prompts
- **Single vs batch:** Single uses `target_product_group_id` on the job; batch queries all pending products for client
- **UUID consistency:** All IDs use UUID type (not str) per 06-01 pattern
- **Cost estimation:** Simple $0.02/product heuristic for estimate endpoint

## Verification Results

All checks passed:
1. Schemas import correctly (RegenerateSingleRequest, RegenerateBatchRequest, RegenerationJobResponse, RegenerationEstimate)
2. Router has all 3 new endpoints (/estimate, /regenerate-single, /regenerate-rejected)
3. Worker builds RegenerationContext when regeneration_count > 0
4. AI service generate_title and generate_description accept regeneration_context parameter

## Commits

| Hash | Type | Description |
|------|------|-------------|
| bc3db92 | feat | Add regeneration API request/response schemas |
| b5d3c5a | feat | Add regeneration API endpoints to router |
| e22220e | feat | Integrate RegenerationContext into generation worker |
