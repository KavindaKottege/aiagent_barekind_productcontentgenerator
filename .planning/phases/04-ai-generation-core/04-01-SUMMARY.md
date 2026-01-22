---
phase: 04
plan: 01
subsystem: ai-generation-foundation
tags: [dependencies, database, models, schemas, langchain, openai, arq, job-tracking, audit-trail]

requires:
  - phase: 03
    deliverables: [ProductGroup model, field selection, variant grouping]
  - phase: 02
    deliverables: [Client model with prompts]
  - phase: 01
    deliverables: [Database, authentication, user model]

provides:
  - GenerationJob and GenerationAudit models
  - Phase 4 dependencies (LangChain, OpenAI, ARQ, tiktoken, tenacity, SSE)
  - Pydantic schemas for generation API
  - Database migration 007 for generation tables

affects:
  - plan: 04-02
    impact: "Job and audit models ready for service layer"
  - plan: 04-03
    impact: "ARQ and LangChain dependencies installed for background workers"
  - plan: 04-04
    impact: "Schemas ready for API endpoints"

tech-stack:
  added:
    - langchain-core >=0.3.0 (prompt templates, chains, callbacks)
    - langchain-openai >=0.2.0 (OpenAI model bindings, structured output)
    - openai >=1.0.0 (Official OpenAI SDK)
    - arq >=0.26.0 (async Redis task queue)
    - redis >=5.0.0 (Redis client for ARQ)
    - tiktoken >=0.8.0 (Official OpenAI tokenizer for cost tracking)
    - tenacity >=9.0.0 (Retry logic with exponential backoff)
    - sse-starlette >=2.0.0 (Server-Sent Events for FastAPI)
  patterns:
    - Decimal precision for cost tracking (10,4 for job totals, 10,6 for audit records)
    - Async background job architecture (ARQ with Redis)
    - Full audit trail pattern (per-product generation attempts)
    - Job status state machine (pending → running → paused/completed/failed/cancelled)
    - Progressive cost tracking (total_cost + projected_cost)

key-files:
  created:
    - backend/requirements.txt (Phase 4 dependencies section)
    - backend/app/models/generation_job.py (Job tracking model)
    - backend/app/models/generation_audit.py (Audit trail model)
    - backend/alembic/versions/007_create_generation_tables.py (Database migration)
    - backend/app/schemas/generation.py (API schemas)
  modified:
    - backend/app/models/__init__.py (Export new models)
    - backend/app/schemas/__init__.py (Export new schemas)

decisions:
  - id: D04-01-01
    decision: "Use ARQ for background job processing"
    rationale: "Native asyncio support for FastAPI, 7x faster than Celery for short jobs, simpler configuration, pessimistic execution prevents double-processing"
    alternatives: ["Celery (more mature but sync-focused)", "FastAPI BackgroundTasks (no persistence)"]

  - id: D04-01-02
    decision: "Store cost with Decimal precision (not float)"
    rationale: "Avoid floating-point precision errors in cost tracking - critical for accurate billing and user trust"
    impact: "All cost fields use Numeric(10,4) for job totals, Numeric(10,6) for per-product audit"

  - id: D04-01-03
    decision: "Full audit trail with per-product generation attempts"
    rationale: "Track every generation attempt (including retries) with prompt, tokens, cost, duration for debugging, cost analysis, and quality improvement"
    impact: "GenerationAudit table stores all attempts, not just successful ones"

  - id: D04-01-04
    decision: "Job status state machine with 6 states"
    rationale: "Clear state transitions: pending (queued) → running (active) → paused/completed/failed/cancelled (terminal states)"
    impact: "Status field indexed for efficient job queries, supports pause/resume workflow"

metrics:
  tasks: 3/3
  commits: 3
  files_created: 5
  files_modified: 2
  duration: 3m 0s
  completed: 2026-01-23
---

# Phase 04 Plan 01: Dependencies and Models Summary

**One-liner:** LangChain/OpenAI/ARQ dependencies installed, GenerationJob and GenerationAudit models created with Decimal cost tracking and full audit trail

## What Was Built

This plan established the foundation for AI generation by installing Phase 4 dependencies (LangChain, OpenAI, ARQ, tiktoken, tenacity, SSE) and creating database models for job tracking and audit trails.

### Task 1: Phase 4 Dependencies

**Added 8 production dependencies:**

1. **langchain-core >=0.3.0** - Prompt templates, chains, callbacks, LLM orchestration framework
2. **langchain-openai >=0.2.0** - OpenAI model bindings with structured output support
3. **openai >=1.0.0** - Official OpenAI SDK for direct API access
4. **arq >=0.26.0** - Async Redis task queue (native asyncio, 7x faster than Celery for short jobs)
5. **redis >=5.0.0** - Redis client for ARQ job queue
6. **tiktoken >=0.8.0** - Official OpenAI tokenizer for accurate token counting and cost calculation
7. **tenacity >=9.0.0** - Retry logic with exponential backoff (OpenAI recommended)
8. **sse-starlette >=2.0.0** - Server-Sent Events for real-time progress updates

