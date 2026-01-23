# Phase 5: Review System - Research

**Researched:** 2026-01-23
**Domain:** Manual review workflow with keyboard navigation, real-time updates, and AI-assisted evaluation
**Confidence:** HIGH

## Summary

This phase implements a keyboard-driven review interface for AI-generated product content. The standard approach uses React keyboard shortcut libraries (react-hotkeys-hook), optimistic UI updates (useOptimistic), and structured AI evaluation via LangChain. The UI follows established patterns for focus management, inline editing with contentEditable, and image galleries with lightbox components.

Key architectural decisions: Status as VARCHAR check constraints (not ENUMs) for workflow flexibility, optimistic updates with useOptimistic for instant feedback, ARQ background jobs for batch AI review with automatic retry, and state management using React Context for review session undo/redo.

**Primary recommendation:** Use react-hotkeys-hook for keyboard shortcuts with scoped focus management, Yet Another React Lightbox for image display, useOptimistic for review action feedback, and extend existing ARQ job pattern for batch AI review with cost tracking.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| react-hotkeys-hook | 4.x | Keyboard shortcuts | Most popular React hotkey library, declarative API, TypeScript support, 1.8M weekly downloads |
| yet-another-react-lightbox | 3.x | Image gallery/lightbox | Modern, performant, React 19 compatible, plugin architecture, responsive image support |
| useOptimistic | React 19 built-in | Optimistic UI updates | Official React hook for instant UI feedback before server confirmation |
| react-contenteditable | 3.x | Inline text editing | Handles contentEditable cursor position issues, 200K+ weekly downloads |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| focus-trap-react | 10.x | Modal focus trapping | For keyboard accessibility in modal dialogs, WCAG 2.1 compliant |
| tenacity | 9.x (Python) | Retry with exponential backoff | For AI review retries, standard Python retry library with backoff strategies |
| LangChain with_structured_output | 1.2+ | AI content validation | For structured AI review responses with automatic validation and retries |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| react-hotkeys-hook | Custom useEffect listeners | react-hotkeys-hook handles edge cases, scopes, and cleanup automatically |
| yet-another-react-lightbox | react-image-lightbox | react-image-lightbox is deprecated, YARL is actively maintained with React 19 support |
| VARCHAR status | PostgreSQL ENUM | VARCHAR with check constraints allows adding review statuses without ALTER TYPE (more flexible) |

**Installation:**
```bash
# Frontend
npm install react-hotkeys-hook yet-another-react-lightbox react-contenteditable focus-trap-react

# Backend (already installed from Phase 4)
# tenacity, langchain, arq
```

## Architecture Patterns

### Recommended Project Structure
```
frontend/app/dashboard/review/
├── [client_id]/
│   └── page.tsx              # Review page with keyboard navigation
├── _components/
│   ├── ReviewInterface.tsx   # Main single-product review UI
│   ├── ImageDisplay.tsx      # Image gallery with lightbox
│   ├── InlineEditor.tsx      # Editable title/description with character counter
│   ├── AIReviewPanel.tsx     # AI feedback display with recommendations
│   └── ReviewStats.tsx       # Progress/completion stats
└── _lib/
    ├── review-actions.ts     # Server actions for approve/reject/edit
    ├── ai-review-actions.ts  # Server actions for AI review
    └── ReviewContext.tsx     # Context for undo/redo state management

backend/app/api/review/
├── routes.py                 # Review endpoints (approve, reject, edit, AI review)
├── ai_review_service.py      # LangChain AI review logic
└── review_jobs.py            # ARQ job for batch AI review
```

### Pattern 1: Keyboard Navigation with Scopes
**What:** Use react-hotkeys-hook with component-scoped shortcuts to prevent global conflicts
**When to use:** Single-page review interface where shortcuts should only work when review UI is focused
**Example:**
```typescript
// Source: https://react-hotkeys-hook.vercel.app/
import { useHotkeys } from 'react-hotkeys-hook';

function ReviewInterface({ productId }: { productId: string }) {
  const reviewRef = useRef<HTMLDivElement>(null);

  // Scoped to review container - only trigger when focused
  useHotkeys('a', () => handleApprove(), { scopes: ['review'] }, [productId]);
  useHotkeys('r', () => handleReject(), { scopes: ['review'] }, [productId]);
  useHotkeys('left', () => handlePrevious(), { scopes: ['review'] }, [productId]);
  useHotkeys('right', () => handleNext(), { scopes: ['review'] }, [productId]);
  useHotkeys('e', () => handleEdit(), { scopes: ['review'] }, [productId]);

  return (
    <div ref={reviewRef} tabIndex={-1} data-scope="review">
      {/* Review UI */}
    </div>
  );
}
```

