# Pitfalls Research

**Domain:** AI-Powered SaaS Content Generation (Next.js + FastAPI + OpenAI/LangChain)
**Researched:** 2026-01-22
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Uncontrolled OpenAI API Cost Explosion

**What goes wrong:**
Production costs spiral out of control. Single user requests can trigger 15+ LLM calls and cost $5 in tokens. One team discovered a $12,000 OpenAI bill caused by a recursive chain with no monitoring. Variable costs tie directly to usage, with recursive chains generating thousands of tokens in seconds.

**Why it happens:**
- LangChain chains make it easy to compose multiple LLM calls without visibility into the total cost
- No token budgets or limits per request or user
- Retry logic without exponential backoff or max attempts
- Missing cost monitoring and alerting
- Developers test with gpt-4 in development, forget to optimize for production

**How to avoid:**
- Implement per-request token budgets using `max_tokens` parameter (set to actual needs, not maximum)
- Track costs in real-time using LangSmith or custom telemetry
- Set up cost alerts before deploying (e.g., alert when daily spend exceeds $X)
- Use cheaper models (gpt-4o-mini) for operations that don't require maximum intelligence
- Implement rate limiting per user/organization
- Add circuit breakers to prevent runaway chains (maxIterations=5, maxToolCalls=10)
- Cache LLM responses for identical requests
- Estimate costs before executing chains and warn users

**Warning signs:**
- API bills increasing faster than user growth
- Average tokens per request above 5,000
- Retry logic triggering frequently
- No cost monitoring dashboard
- Developers unsure what each feature costs
- Chain execution times above 30 seconds regularly

**Phase to address:**
Phase 1 (Foundation) - Cost controls must be architectural from day one. Retrofitting is extremely expensive.

---

### Pitfall 2: OpenAI Rate Limit Errors in Production

**What goes wrong:**
Users encounter "429: Too Many Requests" or RateLimitError during normal usage. OpenAI enforces requests per minute (RPM) and tokens per minute (TPM). For Tier 1: ~500k TPM and ~1,000 RPM. Even legitimate traffic can hit these limits, causing failed generations and poor UX.

**Why it happens:**
- No retry logic with exponential backoff
- Parallel requests exceed rate limits (batch processing Excel rows)
- `max_tokens` set too high, inflating TPM consumption
- Testing doesn't simulate production concurrency
- Using a single API key for all users (shared rate limits)

**How to avoid:**
- Implement exponential backoff retry logic (wait 1s, 2s, 4s, 8s, max 5 retries)
- Set `max_tokens` to actual needs, not maximum (TPM counts max of input + max_tokens)
- Use job queues to serialize/throttle requests instead of parallel processing
- Monitor rate limit headers in responses
- Consider Azure OpenAI for dedicated capacity if needed
- Implement user-facing rate limits before hitting OpenAI's limits
- Test with production-like concurrency

**Warning signs:**
- 429 errors in logs
- Users reporting "generation failed" intermittently
- Spiky traffic patterns causing failures
- No retry logic visible in code
- Excel batch processing runs all rows in parallel

**Phase to address:**
Phase 1 (Foundation) - Must be in place before any user-facing features.

---

### Pitfall 3: LangChain Error Handling Gaps

**What goes wrong:**
Agent execution fails silently or crashes the entire request. Tools fail without graceful degradation. Missing error context makes debugging impossible. Production LangChain applications face runaway agents, inconsistent outputs, fragile tools, and observability blind spots.

**Why it happens:**
- Generic try-except blocks swallow error context
- Tools tested individually but fail in combination
- No structured error handling per tool
- Agent executor doesn't implement proper error recovery
- Missing observability into which tool failed and why

**How to avoid:**
- Wrap each tool with dedicated error handling
- Use structured error types that preserve context (which tool, what inputs, agent state, retry attempts)
- Set `handle_parsing_errors=True` or provide custom error handler in Agent executor
- Implement circuit breaker pattern for external API tools
- Use LangSmith or OpenTelemetry for detailed trace capture
- Validate tool outputs with schemas
- Never let tool errors crash the agent - return error message to agent for recovery
- Test tool combinations, not just individual tools

**Warning signs:**
- Generic error messages like "Agent failed"
- Can't reproduce errors from logs
- Production errors you've never seen in development
- No visibility into which LLM calls happened before failure
- Missing structured logging with trace IDs
- Error rates above 2% in production

**Phase to address:**
Phase 2 (Core Generation) - Must be robust before scaling features.

---