**Installation verified:** All packages installed without conflicts, imports work correctly.

### Task 2: GenerationJob and GenerationAudit Models

**GenerationJob model** (`backend/app/models/generation_job.py`):
- Tracks job status: pending → running → paused/completed/failed/cancelled
- Progress counters: total_count, completed_count, success_count, failed_count
- Cost tracking with Decimal precision: total_cost, projected_cost (Numeric 10,4)
- Time tracking: started_at, completed_at, paused_at
- Error tracking: error_message for failed jobs
- Foreign keys: client_id, user_id (CASCADE delete)
- Relationships: audit_records (one-to-many)

**GenerationAudit model** (`backend/app/models/generation_audit.py`):
- Per-product generation attempt tracking (including retries)
- Model metadata: model_version, temperature
- Full prompt storage: prompt_used (Text field)
- Generated output: generated_title, generated_description
- Token tracking: input_tokens, output_tokens
- Cost tracking: cost per attempt (Numeric 10,6 for precision)
- Character validation: title_length, description_length
- Retry metadata: attempt_number (1 for first, 2+ for retries)
- Success tracking: success flag, error_message
- Performance tracking: duration_ms
- Foreign keys: job_id, product_group_id (CASCADE delete)

**Migration 007** (`backend/alembic/versions/007_create_generation_tables.py`):
- Creates generation_jobs table with indexes on client_id, user_id, status
- Creates generation_audits table with indexes on job_id, product_group_id
- All timestamps use timezone-aware DateTime
- Foreign key constraints with CASCADE delete
- Default values for counters and costs (0)
- Applied successfully to database

### Task 3: Pydantic Schemas for Generation API

**Request schemas:**
- `GenerateRequest` - Start generation job for client
- `PauseJobRequest` - Pause running job
- `ResumeJobRequest` - Resume paused job
- `CancelJobRequest` - Cancel job

**Response schemas:**
- `GenerationJobResponse` - Full job details with all fields
- `GenerationProgressResponse` - Real-time progress with elapsed/remaining time estimates
- `GenerationJobSummary` - Completion summary (successful, failed, total cost, elapsed time)
- `GenerationAuditResponse` - Full audit record details

**List schemas:**
- `JobListResponse` - Paginated job list
- `AuditListResponse` - Paginated audit list

All schemas use `from_attributes=True` for ORM model conversion.

## Deviations from Plan

None - plan executed exactly as written. All dependencies installed, models created, migration applied successfully.

## Decisions Made

**D04-01-01: Use ARQ for background job processing**
- **Rationale:** Native asyncio support for FastAPI, 7x faster than Celery for short jobs, simpler configuration
- **Alternatives considered:** Celery (more mature but sync-focused), FastAPI BackgroundTasks (no persistence)
- **Impact:** Workers will use async/await pattern, Redis required for job queue

**D04-01-02: Store cost with Decimal precision**
- **Rationale:** Avoid floating-point precision errors - critical for accurate billing and user trust
- **Implementation:** Numeric(10,4) for job totals, Numeric(10,6) for per-product audit
- **Impact:** All cost calculations must use Decimal type

**D04-01-03: Full audit trail with per-product generation attempts**
- **Rationale:** Track every generation attempt (including retries) for debugging, cost analysis, quality improvement
- **Storage:** GenerationAudit stores all attempts, not just successful ones
- **Impact:** Complete historical record for cost analysis and prompt optimization

**D04-01-04: Job status state machine with 6 states**
- **States:** pending (queued) → running (active) → paused/completed/failed/cancelled (terminal)
- **Rationale:** Clear state transitions support pause/resume workflow
- **Impact:** Status field indexed for efficient queries, workers check status before each product

## Technical Implementation

### Database Schema

**generation_jobs table:**
```sql
- id (UUID, PK)
- client_id (UUID, FK → clients.id)
- user_id (UUID, FK → users.id)
- status (VARCHAR 50, indexed) - pending/running/paused/completed/failed/cancelled
- total_count, completed_count, success_count, failed_count (INTEGER)
- total_cost, projected_cost (NUMERIC 10,4)
- started_at, completed_at, paused_at (TIMESTAMPTZ)
- error_message (VARCHAR 1000)
- created_at, updated_at (TIMESTAMPTZ)
```

**generation_audits table:**
```sql
- id (UUID, PK)
- job_id (UUID, FK → generation_jobs.id, indexed)
- product_group_id (UUID, FK → product_groups.id, indexed)
- model_version (VARCHAR 100) - "gpt-5.2", "gpt-4o", etc.
- temperature (NUMERIC 3,2)
- prompt_used (TEXT)
- generated_title (VARCHAR 255), generated_description (TEXT)
- input_tokens, output_tokens (INTEGER)
- cost (NUMERIC 10,6)
- title_length, description_length (INTEGER)
- attempt_number (INTEGER) - 1 for first, 2+ for retries
- success (BOOLEAN)
- error_message (VARCHAR 1000)
- duration_ms (INTEGER)
- created_at (TIMESTAMPTZ)
```

