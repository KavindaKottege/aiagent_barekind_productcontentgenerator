# Phase 8: Admin Debug Mode - Research

**Researched:** 2026-01-29
**Domain:** Real-time debug logging, persistent UI panels, admin-only features
**Confidence:** HIGH

## Summary

Phase 8 implements an admin-only debug mode that displays the exact prompts and model parameters sent to OpenAI during content generation. The debug information appears in a persistent bottom panel that updates in real-time as products are generated.

The codebase already captures all the data needed for debug mode. The `GenerationAudit` model stores `prompt_used`, `model_version`, `temperature`, `input_tokens`, `output_tokens`, `cost`, and `duration_ms` for every generation attempt. The `AIGenerationService` already formats the prompt into a `prompt_str` containing `[system]` and `[user]` message blocks before storing it. The key challenge is streaming this data to the frontend in real-time and displaying it in a persistent, non-disruptive panel.

The recommended approach uses Redis Pub/Sub to broadcast debug log entries from the ARQ worker to a new SSE endpoint, which the frontend consumes via polling. The debug panel uses a simple collapsible bottom frame with session-scoped React Context for toggle persistence across page navigation. No database migration is needed since the data already exists in `generation_audits` and can also be pushed through Redis in real-time.

**Primary recommendation:** Use Redis Pub/Sub for real-time debug log streaming from the worker, a new dedicated debug SSE/polling endpoint, and a React Context-managed collapsible bottom panel that persists across navigation via the dashboard layout.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Redis Pub/Sub | Already installed (redis 7-alpine) | Real-time log broadcast from worker to API | Already in stack for ARQ; zero new dependencies |
| sse-starlette | Already installed | SSE endpoint for debug stream | Already used for generation progress streaming |
| React Context | Built-in React 19 | Debug mode toggle persistence across navigation | Already used for ClientContext; same pattern |
| sessionStorage | Browser API | Persist debug mode within browser session | No dependency; survives navigation, clears on close |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lucide-react | 0.562.0 (installed) | Bug/Terminal icons for debug panel | Already in project |
| tailwind-merge | 3.4.0 (installed) | Conditional class composition | Already in project |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Redis Pub/Sub | Database polling (query generation_audits) | Simpler but 1-2s latency; Redis Pub/Sub gives sub-100ms delivery. However, polling the existing job status endpoint (which already polls at 1s intervals) is the simpler path since debug data just needs to be added to that existing poll response. |
| Resizable panel (react-resizable-panels) | Fixed-height collapsible div | Resizable adds a dependency and complexity for a dev tool. A fixed-height collapsible panel with CSS transitions is sufficient. |
| shadcn/ui Resizable component | Custom CSS bottom panel | shadcn Resizable is great for production UIs but overkill for admin debug tooling. Simple CSS is more appropriate. |

**Installation:**
No new npm packages needed. No new pip packages needed. Everything required is already installed.

## Architecture Patterns

### Recommended Project Structure
```
backend/
  app/
    routers/
      debug.py            # New: Debug API endpoints (admin-only)
    schemas/
      debug.py            # New: DebugLogEntry Pydantic schema

frontend/
  src/
    lib/
      debug-context.tsx   # New: DebugProvider with toggle state + log accumulator
    components/
      debug-panel.tsx     # New: Collapsible bottom panel with log display
    app/
      (dashboard)/
        layout.tsx        # Modified: Add DebugPanel rendering
        settings/
          page.tsx        # Modified: Add debug mode toggle card
      actions/
        debug.ts          # New: Server Actions for debug toggle + log fetching
```

### Pattern 1: Data Flow - Worker to Debug Panel (Polling-Based)

**What:** Extend the existing job progress polling to include debug log entries from `generation_audits`.

**When to use:** This is the simpler approach that avoids adding Redis Pub/Sub complexity.

**How it works:**
1. Worker already creates `GenerationAudit` records with `prompt_used`, `model_version`, `temperature`, etc.
2. New backend endpoint `GET /api/debug/logs/{job_id}` returns recent audit entries for a job (admin-only)
3. Frontend debug panel polls this endpoint alongside existing job progress polling (every 1-2s)
4. Debug panel displays new audit entries as they appear