### Pattern 2: Optimistic Review Actions
**What:** Update UI immediately on approve/reject, then sync with server
**When to use:** User actions that should feel instant (approve, reject, undo)
**Example:**
```typescript
// Source: https://react.dev/reference/react/useOptimistic
'use client';

import { useOptimistic } from 'react';
import { approveProduct, rejectProduct } from './review-actions';

function ReviewInterface({ product }: { product: Product }) {
  const [optimisticProduct, setOptimisticProduct] = useOptimistic(
    product,
    (state, newStatus: string) => ({ ...state, review_status: newStatus })
  );

  async function handleApprove() {
    setOptimisticProduct('approved'); // Instant UI update
    await approveProduct(product.id); // Server sync
  }

  async function handleReject() {
    setOptimisticProduct('rejected'); // Instant UI update
    await rejectProduct(product.id); // Server sync
  }

  return (
    <div>
      <h2>{optimisticProduct.generated_title}</h2>
      <p>Status: {optimisticProduct.review_status}</p>
      <button onClick={handleApprove}>Approve (A)</button>
      <button onClick={handleReject}>Reject (R)</button>
    </div>
  );
}
```

### Pattern 3: Inline Editing with Character Counter
**What:** Click-to-edit title/description with live character count validation
**When to use:** Editable generated content that must meet character limits
**Example:**
```typescript
// Based on: https://www.npmjs.com/package/react-contenteditable
import ContentEditable from 'react-contenteditable';
import { useState, useRef } from 'react';

function InlineEditor({
  initialValue,
  minChars,
  maxChars,
  onSave
}: {
  initialValue: string;
  minChars: number;
  maxChars: number;
  onSave: (value: string) => void;
}) {
  const [value, setValue] = useState(initialValue);
  const [isEditing, setIsEditing] = useState(false);
  const contentRef = useRef(value);

  const charCount = value.length;
  const isValid = charCount >= minChars && charCount <= maxChars;

  const handleChange = (evt: any) => {
    const newValue = evt.target.value;
    if (newValue.length <= maxChars) { // Prevent typing beyond limit
      setValue(newValue);
      contentRef.current = newValue;
    }
  };

  const handleSave = () => {
    if (isValid) {
      onSave(value);
      setIsEditing(false);
    }
  };

  return (
    <div>
      <ContentEditable
        html={contentRef.current}
        disabled={!isEditing}
        onChange={handleChange}
        onClick={() => setIsEditing(true)}
        className={isEditing ? 'editing' : ''}
      />
      <div className={`character-counter ${!isValid ? 'invalid' : ''}`}>
        {charCount}/{minChars}-{maxChars}
      </div>
      {isEditing && (
        <>
          <button onClick={handleSave} disabled={!isValid}>Save</button>
          <button onClick={() => setIsEditing(false)}>Cancel (Esc)</button>
        </>
      )}
    </div>
  );
}
```

### Pattern 4: Image Gallery with Lightbox
**What:** Display product images with thumbnail navigation and full-screen lightbox
**When to use:** Review interface needs prominent image display for verification
**Example:**
```typescript
// Source: https://yet-another-react-lightbox.com/
import Lightbox from "yet-another-react-lightbox";
import "yet-another-react-lightbox/styles.css";
import { useState } from 'react';

function ImageDisplay({ images }: { images: string[] }) {
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);

  if (!images || images.length === 0) return <div>No images</div>;

  const slides = images.map(url => ({ src: url }));

  return (
    <>
      <div className="image-gallery">
        <img
          src={images[currentIndex]}
          alt="Main product image"
          onClick={() => setLightboxOpen(true)}
          className="main-image cursor-pointer"
        />
        <div className="thumbnails">
          {images.map((url, idx) => (
            <img
              key={idx}
              src={url}
              alt={`Thumbnail ${idx + 1}`}
              onClick={() => setCurrentIndex(idx)}
              className={idx === currentIndex ? 'active' : ''}
            />
          ))}
        </div>
      </div>

      <Lightbox
        open={lightboxOpen}
        close={() => setLightboxOpen(false)}
        slides={slides}
        index={currentIndex}
      />
    </>
  );
}
```

