---
phase: 07-export-polish
plan: 03
subsystem: frontend-export
tags: [export, dialog, file-download, toast, alert-dialog, server-action]
depends_on:
  requires: ["07-01", "07-02"]
  provides:
    - "ExportButton component in dashboard header"
    - "ExportDialog with stats display and download trigger"
    - "Server actions for export stats and token retrieval"
    - "Client-side .xlsx file download with blob + createObjectURL pattern"
  affects:
    - "07-04 (polish pass may adjust export button styling)"
tech-stack:
  added: []
  patterns:
    - "Token passing pattern: server action returns access_token for client-side fetch to FastAPI"
    - "Fetch + blob + createObjectURL + anchor click for client-side file download"
    - "AlertDialog for confirmation workflow before destructive/significant action"
    - "Skeleton loading state in dialog while fetching stats"
key-files:
  created:
    - frontend/src/app/actions/export.ts
    - frontend/src/components/export-dialog.tsx
    - frontend/src/components/export-button.tsx
  modified:
    - frontend/src/app/(dashboard)/layout.tsx
decisions:
  - decision: "Use AlertDialog (not Dialog) for export confirmation"
    rationale: "AlertDialog is semantically correct for confirmation workflows and matches existing codebase patterns"
  - decision: "Token passing via server action for download fetch"
    rationale: "Same pattern as SSE in review page; httpOnly cookies not accessible in client-side JS for cross-origin fetch"
  - decision: "Local TooltipProvider wrapping instead of global"
    rationale: "Follows existing codebase pattern from generation-progress.tsx; avoids unnecessary global provider"
metrics:
  duration: "2 minutes"
  completed: "2026-01-29"
---

# Phase 7 Plan 3: Frontend Export UI Summary

**One-liner:** Export button in dashboard header with confirmation dialog showing product stats, include-pending checkbox, and client-side .xlsx file download with Sonner toast feedback.

## What Was Built

### Task 1: Export Server Action + Export Dialog Component

**Server Action** (`frontend/src/app/actions/export.ts`):
- `getExportStats(clientId)`: Fetches GET /api/export/{clientId}/stats with bearer token from access_token cookie, returns ExportStats (total, not_generated, approved, pending, rejected)
- `getExportToken()`: Returns the access_token cookie value for client-side fetch to FastAPI binary download endpoint

**Export Dialog** (`frontend/src/components/export-dialog.tsx`):
- AlertDialog-based confirmation workflow with open/close state management via props
- Stats display: bordered card with divided rows showing each status count with color coding (green for approved, red for rejected, gray for not generated)
- Skeleton loading state while fetching stats on dialog open
- "Include content pending approval" checkbox using Radix Checkbox component
- Download handler: getExportToken() -> fetch blob -> createObjectURL -> anchor click -> revoke URL
- File named `{clientName}_products_{YYYY-MM-DD}.xlsx`
- Sonner toast: `toast.success('Export complete')` on success, `toast.error(message)` on failure
- Warning state: amber alert with AlertTriangle icon when no exportable content, with link to /review page
- Download button disabled when no approved products (or no approved + no pending when checkbox unchecked)

### Task 2: Export Button + Header Integration

**Export Button** (`frontend/src/components/export-button.tsx`):
- Client component reading selectedClientId from useSelectedClient() context
- Disabled state with Tooltip ("Select a client to export") when no client selected or "all" selected
- Styled to match header theme: white/transparent outline button with Download icon
- Opens ExportDialog on click, passing clientId and clientName

**Dashboard Layout** (`frontend/src/app/(dashboard)/layout.tsx`):
- ExportButton added after UploadButtonWrapper in header's left flex group
- Receives same `clients` prop as UploadButtonWrapper

## Deviations from Plan

None - plan executed exactly as written.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | b316a13 | Export server action and confirmation dialog |
| 2 | 53728e0 | Export button with header integration |

## Key Files

### Created
- `frontend/src/app/actions/export.ts` -- Server actions for export stats and token retrieval
- `frontend/src/components/export-dialog.tsx` -- Export confirmation dialog with stats, checkbox, download
- `frontend/src/components/export-button.tsx` -- Export button for header with dialog trigger

### Modified
- `frontend/src/app/(dashboard)/layout.tsx` -- Added ExportButton import and placement in header

## Verification Results

- `frontend/src/app/actions/export.ts` exists with getExportStats and getExportToken exports
- `frontend/src/components/export-dialog.tsx` exists with ExportDialog component
- `frontend/src/components/export-button.tsx` exists with ExportButton component
- `frontend/src/app/(dashboard)/layout.tsx` includes ExportButton import and rendering
- `npx tsc --noEmit` passes with zero errors
- All success criteria met:
  1. Export button visible in dashboard header, disabled without client selection
  2. Export dialog opens and populates stats from backend API
  3. Download produces `{ClientName}_products_{YYYY-MM-DD}.xlsx`
  4. Toast notification confirms export completion
  5. "Include content pending approval" checkbox affects download behavior
  6. Zero approved products shows warning with link to review page

## Next Phase Readiness

Frontend export UI is complete. The full export workflow is now end-to-end:
- Backend (07-01): Migration, ExcelExporter service, stats + download API endpoints
- Frontend (07-03): Export button in header, confirmation dialog, client-side download
- Ready for 07-04 (UI polish pass) and 07-05 (final verification)
