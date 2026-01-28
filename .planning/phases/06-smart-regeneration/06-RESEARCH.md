# Phase 6: Smart Regeneration - Research

**Researched:** 2026-01-29
**Domain:** AI regeneration with feedback loops, prompt enhancement, history tracking
**Confidence:** HIGH

## Summary

Phase 6 implements "smart regeneration" - the ability for users to reject products with feedback, then regenerate content using that feedback to improve results. This phase builds on the existing LangChain generation infrastructure (Phase 4) and review system (Phase 5).

The core technical challenges are:
1. **Rejection feedback capture** - Storing user rejection reasons with predefined options
2. **History tracking** - Persisting generation attempts per product for display and restore
3. **Prompt enhancement** - Incorporating rejection feedback + AI review flags into regeneration prompts
4. **Selective regeneration** - Triggering regeneration for rejected products only

**Primary recommendation:** Extend the existing ProductGroup model with rejection reasons, enhance the AIGenerationService.build_*_prompt methods to accept feedback context, and reuse the existing generation worker infrastructure for regeneration jobs.

## Standard Stack

The phase extends existing infrastructure with no new libraries required.

### Core (Already Implemented)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| LangChain | 0.3.x | AI generation with structured output | Already integrated, handles prompt templating |
| SQLAlchemy | 2.x | Async ORM with JSONB support | Already stores generation audits with full history |
| ARQ | 0.26.x | Background job processing | Already handles generation jobs |
| SSE-Starlette | 2.x | Real-time progress streaming | Already used for generation/review progress |

### Supporting (No New Dependencies)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pydantic | 2.x | Schema validation | Already validates AI output structures |
| FastAPI | 0.115.x | REST API endpoints | Already provides generation/review routers |
| React Query | 5.x | Frontend state management | Already handles optimistic updates |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| JSONB for rejection_reasons | Separate table | JSONB simpler for small fixed list, no join needed |
| Reuse generation_audits for history | New history table | GenerationAudit already has all fields needed |
| Worker-based regeneration | Inline API call | Worker allows progress tracking, consistent with existing pattern |

**Installation:**
No new packages needed. Phase extends existing infrastructure.

## Architecture Patterns

### Recommended Changes to Existing Models

```
ProductGroup (extend existing)
  + rejection_reasons: list[str] | None  # JSONB array: ["off_brand_tone", "generic_boring", etc.]
  + regeneration_count: int              # Track how many times regenerated (starts at 0)

GenerationAudit (existing - already has what we need)
  - job_id           # Links to job that created it
  - product_group_id # Links to product
  - attempt_number   # 1, 2, 3... within a single job
  - success          # Whether attempt succeeded
  - generated_title  # The content generated
  - generated_description
  - prompt_used      # Full prompt for debugging
  - cost             # Cost of this attempt
  - created_at       # When generated

# Note: Multiple generation JOBS per product create multiple audit records
# History = all successful GenerationAudit records for a product_group_id
```

### Pattern 1: Enhanced Prompt with Feedback Context
**What:** Modify prompt builder to include rejection reasons and AI flags
**When to use:** On regeneration (regeneration_count > 0)
**Example:**
```python
# Extend existing build_title_prompt and build_description_prompt methods
def build_regeneration_prompt(
    self,
    product_group: ProductGroup,
    primary_product: Product,
    client: Client,
    app_settings: AppSettings | None = None,
    rejection_context: dict | None = None,  # NEW
) -> ChatPromptTemplate:
    # Build base prompt as normal...

    if rejection_context:
        # Add negative guidance section
        feedback_section = self._build_feedback_section(rejection_context)
        user_content += f"\n\n{feedback_section}"

    return ChatPromptTemplate.from_messages(messages)

def _build_feedback_section(self, context: dict) -> str:
    """Build the feedback section for regeneration prompts."""
    sections = []

    # Previous content to avoid
    if context.get("previous_title"):
        sections.append(f"Previous title (DO NOT reuse, was rejected): {context['previous_title']}")
    if context.get("previous_description"):
        sections.append(f"Previous description (DO NOT reuse, was rejected): {context['previous_description'][:500]}...")

    # User rejection reasons
    if context.get("rejection_reasons"):
        reasons = ", ".join(context["rejection_reasons"])
        sections.append(f"User rejected for: {reasons}")

    # AI review flags
    if context.get("ai_flags"):
        flags = ", ".join(context["ai_flags"])
        sections.append(f"AI review flagged: {flags}")

    # Positive framing
    positive_guidance = self._get_positive_guidance(context.get("rejection_reasons", []))
    if positive_guidance:
        sections.append(f"Focus on: {positive_guidance}")

    return "\n".join(sections)

def _get_positive_guidance(self, reasons: list[str]) -> str:
    """Convert negative reasons to positive guidance."""
    guidance = []
    reason_to_positive = {
        "off_brand_tone": "authentic brand voice and personality",
        "generic_boring": "unique, specific, engaging details",
        "factually_wrong": "accuracy and truthfulness to original data",
        "seo_issues": "natural keyword integration and SEO best practices",
    }
    for reason in reasons:
        if reason in reason_to_positive:
            guidance.append(reason_to_positive[reason])
    return ", ".join(guidance)
```