### Pattern 5: AI Review with Structured Output
**What:** Use LangChain with_structured_output for AI accuracy evaluation with automatic validation
**When to use:** Batch or on-demand AI review of generated content against original data
**Example:**
```python
# Source: https://docs.langchain.com/oss/python/langchain/structured-output
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Literal

class AIReviewResult(BaseModel):
    """Structured AI review result with validation."""
    recommendation: Literal["approve", "reject"] = Field(
        description="Whether to approve or reject the generated content"
    )
    reason: str = Field(
        max_length=200,
        description="Brief reason for recommendation (max 2 lines)"
    )
    safety_flags: list[str] = Field(
        default_factory=list,
        description="List of safety concerns: quantity_confusion, misleading_expectations, misrepresentation"
    )
    accuracy_score: float = Field(
        ge=0.0, le=1.0,
        description="Accuracy score from 0.0 to 1.0"
    )

async def review_product_with_ai(
    original_data: dict,
    generated_title: str,
    generated_description: str,
    images: list[str]
) -> AIReviewResult:
    """Review generated content using GPT-5.2 with structured output."""

    llm = ChatOpenAI(model="gpt-5.2", temperature=0.3)

    # with_structured_output with strict=True guarantees schema conformance
    structured_llm = llm.with_structured_output(AIReviewResult, strict=True)

    prompt = f"""Review the AI-generated product content for accuracy.

ORIGINAL DATA:
{original_data}

GENERATED CONTENT:
Title: {generated_title}
Description: {generated_description}

CRITICAL SAFETY CHECKS:
- Quantity confusion: Is it clear if this is 1 item or a set? Is price per-item or per-set?
- Misleading expectations: Does the description accurately represent what they're receiving?
- Misrepresentation: Does it fairly represent what the client called it?

Evaluate if the generated content accurately reflects the original data and images.
Provide your recommendation and brief reason (max 2 lines).
"""

    # Automatic validation and retries handled by LangChain
    result = await structured_llm.ainvoke(prompt)
    return result
```

### Pattern 6: Undo/Redo with Context
**What:** Session-based undo/redo using React Context with history stack
**When to use:** Review session where users need to undo/redo decisions during active session
**Example:**
```typescript
// Based on: https://www.geeksforgeeks.org/reactjs/implementing-undo-redo-functionality-in-react-apps/
import { createContext, useContext, useState, useCallback } from 'react';

interface ReviewAction {
  productId: string;
  status: 'approved' | 'rejected' | 'edited';
  previousStatus: string;
  timestamp: Date;
}

interface ReviewHistory {
  past: ReviewAction[];
  present: ReviewAction | null;
  future: ReviewAction[];
}

const ReviewContext = createContext<{
  history: ReviewHistory;
  recordAction: (action: ReviewAction) => void;
  undo: () => ReviewAction | null;
  redo: () => ReviewAction | null;
  canUndo: boolean;
  canRedo: boolean;
} | null>(null);

export function ReviewProvider({ children }: { children: React.ReactNode }) {
  const [history, setHistory] = useState<ReviewHistory>({
    past: [],
    present: null,
    future: []
  });

  const recordAction = useCallback((action: ReviewAction) => {
    setHistory(prev => ({
      past: prev.present ? [...prev.past, prev.present] : prev.past,
      present: action,
      future: [] // Clear future when new action recorded
    }));
  }, []);

  const undo = useCallback(() => {
    if (history.past.length === 0) return null;

    const previous = history.past[history.past.length - 1];
    const newPast = history.past.slice(0, -1);

    setHistory({
      past: newPast,
      present: previous,
      future: history.present ? [history.present, ...history.future] : history.future
    });

    return previous;
  }, [history]);

  const redo = useCallback(() => {
    if (history.future.length === 0) return null;

    const next = history.future[0];
    const newFuture = history.future.slice(1);

    setHistory({
      past: history.present ? [...history.past, history.present] : history.past,
      present: next,
      future: newFuture
    });

    return next;
  }, [history]);

  return (
    <ReviewContext.Provider value={{
      history,
      recordAction,
      undo,
      redo,
      canUndo: history.past.length > 0,
      canRedo: history.future.length > 0
    }}>
      {children}
    </ReviewContext.Provider>
  );
}

export const useReviewHistory = () => {
  const context = useContext(ReviewContext);
  if (!context) throw new Error('useReviewHistory must be used within ReviewProvider');
  return context;
};
```

