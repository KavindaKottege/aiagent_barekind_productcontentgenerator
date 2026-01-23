# Phase 5: Review System - Context

**Gathered:** 2026-01-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Manual review workflow for AI-generated product content. Users can approve, reject, or edit generated titles and descriptions with keyboard-driven efficiency. AI can assist by evaluating accuracy against original data. Regeneration logic and export functionality are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Review UI Layout
- Single product focus - one product fills the screen, minimal distractions
- Collapsed original data - generated content prominent, original data in collapsible panel (click to expand if needed)
- Product images are KEY - must be displayed prominently from image URLs for verification
- Single main image display - show first image large, thumbnails for others (click to swap)
- Minimal metadata - keep UI clean, focus on generated title/description and images

### Navigation Flow
- Auto-advance after approve/reject - immediately show next product for efficient review
- Keyboard shortcuts (minimal set): A=approve, R=reject, arrow keys for navigation
- Review queue ordered by upload order (row_index) - same order as Excel
- End of queue shows completion message - display stats like 'All products reviewed' and return to list
- Skip to next unreviewed product when needed

### AI-Assisted Modes
- Dual AI review options: on-demand (user clicks 'Get AI feedback' per product) AND batch pre-analysis (trigger AI review for all upfront)
- AI evaluates accuracy only - check if generated content matches original input data and images (no hallucinations)
- Character limit validation handled by code, not AI review
- Status filter system with 6 categories: all, manually approved, manually rejected, manually reviewed, AI approved, AI rejected
- Category indicators show count badges for each status
- AI review processes all generated products regardless of filters
- Track and display AI review costs like generation costs (running total)
- Retry automatically on AI review failures (exponential backoff like generation)
- AI recommendations include brief reason (max 2 lines) - help user pinpoint why approved/rejected

### Edit Workflow
- Click title/description directly to edit (Notion/Linear pattern)
- Character counters always visible during editing (e.g., '45/30-60')
- Save as draft - edited content gets 'edited' status, user must explicitly approve later
- Exit edit with both Escape key and Cancel button for flexibility

### Claude's Discretion
- Exact layout spacing and typography
- Loading states and animations
- Error message wording
- Progress indicator design for batch AI review
- Exact keyboard shortcut assignments (as long as A=approve, R=reject, arrows=navigate)

</decisions>

<specifics>
## Specific Ideas

- "Product images are key for the user to verify" - images must be prominently displayed during review
- Status filter system needs clear separation between manual and AI review statuses for transparency
- Brief AI feedback (max 2 lines) should help user quickly understand approval/rejection reason

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope

</deferred>

---

*Phase: 05-review-system*
*Context gathered: 2026-01-23*