### Pattern 2: Selective Regeneration (Rejected Only)
**What:** Filter generation to only rejected products
**When to use:** Batch regeneration from review or products page
**Example:**
```python
# New endpoint for batch regeneration of rejected products
async def regenerate_rejected_products(
    client_id: UUID,
    db: AsyncSession,
    current_user: User,
    job_manager: JobManager,
) -> GenerationJob:
    # Query only rejected products
    result = await db.execute(
        select(ProductGroup)
        .where(ProductGroup.client_id == client_id)
        .where(ProductGroup.review_status == "rejected")
    )
    rejected_products = result.scalars().all()

    if not rejected_products:
        raise HTTPException(400, "No rejected products to regenerate")

    # Reset their status for regeneration
    for pg in rejected_products:
        pg.status = "pending"
        pg.review_status = None  # Clear review status
        pg.regeneration_count = (pg.regeneration_count or 0) + 1

    # Create and enqueue job (same as existing generation)
    job = await job_manager.create_job(
        client_id=client_id,
        user_id=current_user.id,
        total_count=len(rejected_products),
        is_regeneration=True,  # Flag for worker to use enhanced prompts
    )
    await job_manager.enqueue_job(job)
    return job
```

### Pattern 3: Generation History Display
**What:** Fetch all successful generation attempts for a product
**When to use:** History modal in review UI
**Example:**
```python
# Endpoint to get generation history for a product
@router.get("/product/{product_group_id}/history")
async def get_generation_history(
    product_group_id: UUID,
    db: AsyncSession,
) -> list[GenerationHistoryItem]:
    # Get all successful generation audits ordered by created_at desc
    result = await db.execute(
        select(GenerationAudit)
        .where(GenerationAudit.product_group_id == product_group_id)
        .where(GenerationAudit.success == True)
        .order_by(GenerationAudit.created_at.desc())
    )
    audits = result.scalars().all()

    # Get rejection reasons for each (stored on ProductGroup at time of rejection)
    # Note: We need to capture rejection_reasons at time of rejection
    # and store them with the audit or in a separate snapshot

    return [
        GenerationHistoryItem(
            id=a.id,
            title=a.generated_title,
            description=a.generated_description,
            created_at=a.created_at,
            cost=a.cost,
            # rejection_reasons would need to be stored per-attempt
        )
        for a in audits
    ]
```

### Pattern 4: Restore Previous Version
**What:** One-click restore from history
**When to use:** User clicks "Use this version" in history modal
**Example:**
```python
@router.post("/product/{product_group_id}/restore/{audit_id}")
async def restore_version(
    product_group_id: UUID,
    audit_id: UUID,
    db: AsyncSession,
    current_user: User,
) -> dict:
    # Get the audit record
    audit = await db.get(GenerationAudit, audit_id)
    if not audit or audit.product_group_id != product_group_id:
        raise HTTPException(404, "Version not found")

    # Update product group with restored content
    product_group = await db.get(ProductGroup, product_group_id)
    product_group.generated_title = audit.generated_title
    product_group.generated_description = audit.generated_description
    product_group.review_status = None  # Reset to pending review
    product_group.edited_title = None   # Clear any edits
    product_group.edited_description = None

    await db.commit()
    return {"success": True, "message": "Version restored"}
```

### Anti-Patterns to Avoid
- **Storing rejection reasons only on ProductGroup:** Must also store with audit/history for context
- **Modifying existing GenerationAudit schema unnecessarily:** It already has all needed fields
- **Creating separate "regeneration" worker:** Reuse existing generation_worker with flag
- **Inline regeneration (no background job):** Would lose progress tracking, break soft cap logic

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Background job processing | Custom queue | Existing ARQ workers | Already handles retries, status, progress |
| Progress streaming | WebSocket | Existing SSE infrastructure | Already proven, simpler |
| Prompt templating | String concatenation | LangChain ChatPromptTemplate | Already used, handles proper formatting |
| Cost tracking | Manual calculation | Existing CostTracker class | Already handles per-model pricing |
| Token counting | API calls | Existing tiktoken integration | Already implemented in CostTracker |