### Pattern 7: ARQ Background Job for Batch AI Review
**What:** Extend existing ARQ job pattern for batch AI review with progress tracking and cost calculation
**When to use:** User triggers "Review All" to get AI recommendations for all generated products
**Example:**
```python
# Based on existing Phase 4 ARQ pattern from backend/app/workers/generation_worker.py
from arq import ArqRedis
from app.services.ai_review_service import AIReviewService
from app.models.review_job import ReviewJob
from decimal import Decimal

async def batch_ai_review_worker(ctx: dict, job_id: str) -> None:
    """ARQ worker for batch AI review with progress tracking."""

    async with get_db_session() as db:
        # Get job and products to review
        job = await db.get(ReviewJob, job_id)
        if not job:
            return

        # Update job status
        job.status = "running"
        job.started_at = datetime.utcnow()
        await db.commit()

        # Get all 'generated' product groups for this client
        product_groups = await db.execute(
            select(ProductGroup)
            .where(
                ProductGroup.client_id == job.client_id,
                ProductGroup.status == 'generated'
            )
            .order_by(ProductGroup.row_index)
        )
        product_groups = product_groups.scalars().all()

        job.total_count = len(product_groups)
        await db.commit()

        review_service = AIReviewService(db)

        for group in product_groups:
            # Check for pause/cancel
            await db.refresh(job)
            if job.status in ['paused', 'cancelled']:
                return

            try:
                # AI review with automatic retries via tenacity
                result = await review_service.review_with_retry(
                    product_group=group,
                    job_id=job.id
                )

                # Update product group with AI review
                group.ai_review_status = result.recommendation
                group.ai_review_reason = result.reason
                group.ai_review_safety_flags = result.safety_flags

                job.completed_count += 1
                job.total_cost += result.cost

            except Exception as e:
                job.failed_count += 1
                # Log error but continue

            await db.commit()

        # Mark job complete
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        await db.commit()
```

### Anti-Patterns to Avoid
- **Global keyboard listeners without scopes:** Use scoped hotkeys to prevent conflicts when modals/dialogs are open
- **Throwing validation errors from Server Actions:** Return errors as data with discriminated unions, don't trigger Error Boundary for validation
- **PostgreSQL ENUMs for review status:** Use VARCHAR with check constraints - easier to add new statuses (manually_reviewed, ai_approved, ai_rejected, edited)
- **Cursor position bugs in contentEditable:** Use react-contenteditable library which handles cursor preservation, not raw contentEditable
- **Optimistic updates without error rollback:** useOptimistic automatically reverts on error, but handle edge cases with toast notifications

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Keyboard shortcuts | Custom keydown listeners with cleanup | react-hotkeys-hook | Handles scopes, modifier keys, sequences, cleanup, memory leaks automatically |
| Image lightbox | Custom modal with prev/next | yet-another-react-lightbox | Handles keyboard navigation, touch gestures, preloading, responsive images, accessibility |
| ContentEditable cursor | Manual selection/range APIs | react-contenteditable | Cursor position preservation is complex with React re-renders, library handles edge cases |
| Focus trap in modals | Manual focus management | focus-trap-react | WCAG 2.1 compliance, handles Tab/Shift+Tab, Escape key, initial focus, focus restoration |
| Exponential backoff | Custom retry with setTimeout | tenacity library | Handles jitter, max attempts, different backoff strategies, proven patterns |
| Optimistic UI state | Manual state with rollback logic | useOptimistic hook | Built-in React 19 hook, automatic rollback on error, integrates with Server Actions |

