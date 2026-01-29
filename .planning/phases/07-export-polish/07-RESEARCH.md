# Phase 7: Export & Polish - Research

**Researched:** 2026-01-29
**Domain:** Excel export reconstruction, UI polish, error handling
**Confidence:** HIGH

## Summary

Phase 7 has two major workstreams: (1) building an Excel export endpoint that reconstructs the original uploaded spreadsheet with updated content, and (2) polishing the entire application UI for a consistent, modern SaaS experience.

The export feature requires reconstructing Excel files from database records using openpyxl (already installed at v3.1.5). The key challenge is rebuilding the original column structure from a combination of mapped fields (via `ExactColumnMapper.COLUMN_MAP`) and unmapped fields (stored as JSONB `unmapped_data` on each Product). The approach is to query all products for a client ordered by `row_index`, resolve effective content from the ProductGroup, and write a new workbook using openpyxl's standard (non-read-only) Workbook mode. FastAPI's `StreamingResponse` with a `BytesIO` buffer is the standard pattern for returning generated files.

The polish workstream involves installing Sonner for toast notifications, adding shadcn/ui Skeleton components for loading states, implementing Next.js App Router error boundaries (`error.tsx` / `global-error.tsx`), and doing a consistency pass on spacing, typography, and transitions across all pages.

**Primary recommendation:** Use openpyxl `Workbook` (standard mode) writing to `BytesIO`, serve via FastAPI `StreamingResponse`. Install Sonner via `npx shadcn@latest add sonner`. Use Next.js file-convention `error.tsx` for error boundaries. Client-side file download uses the standard `fetch -> blob -> createObjectURL -> anchor click` pattern.

## Standard Stack

### Core (Export)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openpyxl | 3.1.5 (installed) | Write .xlsx files from scratch | Already used for reading; full write support in standard mode |
| FastAPI StreamingResponse | (built-in) | Serve generated file as download | Standard FastAPI pattern for binary responses |

### Core (Polish)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| sonner | latest (2.x) | Toast notifications | shadcn/ui recommended; decision locked in CONTEXT.md |
| shadcn/ui skeleton | (copy-paste) | Loading state placeholders | Already using shadcn/ui component system |
| Next.js error.tsx | (built-in) | Error boundaries | Framework convention; no external dep needed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lucide-react | 0.562.0 (installed) | Icons for export button, empty states | Already installed; use Download, FileSpreadsheet icons |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| openpyxl standard mode | openpyxl write_only mode | write_only is more memory-efficient but cannot set column widths or cell formatting; standard mode is fine for typical product catalogs (<10K rows) |
| BytesIO + StreamingResponse | FileResponse + temp file | Adds disk I/O and cleanup complexity; BytesIO is simpler and sufficient |
| Sonner | react-hot-toast | Sonner is the shadcn/ui blessed choice; locked decision |

**Installation:**
```bash
# Frontend (from frontend/ directory)
npx shadcn@latest add sonner
npx shadcn@latest add skeleton

# Backend: no new deps needed (openpyxl already installed)
```

## Architecture Patterns

### Backend: Export Endpoint

```
backend/app/
├── routers/
│   └── export.py          # New router: GET /export/{client_id}
├── services/
│   └── excel_exporter.py  # New service: ExcelExporter class
└── schemas/
    └── export.py          # New schema: ExportStatsResponse
```

**Router registration in `main.py`:**
- Add `export_router` to the router includes with prefix `/api`
- Add to `__init__.py` exports

### Frontend: Export Components