### Dependencies Rationale

1. **LangChain** - Industry standard for LLM orchestration, native OpenAI integration, structured output validation
2. **OpenAI SDK** - Official API client, handles rate limits, streaming
3. **ARQ** - Chosen over Celery for native asyncio support (FastAPI compatibility), simpler config, faster for short jobs
4. **tiktoken** - Official OpenAI tokenizer, 3-6x faster than alternatives, required for accurate cost tracking
5. **tenacity** - OpenAI recommended retry library, supports exponential backoff, Retry-After header respect
6. **sse-starlette** - Production-ready SSE for FastAPI, W3C compliant, better than polling for real-time progress

## Testing Performed

1. **Dependency installation:** `pip install -r requirements.txt` succeeded without conflicts
2. **Import verification:** All Phase 4 packages import correctly (langchain_openai, arq, tiktoken, tenacity, sse_starlette)
3. **Migration application:** `alembic upgrade head` applied migration 007 successfully
4. **Table verification:** Both generation_jobs and generation_audits tables created with correct columns and indexes
5. **Model imports:** GenerationJob and GenerationAudit models import and reference correct tables
6. **Schema imports:** All Pydantic schemas import correctly from app.schemas.generation

## Files Changed

**Created:**
- `backend/app/models/generation_job.py` (94 lines) - Job tracking model
- `backend/app/models/generation_audit.py` (96 lines) - Audit trail model
- `backend/alembic/versions/007_create_generation_tables.py` (92 lines) - Migration
- `backend/app/schemas/generation.py` (130 lines) - API schemas

**Modified:**
- `backend/requirements.txt` (+10 lines) - Phase 4 dependencies section
- `backend/app/models/__init__.py` (+3 lines) - Export new models
- `backend/app/schemas/__init__.py` (+13 lines) - Export new schemas

**Total:** 5 files created, 2 files modified, 425+ lines added

## Commits

1. **16f12e2** - `feat(04-01): add Phase 4 AI generation dependencies`
   - Added 8 production dependencies to requirements.txt
   - LangChain, OpenAI, ARQ, tiktoken, tenacity, sse-starlette

2. **3b0fc23** - `feat(04-01): create GenerationJob and GenerationAudit models with migration`
   - GenerationJob model with status tracking, progress counters, Decimal cost fields
   - GenerationAudit model with full audit trail (prompt, tokens, cost, duration)
   - Migration 007 with proper indexes and foreign keys
   - Updated models/__init__.py exports

3. **476b4b0** - `feat(04-01): create Pydantic schemas for generation API`
   - Request/response schemas for generation endpoints
   - Progress tracking schemas with time estimates
   - Summary and list schemas for completion stats
   - Updated schemas/__init__.py exports

## Next Phase Readiness

**Ready for 04-02 (AI Generation Service Layer):**
- ✅ GenerationJob and GenerationAudit models available
- ✅ LangChain and OpenAI dependencies installed
- ✅ tiktoken available for token counting
- ✅ tenacity available for retry logic
- ✅ Database tables created with proper indexes
- ✅ Pydantic schemas ready for API validation

**Ready for 04-03 (ARQ Background Workers):**
- ✅ ARQ and Redis dependencies installed
- ✅ Job status tracking model ready
- ✅ Audit trail model ready for per-product recording

**Ready for 04-04 (Real-time Progress with SSE):**
- ✅ sse-starlette installed
- ✅ GenerationProgressResponse schema ready
- ✅ Job model has all fields for progress tracking

**Blockers:** None

**Concerns:** None - all dependencies installed cleanly, models tested, migration applied successfully

## Lessons Learned

1. **Decimal precision critical for cost tracking** - Using Numeric instead of Float prevents rounding errors that could accumulate across thousands of products
2. **Full audit trail pays dividends** - Tracking every attempt (including failures) enables cost analysis, prompt optimization, and debugging
3. **ARQ simpler than expected** - Native asyncio support makes integration with FastAPI straightforward compared to Celery
4. **Indexed status field essential** - Will enable efficient queries for active jobs, failed jobs, etc.

## Performance Metrics

- **Duration:** 3 minutes
- **Tasks completed:** 3/3 (100%)
- **Dependencies added:** 8 packages
- **Models created:** 2 (GenerationJob, GenerationAudit)
- **Database tables:** 2 with 6 indexes total
- **API schemas:** 11 schemas for requests, responses, lists, summaries

---

*Phase: 04-ai-generation-core*
*Plan: 01 of 5*
*Completed: 2026-01-23*