**Key insight:** Keyboard navigation and contentEditable editing have many edge cases (focus management, cursor position, modifier keys, cleanup). Libraries solve these with years of production testing. Building custom often leads to bugs in accessibility and user experience.

## Common Pitfalls

### Pitfall 1: ContentEditable Cursor Jumping
**What goes wrong:** When editing contentEditable elements in React, cursor jumps to start/end on every keystroke due to re-renders
**Why it happens:** React re-renders the component, recreates the DOM node, and loses cursor position. Updating textContent directly causes cursor reset.
**How to avoid:**
- Use react-contenteditable library which preserves cursor position
- Use `useLayoutEffect` instead of `useEffect` for cursor restoration (synchronous DOM mutation)
- Only update innerHTML when value actually changes (conditional assignment)
**Warning signs:** User types and cursor jumps to beginning/end after each character

### Pitfall 2: Keyboard Shortcuts Without Focus Management
**What goes wrong:** Keyboard shortcuts trigger even when user is typing in input fields, or when modals are open
**Why it happens:** Global event listeners don't check focus context or element hierarchy
**How to avoid:**
- Use scoped hotkeys with react-hotkeys-hook
- Check if target element is input/textarea before triggering
- Disable shortcuts when modals/dialogs are open using scope management
- Add `tabIndex={-1}` to review container and use data attributes for scope
**Warning signs:** Shortcuts trigger while typing in search box, shortcuts work in background when modal is open

### Pitfall 3: Optimistic Updates Without Server Sync
**What goes wrong:** UI shows approved/rejected status, but server action fails silently. User thinks action succeeded but it didn't.
**Why it happens:** Using optimistic state without awaiting server action, or not handling errors from Server Actions
**How to avoid:**
- Always await Server Action after optimistic update
- useOptimistic automatically reverts on error, but add toast notification
- Use try/catch in Server Actions and return errors as data
- Display loading states for server sync even with optimistic UI
**Warning signs:** User approves products, refreshes page, sees status reverted to previous state

### Pitfall 4: PostgreSQL ENUM for Review Status
**What goes wrong:** Adding new review statuses (like 'ai_approved', 'ai_rejected', 'manually_reviewed') requires ALTER TYPE migration which locks table
**Why it happens:** PostgreSQL ENUMs are immutable - can't remove values, changing order is complex
**How to avoid:**
- Use VARCHAR with check constraint instead of ENUM
- Check constraint can be dropped and recreated without table lock
- Makes adding review statuses as simple as updating constraint
**Warning signs:** Migration takes long time on large tables, production downtime for adding status

### Pitfall 5: Race Conditions in Batch AI Review
**What goes wrong:** User starts batch AI review, then manually reviews products. AI review overwrites manual decisions.
**Why it happens:** Background job doesn't check current status before updating
**How to avoid:**
- Worker should only update products with status='generated' (skip if already manually reviewed)
- Use optimistic locking with updated_at timestamp check
- Display warning if batch review is running when user tries manual review
- Allow cancelling batch review from UI
**Warning signs:** User's manual approvals get overwritten by AI review that started earlier

### Pitfall 6: Missing Character Limit Validation on Edit
**What goes wrong:** User edits description to 5000 characters, saves, but backend validation rejects it
**Why it happens:** Frontend doesn't enforce same character limits as AI generation
**How to avoid:**
- Share character limit constants between frontend and backend (30-60 title, 2000-3000 description)
- Real-time validation during editing with visual feedback
- Disable Save button when out of range
- Display clear error message showing exact limits
**Warning signs:** User spends time editing, clicks Save, gets validation error

### Pitfall 7: Image Loading Performance
**What goes wrong:** Review page loads slowly when product has 10+ high-resolution images
**Why it happens:** Loading all images at full resolution simultaneously
**How to avoid:**
- Use responsive images with srcSet for automatic resolution switching
- Lazy load thumbnail images
- Lightbox preloads limited number of images (yet-another-react-lightbox default)
- Consider image CDN with automatic resizing (Cloudinary, imgix)
**Warning signs:** Review page takes 5+ seconds to load, browser memory usage spikes

