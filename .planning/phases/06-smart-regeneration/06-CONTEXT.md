# Phase 6: Smart Regeneration - Context

**Gathered:** 2026-01-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Regenerate rejected products with enhanced prompts that learn from rejection feedback. Users can provide rejection reasons, view generation history, and trigger regeneration for single products or batches. System incorporates feedback into improved prompts.

</domain>

<decisions>
## Implementation Decisions

### Rejection feedback capture
- Predefined options only (no free text field)
- Providing a reason is optional (can reject without selecting)
- Multiple reasons can be selected per product
- Rejection reasons focused on content quality + SEO:
  - Off-brand tone
  - Generic/boring
  - Factually wrong
  - SEO issues
  - (Character limits already handled upstream, excluded)

### Regeneration triggers
- Both single product and batch regeneration supported
- Single product: regenerate button in review UI
- Batch: button in products page header AND review page
- Confirmation dialog before batch regeneration showing:
  - Count of products to regenerate
  - Estimated cost
- After regeneration, product returns to pending review status (no auto-approve)

### Prompt enhancement logic
- Include both positive and negative framing in regeneration prompts
  - Negative: "Avoid: off-brand tone, generic content"
  - Positive: "Focus on: brand-specific language, unique details"
- Include previous generated content in prompt so model sees what to avoid
- Combine manual rejection reasons AND AI review flags for fullest context
- Unlimited retry attempts (no hard cap on regenerations per product)

### Generation history display
- History shown in modal/dialog (not inline expandable)
- Each attempt shows: content (title + description), timestamp, rejection reasons, cost
- One-click restore button to use any previous attempt as current
- History only accessible in review UI (not products list)

### Claude's Discretion
- Exact wording of predefined rejection reasons
- Modal layout and styling for history view
- How "restore previous version" interacts with review status

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-smart-regeneration*
*Context gathered: 2026-01-29*
