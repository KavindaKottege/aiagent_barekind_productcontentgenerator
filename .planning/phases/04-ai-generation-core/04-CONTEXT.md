# Phase 4: AI Generation Core - Context

**Gathered:** 2026-01-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Generate optimized product titles and descriptions at scale (5,000-10,000 products per batch) with real-time cost tracking, progress visibility, and robust error handling. This phase delivers the core content generation workflow: trigger generation → monitor progress → handle failures automatically → show completion summary. Review and export are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Generation Execution Model

- **Background job architecture**: Claude's discretion on implementation approach (Celery/Redis, long-polling, or other)
- **Continues in background**: Generation keeps running if user navigates away or closes browser
- **Parallel jobs per client**: Multiple clients can have simultaneous generation jobs running
- **Inline progress UI**: Progress appears directly on the page where Generate button was clicked (products list page)
- **Generate button on products list**: Initiate generation from products page after upload and field selection
- **Smart defaults only**: No settings modal or configuration before generation - use client's field selection and status filter already set
- **Block uploads during generation**: Prevent new upload while generation running (show blocking message)
- **Original Excel row order**: Process products in same order as uploaded file (top to bottom)
- **Completion summary**: Show stats (products generated, total cost, success rate, time elapsed) when job finishes
- **Cancel button always visible**: User can stop generation anytime - keeps products already generated with 'generated' status
- **Pause = graceful cancel + resume = skip completed**: Simple pause/resume - pause stops cleanly, resume skips products already in 'generated' status and continues with remaining 'pending' products
- **No job history**: Only show current/active jobs in UI (no historical generation log)
- **Auto-batch with progress**: System internally processes in chunks (batch size TBD) for rate limit management, but user sees single unified job with continuous progress
- **Shared execution system**: Regeneration (Phase 6) reuses same generation infrastructure - just another job type that targets 'rejected' status products

### Model and LangChain Integration

- **GPT-5.2 model**: Use latest GPT-5.2 for generation (user specified - verify model name during planning)
- **Full LangChain integration**: Use LangChain framework for prompt templates, chains, callbacks, token counting, retry logic
- **Generate once per product group**: Single API call per ProductGroup - same title/description applied to all variants (color, size options)
- **Full audit trail storage**: Store per generation attempt: prompt used, model version, timestamp, tokens consumed, cost, character counts, retry attempts, success/failure reason
- **Global temperature setting**: Single configurable temperature in app settings (applies to all clients) - not per-client

### Real-time Review Integration

- **Review during generation**: Users can start reviewing completed products while generation continues running
- **Real-time updates in review**: New products appear in review queue automatically as they complete (no page refresh needed)
- **Status badge in header**: Small badge/indicator in navigation shows active generation - click for details (doesn't obstruct review workflow)

### Cost Controls and Visibility

- **Total + projected cost display**: Show '$3.42 spent, ~$15.80 projected for 500 products' based on running average
- **$500 soft cap behavior**: Generation auto-pauses when cost hits limit - show dialog requiring explicit confirmation to continue with projected total
- **Configurable soft cap**: Global app setting (admin only) for cost limit - defaults to $500
- **Job-level cost storage**: Track total cost per generation job (not per individual product)
- **Cost dashboard**: Dedicated page showing total spend, spend by client, spend over time, average cost per product

### Retry and Failure Handling

- **Adaptive rate limit handling**: Read OpenAI's Retry-After header and respect exact wait time (most efficient)
- **3 retry attempts max**: Original attempt + 3 retries = 4 total attempts before marking product as failed
- **Character limit retry strategy**: If title/description exceeds limits, automatically retry with stricter prompt including explicit character limit enforcement
- **Failed status marking**: Products that fail after all retries marked with status='failed' and error message stored (user can view and manually retry later)

### Progress Tracking UX

- **Progress info shown**: Count + cost + time - '127 / 500 — $3.42 spent ($13.50 projected) — 2m 15s elapsed (est. 8m 30s remaining)'
- **Update frequency**: Send progress update after every product completion (real-time, most responsive)
- **Progress communication method**: Claude's discretion (WebSocket, SSE, or polling based on complexity vs real-time needs)
- **Persistent progress on return**: When user returns to app, immediately display current generation progress if job running - auto-reconnect to updates

### Claude's Discretion

- Background job implementation (Celery/Redis vs long-polling vs other approach)
- Internal batch size for rate limit management
- Progress communication technology (WebSocket vs SSE vs polling)
- Exact character limit retry prompt wording
- Time estimation algorithm for completion ETA
- Token counting and cost calculation precision

</decisions>

<specifics>
## Specific Ideas

- GPT-5.2 model requested (verify correct model name during research - may be GPT-4o or claude-opus-4-5)
- User emphasized: "make sure that generation and review can be done together, so that user can review as the next products are being generated" - seamless parallel workflow is critical
- Agencies need visibility but shouldn't be blocked - background execution with persistent progress on return
- Block uploads during generation to prevent data loss or confusion

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope. Review system (Phase 5), smart regeneration with feedback (Phase 6), and export (Phase 7) are already separate phases.

</deferred>

---

*Phase: 04-ai-generation-core*
*Context gathered: 2026-01-22*