## Code Examples

Verified patterns from official sources:

### Server Action with Error Handling (Next.js 15 Pattern)
```typescript
// Source: https://medium.com/@pawantripathi648/next-js-server-actions-error-handling-the-pattern-i-wish-i-knew-earlier-e717f28f2f75
'use server';

import { z } from 'zod';

const ApproveSchema = z.object({
  productGroupId: z.string().uuid(),
  editedTitle: z.string().min(30).max(60).optional(),
  editedDescription: z.string().min(2000).max(3000).optional(),
});

type ActionState = {
  success: boolean;
  message?: string;
  errors?: Record<string, string[]>;
};

export async function approveProduct(
  prevState: ActionState,
  formData: FormData
): Promise<ActionState> {
  // Validate input
  const parsed = ApproveSchema.safeParse({
    productGroupId: formData.get('productGroupId'),
    editedTitle: formData.get('editedTitle'),
    editedDescription: formData.get('editedDescription'),
  });

  if (!parsed.success) {
    return {
      success: false,
      errors: parsed.error.flatten().fieldErrors,
    };
  }

  try {
    const accessToken = await getAccessToken();
    const response = await fetch(`${API_URL}/api/review/approve`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(parsed.data),
    });

    if (!response.ok) {
      return {
        success: false,
        message: 'Failed to approve product',
      };
    }

    return {
      success: true,
      message: 'Product approved successfully',
    };
  } catch (error) {
    return {
      success: false,
      message: 'Network error occurred',
    };
  }
}
```

### Tenacity Retry with Exponential Backoff
```python
# Source: https://johal.in/tenacity-retries-exponential-backoff-decorators-2026/
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from openai import RateLimitError, APIError
from decimal import Decimal

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((RateLimitError, APIError)),
)
async def review_with_ai_retry(
    product_group: ProductGroup,
    original_data: dict,
) -> AIReviewResult:
    """AI review with automatic retry on rate limits and API errors."""

    llm = ChatOpenAI(model="gpt-5.2", temperature=0.3)
    structured_llm = llm.with_structured_output(AIReviewResult, strict=True)

    prompt = build_review_prompt(product_group, original_data)

    # This will retry up to 3 times with exponential backoff:
    # Attempt 1: immediate
    # Attempt 2: wait 2 seconds
    # Attempt 3: wait 4 seconds
    result = await structured_llm.ainvoke(prompt)

    return result
```