```
frontend/src/
├── app/
│   ├── (dashboard)/
│   │   ├── layout.tsx                 # Add ExportButton next to UploadButtonWrapper
│   │   ├── dashboard/
│   │   │   └── page.tsx               # Redesign with guided empty state
│   │   ├── products/
│   │   │   └── loading.tsx            # New: skeleton loader
│   │   ├── review/
│   │   │   └── loading.tsx            # New: skeleton loader
│   │   └── error.tsx                  # New: dashboard error boundary
│   ├── error.tsx                      # New: root error boundary
│   ├── global-error.tsx               # New: global error boundary (wraps root layout)
│   └── layout.tsx                     # Add <Toaster /> from sonner
│   └── actions/
│       └── export.ts                  # New: export server action / client fetch helper
├── components/
│   ├── export-button.tsx              # New: export button with dialog
│   ├── export-dialog.tsx              # New: confirmation dialog with stats
│   └── ui/
│       ├── sonner.tsx                 # Added by shadcn CLI
│       └── skeleton.tsx               # Added by shadcn CLI
```

### Pattern 1: Excel Reconstruction (Backend)

**What:** Rebuild original Excel from database records, replacing only Product Name and Description for qualifying products.

**When to use:** Export endpoint.

**Algorithm:**
1. Query all products for client, ordered by `row_index`, joined with their ProductGroup
2. Determine column order: use `ExactColumnMapper.COLUMN_MAP` (reverse lookup) for mapped fields + collect all unique unmapped_data keys across all products (preserving order from first product that has each key)
3. For each product row:
   - Determine if content should be updated (based on group review_status and include_pending flag)
   - If updating: use effective content (edited_* if set, else generated_*) from the ProductGroup
   - Reconstruct full row in original column order
4. Write to openpyxl Workbook, save to BytesIO, return as StreamingResponse

**Key insight:** The original column headers are recoverable. Mapped columns have exact header names in `COLUMN_MAP` values (e.g., `'Product Name (English)'`, `'Description (English)'`). Unmapped columns have their original header names preserved as JSONB keys in `unmapped_data`.

```python
# Source: codebase analysis of ExactColumnMapper.COLUMN_MAP
REVERSE_COLUMN_MAP = {v: k for k, v in ExactColumnMapper.COLUMN_MAP.items()}
# e.g., {'Product Name (English)': 'product_name', 'Description (English)': 'description', ...}
```

### Pattern 2: File Download from FastAPI (Frontend)

**What:** Client-side binary file download via fetch + blob + anchor click.

**When to use:** Export button click handler.

**Critical detail:** Server Actions in Next.js cannot return binary data. The export must use a direct client-side `fetch()` to the FastAPI backend, not a Server Action.

```typescript
// Source: standard web API pattern
async function downloadExport(clientId: string, includePending: boolean) {
  const response = await fetch(
    `${API_URL}/api/export/${clientId}?include_pending=${includePending}`,
    {
      headers: { 'Authorization': `Bearer ${accessToken}` },
    }
  );

  if (!response.ok) throw new Error('Export failed');

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = response.headers.get('Content-Disposition')
    ?.split('filename=')[1]?.replace(/"/g, '') || 'export.xlsx';
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}
```

### Pattern 3: Export Stats Endpoint (Backend)

**What:** Separate endpoint to get export statistics for the confirmation dialog (product counts by status).

**When to use:** When user clicks Export button, before showing confirmation dialog.

**Why separate:** The stats are needed to populate the dialog before the actual download. This avoids computing stats and generating the file in one call.

```python
# GET /api/export/{client_id}/stats
# Returns: { total, not_generated, approved, pending, rejected }
```

### Pattern 4: Error Boundaries (Next.js)

**What:** Hierarchical error boundaries using Next.js file conventions.

**Structure:**
- `app/global-error.tsx` -- catches root layout errors (must include `<html>` and `<body>`)
- `app/error.tsx` -- root error boundary inside root layout
- `app/(dashboard)/error.tsx` -- dashboard-level boundary, keeps header visible

```typescript
// Source: Next.js App Router docs
'use client'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div>
      <h2>Something went wrong</h2>
      <button onClick={() => reset()}>Try again</button>
    </div>
  )
}
```

### Pattern 5: Sonner Toast Integration

**What:** Global toast provider in root layout, callable from any client component.

```typescript
// In app/layout.tsx:
import { Toaster } from 'sonner'
// Add <Toaster richColors position="bottom-right" /> inside <body>

// In any client component:
import { toast } from 'sonner'
toast.success('Export complete')
toast.error('Export failed: no approved products')
toast.promise(exportPromise, {
  loading: 'Preparing export...',
  success: 'Export complete',
  error: 'Export failed',
})
```