```python
# backend/app/routers/debug.py
@router.get("/logs/{job_id}")
async def get_debug_logs(
    job_id: UUID,
    since: datetime | None = Query(None),  # Only return logs after this timestamp
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),  # Admin only
):
    """Get debug log entries for a generation job."""
    query = (
        select(GenerationAudit)
        .where(GenerationAudit.job_id == job_id)
        .order_by(GenerationAudit.created_at.asc())
    )
    if since:
        query = query.where(GenerationAudit.created_at > since)

    result = await db.execute(query)
    audits = result.scalars().all()
    return [DebugLogEntry.model_validate(audit) for audit in audits]
```

### Pattern 2: Debug Context Provider (Session Persistence)

**What:** React Context wrapping the dashboard layout, persisting debug mode toggle to sessionStorage.

**When to use:** Always -- this is how the debug panel survives page navigation.

**Why sessionStorage over localStorage:** Debug mode should auto-disable when the browser tab is closed (it's a session-scoped developer tool, not a permanent preference). This matches the success criteria "persists across page navigation within the session."

```typescript
// frontend/src/lib/debug-context.tsx
'use client'

import { createContext, useContext, useEffect, useState, useCallback } from 'react'

interface DebugLogEntry {
  id: string
  product_group_id: string
  product_name: string
  task: 'title' | 'description'
  system_prompt: string
  user_prompt: string
  model_version: string
  temperature: number
  input_tokens: number
  output_tokens: number
  cost: string
  duration_ms: number
  success: boolean
  error_message: string | null
  generated_title: string | null
  generated_description: string | null
  created_at: string
}

interface DebugContextType {
  isDebugEnabled: boolean
  setDebugEnabled: (enabled: boolean) => void
  debugLogs: DebugLogEntry[]
  addLogs: (logs: DebugLogEntry[]) => void
  clearLogs: () => void
}

const STORAGE_KEY = 'debugModeEnabled'

export function DebugProvider({
  children,
  isAdmin
}: {
  children: React.ReactNode
  isAdmin: boolean
}) {
  const [isDebugEnabled, setDebugEnabledState] = useState(false)
  const [debugLogs, setDebugLogs] = useState<DebugLogEntry[]>([])

  // Load from sessionStorage on mount
  useEffect(() => {
    if (!isAdmin) return
    const stored = sessionStorage.getItem(STORAGE_KEY)
    if (stored === 'true') {
      setDebugEnabledState(true)
    }
  }, [isAdmin])

  const setDebugEnabled = useCallback((enabled: boolean) => {
    setDebugEnabledState(enabled)
    sessionStorage.setItem(STORAGE_KEY, String(enabled))
    if (!enabled) {
      setDebugLogs([]) // Clear logs when disabling
    }
  }, [])

  const addLogs = useCallback((newLogs: DebugLogEntry[]) => {
    setDebugLogs(prev => [...prev, ...newLogs])
  }, [])

  const clearLogs = useCallback(() => {
    setDebugLogs([])
  }, [])

  // Non-admin: render children without debug capability
  if (!isAdmin) {
    return <>{children}</>
  }

  return (
    <DebugContext.Provider value={{
      isDebugEnabled, setDebugEnabled, debugLogs, addLogs, clearLogs
    }}>
      {children}
    </DebugContext.Provider>
  )
}
```

### Pattern 3: Collapsible Bottom Debug Panel

**What:** A fixed-position bottom panel that shows debug log entries with syntax-highlighted prompts.

**When to use:** When debug mode is enabled by admin.

```typescript
// frontend/src/components/debug-panel.tsx
'use client'

export function DebugPanel() {
  const { isDebugEnabled, debugLogs, clearLogs } = useDebug()
  const [isExpanded, setIsExpanded] = useState(true)
  const [selectedLog, setSelectedLog] = useState<DebugLogEntry | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  if (!isDebugEnabled) return null

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 border-t-2 border-orange-500 bg-gray-900 text-gray-100">
      {/* Header bar - always visible */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800 cursor-pointer"
           onClick={() => setIsExpanded(!isExpanded)}>
        <div className="flex items-center gap-2">
          <Bug className="h-4 w-4 text-orange-400" />
          <span className="text-sm font-mono font-medium">Debug Mode</span>
          <Badge>{debugLogs.length} entries</Badge>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="ghost" onClick={clearLogs}>Clear</Button>
          <ChevronDown className={`h-4 w-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
        </div>
      </div>
      {/* Expandable content */}
      {isExpanded && (
        <div className="h-64 overflow-auto font-mono text-xs">
          {/* Log entries list + detail view */}
        </div>
      )}
    </div>
  )
}
```

### Pattern 4: Parsing prompt_used for Structured Display

**What:** The `prompt_used` field in GenerationAudit stores prompts in the format `[system] content\n[user] content`. Parse this to display system and user prompts separately.

**When to use:** When rendering debug log entries in the panel.

```typescript
function parsePromptUsed(promptUsed: string): { system: string; user: string } {
  const systemMatch = promptUsed.match(/\[system\]\s*([\s\S]*?)(?=\[user\]|$)/)
  const userMatch = promptUsed.match(/\[user\]\s*([\s\S]*)$/)
  return {
    system: systemMatch?.[1]?.trim() || '',
    user: userMatch?.[1]?.trim() || '',
  }
}
```

### Anti-Patterns to Avoid
- **Don't add a new database column for debug mode toggle:** Debug mode is a session-level UI preference, not persisted user data. Use sessionStorage.
- **Don't build a WebSocket connection for debug:** The existing polling pattern (1s interval) is sufficient for debug log delivery. Adding WebSocket infrastructure for a single admin feature is over-engineering.
- **Don't stream raw prompts through the existing SSE progress endpoint:** The progress endpoint is consumed by all users, not just admins. Debug data should be on a separate admin-only endpoint.
- **Don't create a new database table for debug logs:** The `generation_audits` table already stores everything needed (prompt_used, model_version, temperature, tokens, cost, duration_ms, success/error status).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Debug log storage | Custom log table or in-memory store | Existing `generation_audits` table | Already stores prompt_used, model, temperature, tokens, cost, duration for every attempt |
| Prompt formatting for display | Custom prompt serializer | Parse existing `[system] ... [user] ...` format from `prompt_used` | AIGenerationService already formats prompts this way |
| Admin-only access control | Custom auth check | Existing `get_current_admin` dependency | Already used across settings endpoints |
| Session-scoped persistence | Custom cookie/DB solution | Browser sessionStorage | Built-in, clears on tab close, survives navigation |
| Real-time log delivery | Custom pub/sub | Polling the debug endpoint at 1-2s intervals | Matches existing generation-progress polling pattern |

**Key insight:** The `GenerationAudit` model already captures 100% of the data needed for the debug panel. The challenge is purely UI/UX: polling for new audit entries and displaying them in a persistent, collapsible panel.

## Common Pitfalls

### Pitfall 1: Debug Panel Blocking Page Content
**What goes wrong:** A fixed-position bottom panel covers the bottom of the page content, making some content unreachable.
**Why it happens:** The panel sits on top of `<main>` content without adjusting the page layout.
**How to avoid:** Add `pb-72` (or dynamic padding) to the `<main>` element when debug mode is enabled. The dashboard layout already renders `<main>` -- conditionally add bottom padding.
**Warning signs:** Content cut off at the bottom of pages when debug panel is open.

### Pitfall 2: Debug Logs Accumulating Without Bound
**What goes wrong:** Memory grows unbounded as debug logs accumulate across multiple generation runs.
**Why it happens:** Logs are kept in React state and never pruned.
**How to avoid:** Cap debug logs to the most recent N entries (e.g., 500). Provide a "Clear" button. Clear logs when debug mode is toggled off.
**Warning signs:** Browser becomes sluggish after running generation for many products.

### Pitfall 3: Context Reset on Full Page Refresh
**What goes wrong:** Debug mode toggle resets when user refreshes the page.
**Why it happens:** React Context state is lost on full page refresh.
**How to avoid:** Initialize Context state from sessionStorage on mount (already shown in the pattern above). The toggle state persists; accumulated logs do not (acceptable for a debug tool).
**Warning signs:** User has to re-enable debug mode after every page refresh.

### Pitfall 4: Debug Endpoint Exposed to Non-Admin Users
**What goes wrong:** Regular users can access debug log endpoint and see system prompts.
**Why it happens:** Endpoint uses `get_current_user` instead of `get_current_admin`.
**How to avoid:** Use the existing `get_current_admin` dependency for all debug endpoints. Also conditionally render the debug toggle only for admin users on the frontend.
**Warning signs:** Non-admin users seeing debug-related UI elements.

### Pitfall 5: Polling Debug Logs When No Generation is Active
**What goes wrong:** Frontend polls debug endpoint continuously even when no generation is running, wasting API calls.
**Why it happens:** Debug panel polls unconditionally once enabled.
**How to avoid:** Only poll for debug logs when there is an active generation job. The generation-progress component already tracks job status -- coordinate polling through the same mechanism.
**Warning signs:** Backend logs showing constant debug endpoint hits with no new data.

### Pitfall 6: Prompt Display Truncation
**What goes wrong:** The `prompt_used` field in GenerationAudit is truncated to 10,000 characters (`prompt_str[:10000]`). Long description prompts with extensive brand context may be cut off.
**Why it happens:** The AI service truncates prompts before storing them.
**How to avoid:** For the debug panel, this is actually fine -- 10,000 chars is more than enough to show the full prompt structure. But document this limitation in the UI so admins know truncation may occur for very long prompts.
**Warning signs:** Debug panel showing prompts ending with "..." without the user realizing data was truncated.

## Code Examples

### Example 1: Backend Debug Router (Admin-Only)
```python
# backend/app/routers/debug.py
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.generation_audit import GenerationAudit
from app.models.generation_job import GenerationJob
from app.models.user import User
from app.utils.dependencies import get_current_admin

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/logs/{job_id}")
async def get_debug_logs(
    job_id: UUID,
    since: datetime | None = Query(None, description="Only return logs created after this timestamp"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Get debug log entries for a generation job. Admin only."""
    # Verify job exists and belongs to user's org
    query = (
        select(GenerationAudit)
        .where(GenerationAudit.job_id == job_id)
        .order_by(GenerationAudit.created_at.asc())
    )
    if since:
        query = query.where(GenerationAudit.created_at > since)
    query = query.limit(limit)

    result = await db.execute(query)
    audits = result.scalars().all()

    return [
        {
            "id": str(a.id),
            "product_group_id": str(a.product_group_id),
            "attempt_number": a.attempt_number,
            "prompt_used": a.prompt_used,
            "model_version": a.model_version,
            "temperature": float(a.temperature),
            "input_tokens": a.input_tokens,
            "output_tokens": a.output_tokens,
            "cost": str(a.cost),
            "duration_ms": a.duration_ms,
            "success": a.success,
            "error_message": a.error_message,
            "generated_title": a.generated_title,
            "generated_description": a.generated_description,
            "title_length": a.title_length,
            "description_length": a.description_length,
            "created_at": a.created_at.isoformat(),
        }
        for a in audits
    ]
```

### Example 2: Dashboard Layout Integration
```tsx
// Conceptual modification to (dashboard)/layout.tsx
import { DebugPanel } from '@/components/debug-panel'
import { DebugProvider } from '@/lib/debug-context'

export default async function DashboardLayout({ children }) {
  const user = await getUser()

  return (
    <DebugProvider isAdmin={user.is_admin}>
      <div className="min-h-screen bg-gray-50">
        <header>...</header>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
        <DebugPanel />
      </div>
    </DebugProvider>
  )
}
```

### Example 3: Settings Page Debug Toggle
```tsx
// Added to settings/page.tsx
{user.is_admin && (
  <Card>
    <CardHeader>
      <CardTitle>Debug Mode</CardTitle>
      <CardDescription>
        Show AI prompts and model parameters during content generation
      </CardDescription>
    </CardHeader>
    <CardContent>
      <DebugToggle />
    </CardContent>
  </Card>
)}
```

### Example 4: Debug Log Entry Display
```tsx
function DebugLogEntry({ log }: { log: DebugLogEntry }) {
  const { system, user } = parsePromptUsed(log.prompt_used)

  return (
    <div className="border-b border-gray-700 p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-orange-400 font-bold">
          {log.success ? 'OK' : 'FAIL'} - Attempt #{log.attempt_number}
        </span>
        <span className="text-gray-500 text-xs">
          {log.model_version} | temp={log.temperature} | {log.duration_ms}ms | ${log.cost}
        </span>
      </div>
      <details className="mb-1">
        <summary className="text-blue-400 cursor-pointer text-xs">System Prompt ({system.length} chars)</summary>
        <pre className="text-gray-300 whitespace-pre-wrap text-xs mt-1 pl-2 border-l-2 border-blue-800">{system}</pre>
      </details>
      <details className="mb-1">
        <summary className="text-green-400 cursor-pointer text-xs">User Prompt ({user.length} chars)</summary>
        <pre className="text-gray-300 whitespace-pre-wrap text-xs mt-1 pl-2 border-l-2 border-green-800">{user}</pre>
      </details>
      {log.input_tokens > 0 && (
        <div className="text-gray-500 text-xs mt-1">
          Tokens: {log.input_tokens} in / {log.output_tokens} out
        </div>
      )}
    </div>
  )
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Browser console.log debugging | Structured debug panels in UI | Common in 2024+ | Better UX for admin users |
| WebSocket for all real-time | SSE for server-to-client streams | Established pattern | Simpler, HTTP-native, auto-reconnect |
| Redux/Zustand for all state | React Context for scoped state | React 18/19 era | No extra dependency for simple toggle state |
| Resizable panels for all panels | Collapsible fixed-height for simple cases | Practical wisdom | Less complexity for admin tooling |

**Deprecated/outdated:**
- Using EventSource directly for admin features when simple polling suffices (existing project already uses polling for generation progress)

## Open Questions

1. **Debug log polling frequency**
   - What we know: Generation progress polls at 1s intervals. Debug logs could piggyback on this or poll independently.
   - What's unclear: Whether 1s polling is fast enough for debug or if sub-second polling is needed.
   - Recommendation: Use 2s polling for debug logs (separate from progress polling). Debug is for inspection, not real-time monitoring, so 2s latency is acceptable.

2. **Should debug logs include AI review audit entries too?**
   - What we know: Phase 5 AI review also uses LangChain and creates its own audit records.
   - What's unclear: Whether the admin wants to debug review prompts or only generation prompts.
   - Recommendation: Start with generation audit logs only. The endpoint can be extended later to include review audit entries if needed.

3. **Panel height preference**
   - What we know: A fixed height (e.g., 256px / h-64) works for most cases. A resizable panel adds dependency complexity.
   - What's unclear: Whether admin will want to resize the panel.
   - Recommendation: Use fixed height with the option to expand to full screen (toggle between h-64 and h-96). Avoid adding react-resizable-panels for a single admin feature.

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `backend/app/services/ai_generation.py` - Prompt building and audit trail creation
- Codebase analysis: `backend/app/models/generation_audit.py` - `prompt_used`, `model_version`, `temperature` fields
- Codebase analysis: `backend/app/workers/generation_worker.py` - Worker flow and audit creation points
- Codebase analysis: `frontend/src/lib/client-context.tsx` - Existing Context pattern for cross-navigation state
- Codebase analysis: `frontend/src/components/generation-progress.tsx` - Existing polling pattern (1s intervals)
- Codebase analysis: `frontend/src/app/(dashboard)/layout.tsx` - Dashboard layout structure
- Codebase analysis: `frontend/src/app/(dashboard)/settings/page.tsx` - Settings page admin cards

### Secondary (MEDIUM confidence)
- [Next.js App Router documentation](https://nextjs.org/docs/pages/building-your-application/routing/pages-and-layouts) - Layout state persistence during soft navigation
- [Vercel KB: React Context state management in Next.js](https://vercel.com/kb/guide/react-context-state-management-nextjs) - Context provider placement patterns
- [shadcn/ui Resizable component](https://ui.shadcn.com/docs/components/resizable) - Evaluated but not recommended for this use case

### Tertiary (LOW confidence)
- [SSE + FastAPI + Redis Pub/Sub pattern](https://medium.com/deepdesk/server-sent-events-in-fastapi-using-redis-pub-sub-eba1dbfe8031) - Alternative real-time approach (not recommended over polling for this feature)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All components already in the codebase; no new dependencies
- Architecture: HIGH - Follows existing patterns (Context, polling, admin-only endpoints)
- Pitfalls: HIGH - Based on direct codebase analysis and understanding of existing data flow
- Code examples: HIGH - Based on actual codebase models, schemas, and patterns

**Research date:** 2026-01-29
**Valid until:** 2026-03-01 (stable - all patterns are established in the existing codebase)