### Focus Trap for Modal Keyboard Navigation
```typescript
// Source: https://blog.logrocket.com/build-accessible-modal-focus-trap-react/
import FocusTrap from 'focus-trap-react';
import { useHotkeys } from 'react-hotkeys-hook';

function AIReviewModal({ isOpen, onClose, feedback }: {
  isOpen: boolean;
  onClose: () => void;
  feedback: string;
}) {
  // Escape key to close
  useHotkeys('esc', () => onClose(), { enabled: isOpen });

  if (!isOpen) return null;

  return (
    <FocusTrap>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        className="modal-overlay"
      >
        <div className="modal-content">
          <h2 id="modal-title">AI Review Feedback</h2>
          <p>{feedback}</p>
          <button onClick={onClose} autoFocus>
            Close (Esc)
          </button>
        </div>
      </div>
    </FocusTrap>
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| useFormState | useActionState | React 19 (2024) | Renamed hook with same functionality for Server Action state |
| Simple React Lightbox | Yet Another React Lightbox | 2023 | SRL deprecated, YARL is modern replacement with React 19 support |
| Custom undo/redo | useState with history stack | 2020+ | Pattern is stable, libraries like redux-undo exist but overkill for session-only undo |
| Draft.js for inline editing | react-contenteditable | 2021+ | Draft.js too heavy for simple inline editing, react-contenteditable handles cursor issues |
| PostgreSQL ENUM | VARCHAR + check constraint | 2020+ | Flexibility preferred over type safety for workflow statuses that evolve |

**Deprecated/outdated:**
- **useFormState**: Renamed to useActionState in React 19
- **Simple React Lightbox**: Deprecated in 2023, use Yet Another React Lightbox
- **Draft.js for simple editing**: Too heavy for inline text editing, use contenteditable with react-contenteditable wrapper

## Open Questions

Things that couldn't be fully resolved:

1. **GPT-5.2 Pricing for AI Review**
   - What we know: GPT-5.2 exists (released August 2025), LangChain supports with_structured_output
   - What's unclear: Exact pricing per token for GPT-5.2 (need to check OpenAI pricing API)
   - Recommendation: Use same cost tracking pattern as Phase 4 (tiktoken + CostTracker), fetch current pricing from OpenAI API

2. **Review Status Values**
   - What we know: Current status is VARCHAR(50) in product_groups table, default 'pending'
   - What's unclear: Complete list of status values used across phases (generated, pending, etc.)
   - Recommendation: Define complete status enum-like values: pending, generated, manually_approved, manually_rejected, ai_approved, ai_rejected, edited. Use check constraint.

3. **Real-time Updates for Concurrent Review**
   - What we know: SSE pattern exists from Phase 4 for generation progress
   - What's unclear: Whether review should support real-time updates when multiple users review same client
   - Recommendation: Start without real-time (single-user assumption), add SSE for review progress if needed. Use optimistic updates for single user.

4. **Image URL Storage Format**
   - What we know: Images stored as JSONB array in products table
   - What's unclear: Are these full URLs or relative paths? CDN or direct storage?
   - Recommendation: Check existing product data to confirm format. If external URLs, add image loading error handling.

## Sources

### Primary (HIGH confidence)
- **react-hotkeys-hook official docs** - https://react-hotkeys-hook.vercel.app/
- **Yet Another React Lightbox official docs** - https://yet-another-react-lightbox.com/
- **React useOptimistic official docs** - https://react.dev/reference/react/useOptimistic
- **LangChain Structured Output docs** - https://docs.langchain.com/oss/python/langchain/structured-output
- **Existing codebase** - backend/app/models/product_group.py, generation_job.py, generation_audit.py

### Secondary (MEDIUM confidence)
- [Next.js Server Actions Error Handling Guide](https://medium.com/@pawantripathi648/next-js-server-actions-error-handling-the-pattern-i-wish-i-knew-earlier-e717f28f2f75) - Production-ready error patterns
- [Tenacity Retries with Exponential Backoff](https://johal.in/tenacity-retries-exponential-backoff-decorators-2026/) - ARQ retry patterns
- [Building Resilient Task Queues in FastAPI with ARQ](https://davidmuraya.com/blog/fastapi-arq-retries/) - ARQ retry implementation
- [LogRocket: Build Accessible Modal with Focus Trap](https://blog.logrocket.com/build-accessible-modal-focus-trap-react/) - Focus trap patterns
- [PostgreSQL ENUM vs Lookup Table](https://www.cybertec-postgresql.com/en/lookup-table-or-enum-type/) - Database design decision
- [Implementing State Machines in PostgreSQL](https://felixge.de/2017/07/27/implementing-state-machines-in-postgresql/) - Workflow state patterns

### Tertiary (LOW confidence)
- [React Undo/Redo Functionality Guide](https://www.geeksforgeeks.org/reactjs/implementing-undo-redo-functionality-in-react-apps/) - General pattern, needs verification
- [ContentEditable Cursor Issues](https://github.com/facebook/react/issues/2047) - Long-standing React issue, multiple solutions exist

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official documentation for all libraries, npm downloads verified, React 19 compatibility confirmed
- Architecture: HIGH - Patterns based on official docs (React, Next.js, LangChain), verified with existing codebase structure
- Pitfalls: MEDIUM-HIGH - ContentEditable and keyboard shortcuts pitfalls well-documented, some from experience reports rather than official docs
- AI Review: MEDIUM - LangChain structured output well-documented, GPT-5.2 pricing needs verification

**Research date:** 2026-01-23
**Valid until:** 2026-02-23 (30 days - stable ecosystem, but verify GPT-5.2 pricing and LangChain updates)
