# Phase 4: AI Generation Core - Research

**Researched:** 2026-01-23
**Domain:** Large-scale AI content generation with LangChain, OpenAI API, background job processing, and real-time progress tracking
**Confidence:** HIGH

## Summary

This phase implements large-scale AI content generation (5,000-10,000 products per batch) using LangChain with OpenAI's GPT-5.2 model, background job processing for long-running operations, and real-time progress tracking via Server-Sent Events. The standard approach combines ARQ (async Redis queue) for job management, LangChain for prompt engineering and token tracking, and FastAPI's native SSE support for real-time updates.

The architecture requires careful attention to rate limiting (OpenAI's Retry-After header), cost tracking (tiktoken for token counting), and concurrent database updates (SQLAlchemy async with proper locking). The user specified GPT-5.2 as the model choice, which is OpenAI's flagship model released in late 2025 with API identifiers `gpt-5.2`, `gpt-5.2-chat-latest`, and `gpt-5.2-pro`.

**Primary recommendation:** Use ARQ for background jobs (native asyncio support for FastAPI), LangChain for prompt templates and structured output validation, Server-Sent Events for real-time progress (simpler than WebSocket for unidirectional updates), and Tenacity for retry logic with exponential backoff. Implement cost tracking at the job level with running totals and ETA calculations based on running averages.

## Standard Stack

The established libraries/tools for this domain:

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| langchain-core | >=0.3.0 | Prompt templates, chains, callbacks | Industry standard for LLM orchestration, native OpenAI integration |
| langchain-openai | >=0.2.0 | OpenAI model bindings | Official LangChain provider for OpenAI, supports structured output |
| openai | >=1.0.0 | OpenAI API client | Official SDK, handles rate limits, streaming |
| arq | >=0.26.0 | Async Redis task queue | Native asyncio support, 7x faster than RQ for short jobs, pessimistic execution |
| redis | >=5.0.0 | Redis client for ARQ | Standard async Redis client for Python |
| tiktoken | >=0.8.0 | Token counting for OpenAI models | Official OpenAI tokenizer, 3-6x faster than alternatives |
| tenacity | >=9.0.0 | Retry logic with exponential backoff | OpenAI recommended, Apache 2.0, decorator-based API |
| sse-starlette | >=2.0.0 | Server-Sent Events for FastAPI | Production-ready SSE, W3C compliant, Starlette/FastAPI native |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | >=2.0.0 | Structured output validation | Already in project, use for LLM response schemas |
| asyncpg | >=0.29.0 | Async PostgreSQL driver | Already in project, use for job status persistence |
| sqlalchemy[asyncio] | >=2.0.0 | Async ORM | Already in project, use for job/audit models |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ARQ | Celery + Redis | Celery more feature-rich but sync-focused, requires more config, heavier for async FastAPI |
| ARQ | FastAPI BackgroundTasks | Built-in but no persistence, crashes lose jobs, no status tracking, blocks event loop for heavy tasks |
| SSE | WebSocket | WebSocket bidirectional but overkill for one-way progress updates, more complex connection management |
| SSE | Polling | Polling simpler but inefficient, higher latency, more server load |
| Tenacity | backoff library | Both work, Tenacity has better docs and more flexible API |
| tiktoken | LangChain token counting | tiktoken more accurate and faster, LangChain uses tiktoken internally |

**Installation:**

```bash
# Add to backend/requirements.txt
langchain-core>=0.3.0
langchain-openai>=0.2.0
openai>=1.0.0
arq>=0.26.0
redis>=5.0.0
tiktoken>=0.8.0
tenacity>=9.0.0
sse-starlette>=2.0.0
```

## Architecture Patterns

### Recommended Project Structure

```
backend/app/
├── services/
│   ├── ai_generation.py        # LangChain prompt building, OpenAI calls
│   ├── job_manager.py           # ARQ job enqueue/status/cancel operations
│   └── cost_tracker.py          # Token counting, cost calculation
├── workers/
│   ├── __init__.py
│   ├── generation_worker.py     # ARQ worker functions
│   └── worker_settings.py       # ARQ WorkerSettings config
├── models/
│   ├── generation_job.py        # Job status, progress, cost tracking
│   └── generation_audit.py      # Per-product generation audit trail
├── routers/
│   ├── generation.py            # POST /generate, GET /jobs/{id}
│   └── generation_sse.py        # GET /jobs/{id}/progress (SSE endpoint)
└── schemas/
    ├── generation.py            # Request/response schemas
    └── ai_output.py             # Pydantic models for structured LLM output
```

### Pattern 1: ARQ Background Job Pattern

**What:** Async task queue with Redis backing, separate worker process for job execution
**When to use:** Long-running operations (5k-10k products), need persistence, want status tracking

**Example:**

```python
# workers/worker_settings.py
from arq import WorkerSettings
from app.config import settings

async def startup(ctx):
    """Initialize worker context with DB pool, etc."""
    ctx['db_pool'] = await create_async_engine(settings.DATABASE_URL)

async def shutdown(ctx):
    """Cleanup worker resources."""
    await ctx['db_pool'].dispose()

class WorkerSettings:
    redis_settings = settings.REDIS_URL
    functions = [generation_worker]
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 10  # Concurrent jobs per worker
    job_timeout = 3600  # 1 hour max per job
    keep_result = 3600  # Keep job result for 1 hour

# workers/generation_worker.py
from arq.connections import ArqRedis
from app.services.ai_generation import AIGenerationService
from app.services.cost_tracker import CostTracker

async def generation_worker(ctx, job_id: str, client_id: int, user_id: int):
    """Worker function for AI generation job."""
    db = ctx['db_pool']

    service = AIGenerationService(db)
    tracker = CostTracker()

    try:
        await service.update_job_status(job_id, 'running')

        # Fetch products in batches
        products = await service.get_pending_products(client_id)
        total = len(products)

        for idx, product in enumerate(products):
            # Generate content
            result = await service.generate_content(product, tracker)

            # Update progress
            progress = {
                'completed': idx + 1,
                'total': total,
                'cost': tracker.total_cost,
                'projected_cost': tracker.projected_cost(total, idx + 1)
            }
            await service.update_job_progress(job_id, progress)

            # Check pause/cancel
            job_status = await service.get_job_status(job_id)
            if job_status in ['paused', 'cancelled']:
                break

        await service.update_job_status(job_id, 'completed')

    except Exception as e:
        await service.update_job_status(job_id, 'failed', str(e))
        raise

# services/job_manager.py
from arq import create_pool
from arq.jobs import Job

class JobManager:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._pool = None

    async def get_pool(self) -> ArqRedis:
        if not self._pool:
            self._pool = await create_pool(self.redis_url)
        return self._pool

    async def enqueue_generation(
        self, job_id: str, client_id: int, user_id: int
    ) -> Job:
        pool = await self.get_pool()
        job = await pool.enqueue_job(
            'generation_worker',
            job_id,
            client_id,
            user_id,
            _job_id=job_id  # Use our UUID as ARQ job ID
        )
        return job

    async def get_job_status(self, job_id: str) -> dict:
        pool = await self.get_pool()
        job = Job(job_id, pool)
        return await job.info()
```

**Source:** [ARQ Official Documentation](https://arq-docs.helpmanual.io/), [FastAPI-ARQ Tutorial](https://davidmuraya.com/blog/fastapi-background-tasks-arq-vs-built-in/)

### Pattern 2: LangChain Structured Output with Pydantic

**What:** Use LangChain's `.with_structured_output()` for validated LLM responses
**When to use:** Need guaranteed JSON format, want automatic validation, character limit enforcement

**Example:**

```python
# schemas/ai_output.py
from pydantic import BaseModel, Field, field_validator

class ProductContent(BaseModel):
    """Structured output schema for product generation."""
    title: str = Field(..., min_length=30, max_length=60)
    description: str = Field(..., min_length=2000, max_length=3000)

    @field_validator('title')
    def validate_title_length(cls, v):
        if not 30 <= len(v) <= 60:
            raise ValueError(f"Title must be 30-60 chars, got {len(v)}")
        return v

    @field_validator('description')
    def validate_description_length(cls, v):
        if not 2000 <= len(v) <= 3000:
            raise ValueError(f"Description must be 2000-3000 chars, got {len(v)}")
        return v

# services/ai_generation.py
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.schemas.ai_output import ProductContent

class AIGenerationService:
    def __init__(self, db):
        self.db = db
        self.model = ChatOpenAI(
            model="gpt-5.2",
            temperature=0.7,  # From app settings
            api_key=settings.OPENAI_API_KEY
        ).with_structured_output(ProductContent, strict=True)

    def build_prompt(self, product: ProductGroup, client_prompts: dict) -> str:
        """Build prompt dynamically based on selected fields."""
        # Get client's ai_input_fields setting
        fields = client.ai_input_fields or [
            'product_name', 'description', 'product_type',
            'option_name', 'country_of_origin', 'sku', 'images'
        ]

        # Build field context
        field_data = []
        for field in fields:
            value = getattr(product, field, None)
            if value:
                field_data.append(f"{field}: {value}")

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", client_prompts['title_prompt'] or DEFAULT_TITLE_PROMPT),
            ("system", client_prompts['description_prompt'] or DEFAULT_DESC_PROMPT),
            ("system", "CHARACTER LIMITS: Title must be exactly 30-60 characters. Description must be exactly 2000-3000 characters. Count carefully."),
            ("user", "Product details:\n" + "\n".join(field_data))
        ])

        return prompt_template

    async def generate_content(
        self, product: ProductGroup, tracker: CostTracker
    ) -> ProductContent:
        """Generate content with retry logic and token tracking."""
        prompt = self.build_prompt(product, client_prompts)

        # Use with_retry for automatic retry on failures
        from tenacity import retry, stop_after_attempt, wait_exponential

        @retry(
            stop=stop_after_attempt(4),  # 1 original + 3 retries
            wait=wait_exponential(multiplier=1, min=4, max=60),
            reraise=True
        )
        async def _generate_with_retry():
            try:
                # Invoke model with structured output
                result = await self.model.ainvoke(prompt)

                # Track tokens (from response metadata)
                usage = result.response_metadata.get('token_usage', {})
                tracker.add_tokens(
                    usage.get('prompt_tokens', 0),
                    usage.get('completion_tokens', 0)
                )

                return result

            except ValidationError as e:
                # Character limit violated - modify prompt and retry
                if 'must be' in str(e) and 'chars' in str(e):
                    prompt.messages.append(
                        ("system", "CRITICAL: Previous output violated character limits. You MUST count characters and stay within 30-60 for title, 2000-3000 for description.")
                    )
                raise

        return await _generate_with_retry()
```

**Source:** [LangChain Structured Output Documentation](https://docs.langchain.com/oss/python/langchain/structured-output), [Pydantic Validation Guide](https://www.oreateai.com/blog/langchain-structured-output-pydantic/a501c565cd439d58bb1c5fb94af3b084)

### Pattern 3: Server-Sent Events for Real-Time Progress

**What:** HTTP-based unidirectional streaming from server to client
**When to use:** Real-time progress updates, simpler than WebSocket, works through firewalls

**Example:**

```python
# routers/generation_sse.py
from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse
from app.services.job_manager import JobManager
import asyncio

router = APIRouter()

@router.get("/jobs/{job_id}/progress")
async def stream_job_progress(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager),
    current_user: User = Depends(get_current_user)
):
    """Stream job progress via SSE."""

    async def event_generator():
        """Generate SSE events for job progress."""
        try:
            while True:
                # Poll job status from database
                job = await job_manager.get_job_with_progress(job_id)

                if not job:
                    yield {
                        "event": "error",
                        "data": json.dumps({"error": "Job not found"})
                    }
                    break

                # Send progress update
                yield {
                    "event": "progress",
                    "data": json.dumps({
                        "status": job.status,
                        "completed": job.completed_count,
                        "total": job.total_count,
                        "cost": str(job.total_cost),
                        "projected_cost": str(job.projected_cost),
                        "elapsed_time": job.elapsed_seconds,
                        "estimated_remaining": job.estimated_seconds_remaining
                    })
                }

                # End stream when job finishes
                if job.status in ['completed', 'failed', 'cancelled']:
                    yield {
                        "event": "complete",
                        "data": json.dumps({
                            "status": job.status,
                            "summary": {
                                "total_products": job.total_count,
                                "successful": job.success_count,
                                "failed": job.failed_count,
                                "total_cost": str(job.total_cost),
                                "elapsed_time": job.elapsed_seconds
                            }
                        })
                    }
                    break

                # Poll every 500ms (2 updates/second)
                await asyncio.sleep(0.5)

        except asyncio.CancelledError:
            # Client disconnected
            pass

    return EventSourceResponse(event_generator())
```

**Source:** [FastAPI SSE Tutorial](https://mahdijafaridev.medium.com/implementing-server-sent-events-sse-with-fastapi-real-time-updates-made-simple-6492f8bfc154), [sse-starlette PyPI](https://pypi.org/project/sse-starlette/)

### Pattern 4: OpenAI Rate Limit Handling with Retry-After

**What:** Respect OpenAI's Retry-After header for adaptive rate limiting
**When to use:** All OpenAI API calls to avoid 429 errors and optimize throughput

**Example:**

```python
# services/ai_generation.py
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import RateLimitError
import time

class AdaptiveRateLimiter:
    """Handles OpenAI rate limits with Retry-After header."""

    def __init__(self):
        self.last_retry_after = None
        self.backoff_until = None

    async def wait_if_needed(self):
        """Wait if we have active backoff."""
        if self.backoff_until:
            wait_seconds = self.backoff_until - time.time()
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
            self.backoff_until = None

    def handle_rate_limit(self, error: RateLimitError):
        """Extract Retry-After and set backoff."""
        retry_after = error.response.headers.get('Retry-After')
        if retry_after:
            self.backoff_until = time.time() + int(retry_after)
            self.last_retry_after = int(retry_after)
        else:
            # Fallback exponential backoff if no header
            self.backoff_until = time.time() + (self.last_retry_after or 1) * 2

# Use with tenacity
from tenacity import retry, stop_after_attempt, wait_random_exponential

@retry(
    stop=stop_after_attempt(4),
    wait=wait_random_exponential(multiplier=1, min=1, max=60),
    retry=retry_if_exception_type(RateLimitError),
    reraise=True
)
async def call_openai_with_retry(prompt: str):
    """Call OpenAI with automatic retry on rate limits."""
    try:
        return await openai_client.chat.completions.create(
            model="gpt-5.2",
            messages=[{"role": "user", "content": prompt}]
        )
    except RateLimitError as e:
        # Log rate limit hit
        logger.warning(f"Rate limit hit, retrying after backoff")
        raise
```

**Source:** [OpenAI Rate Limits Documentation](https://platform.openai.com/docs/guides/rate-limits), [OpenAI Cookbook - Handling Rate Limits](https://cookbook.openai.com/examples/how_to_handle_rate_limits)

### Pattern 5: Cost Tracking with Running Averages

**What:** Track tokens per generation, calculate running average, project total cost
**When to use:** Real-time cost visibility, soft cap enforcement, user transparency

**Example:**

```python
# services/cost_tracker.py
from decimal import Decimal
import tiktoken

class CostTracker:
    """Tracks tokens and costs for generation jobs."""

    # GPT-5.2 pricing (as of Jan 2026)
    PRICING = {
        'gpt-5.2': {
            'input': Decimal('1.75') / Decimal('1_000_000'),   # $1.75/1M tokens
            'output': Decimal('14.00') / Decimal('1_000_000'),  # $14.00/1M tokens
            'cached_input': Decimal('0.175') / Decimal('1_000_000')  # 90% discount
        }
    }

    def __init__(self, model: str = 'gpt-5.2'):
        self.model = model
        self.encoding = tiktoken.encoding_for_model(model)

        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_generations = 0
        self.total_cost = Decimal('0')

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        return len(self.encoding.encode(text))

    def add_tokens(self, input_tokens: int, output_tokens: int):
        """Add token usage and calculate cost."""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_generations += 1

        pricing = self.PRICING[self.model]
        input_cost = Decimal(input_tokens) * pricing['input']
        output_cost = Decimal(output_tokens) * pricing['output']

        self.total_cost += (input_cost + output_cost)

    def average_cost_per_generation(self) -> Decimal:
        """Calculate running average cost per product."""
        if self.total_generations == 0:
            return Decimal('0')
        return self.total_cost / Decimal(self.total_generations)

    def projected_cost(self, total_products: int, completed: int) -> Decimal:
        """Project total cost based on running average."""
        avg_cost = self.average_cost_per_generation()
        remaining = total_products - completed
        return self.total_cost + (avg_cost * Decimal(remaining))

    def check_soft_cap(self, soft_cap: Decimal) -> bool:
        """Check if current cost exceeds soft cap."""
        return self.total_cost >= soft_cap

    def to_dict(self) -> dict:
        """Export tracking data."""
        return {
            'total_input_tokens': self.total_input_tokens,
            'total_output_tokens': self.total_output_tokens,
            'total_cost': float(self.total_cost),
            'average_cost': float(self.average_cost_per_generation()),
            'generations': self.total_generations
        }
```

**Source:** [OpenAI API Pricing](https://platform.openai.com/docs/pricing), [tiktoken GitHub](https://github.com/openai/tiktoken), [Token Counting Guide](https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them)

### Anti-Patterns to Avoid

- **Using FastAPI BackgroundTasks for long-running jobs:** No persistence, no status tracking, crashes lose all work, blocks event loop
- **Polling database every 100ms for progress:** Inefficient, high DB load; use SSE with 500ms-1s poll interval or Redis pub/sub
- **Storing full prompts in job progress table:** Bloats table; store in audit trail only, reference by job_id
- **Counting characters instead of tokens for cost:** Inaccurate (1 token ≠ 1 char); always use tiktoken
- **Ignoring streaming token count issues:** LangChain's `get_openai_callback` returns zero tokens when streaming; use response metadata instead
- **Global OpenAI client without connection pooling:** Connection leaks; use httpx with connection pool limits
- **Hardcoded retry delays:** Use Retry-After header from OpenAI, fallback to exponential backoff
- **Updating job progress on every token:** Database overwhelm; batch updates every N products (e.g., every 5-10 products)
- **Not using database-side updates for concurrent access:** Race conditions; use SQLAlchemy `update()` with WHERE clause, not fetch-modify-update

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Token counting | Character count * 0.75 estimate | tiktoken library | Token-to-char ratio varies by language/content, tiktoken is official OpenAI tokenizer, 3-6x faster than alternatives |
| Retry logic | Custom sleep loops | Tenacity with wait_exponential | Handles jitter, max attempts, exponential backoff, Retry-After header respect, exception filtering |
| Background job queue | Python threading or multiprocessing | ARQ (or Celery) | Need persistence (crashes), status tracking, distributed workers, health checks |
| SSE connection management | Raw asyncio generators | sse-starlette EventSourceResponse | Handles connection cleanup, client reconnect, proper headers, event formatting |
| Prompt template management | String formatting | LangChain PromptTemplate | Variable validation, message roles, template reuse, few-shot examples |
| LLM output validation | Regex parsing of text | LangChain with_structured_output | Uses OpenAI function calling for guaranteed JSON, automatic validation, retry on format errors |
| Rate limit detection | Catch generic exceptions | Specific RateLimitError handling | OpenAI SDK provides typed exceptions, access to Retry-After header, proper error context |
| Cost calculation | Manual pricing tables | tiktoken + pricing config | Pricing changes, tiktoken ensures accurate token count, Decimal for precision |
| Job status tracking | In-memory dictionaries | PostgreSQL with proper indexes | Persistence, crash recovery, multi-worker coordination, audit trail |
| Database connection pooling | Manual connection management | SQLAlchemy AsyncEngine with pool | Connection reuse, health checks, timeout handling, automatic cleanup |

**Key insight:** AI generation at scale has many edge cases (rate limits, token counting precision, concurrent job coordination, connection cleanup) that standard libraries handle better than custom code. Use battle-tested libraries and focus on business logic.

## Common Pitfalls

### Pitfall 1: Streaming Token Count Loss

**What goes wrong:** Using LangChain's `get_openai_callback()` with streaming returns zero token counts, causing cost tracking to fail

**Why it happens:** OpenAI streaming API doesn't include token usage in stream chunks by default; must opt-in with `stream_options={"include_usage": true}`

**How to avoid:**
- Don't rely on `get_openai_callback()` for streaming
- Access token usage from response metadata: `result.response_metadata.get('token_usage')`
- For true streaming UI, estimate tokens with tiktoken upfront, refine with actual usage after stream completes
- Use non-streaming for this phase (simpler, accurate token counts)

**Warning signs:** Cost always shows $0.00, token counts in audit table are zero

**Source:** [LangChain GitHub Issue #30390](https://github.com/langchain-ai/langchain/issues/30390), [LangChain Token Counting Issue #13430](https://github.com/langchain-ai/langchain/issues/13430)

### Pitfall 2: Connection Pool Exhaustion in Workers

**What goes wrong:** ARQ workers leak database connections, eventually hitting max connections and blocking new jobs

**Why it happens:** Async context managers not properly closed, SQLAlchemy sessions not disposed, connection pool not configured for worker lifecycle

**How to avoid:**
- Use async context manager for sessions: `async with session_factory() as session:`
- Configure engine pool size: `create_async_engine(url, pool_size=10, max_overflow=20)`
- Set `pool_pre_ping=True` to check connection health before use
- Use ARQ's `on_shutdown` to explicitly dispose engine: `await ctx['db_pool'].dispose()`
- Set `pool_recycle=3600` to recycle connections every hour (prevents stale connections)

**Warning signs:** "Too many connections" errors, worker processes hanging, Redis job queue backing up

**Source:** [SQLAlchemy Async Best Practices](https://uniguardme.com/blog/fastapi-and-sqlalchemy-mastering-async), [Connection Pool Issues](https://coderanch.com/t/525566/databases/ConnectionPool-causing-memory-leak)

### Pitfall 3: Race Conditions in Job Status Updates

**What goes wrong:** Multiple workers or concurrent requests update job status, causing lost updates or inconsistent state (e.g., job marked "paused" but worker continues processing)

**Why it happens:** Using fetch-then-update pattern instead of atomic database operations, no locking on status transitions

**How to avoid:**
- Use SQLAlchemy's `update()` with WHERE clause for atomic updates:
  ```python
  stmt = update(GenerationJob).where(
      GenerationJob.id == job_id,
      GenerationJob.status == 'running'  # Only update if still running
  ).values(status='paused')
  result = await session.execute(stmt)
  if result.rowcount == 0:
      # Status already changed, handle accordingly
  ```
- Use database-level optimistic locking with version column
- For reads requiring consistency, use `with_for_update()` (pessimistic lock)
- Check job status before each batch of products, not just at start

**Warning signs:** Jobs show "paused" but keep generating, cost exceeds soft cap, duplicate generations

**Source:** [FastAPI Race Conditions](https://python.plainenglish.io/optimising-database-updates-in-fastapi-application-to-prevent-race-conditions-eda349b5a68e), [SQLAlchemy Locks](https://medium.com/@mojimich2015/sqlalchemy-database-locks-using-fastapi-a-simple-guide-3e7dcd552d87)

### Pitfall 4: Character Limit Violations Not Caught

**What goes wrong:** LLM generates title with 61 characters or description with 1,950 characters, but system doesn't retry, stores invalid content

**Why it happens:** Pydantic validation not enabled, structured output not used, character counting done on tokens instead of actual characters

**How to avoid:**
- Use Pydantic models with `field_validator` for character counts:
  ```python
  @field_validator('title')
  def validate_title(cls, v):
      if not 30 <= len(v) <= 60:
          raise ValueError(f"Title must be 30-60 chars, got {len(v)}")
      return v
  ```
- Enable strict mode: `.with_structured_output(ProductContent, strict=True)`
- In retry prompt, explicitly state character limits: "Title MUST be 30-60 characters. Description MUST be 2000-3000 characters. Count carefully."
- After retry failure, log violation and mark as failed with clear error message

**Warning signs:** Products have titles longer than 60 chars, descriptions under 2000 chars, no retry attempts logged

**Source:** [Pydantic Validation Guide](https://www.oreateai.com/blog/langchain-structured-output-pydantic/a501c565cd439d58bb1c5fb94af3b084)

### Pitfall 5: Cost Tracking Drift from Actual OpenAI Charges

**What goes wrong:** Internal cost tracking shows $12.50, but OpenAI bill shows $13.20 for same job

**Why it happens:** Using rough estimates (chars * 0.75), not counting system messages in prompts, pricing table outdated, Decimal precision issues

**How to avoid:**
- Always use tiktoken to count actual tokens
- Count ALL messages including system prompts: `encoding.encode(str(all_messages))`
- Store pricing as Decimal (not float) for precision: `Decimal('1.75')`
- Count tokens for both input (prompt + examples) and output (generation)
- Add 10% buffer to projected costs for safety margin
- Verify pricing monthly from OpenAI pricing page
- Use actual token counts from API responses, not pre-counted estimates

**Warning signs:** Projected costs consistently under actual costs, users surprised by bills, token counts don't match OpenAI dashboard

**Source:** [OpenAI Token Counting](https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them), [tiktoken Documentation](https://github.com/openai/tiktoken)

### Pitfall 6: Soft Cap Not Enforced (Runaway Costs)

**What goes wrong:** Job exceeds $500 soft cap but continues running, user gets $800 bill

**Why it happens:** Cost check only at job start/end, not during execution; worker ignores paused status; no user confirmation required

**How to avoid:**
- Check cost after every product generation:
  ```python
  if tracker.check_soft_cap(soft_cap):
      await job_manager.pause_job(job_id, reason='soft_cap_hit')
      await notification_service.notify_user(
          user_id,
          f"Generation paused: ${tracker.total_cost:.2f} spent, ${tracker.projected_cost(total, completed):.2f} projected"
      )
      break
  ```
- Require explicit user action to continue (API call to resume job with higher cap)
- Log soft cap hit with timestamp, current cost, projected cost
- Resume only if user confirms OR job updated with higher cap
- Store cap acknowledgment in audit trail

**Warning signs:** Jobs complete without pausing despite exceeding cap, no user notifications, runaway costs reported

**Source:** [Production Pitfalls](https://medium.com/codetodeploy/production-pitfalls-of-langchain-nobody-warns-you-about-44a86e2df29e)

### Pitfall 7: Memory Leaks in Long-Running Workers

**What goes wrong:** ARQ worker memory grows from 200MB to 2GB over 1000 products, eventually crashes

**Why it happens:** LangChain chains accumulate callbacks in memory, Pydantic models not garbage collected, prompt templates cached indefinitely, database sessions not closed

**How to avoid:**
- Create fresh LangChain model instance for each batch (not globally):
  ```python
  for batch in batches:
      model = ChatOpenAI(...).with_structured_output(...)  # Fresh instance
      results = await process_batch(batch, model)
      del model  # Explicit cleanup
  ```
- Use session-scoped database connections, close after each batch
- Clear prompt template caches periodically
- Monitor worker memory, restart workers after N jobs (ARQ health checks)
- Set ARQ `max_jobs=100` to restart worker after 100 jobs
- Use `tracemalloc` in development to identify leaks

**Warning signs:** Worker RSS memory grows continuously, worker crashes after ~1000 products, "Out of memory" errors

**Source:** [Memory Leaks in Background Workers](https://github.com/taskforcesh/bullmq/issues/282), [Connection Pool Leaks](https://support.aspnetzero.com/QA/Questions/10756/Connection-leakConnection-pool-issue-with-background-job)

### Pitfall 8: SSE Connection Accumulation (Zombie Connections)

**What goes wrong:** SSE connections remain open after user navigates away, server hits connection limit, new users can't connect

**Why it happens:** Client doesn't close EventSource on unmount, server doesn't detect disconnection, no connection timeout

**How to avoid:**
- Frontend: Close EventSource on component unmount:
  ```javascript
  useEffect(() => {
      const eventSource = new EventSource(`/api/jobs/${jobId}/progress`)
      return () => eventSource.close()  // Cleanup
  }, [jobId])
  ```
- Backend: Handle `asyncio.CancelledError` to detect client disconnect
- Set SSE connection timeout (5 minutes idle = disconnect)
- Send periodic "ping" events (every 30s) to keep connection alive
- Track active connections, log when they exceed threshold
- Use `sse-starlette`'s built-in connection management

**Warning signs:** Server file descriptor limit hit, "Too many open files" errors, SSE endpoint slow for new users

**Source:** [FastAPI SSE Best Practices](https://mahdijafaridev.medium.com/implementing-server-sent-events-sse-with-fastapi-real-time-updates-made-simple-6492f8bfc154)

## Code Examples

Verified patterns from official sources:

### LangChain Prompt Template with Dynamic Fields

```python
# Source: LangChain Prompt Templates Documentation
from langchain_core.prompts import ChatPromptTemplate

def build_dynamic_prompt(product: ProductGroup, client: Client) -> ChatPromptTemplate:
    """Build prompt dynamically based on client's selected fields."""

    # Get selected fields (or defaults)
    selected_fields = client.ai_input_fields or [
        'product_name', 'description', 'product_type',
        'option_name', 'country_of_origin', 'sku', 'images'
    ]

    # Build field context
    field_context = []
    for field in selected_fields:
        value = getattr(product, field, None)
        if value:
            if field == 'images' and isinstance(value, list):
                field_context.append(f"Images: {len(value)} product images available")
            else:
                field_context.append(f"{field.replace('_', ' ').title()}: {value}")

    # Custom prompts from client settings (or defaults)
    title_prompt = client.title_prompt or """
    You are an expert product title writer for online marketplaces.
    Create a compelling, SEO-optimized product title that is EXACTLY 30-60 characters long.
    Count every character including spaces. The title must be between 30 and 60 characters.
    """

    description_prompt = client.description_prompt or """
    You are an expert product description writer for online marketplaces.
    Create a detailed, engaging product description that is EXACTLY 2000-3000 characters long.
    Count every character including spaces and punctuation. The description must be between 2000 and 3000 characters.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", title_prompt),
        ("system", description_prompt),
        ("system", "CHARACTER LIMIT ENFORCEMENT: You MUST count characters carefully. Title: 30-60 chars. Description: 2000-3000 chars. Do not violate these limits."),
        ("user", "Product information:\n\n" + "\n".join(field_context))
    ])

    return prompt
```

### Tenacity Retry with OpenAI Rate Limits

```python
# Source: OpenAI Cookbook - How to Handle Rate Limits
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type
)
from openai import RateLimitError, APIError

@retry(
    stop=stop_after_attempt(4),  # 1 original + 3 retries
    wait=wait_random_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((RateLimitError, APIError)),
    reraise=True
)
async def generate_with_retry(model, prompt):
    """Generate content with automatic retry on rate limits."""
    return await model.ainvoke(prompt)
```

### ARQ Job Status Checking in Worker

```python
# Source: ARQ Documentation
async def generation_worker(ctx, job_id: str, client_id: int):
    """Worker with pause/cancel support."""
    service = AIGenerationService(ctx['db'])

    products = await service.get_pending_products(client_id)

    for idx, product in enumerate(products):
        # Check for pause/cancel before each product
        job = await service.get_job(job_id)

        if job.status == 'cancelled':
            await service.finalize_job(job_id, 'cancelled')
            return {'status': 'cancelled', 'completed': idx}

        if job.status == 'paused':
            await service.finalize_job(job_id, 'paused')
            return {'status': 'paused', 'completed': idx}

        # Generate content
        result = await service.generate_content(product)

        # Update progress
        await service.update_progress(job_id, idx + 1, len(products))
```

### Atomic Job Status Update with SQLAlchemy

```python
# Source: FastAPI SQLAlchemy Concurrency Best Practices
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

async def pause_job(session: AsyncSession, job_id: str) -> bool:
    """Atomically pause a running job."""
    stmt = (
        update(GenerationJob)
        .where(
            GenerationJob.id == job_id,
            GenerationJob.status == 'running'  # Only if still running
        )
        .values(
            status='paused',
            paused_at=datetime.utcnow()
        )
    )

    result = await session.execute(stmt)
    await session.commit()

    # Check if update succeeded
    if result.rowcount == 0:
        # Job wasn't running, already paused/completed/cancelled
        return False

    return True
```

### SSE Event Generator with Proper Cleanup

```python
# Source: sse-starlette Documentation
from sse_starlette.sse import EventSourceResponse
import asyncio

async def progress_event_generator(job_id: str, db):
    """Generate SSE events with proper cleanup."""
    try:
        while True:
            job = await get_job_with_progress(db, job_id)

            if not job:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "Job not found"})
                }
                break

            # Send progress
            yield {
                "event": "progress",
                "data": json.dumps({
                    "completed": job.completed_count,
                    "total": job.total_count,
                    "cost": str(job.total_cost),
                    "projected_cost": str(job.projected_cost)
                })
            }

            # Complete on terminal status
            if job.status in ['completed', 'failed', 'cancelled', 'paused']:
                yield {
                    "event": "complete",
                    "data": json.dumps({"status": job.status})
                }
                break

            await asyncio.sleep(0.5)  # 2 updates/second

    except asyncio.CancelledError:
        # Client disconnected, cleanup
        pass
    finally:
        # Always cleanup database connection
        await db.close()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Celery for async tasks | ARQ for FastAPI async | 2023-2024 | Native asyncio, 7x faster for short jobs, simpler config |
| Manual OpenAI API calls | LangChain with structured output | 2024-2025 | Guaranteed JSON format, automatic validation, easier prompt management |
| Polling for progress | Server-Sent Events | 2023-2024 | Lower latency, less server load, real-time updates |
| Exponential backoff only | Retry-After header + backoff | 2025-2026 | More efficient rate limit handling, faster recovery |
| cl100k_base encoding | o200k_base encoding | Late 2025 | GPT-5.2 and newer models use o200k_base |
| LangChain callbacks for tokens | Response metadata + tiktoken | 2025 | More accurate, works with streaming |
| OpenAI Batch API for scale | Standard API with streaming | 2025-2026 | Batch has 24hr latency, standard with streaming better UX for 5-10k products |
| Float for cost calculations | Decimal for precision | Always | Avoid floating-point precision errors in cost tracking |

**Deprecated/outdated:**

- **Celery for async Python web apps:** Still works but ARQ is better fit for asyncio-native frameworks like FastAPI
- **LangChain's `get_openai_callback()` for streaming:** Returns zero tokens with streaming, use response metadata instead
- **Manual JSON parsing from LLM text:** OpenAI function calling (structured output) guarantees JSON format
- **Fixed retry delays:** OpenAI provides Retry-After header, use it for optimal throughput
- **GPT-4 for production:** GPT-5.2 is more cost-efficient per quality unit despite higher per-token cost

## Open Questions

Things that couldn't be fully resolved:

1. **GPT-5.2 vs GPT-5.2-pro model choice**
   - What we know: GPT-5.2 is standard model ($1.75/$14 per 1M tokens), GPT-5.2-pro uses more compute for better answers (pricing unclear from search results)
   - What's unclear: Exact pricing for GPT-5.2-pro, whether quality improvement justifies cost for product content generation
   - Recommendation: Start with GPT-5.2 standard, make model configurable in app settings for easy A/B testing

2. **Optimal batch size for rate limit management**
   - What we know: OpenAI has rate limits by tokens/minute and requests/minute, varies by tier
   - What's unclear: Project's tier limits, optimal batch size to maximize throughput without hitting limits
   - Recommendation: Start with 10 products per batch, monitor rate limit errors, adjust dynamically based on Retry-After headers

3. **ARQ vs Celery final decision**
   - What we know: ARQ is 7x faster for short jobs, native asyncio, simpler; Celery more mature, more features
   - What's unclear: Team familiarity with either, whether advanced features (task routing, priority queues) needed in future
   - Recommendation: Use ARQ for this phase (better FastAPI fit), can migrate to Celery later if needed (interface similar)

4. **SSE vs WebSocket for progress updates**
   - What we know: SSE simpler, unidirectional, works through firewalls; WebSocket bidirectional, more complex
   - What's unclear: Whether future phases need bidirectional communication (e.g., user feedback during generation)
   - Recommendation: Use SSE for this phase (simpler, sufficient), can add WebSocket in Phase 6 if needed for real-time feedback

5. **Token counting precision for cached prompts**
   - What we know: OpenAI provides 90% discount on cached input tokens, requires prompt caching setup
   - What's unclear: Whether prompt caching applies to structured output, how to detect cached tokens in response
   - Recommendation: Ignore caching for v1 cost tracking (conservative estimates), investigate for future optimization

## Sources

### Primary (HIGH confidence)

- [OpenAI API Rate Limits Documentation](https://platform.openai.com/docs/guides/rate-limits) - Official rate limiting guidance
- [OpenAI Cookbook - Handling Rate Limits](https://cookbook.openai.com/examples/how_to_handle_rate_limits) - Retry strategies
- [OpenAI API Pricing](https://platform.openai.com/docs/pricing) - GPT-5.2 pricing ($1.75/$14 per 1M tokens)
- [OpenAI Models Documentation - GPT-5.2](https://platform.openai.com/docs/models/gpt-5.2) - Model identifiers and capabilities
- [tiktoken GitHub Repository](https://github.com/openai/tiktoken) - Official tokenizer
- [ARQ Official Documentation](https://arq-docs.helpmanual.io/) - Task queue features
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/) - When to use vs external queues
- [LangChain Structured Output Documentation](https://docs.langchain.com/oss/python/langchain/structured-output) - with_structured_output usage
- [Tenacity Documentation](https://tenacity.readthedocs.io/) - Retry library
- [sse-starlette PyPI](https://pypi.org/project/sse-starlette/) - SSE library for FastAPI

### Secondary (MEDIUM confidence)

- [Managing Background Tasks in FastAPI: ARQ vs BackgroundTasks](https://davidmuraya.com/blog/fastapi-background-tasks-arq-vs-built-in/) - ARQ tutorial (Aug 2025)
- [Building Resilient Task Queues with ARQ Retries](https://davidmuraya.com/blog/fastapi-arq-retries/) - ARQ retry patterns (Oct 2025)
- [Implementing SSE with FastAPI](https://mahdijafaridev.medium.com/implementing-server-sent-events-sse-with-fastapi-real-time-updates-made-simple-6492f8bfc154) - SSE tutorial
- [LangChain Structured Output with Pydantic](https://www.oreateai.com/blog/langchain-structured-output-pydantic/a501c565cd439d58bb1c5fb94af3b084) - Validation patterns
- [FastAPI Polling Strategy for Long Tasks](https://openillumi.com/en/en-fastapi-long-task-progress-polling/) - Progress tracking (Oct 2025)
- [Optimising Database Updates in FastAPI](https://python.plainenglish.io/optimising-database-updates-in-fastapi-application-to-prevent-race-conditions-eda349b5a68e) - Race condition prevention
- [SQLAlchemy Async Session Management](https://uniguardme.com/blog/fastapi-and-sqlalchemy-mastering-async) - Connection pooling
- [OpenAI Token Counting Guide](https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them) - Official token counting
- [Tenacity Retry Tutorial](https://johal.in/tenacity-retries-exponential-backoff-decorators-2026/) - 2026 guide

### Tertiary (LOW confidence - for validation)

- [Production Pitfalls of LangChain](https://medium.com/codetodeploy/production-pitfalls-of-langchain-nobody-warns-you-about-44a86e2df29e) - Jan 2026 blog post
- [LangChain Token Counting Issues](https://github.com/langchain-ai/langchain/issues/30390) - Streaming token bug (Mar 2025)
- [Common AI Content Generation Mistakes](https://www.highervisibility.com/seo/learn/common-pitfalls-ai-generated-content/) - 2025 article
- [FastAPI Race Conditions Blog](https://datasciocean.com/en/other/fastapi-race-condition/) - Feb 2025
- [Connection Pool Memory Leaks](https://support.aspnetzero.com/QA/Questions/10756/Connection-leakConnection-pool-issue-with-background-job) - General pattern

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - Official documentation verified for all core libraries (LangChain, OpenAI, ARQ, tiktoken, Tenacity, sse-starlette)
- Architecture patterns: HIGH - Patterns verified through official docs and recent tutorials from 2025-2026
- Pitfalls: MEDIUM-HIGH - Pitfalls verified through GitHub issues, multiple blog posts, and production experience reports
- GPT-5.2 specifics: MEDIUM - Model exists and is available, pricing verified, but limited production experience reports (recently released Dec 2025)
- Cost tracking precision: HIGH - tiktoken is official OpenAI library, pricing verified from official page
- ARQ vs Celery recommendation: MEDIUM - ARQ clearly better for asyncio, but less mature ecosystem than Celery

**Research date:** 2026-01-23

**Valid until:** ~30 days (Feb 2026) for stable components (ARQ, SQLAlchemy, FastAPI patterns), ~7 days for fast-moving components (GPT-5.2 pricing/features, LangChain updates, OpenAI rate limits)

**Note:** GPT-5.2 was released December 2025, so production patterns are still emerging. Monitor LangChain and OpenAI release notes for updates.