### Anti-Patterns to Avoid
- **Loading original Excel file to modify it:** Don't try to load the original uploaded file. It was deleted after parsing. Reconstruct from database records.
- **Server Actions for binary downloads:** Server Actions serialize return values. They cannot return a Blob/File. Use direct client-side fetch.
- **Single export endpoint for stats + file:** Separating stats query from file generation gives better UX (instant dialog population, then download on confirm).
- **Custom toast implementation:** Sonner is the blessed choice. Don't build a custom toast system.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Toast notifications | Custom toast context/reducer | Sonner (`toast()`) | Handles positioning, stacking, dismissal, animations, accessibility, promise integration |
| Loading skeletons | Custom div with animate-pulse | shadcn/ui Skeleton component | Consistent styling, proper animation, matches component library |
| Error boundaries | Custom ErrorBoundary class component | Next.js `error.tsx` file convention | Framework handles the boundary creation, provides `reset()`, handles server/client split |
| Excel column ordering | Manual column index tracking | Derive from `ExactColumnMapper.COLUMN_MAP` + `unmapped_data` keys | Column map is the single source of truth for mapped columns |
| File download trigger | Custom download logic | Standard blob + createObjectURL pattern | Well-tested browser API pattern; no library needed |
| Export dialog | Custom modal | shadcn/ui AlertDialog (already installed) | Matches existing dialog patterns in codebase (upload modal uses Dialog) |

**Key insight:** The export's column reconstruction is the only genuinely custom logic. Everything else has an existing solution in the stack.

## Common Pitfalls

### Pitfall 1: Column Order Not Preserved in Export
**What goes wrong:** Exported Excel has columns in wrong order (alphabetical, or random dict order).
**Why it happens:** JSONB `unmapped_data` is an unordered dict; Python dict iteration order is insertion order but may not match original Excel order.
**How to avoid:** The original column order must be reconstructed from:
1. Use the FIRST product's `unmapped_data` keys to establish unmapped column order (since all products for a client come from the same Excel, they share the same unmapped columns).
2. Interleave mapped and unmapped columns in the order they appeared in the original Excel. Since `ExactColumnMapper.COLUMN_MAP` maps field names to exact Excel header names, we can rebuild the full header list.
3. **Better approach:** Store the original header order. Currently, the upload endpoint doesn't persist the original header list. The `UploadResponse` returns `mapped_columns` and `unmapped_columns` but this isn't stored in the database. **We need to store the original column order somewhere** -- either on the Client model (e.g., `excel_column_order: list[str]`) or derive it from the first product.
**Warning signs:** Columns appear shuffled in exported file.

