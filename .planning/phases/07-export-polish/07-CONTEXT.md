# Phase 7: Export & Polish - Context

**Gathered:** 2026-01-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can download approved content in original Excel format with all columns preserved, plus final UX refinements for a polished SaaS experience. The export reconstructs the original uploaded Excel with updated Product Name and Description columns for approved products. The polish pass ensures consistent styling, proper error handling, and responsive design across all pages.

</domain>

<decisions>
## Implementation Decisions

### Export button placement & visibility
- Export button lives in the app header, next to the upload products button
- Always visible, but disabled/greyed out with tooltip when no client selected or no approved products
- Export is per selected client only (no cross-client export)

### Export flow
- Click export opens a confirmation dialog before download
- Dialog shows: total products, not-generated count, approved count, pending count, rejected count (totals match)
- Checkbox in dialog: "Include content pending approval" (off by default)
- Download produces .xlsx file only (no CSV or other formats)
- File named: `{ClientName}_products_{YYYY-MM-DD}.xlsx`
- After download: toast notification "Export complete" — no other UI changes

### Export content rules — what gets updated
- ALL products included in the output spreadsheet (not just approved)
- Only approved products have their Product Name and Description columns updated with generated content
- If "Include content pending approval" is checked: any generated, non-rejected product also gets updated (regardless of manual/AI review status)
- Rejected and non-generated products keep their original values unchanged
- If user edited generated content, the edited version is always used (not original generated)
- For grouped option variants: generated title/description copied to ALL variant rows in the Excel

### Export content rules — Excel fidelity
- Full reconstruction of original Excel structure: all columns in original order, original header names
- Only Product Name and Description columns are modified; all other columns preserved as-is
- Original row ordering preserved (using row_index field)
- Original column headers preserved exactly as uploaded

### Zero approved export
- Block export with message: "No approved products to export" with link to review page

### Dashboard polish scope
- Consistency pass across all pages for spacing, typography, button styles, loading states
- Notion-style aesthetic: warm, spacious, content-first with gentle UI elements
- Keep existing shadcn color palette defaults — focus on spacing and layout consistency
- Keep current navigation structure — just ensure consistent styling
- Add subtle animations/transitions for page changes, hover states, expanding cards
- Guided empty state for new users: welcome message with steps (1. Create client, 2. Upload products, 3. Generate)
- Skeleton loaders (content placeholders) for loading states instead of spinners

### Error handling
- Toast notification system (Sonner) for all success/error/warning messages — consistent across app
- Error boundaries: root-level boundary as safety net + per-page boundaries for better recovery
- Both follow standard Next.js App Router error.tsx pattern

### Claude's Discretion
- Exact toast positioning and timing
- Skeleton loader shapes and animation details
- Specific pages that need the most polish attention
- Error boundary fallback UI design
- Transition/animation timing and easing
- Export dialog layout and styling

</decisions>

<specifics>
## Specific Ideas

- Notion-style feel: warm, spacious, content-first — but using existing shadcn palette (no color overhaul)
- Guided empty state should walk a new user through the workflow: create client -> upload -> generate
- Export dialog should make it very clear what the counts represent and that they total correctly
- "Include content pending approval" is the exact checkbox label

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-export-polish*
*Context gathered: 2026-01-29*