### Pitfall 4: Excel Processing Memory Crashes

**What goes wrong:**
Node.js process crashes with "JavaScript heap out of memory" when processing large Excel files. A 2.3MB file with 11,000 rows × 33 columns can consume 600MB RAM. Users upload 50MB+ files and the server dies.

**Why it happens:**
- Loading entire Excel file into memory at once
- Using non-streaming Excel libraries (SheetJS without streaming mode)
- Not limiting file upload size
- Processing all rows in parallel instead of batching
- ExcelJS doesn't release memory after reading/writing
- No memory profiling in development with realistic file sizes

**How to avoid:**
- Use ExcelJS streaming API for files >10MB or >10,000 rows
- Always call `.commit()` when writing with ExcelJS
- Disable Excel features you don't use (reduces memory)
- Limit upload file size (e.g., 25MB max) with clear error messages
- Process rows in batches (100-500 rows at a time)
- Use streaming write for output generation
- Test with realistic large files in development
- Monitor memory usage and set Node.js heap limits appropriately

**Warning signs:**
- "heap out of memory" errors in logs
- Memory usage growing linearly with file size
- Server crashes when processing large files
- No file size limits enforced
- Loading entire workbook before processing
- Using `xlsx.readFile()` instead of streaming

**Phase to address:**
Phase 2 (Core Generation) - Critical for production readiness.

---

### Pitfall 5: FastAPI Background Tasks Misuse

**What goes wrong:**
Long-running content generation tasks block API responses or fail silently. Built-in BackgroundTasks has critical limitations: no status tracking, no return value access, tasks run in same process (CPU-intensive tasks slow entire API), and if server crashes, tasks are lost.

**Why it happens:**
- Using BackgroundTasks for operations longer than 30 seconds
- No job queue for persistent task tracking
- Missing progress updates for users
- Client doesn't know if generation succeeded or failed
- No way to cancel long-running tasks

**How to avoid:**
- Use built-in BackgroundTasks only for fire-and-forget operations <30 seconds (email notifications)
- Implement proper job queue (Redis + ARQ for async-first, or Celery) for content generation
- Store job status in database with states: pending, running, completed, failed
- Provide job status endpoint for polling or WebSocket for real-time updates
- Implement task timeouts and cancellation
- Log all background task failures
- Consider serverless limitations if deploying to Vercel (10s timeout on free tier)

**Warning signs:**
- API requests timing out during generation
- Users have no way to check generation status
- Tasks failing silently with no error reporting
- Missing job queue infrastructure
- FastAPI logs show BackgroundTasks for long operations
- No database table for job tracking

**Phase to address:**
Phase 2 (Core Generation) - Required for async content generation workflow.

---

### Pitfall 6: Next.js + FastAPI CORS & Authentication Hellscape

**What goes wrong:**
CORS errors in production despite working locally. Authentication breaks when deploying frontend and backend separately. Cookie transmission fails in multi-layer architecture (Next.js client → Next.js server → FastAPI). NextAuth tight coupling makes FastAPI endpoints dependent on Next.js payload.

**Why it happens:**
- Using wildcard "*" for CORS allow_origins in production
- Not understanding the request flow: browser → Next.js → FastAPI requires cookie forwarding
- CORS middleware ordered incorrectly (must be last)
- Different domains for frontend/backend in production vs. localhost
- Not rebuilding Docker images after CORS config changes
- Missing CORS headers for preflight OPTIONS requests

**How to avoid:**
- Set specific allowed origins in production (no wildcards): `["https://app.example.com"]`
- Place CORSMiddleware after all other middleware in FastAPI
- Forward authentication cookies from Next.js server to FastAPI using `@hey-api/client-next`
- Best practice: Deploy frontend and backend on same domain (avoids CORS entirely)
- If using NextAuth, use FastAPI library for NextAuth token validation
- Test authentication flow in production-like environment before deployment
- Document the full request path and where auth happens

**Warning signs:**
- CORS errors only in production, not development
- Authentication works in Postman but fails from browser
- Cookies not being sent to backend
- Using `allow_origins=["*"]` in production code
- No documented authentication architecture
- Different domains for API and app

**Phase to address:**
Phase 1 (Foundation) - Must establish correct architecture early.

---

### Pitfall 7: Multi-Tenant Data Leakage

**What goes wrong:**
Users can access other organizations' data by modifying IDs. Missing WHERE clauses in queries expose cross-tenant data. Even small oversights like missing `organization_id` in one endpoint lead to catastrophic data breaches. Single layer of defense (like RLS) eventually fails.