### Pitfall 2: Missing Unmapped Column Values for Some Products
**What goes wrong:** Some products have different unmapped columns than others (e.g., some rows had values in a column, others didn't).
**Why it happens:** The `unmapped_data` JSONB only stores keys that had values in the original row. If a cell was empty/None in the original Excel, the key may be omitted from `unmapped_data`.
**How to avoid:** When building the column set, union all `unmapped_data` keys across all products. Use `None`/empty string for missing keys in any given row.
**Warning signs:** Some cells appear empty that shouldn't be, or columns are missing entirely.

### Pitfall 3: Variant Content Propagation
**What goes wrong:** Only the first variant row gets updated content; other variant rows in the same group keep original values.
**Why it happens:** The generated content lives on the ProductGroup, not on individual Products. When iterating products for export, developer forgets to look up the group's effective content for each product.
**How to avoid:** For every product, look up its `group.review_status` and the group's effective title/description. Apply the same content update to ALL products in the group.
**Warning signs:** Only first row of a variant group has new content in exported Excel.

### Pitfall 4: Auth Token Not Available for Client-Side Fetch
**What goes wrong:** The export download fetch fails with 401 because the access_token is in an httpOnly cookie.
**Why it happens:** `httpOnly` cookies are not accessible via JavaScript, but they ARE sent automatically with same-origin fetch requests. However, the FastAPI backend is on a different origin (localhost:8000 vs localhost:3000).
**How to avoid:** Two options:
1. **Proxy approach:** Create a Next.js API route (`app/api/export/route.ts`) that forwards the request to FastAPI, passing along the cookie. This keeps auth simple.
2. **Direct fetch with credentials:** Use `credentials: 'include'` on the fetch, and ensure CORS is configured correctly on FastAPI (already has `allow_credentials=True`).
3. **Token passing:** Get the access token via a Server Action and pass it to the client component (similar to how the review page passes `accessToken` to the SSE client).
**Warning signs:** 401 errors on export attempts.
**Recommendation:** Use option 3 (token passing) since it already works for SSE in the review page -- the pattern is established.

### Pitfall 5: Sanitized Values Not Reversed on Export
**What goes wrong:** Values that were sanitized during upload (e.g., formula injection prevention adding `'` prefix) get exported with the sanitization prefix.
**Why it happens:** `ExactColumnMapper._sanitize()` prepends `'` to values starting with `=`, `+`, `-`, `@`.
**How to avoid:** When exporting, check if values start with `'` followed by `=`, `+`, `-`, `@` and remove the prefix. OR accept that sanitized values are safer and document this behavior.
**Warning signs:** Cells in exported Excel show leading apostrophes.
**Recommendation:** Keep sanitized values as-is. The sanitization prevents formula injection which is a security feature. The `'` prefix is invisible in Excel (Excel treats it as a text prefix marker).

### Pitfall 6: Sonner Not Rendering in Server Components
**What goes wrong:** `toast()` calls in server actions or server components fail silently.
**Why it happens:** Sonner's `toast()` function only works in client components. Server Actions run on the server.
**How to avoid:** Return success/error from server actions, then call `toast()` in the client component's response handler.
**Warning signs:** No toasts appear after server action calls.

### Pitfall 7: Large Export Memory Issues
**What goes wrong:** Export of very large product catalogs (5000+ rows) consumes excessive memory.
**Why it happens:** Loading all products into memory, then building the workbook, then converting to BytesIO -- all in memory simultaneously.
**How to avoid:** For the expected scale (hundreds to low thousands of products), standard Workbook mode is fine. If scale becomes an issue later, switch to write_only mode. For now, don't over-optimize.
**Warning signs:** Slow export times, memory spikes in backend.

## Code Examples

### Excel Export Service (Backend)

```python
# backend/app/services/excel_exporter.py
# Source: openpyxl docs + codebase patterns

from io import BytesIO
from openpyxl import Workbook
from app.services.column_mapper import ExactColumnMapper

class ExcelExporter:
    """Export products back to Excel format preserving original structure."""

    # Reverse map: Excel header name -> field name
    REVERSE_MAP = {v: k for k, v in ExactColumnMapper.COLUMN_MAP.items()}

    def export(
        self,
        products: list[dict],  # Products with group info, ordered by row_index
        column_order: list[str],  # Original Excel column headers in order
        include_pending: bool = False,
    ) -> BytesIO:
        wb = Workbook()
        ws = wb.active
        ws.title = "Products"

        # Write header row
        ws.append(column_order)

        # Write data rows
        for product in products:
            row = []
            for col_header in column_order:
                field_name = self.REVERSE_MAP.get(col_header)
                if field_name:
                    # Mapped column -- check if we should use generated content
                    if field_name == 'product_name' and product.get('_use_generated'):
                        row.append(product.get('effective_title', product.get('product_name', '')))
                    elif field_name == 'description' and product.get('_use_generated'):
                        row.append(product.get('effective_description', product.get('description', '')))
                    else:
                        row.append(product.get(field_name, ''))
                else:
                    # Unmapped column -- pull from unmapped_data
                    row.append(product.get('unmapped_data', {}).get(col_header, ''))
            ws.append(row)

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer
```

### Export API Endpoint (Backend)

```python
# backend/app/routers/export.py
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/export", tags=["export"])

@router.get("/{client_id}")
async def export_products(
    client_id: UUID,
    include_pending: bool = Query(False),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. Validate client ownership
    # 2. Query products with groups
    # 3. Determine column order
    # 4. Build export data with effective content
    # 5. Generate Excel

    buffer = exporter.export(products_data, column_order, include_pending)

    filename = f"{client.brand_name}_products_{date.today().isoformat()}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
```

### Export Stats Endpoint (Backend)

```python
@router.get("/{client_id}/stats")
async def get_export_stats(
    client_id: UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # Count product groups by status
    # Returns: total, not_generated, approved, pending, rejected
    # "approved" = review_status in ('approved', 'edited')
    # "pending" = status == 'generated' AND review_status IS NULL
    # "rejected" = review_status == 'rejected'
    # "not_generated" = status != 'generated'
    pass
```

### Client-Side Download (Frontend)

```typescript
// frontend/src/components/export-button.tsx
'use client'

import { toast } from 'sonner'

async function handleExport(
  clientId: string,
  includePending: boolean,
  accessToken: string,
  clientName: string,
) {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  try {
    const response = await fetch(
      `${API_URL}/api/export/${clientId}?include_pending=${includePending}`,
      {
        headers: { Authorization: `Bearer ${accessToken}` },
      }
    )

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Export failed' }))
      throw new Error(err.detail || 'Export failed')
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const today = new Date().toISOString().split('T')[0]
    a.download = `${clientName}_products_${today}.xlsx`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)

    toast.success('Export complete')
  } catch (error) {
    toast.error(error instanceof Error ? error.message : 'Export failed')
  }
}
```

### Error Boundary (Frontend)

```typescript
// frontend/src/app/(dashboard)/error.tsx
'use client'

import { Button } from '@/components/ui/button'

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
      <h2 className="text-xl font-semibold text-gray-900">
        Something went wrong
      </h2>
      <p className="text-gray-600 text-center max-w-md">
        {error.message || 'An unexpected error occurred. Please try again.'}
      </p>
      <Button onClick={reset}>Try again</Button>
    </div>
  )
}
```

### Skeleton Loader (Frontend)

```typescript
// frontend/src/app/(dashboard)/products/loading.tsx
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent, CardHeader } from '@/components/ui/card'

export default function ProductsLoading() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-9 w-48" /> {/* Page title */}
      <div className="space-y-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-4">
              <div className="flex items-center gap-4">
                <Skeleton className="h-12 w-12 rounded" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-1/2" />
                </div>
                <Skeleton className="h-6 w-20 rounded-full" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Loading spinners | Skeleton loaders | 2023+ | Better perceived performance; content-shaped placeholders |
| Custom toast components | Sonner library | 2024+ | Standardized, accessible, promise-aware toast system |
| try/catch in every component | error.tsx file convention | Next.js 13+ (2023) | Framework-managed error boundaries with recovery |
| CSV export | .xlsx export via openpyxl | N/A | Preserves formatting, column types, multi-sheet support |

**Deprecated/outdated:**
- **react-toastify:** Still works but Sonner is the shadcn/ui blessed choice with better defaults
- **Class-based ErrorBoundary components:** Replaced by Next.js file convention `error.tsx`
- **Loading spinners for page transitions:** Skeleton loaders with `loading.tsx` are the modern pattern

## Column Order Reconstruction Strategy

This is the most technically challenging aspect of the export. Here is the recommended approach:

### Option A: Store column order at upload time (RECOMMENDED)

Add a `excel_column_order` field to the Client model (or a new `upload_metadata` table):

```python
# On Client model:
excel_column_order: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
```

During upload in `products.py`, after mapping columns, save the header order:

```python
# After mapping, store the original column order on the client
client.excel_column_order = headers  # The original Excel headers list
```

**Pros:** Exact original order. Reliable. Simple to implement.
**Cons:** Requires a migration. Requires modifying upload endpoint.

### Option B: Derive column order from data (FALLBACK)

If we don't want to modify the upload:

1. Start with ALL Excel header names from `ExactColumnMapper.COLUMN_MAP` values
2. Add all unique keys from `unmapped_data` across all products
3. The problem: we don't know the interleaving order of mapped vs unmapped columns

We could use a heuristic: Faire templates have a known column order. Since this app is specifically for Faire product templates, we could hardcode the known Faire column order as a fallback.

**Recommendation:** Use Option A. It's a small migration (add one nullable JSON column to clients), a small code change in the upload endpoint, and guarantees correct export column order. This is the clean solution.

## Open Questions

1. **Column order storage**
   - What we know: The original Excel column order is not currently persisted in the database. The `UploadResponse` returns it but it's ephemeral.
   - What's unclear: Whether adding a column to the Client model is acceptable, or if a separate metadata table is preferred.
   - Recommendation: Add `excel_column_order: JSON | None` to the Client model. It's the simplest approach with one migration.

2. **Metadata rows in export**
   - What we know: The upload parser skips metadata/header rows (rows with patterns like "info_", "Optional", etc.). These rows exist in some Faire templates between the header and data.
   - What's unclear: Should these rows be included in the export? They were filtered out during parsing and not stored.
   - Recommendation: Don't include them. They are template metadata, not product data. The exported file will be cleaner without them.

3. **Made_to_order boolean serialization**
   - What we know: `made_to_order` is stored as a Python boolean. The original Excel may have had it as "Yes"/"No" or "TRUE"/"FALSE".
   - What's unclear: The exact original format.
   - Recommendation: Export as the Python value. openpyxl will write True/False which Excel displays correctly.

4. **Images column format**
   - What we know: Images are parsed from space/comma/newline-separated URLs into a JSON array. On export, they need to be converted back to a string.
   - What's unclear: The original separator (space, comma, or newline).
   - Recommendation: Join with space separator on export (matches Faire's format: space-separated URLs).

## Sources

### Primary (HIGH confidence)
- **Codebase analysis** - Direct reading of all models, services, routers, schemas, and frontend components
- **openpyxl 3.1.5** - [Official docs: Optimised Modes](https://openpyxl.readthedocs.io/en/stable/optimized.html), [Simple usage](https://openpyxl.readthedocs.io/en/stable/usage.html)
- **FastAPI** - [Custom Response docs](https://fastapi.tiangolo.com/advanced/custom-response/) for StreamingResponse
- **Next.js** - [Error Handling docs](https://nextjs.org/docs/app/getting-started/error-handling), [error.tsx convention](https://nextjs.org/docs/app/api-reference/file-conventions/error), [loading.tsx convention](https://nextjs.org/docs/app/api-reference/file-conventions/loading)
- **shadcn/ui** - [Sonner component](https://ui.shadcn.com/docs/components/sonner), [Skeleton component](https://ui.shadcn.com/docs/components/skeleton)

### Secondary (MEDIUM confidence)
- **Web search** - FastAPI StreamingResponse with BytesIO pattern verified against official FastAPI docs
- **Web search** - Sonner setup with Next.js App Router verified against shadcn/ui docs and GitHub repo
- **Web search** - Client-side file download pattern (fetch + blob + createObjectURL) confirmed across multiple sources

### Tertiary (LOW confidence)
- **Notion-style UI patterns** - General design direction based on web search; specific implementation details are at Claude's discretion per CONTEXT.md

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already installed or are shadcn/ui components; openpyxl write capabilities verified in official docs
- Architecture: HIGH - Patterns derived from existing codebase conventions; export endpoint follows established router patterns
- Export logic: HIGH - Column mapping is fully documented in `ExactColumnMapper.COLUMN_MAP`; `unmapped_data` structure is clear from codebase
- Pitfalls: HIGH - Identified through detailed codebase analysis (auth pattern, column order gap, variant propagation)
- Polish patterns: MEDIUM - Sonner and Skeleton are standard, but specific Notion-style design details are subjective

**Research date:** 2026-01-29
**Valid until:** 2026-02-28 (stable libraries, no expected breaking changes)