**Key insight:** The existing generation infrastructure (Phase 4) handles all the hard parts. This phase is primarily about data model extension and prompt enhancement, not new infrastructure.

## Common Pitfalls

### Pitfall 1: Losing Context on Multiple Regenerations
**What goes wrong:** Second regeneration doesn't know about first regeneration's rejection
**Why it happens:** Only storing current rejection_reasons, not history
**How to avoid:** Store rejection_reasons snapshot with each generation attempt (either in audit or new field)
**Warning signs:** "Why did the AI make the same mistake twice?"

### Pitfall 2: Prompt Length Explosion
**What goes wrong:** Including full previous content bloats prompt, hits token limits
**Why it happens:** Naively including entire previous title + description
**How to avoid:** Truncate previous content (first 500 chars of description), summarize rejection reasons
**Warning signs:** API errors about token limits, increasing costs

### Pitfall 3: Inconsistent State After Restore
**What goes wrong:** Restored version keeps old review status or edits
**Why it happens:** Only updating generated_* fields, not clearing review state
**How to avoid:** Always reset review_status, edited_*, reviewed_at when restoring
**Warning signs:** "I restored but it still shows as approved"

### Pitfall 4: Race Condition on Batch Regeneration
**What goes wrong:** User modifies rejection reasons while batch regeneration in progress
**Why it happens:** Prompt built at job start, not at product processing time
**How to avoid:** Build regeneration context per-product within worker loop
**Warning signs:** "The regenerated content doesn't reflect my updated rejection reasons"

### Pitfall 5: Unclear History Attribution
**What goes wrong:** User can't tell which attempt was the original vs regenerated
**Why it happens:** All attempts look identical in history
**How to avoid:** Add attempt_number or regeneration_count to history display
**Warning signs:** "Which one was my original generation?"

## Code Examples

### Rejection Reasons Enum (Frontend + Backend)
```typescript
// frontend/src/lib/rejection-reasons.ts
export const REJECTION_REASONS = {
  off_brand_tone: "Off-brand tone",
  generic_boring: "Generic/boring",
  factually_wrong: "Factually wrong",
  seo_issues: "SEO issues",
} as const;

export type RejectionReason = keyof typeof REJECTION_REASONS;
```

```python
# backend/app/schemas/regeneration.py
from typing import Literal
from pydantic import BaseModel

RejectionReasonType = Literal[
    "off_brand_tone",
    "generic_boring",
    "factually_wrong",
    "seo_issues",
]

class RejectWithReasonsRequest(BaseModel):
    product_group_id: str
    rejection_reasons: list[RejectionReasonType] = []  # Optional, can be empty

class RegenerateRequest(BaseModel):
    client_id: str  # For batch regeneration of rejected products

class RegenerateSingleRequest(BaseModel):
    product_group_id: str  # For single product regeneration

class GenerationHistoryItem(BaseModel):
    id: str
    title: str | None
    description: str | None
    created_at: str
    cost: str
    rejection_reasons: list[str]  # Reasons that led to this regeneration
    is_current: bool  # Is this the currently active version?
```

### Reject with Reasons Endpoint
```python
# backend/app/routers/review.py (extend existing)
@router.post("/reject-with-reasons", response_model=ReviewActionResponse)
async def reject_with_reasons(
    request: RejectWithReasonsRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ReviewActionResponse:
    """Reject a product with optional rejection reasons."""
    # Get product group
    result = await db.execute(
        select(ProductGroup).where(ProductGroup.id == request.product_group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(404, "Product not found")

    if group.user_id != current_user.id:
        raise HTTPException(403, "Not authorized")

    # Update with rejection reasons
    await db.execute(
        update(ProductGroup)
        .where(ProductGroup.id == request.product_group_id)
        .values(
            review_status="rejected",
            rejection_reasons=request.rejection_reasons,  # NEW JSONB field
            reviewed_at=func.now(),
        )
    )
    await db.commit()

    # Get next unreviewed (same as existing reject)
    next_result = await db.execute(
        select(ProductGroup)
        .where(ProductGroup.client_id == group.client_id)
        .where(ProductGroup.status == "generated")
        .where(ProductGroup.review_status.is_(None))
        .order_by(ProductGroup.first_row_index)
        .limit(1)
    )
    next_group = next_result.scalar_one_or_none()

    return ReviewActionResponse(
        success=True,
        message="Product rejected with feedback",
        next_product_id=next_group.id if next_group else None,
    )
```