**Why it happens:**
- Client-supplied IDs without authorization checks
- Inconsistent tenant filtering across endpoints
- Copy-pasting queries and forgetting `WHERE organization_id = $1`
- Testing with single tenant, missing multi-tenant bugs
- No automated testing for tenant isolation

**How to avoid:**
- Implement row-level security (RLS) in database as baseline
- Add application-level tenant checks (defense in depth, never rely on single layer)
- Use query builder or ORM that enforces tenant filters automatically
- Extract current user's organization from JWT, never from request parameters
- Code review checklist: "Does this query filter by organization_id?"
- Automated tests: Create two orgs, verify user A cannot access org B's data
- Use database views that automatically filter by tenant
- Log all data access with tenant context for audit trails

**Warning signs:**
- Queries missing organization_id filters
- Taking organization ID from request body/query params
- No automated multi-tenant test suite
- Database queries don't consistently use tenant context
- Missing audit logging
- RLS not configured in database

**Phase to address:**
Phase 1 (Foundation) - Multi-tenancy must be architectural from start.

---

### Pitfall 8: AI Hallucination Quality Control Failure

**What goes wrong:**
AI generates plausible but incorrect product descriptions. Users publish hallucinated content to live e-commerce sites, damaging client relationships. 77% of businesses are concerned about AI hallucinations, and even latest models have >15% hallucination rates. It's mathematically proven hallucinations cannot be completely eliminated.

**Why it happens:**
- No human review loop before content goes live
- Trusting AI output without validation
- Poor training data or biases in prompts
- Missing quality checks specific to e-commerce domain
- No way for users to report/flag bad outputs