### Frontend Rejection Reason Selection
```typescript
// frontend/src/components/review/rejection-reasons-dialog.tsx
import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Checkbox } from '@/components/ui/checkbox'
import { Button } from '@/components/ui/button'
import { REJECTION_REASONS, RejectionReason } from '@/lib/rejection-reasons'

interface Props {
  open: boolean
  onClose: () => void
  onConfirm: (reasons: RejectionReason[]) => void
}

export function RejectionReasonsDialog({ open, onClose, onConfirm }: Props) {
  const [selected, setSelected] = useState<RejectionReason[]>([])

  const toggle = (reason: RejectionReason) => {
    setSelected(prev =>
      prev.includes(reason)
        ? prev.filter(r => r !== reason)
        : [...prev, reason]
    )
  }

  const handleConfirm = () => {
    onConfirm(selected)
    setSelected([])
    onClose()
  }

  const handleSkip = () => {
    onConfirm([])  // Reject without reasons
    setSelected([])
    onClose()
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Why are you rejecting this content?</DialogTitle>
        </DialogHeader>

        <p className="text-sm text-gray-600 mb-4">
          Select any issues to help improve regeneration (optional)
        </p>

        <div className="space-y-3">
          {Object.entries(REJECTION_REASONS).map(([key, label]) => (
            <label key={key} className="flex items-center gap-2 cursor-pointer">
              <Checkbox
                checked={selected.includes(key as RejectionReason)}
                onCheckedChange={() => toggle(key as RejectionReason)}
              />
              <span>{label}</span>
            </label>
          ))}
        </div>

        <div className="flex gap-3 mt-6">
          <Button variant="outline" onClick={handleSkip}>
            Skip
          </Button>
          <Button onClick={handleConfirm}>
            Reject with Feedback
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Discard rejected content | Keep history, allow restore | 2024+ | Preserves work, enables comparison |
| Simple retry prompts | Include negative examples in prompt | 2024+ | Significantly improves regeneration quality |
| Separate regeneration flow | Same flow with enhanced context | Current | Simpler codebase, consistent UX |

**Deprecated/outdated:**
- **Separate regeneration endpoints:** Should reuse existing generation flow with flags
- **Free-text rejection feedback:** Predefined options are more structured and usable

## Open Questions

Things that couldn't be fully resolved:

1. **Should rejection_reasons be stored per-audit or per-product-group?**
   - What we know: Product group stores current reasons; history needs per-attempt reasons
   - What's unclear: Best schema design for historical context
   - Recommendation: Store on ProductGroup for current, snapshot to audit metadata JSONB on regeneration

2. **How to handle cost estimation for batch regeneration?**
   - What we know: Existing soft cap logic works for generation
   - What's unclear: Should regeneration have separate cost tracking?
   - Recommendation: Reuse existing cost tracking, it will just be a new job

3. **Should restored versions count as "regeneration"?**
   - What we know: Restore sets content but isn't a new AI call
   - What's unclear: Whether regeneration_count should increment
   - Recommendation: No, restore is different from regeneration (no AI call, no cost)

## Sources

### Primary (HIGH confidence)
- Existing codebase analysis: `backend/app/services/ai_generation.py` - Current prompt building patterns
- Existing codebase: `backend/app/models/generation_audit.py` - Already tracks all attempt data needed
- Existing codebase: `backend/app/workers/generation_worker.py` - Reusable worker pattern

### Secondary (MEDIUM confidence)
- [Prompt Chaining Guide](https://www.promptingguide.ai/techniques/prompt_chaining) - Feedback loop patterns
- [LangChain Few-Shot Prompting](https://python.langchain.com/docs/concepts/few_shot_prompting/) - Example-based guidance
- [Voiceflow Prompt Chaining Tutorial](https://www.voiceflow.com/blog/prompt-chaining) - Interactive chaining patterns

### Tertiary (LOW confidence)
- [ArXiv: Prompt Repetition](https://arxiv.org/html/2512.14982v1) - Research on prompt effectiveness (not directly applicable)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new dependencies, extends existing infrastructure
- Architecture: HIGH - Patterns derived from existing codebase analysis
- Pitfalls: HIGH - Based on understanding of existing state management

**Research date:** 2026-01-29
**Valid until:** 2026-03-01 (stable domain, existing patterns)