**How to avoid:**
- Implement mandatory human review before publishing (don't auto-publish AI content)
- Build "Auto Review" feature (already in your prototype) - surface it prominently
- Add confidence scores to generated content
- Provide editing interface for human refinement
- Track and display which content is AI-generated vs. human-edited
- Implement domain-specific validation (e.g., product attributes must match Excel data exactly)
- Add user feedback loop to flag hallucinations
- Test with "test-time compute" models (GPT-4 with reasoning) for complex content
- Show diffs when regenerating content so users can verify changes

**Warning signs:**
- Users reporting factual errors in generated content
- No review step in workflow
- Auto-publishing to production without human check
- Missing edit UI for AI outputs
- No tracking of AI vs. human-edited content
- Clients complaining about incorrect product details

**Phase to address:**
Phase 2 (Core Generation) - Quality controls must ship with generation features.

---

### Pitfall 9: Vercel Serverless Deployment Limitations

**What goes wrong:**
FastAPI deployment fails due to 250MB uncompressed size limit. LangChain, OpenAI SDK, and dependencies exceed Vercel's function size limits. 10-second timeout kills long-running generation tasks. Cold starts add 2-5 seconds to first request.

**Why it happens:**
- Vercel designed for Next.js frontends, not Python backends
- FastAPI + LangChain dependencies are heavy (often 200MB+)
- Including unnecessary files in deployment
- Not understanding serverless constraints
- Using Vercel because it's easy for Next.js, not because it fits backend needs

**How to avoid:**
- **Option 1 (Recommended):** Deploy FastAPI separately to proper backend platform (Railway, Render, Fly.io, AWS Lambda with API Gateway, GCP Cloud Run)
- **Option 2:** If using Vercel, exclude unnecessary files using `excludeFiles` in vercel.json
- **Option 3:** Split heavy dependencies into separate services
- Use environment variables for large config instead of bundling
- Implement job queue for tasks exceeding timeout (offload to separate worker)
- Test deployment package size before pushing to production
- Consider containerized deployment for full control

**Warning signs:**
- "Function exceeds 250MB" deployment errors
- Timeouts on generation endpoints
- Cold start latency above 3 seconds
- Fighting platform limitations instead of building features
- Multiple GitHub issues about Vercel deployment

**Phase to address:**
Phase 0 (Architecture Decision) - Choose deployment platform based on requirements, not convenience.

---

### Pitfall 10: Streaming Response Timeout Issues

**What goes wrong:**
Long-running AI generations timeout before completion. Users see partial content then connection drops. OpenAI streaming breaks if generation takes too long. No indication to user that generation is still in progress.

**Why it happens:**
- Not using streaming API for long generations
- Reverse proxy (nginx, cloudflare) has shorter timeout than generation time
- No keep-alive signals during long operations
- Client-side timeout shorter than server timeout
- Missing loading indicators during streaming

**How to avoid:**
- Use OpenAI streaming API for all content generation (partial results appear within 5-6 seconds)
- If no tokens after 6 seconds, terminate and retry
- Configure reverse proxy timeouts appropriately (120+ seconds for streaming)
- Send periodic keep-alive events (heartbeat every 15 seconds)
- Implement client-side timeout handling with retry
- Show progressive loading with token counts or estimated time
- Consider chunking long content into multiple requests
- Fallback to job queue if streaming fails

**Warning signs:**
- Users reporting "generation stops halfway"
- Timeout errors in proxy logs
- Not using streaming API
- No progressive loading UI
- 504 Gateway Timeout errors
- Missing timeout configuration documentation

**Phase to address:**
Phase 2 (Core Generation) - Streaming should be default from start.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Using `max_tokens` at model maximum | Simpler code, no calculation | Inflated costs, rate limit waste | Never - always calculate needed tokens |
| Generic try-except blocks | Fast to write | Impossible to debug production issues | Never - use typed exceptions |
| Loading entire Excel in memory | Simple code | Memory crashes, scale limits | Only for files <5MB, <1000 rows |
| Built-in BackgroundTasks for generation | No infrastructure setup | Lost tasks, no status, blocks workers | Never for tasks >30s or user-facing |
| CORS wildcard "*" | Works everywhere | Security risk, production issues | Only in local development |
| Single API key for all users | Easy setup | Shared rate limits, no user tracking | Only for MVP with <10 users |
| No cost monitoring | Faster to ship | Surprise bills, no optimization | Never - instrument from day 1 |
| Skipping multi-tenant tests | Faster testing | Data leakage in production | Never in multi-tenant SaaS |
| Auto-publishing AI content | Seamless UX | Hallucinations in production | Never - always require review |
| Deploying to Vercel for simplicity | Easy Next.js integration | Size limits, timeouts, fighting platform | Only for prototype/MVP |

---

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| OpenAI API | No retry logic for rate limits | Implement exponential backoff (1s, 2s, 4s, 8s, max 5 retries) |
| LangChain Tools | Tools tested individually only | Test tool combinations, implement per-tool error handling |
| Excel Processing | Loading entire file with `readFile()` | Use ExcelJS streaming API for files >10MB |
| FastAPI → Next.js | Not forwarding auth cookies through layers | Use `@hey-api/client-next` with cookie forwarding |
| Background Jobs | Using built-in BackgroundTasks for long operations | Use Redis + ARQ or Celery with status tracking |
| Database Queries | Missing `organization_id` filters | Use ORM with automatic tenant filtering + RLS |
| OpenAI Streaming | No timeout handling | Terminate if no tokens after 6s, implement keep-alive |
| File Uploads | No size limits | Enforce limits (25MB) with clear error messages |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Parallel LLM calls per Excel row | Fast for 10 rows | Rate limits, timeout batches, serialize with queue | >50 rows or >5 concurrent users |
| In-memory job tracking | Simple state management | Lost on restart, use Redis/DB for persistence | First server restart with pending jobs |
| Synchronous content generation | Simple request/response | API timeouts, poor UX, use job queue + polling | Generation >10 seconds |
| No caching of LLM responses | Fresh results | Expensive repeated calls, add Redis cache for identical requests | >100 generations/day |
| Single API key shared | Easy setup | Rate limit sharing, no user quotas, use key per org or tier | >10 concurrent users |
| Loading full generation history | Works with 10 records | Slow queries, paginate and index properly | >1,000 generations per user |
| No database connection pooling | Works with low traffic | Connection exhaustion, use pgBouncer or pooling | >50 concurrent requests |

---

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing OpenAI API keys in frontend | Key theft, unlimited usage | Store in backend env vars only, never expose to client |
| Client-supplied organization_id | Cross-tenant data access | Extract from JWT, validate in middleware, never trust client |
| No API key rotation policy | Compromised keys used indefinitely | Rotate every 90 days, support multiple active keys |
| Logging full prompts/responses | PII exposure in logs | Sanitize logs, redact sensitive data, use structured logging |
| No rate limiting per user | API abuse, cost attacks | Implement per-user quotas (e.g., 100 generations/day) |
| Missing input validation on Excel | Malicious file upload, XSS in content | Validate file type, size, scan for malicious content |
| API keys in version control | Public exposure, GitHub scanning | Use env files in .gitignore, scan with tools like git-secrets |
| No audit trail | Can't investigate breaches | Log all data access with user/org/timestamp |

---

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No progress indicator during generation | Users think it's broken, refresh/leave | Show streaming tokens or progress percentage |
| Cryptic error "Generation failed" | Users don't know what to fix | Surface actionable errors: "Rate limit exceeded, try again in 1 minute" |
| No way to edit AI output | Forced to regenerate if 95% is good | Provide inline editing before accepting |
| Regeneration loses previous version | Can't compare or roll back | Show diff view, allow version selection |
| No indication which content is AI vs human | Trust issues, unclear quality | Tag AI-generated content, show confidence scores |
| Upload fails with no explanation | Frustration, support tickets | Validate file size/format before upload, show specific errors |
| Long generation with no cancellation | Users stuck waiting | Allow canceling jobs, implement timeout UX |
| No draft/preview mode | Accidental publishing to production | Require explicit publish action after review |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **OpenAI Integration:** Often missing exponential backoff retry logic — verify error handling tests
- [ ] **Cost Tracking:** Often missing per-request monitoring — verify LangSmith/telemetry integration
- [ ] **Excel Processing:** Often missing streaming for large files — verify test with 50MB file
- [ ] **Background Jobs:** Often missing status tracking — verify job state persisted in DB
- [ ] **Multi-tenancy:** Often missing organization_id filters — verify cross-tenant access tests
- [ ] **CORS Config:** Often using wildcards — verify production config has specific origins
- [ ] **Error Messages:** Often generic "failed" — verify user-facing messages are actionable
- [ ] **AI Quality Control:** Often missing review step — verify mandatory human approval workflow
- [ ] **Rate Limiting:** Often missing user quotas — verify per-user/org limits enforced
- [ ] **Streaming Responses:** Often missing timeout handling — verify keep-alive and fallback
- [ ] **File Upload:** Often missing size limits — verify 25MB limit with clear error
- [ ] **Memory Management:** Often loading entire Excel — verify streaming API used

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Cost explosion | HIGH | 1. Emergency: Disable affected endpoints 2. Add rate limits 3. Implement cost monitoring 4. Refactor chains to reduce calls 5. Switch to cheaper models |
| Data leakage | CRITICAL | 1. Immediate: Revoke all sessions 2. Audit logs for breach scope 3. Add RLS to database 4. Add application-level checks 5. Notify affected users 6. Regulatory compliance actions |
| Memory crashes | MEDIUM | 1. Increase Node.js heap limit temporarily 2. Add file size limits 3. Implement streaming 4. Deploy fix 5. Test with large files |
| Lost background jobs | MEDIUM | 1. Implement job queue with persistence 2. Migrate in-progress jobs 3. Re-run failed jobs 4. Notify users of status |
| CORS issues | LOW | 1. Update allowed origins 2. Rebuild/redeploy 3. Clear CDN cache 4. Test from production domain |
| Rate limit errors | LOW | 1. Implement exponential backoff 2. Add user-facing rate limits 3. Queue requests instead of failing |
| Hallucinations published | HIGH | 1. Content recall/review 2. Add mandatory review step 3. Implement confidence scoring 4. User notification |
| Vercel size limit | MEDIUM | 1. Migrate backend to proper platform 2. Update frontend API URLs 3. Test end-to-end |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Cost explosion | Phase 1: Foundation | LangSmith cost dashboard shows per-request costs |
| Rate limit errors | Phase 1: Foundation | Load test generates 50 concurrent requests without errors |
| Multi-tenant leakage | Phase 1: Foundation | Automated test: User A cannot access Org B's data |
| CORS/Auth issues | Phase 1: Foundation | Frontend successfully authenticates with production API |
| Vercel limitations | Phase 0: Architecture | Backend deployment platform documented and tested |
| LangChain errors | Phase 2: Core Generation | Error logs include trace ID, tool name, inputs, agent state |
| Excel memory crashes | Phase 2: Core Generation | 50MB Excel file processes without memory errors |
| Background job tracking | Phase 2: Core Generation | Job status endpoint returns pending/running/completed/failed states |
| Streaming timeouts | Phase 2: Core Generation | 60-second generation completes with progressive updates |
| AI hallucinations | Phase 2: Core Generation | Review workflow blocks publishing until human approval |

---

## Sources

### Next.js + FastAPI Integration
- [Integrate FastAPI Framework with Next.js and Deploy 2026](https://codevoweb.com/integrate-fastapi-framework-with-nextjs-and-deploy/)
- [Combining Next.js and NextAuth with a FastAPI backend](https://tom.catshoek.dev/posts/nextauth-fastapi/)
- [Next.js server actions with FastAPI backend and OpenAPI client](https://nemanjamitic.com/blog/2026-01-03-nextjs-server-actions-fastapi-openapi)

### OpenAI API Cost & Rate Limiting
- [Rate limits | OpenAI API](https://platform.openai.com/docs/guides/rate-limits)
- [How to handle rate limits | OpenAI Cookbook](https://cookbook.openai.com/examples/how_to_handle_rate_limits)
- [A practical guide to OpenAI rate limits](https://www.eesel.ai/blog/openai-rate-limits)

### LangChain Production Issues
- [Production Pitfalls of LangChain Nobody Warns You About](https://medium.com/codetodeploy/production-pitfalls-of-langchain-nobody-warns-you-about-44a86e2df29e)
- [LangChain Agent Error Handling Best Practices](https://benny.ghost.io/blog/langchain-agent-error-handling-best-practices/)
- [The Langchain Dilemma: An AI Engineer's Perspective on Production Readiness](https://medium.com/@neeldevenshah/the-langchain-dilemma-an-ai-engineers-perspective-on-production-readiness-bc21dd61de34)

### LangChain Cost Management
- [LangChain Cost Management & Token Tracking](https://apxml.com/courses/langchain-production-llm/chapter-6-optimizing-scaling-langchain/cost-management-token-tracking)
- [LangChain Observability: Monitoring Guide for Production Apps](https://uptrace.dev/blog/langchain-observability)

### Excel Processing
- [Process huge excel file in node js using streams](https://riddheshganatra.medium.com/process-huge-excel-file-in-node-js-using-streams-67d55f19d038)
- [How to Read Excel Files as Stream in ExcelJS with Node.js: 2026 Guide](https://copyprogramming.com/howto/stream-huge-excel-file-using-exceljs-in-node)

### FastAPI Background Tasks
- [Understanding Pitfalls of Async Task Management in FastAPI Requests](https://leapcell.io/blog/understanding-pitfalls-of-async-task-management-in-fastapi-requests)
- [Managing Background Tasks in FastAPI: BackgroundTasks vs ARQ + Redis](https://davidmuraya.com/blog/fastapi-background-tasks-arq-vs-built-in/)
- [Background Tasks - FastAPI](https://fastapi.tiangolo.com/tutorial/background-tasks/)

### CORS & Authentication
- [Mastering CORS: Configuring Cross-Origin Resource Sharing in FastAPI and Next.js](https://medium.com/@vaibhavtiwari.945/mastering-cors-configuring-cross-origin-resource-sharing-in-fastapi-and-next-js-28c61272084b)
- [Blocked by CORS in FastAPI? Here's How to Fix It](https://davidmuraya.com/blog/fastapi-cors-configuration/)

### AI Hallucinations & Quality
- [AI Hallucinations in 2026: What They Are and Why They Matter](https://kanerika.com/blogs/ai-hallucinations/)
- [6 Risks of Generative AI & How to Mitigate Them in 2026](https://research.aimultiple.com/risks-of-generative-ai/)

### Multi-Tenancy & Security
- [Multi-Tenant Leakage: When Row-Level Security Fails in SaaS](https://instatunnel.my/blog/multi-tenant-leakage-when-row-level-security-fails-in-saas)
- [API Security for SaaS: Protect Multi-Tenant Apps & Data](https://www.indusface.com/blog/api-security-for-saas-platforms/)
- [The State of API Security in 2026: Common Misconfigurations and Exploitation Vectors](https://www.appsecure.security/blog/state-of-api-security-common-misconfigurations)

### Vercel Deployment
- [FastAPI on Vercel](https://vercel.com/docs/frameworks/backend/fastapi)
- [Vercel Functions Limits](https://vercel.com/docs/functions/limitations)
- [Vercel App Guide: Complete Guide to Deployment, Templates, and Pricing in 2026](https://kuberns.com/blogs/post/vercel-app-guide/)

### Streaming & Timeouts
- [Streaming API responses | OpenAI API](https://platform.openai.com/docs/guides/streaming-responses)
- [How To Fix OpenAI Rate Limits & Timeout Errors](https://medium.com/@puneet1337/how-to-fix-openai-rate-limits-timeout-errors-cd3dc5ddd50b)

---

*Pitfalls research for: AI-Powered SaaS Content Generation*
*Researched: 2026-01-22*
