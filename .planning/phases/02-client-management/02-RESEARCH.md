# Phase 2: Client Management - Research

**Researched:** 2026-01-22
**Domain:** CRUD operations with multi-tenant client profiles, form handling with tabs, state management
**Confidence:** HIGH

## Summary

Phase 2 implements a classic multi-tenant client profile management system where users create and manage client records with brand information and optional custom AI prompts. The technical foundation is well-established: FastAPI async CRUD with SQLAlchemy relationships, Next.js Server Actions with Zod validation, and shadcn/ui components for forms and dropdowns.

The standard approach uses a foreign key relationship from clients table to users table, with eager loading strategies to avoid async lazy-loading pitfalls. Frontend uses Server Actions with `useActionState` for form handling, `useOptimistic` for instant UI updates, and localStorage for selected client persistence. Admin-only delete operations use dependency injection for permission checks at the route level.

**Primary recommendation:** Follow FastAPI async patterns with explicit eager loading, use Next.js Server Actions with Zod validation, implement optimistic updates for list operations, and use shadcn/ui AlertDialog for delete confirmations.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy | 2.0+ | Async ORM with relationship support | Industry standard, async-first with explicit relationship loading |
| Zod | 4.x | Schema validation (TypeScript) | Type-safe validation, works seamlessly with Server Actions |
| shadcn/ui | Latest | UI component primitives | Accessible, customizable, built on Radix UI primitives |
| FastAPI Depends | Built-in | Dependency injection for permissions | Native FastAPI pattern for reusable route guards |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| React useOptimistic | React 19+ | Optimistic UI updates | Create/delete operations to show instant feedback |
| React useActionState | React 19+ | Server Action state management | Form submission with validation errors |
| Alembic | 1.13+ | Database migrations | Already in use; add client table migration |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| localStorage | Server-side session storage | localStorage is simpler for non-sensitive client selection state |
| useOptimistic | Manual state + loading flags | useOptimistic automates rollback on server response |
| AlertDialog | Regular Dialog | AlertDialog forces explicit confirmation, better UX for destructive actions |

**Installation:**
```bash
# Backend: Already have core dependencies
# No new backend packages needed

# Frontend: Likely need shadcn/ui components
npx shadcn@latest add select badge dialog alert-dialog tabs textarea
```

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── models/
│   ├── user.py          # Existing
│   └── client.py        # New: Client model with user_id FK
├── routers/
│   └── clients.py       # New: CRUD endpoints
├── dependencies/
│   └── auth.py          # Enhance: Add admin_required dependency
└── dal/
    └── clients.py       # New: Data Access Layer for clients

frontend/src/
├── app/(dashboard)/
│   └── clients/
│       ├── page.tsx     # Client list/management page
│       ├── [id]/
│       │   └── page.tsx # Edit client page
│       └── new/
│           └── page.tsx # Create client page
├── components/
│   ├── client-selector.tsx  # Dropdown in header/toolbar
│   └── forms/
│       └── client-form.tsx  # Multi-tab form component
├── actions/
│   └── clients.ts       # Server Actions for CRUD
└── lib/
    └── client-context.tsx   # Selected client state management
```

### Pattern 1: Foreign Key Relationship with Eager Loading
**What:** Client model with `user_id` foreign key, always eager-load the relationship in queries
**When to use:** All async SQLAlchemy queries that access relationships
**Example:**
```python
# Source: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
# backend/app/models/client.py
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID
from app.database import Base

class Client(Base):
    __tablename__ = "clients"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_name: Mapped[str] = mapped_column(String(255), nullable=False)
    story: Mapped[str | None] = mapped_column(Text, nullable=True)
    tone: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str | None] = mapped_column(String(100), nullable=True)
    guidelines: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Custom prompts (optional overrides)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    task1_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    task2_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship - use lazy="raise" to prevent accidental lazy loading
    user: Mapped["User"] = relationship(back_populates="clients", lazy="raise")

# backend/app/dal/clients.py - Always use eager loading
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def get_clients_for_user(db: AsyncSession, user_id: UUID) -> list[Client]:
    result = await db.execute(
        select(Client)
        .where(Client.user_id == user_id)
        .options(selectinload(Client.user))  # Eager load relationship
        .order_by(Client.brand_name)
    )
    return result.scalars().all()
```

### Pattern 2: Admin-Only Permission Dependency
**What:** Reusable dependency that raises 403 if user is not admin
**When to use:** Delete client endpoint, prompt settings endpoints
**Example:**
```python
# Source: https://fastapi.tiangolo.com/tutorial/dependencies/
# backend/app/dependencies/auth.py
from fastapi import HTTPException, status, Depends
from app.models.user import User
from app.dependencies.auth import get_current_user  # Existing

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency that ensures current user is an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

# backend/app/routers/clients.py
@router.delete("/clients/{client_id}")
async def delete_client(
    client_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)  # Enforces admin check
):
    # Delete logic here
    pass
```

### Pattern 3: Multi-Tab Form with Server Actions
**What:** Client Component with tabs, Server Actions for validation/submission
**When to use:** Client create/edit forms
**Example:**
```typescript
// Source: https://nextjs.org/docs/app/guides/forms
// frontend/src/components/forms/client-form.tsx
'use client'
import { useActionState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { createClient, updateClient } from '@/actions/clients'

export function ClientForm({ client }: { client?: Client }) {
  const action = client ? updateClient.bind(null, client.id) : createClient
  const [state, formAction, pending] = useActionState(action, { errors: {} })

  return (
    <form action={formAction}>
      <Tabs defaultValue="brand">
        <TabsList>
          <TabsTrigger value="brand">Brand & Guidelines</TabsTrigger>
          <TabsTrigger value="prompts">Custom Prompts (Optional)</TabsTrigger>
        </TabsList>

        <TabsContent value="brand">
          <Input name="brand_name" required />
          {state.errors?.brand_name && <p className="text-red-500">{state.errors.brand_name}</p>}

          <Textarea name="story" />
          <Input name="tone" />
          <Input name="language" />
          <Textarea name="guidelines" />
        </TabsContent>

        <TabsContent value="prompts">
          <Textarea name="system_prompt" placeholder="Leave blank to use app defaults" />
          <Textarea name="task1_prompt" placeholder="Leave blank to use app defaults" />
          <Textarea name="task2_prompt" placeholder="Leave blank to use app defaults" />
        </TabsContent>
      </Tabs>

      <button type="submit" disabled={pending}>
        {pending ? 'Saving...' : 'Save Client'}
      </button>
    </form>
  )
}

// frontend/src/actions/clients.ts
'use server'
import { z } from 'zod'

const schema = z.object({
  brand_name: z.string().min(1, "Brand name is required"),
  story: z.string().optional(),
  tone: z.string().optional(),
  language: z.string().optional(),
  guidelines: z.string().optional(),
  system_prompt: z.string().optional(),
  task1_prompt: z.string().optional(),
  task2_prompt: z.string().optional(),
})

export async function createClient(prevState: any, formData: FormData) {
  const validatedFields = schema.safeParse(Object.fromEntries(formData))

  if (!validatedFields.success) {
    return { errors: validatedFields.error.flatten().fieldErrors }
  }

  // Call backend API with getAccessToken()
  // ...
}
```

### Pattern 4: Optimistic Client List Updates
**What:** Use `useOptimistic` to instantly show create/delete results
**When to use:** Client list page, client selector dropdown
**Example:**
```typescript
// Source: https://react.dev/reference/react/useOptimistic
// frontend/src/app/(dashboard)/clients/page.tsx
'use client'
import { useOptimistic } from 'react'
import { deleteClient } from '@/actions/clients'

export default function ClientsPage({ initialClients }: { initialClients: Client[] }) {
  const [optimisticClients, removeOptimisticClient] = useOptimistic(
    initialClients,
    (state, clientIdToRemove: string) => state.filter(c => c.id !== clientIdToRemove)
  )

  async function handleDelete(clientId: string) {
    removeOptimisticClient(clientId)  // Instant UI update
    await deleteClient(clientId)      // Actual deletion
  }

  return (
    <ul>
      {optimisticClients.map(client => (
        <li key={client.id}>
          {client.brand_name}
          <button onClick={() => handleDelete(client.id)}>Delete</button>
        </li>
      ))}
    </ul>
  )
}
```

### Pattern 5: Selected Client Persistence
**What:** Context provider with localStorage sync for selected client
**When to use:** App-wide selected client state
**Example:**
```typescript
// Source: https://github.com/osehmathias/next-js-context
// frontend/src/lib/client-context.tsx
'use client'
import { createContext, useContext, useEffect, useState } from 'react'

const ClientContext = createContext<{
  selectedClientId: string | null
  setSelectedClientId: (id: string | null) => void
}>({ selectedClientId: null, setSelectedClientId: () => {} })

export function ClientProvider({ children }: { children: React.ReactNode }) {
  const [selectedClientId, setSelectedClientId] = useState<string | null>(null)

  // Load from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem('selectedClientId')
    if (stored) setSelectedClientId(stored)
  }, [])

  // Sync to localStorage on change
  useEffect(() => {
    if (selectedClientId) {
      localStorage.setItem('selectedClientId', selectedClientId)
    } else {
      localStorage.removeItem('selectedClientId')
    }
  }, [selectedClientId])

  return (
    <ClientContext.Provider value={{ selectedClientId, setSelectedClientId }}>
      {children}
    </ClientContext.Provider>
  )
}

export const useSelectedClient = () => useContext(ClientContext)
```

### Anti-Patterns to Avoid
- **Lazy loading relationships in async SQLAlchemy:** Always use `selectinload()` or `joinedload()`, never rely on lazy loading (causes MissingGreenlet errors)
- **CASCADE delete without ON DELETE CASCADE:** Set foreign key with `ondelete="CASCADE"` to automatically clean up clients when user is deleted
- **Storing selected client server-side:** Use localStorage for non-sensitive client selection state; server-side storage adds unnecessary complexity
- **Regular Dialog for delete operations:** Use AlertDialog to force explicit confirmation for destructive actions
- **Sharing AsyncSession across requests:** Each request needs its own session instance; never reuse sessions

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Form validation | Custom regex patterns | Zod schemas with `.safeParse()` | Type safety, comprehensive error messages, composable schemas |
| Accessible dropdowns | Custom div + state | shadcn/ui Select (Radix UI) | ARIA attributes, keyboard navigation, screen reader support built-in |
| Optimistic updates | Manual state + rollback logic | React `useOptimistic` hook | Automatic rollback when server responds, less boilerplate |
| Permission checks | Inline if statements in routes | FastAPI Depends with reusable guards | DRY principle, testable, composable, automatic 403 responses |
| Confirmation dialogs | Custom modal + state | shadcn/ui AlertDialog | Accessible, focus trap management, keyboard handling, mobile-optimized |
| Character counters | Manual length calculation | Built-in maxLength + display logic | Browser validation, accessibility, standard UX pattern |

**Key insight:** Form handling, accessibility, and state management have mature patterns in 2026. Don't rebuild what shadcn/ui, Zod, and React hooks already provide.

## Common Pitfalls

### Pitfall 1: Async Lazy Loading MissingGreenlet Error
**What goes wrong:** Accessing relationships like `client.user.email` in async routes raises `MissingGreenlet: greenlet_spawn has not been called` error
**Why it happens:** SQLAlchemy can't perform implicit I/O in async contexts; lazy loading requires synchronous database access
**How to avoid:**
- Set `lazy="raise"` on relationship definitions to fail fast during development
- Always use `.options(selectinload(Model.relationship))` in queries
- Set `expire_on_commit=False` on AsyncSession to prevent attribute expiration
**Warning signs:** Stack traces mentioning greenlets, errors when accessing related objects after query

### Pitfall 2: Form Validation Without Exclude Unset
**What goes wrong:** PATCH/update endpoints overwrite fields with None/empty when user only wants to update one field
**Why it happens:** FormData contains all form fields, including unchanged ones; sending all fields replaces existing values
**How to avoid:** Use `model.model_dump(exclude_unset=True)` to only send fields user actually modified
**Warning signs:** Optional fields getting cleared unexpectedly, users complaining about lost data after edits

### Pitfall 3: localStorage Access During SSR
**What goes wrong:** Server-side rendering crashes with "localStorage is not defined" error
**Why it happens:** localStorage only exists in browser, not in Node.js during SSR
**How to avoid:**
- Only access localStorage in `useEffect` hooks (client-side only)
- Check `typeof window !== 'undefined'` before accessing window APIs
- Use Client Components (`'use client'`) for components that need localStorage
**Warning signs:** Build-time or initial load errors mentioning window/localStorage

### Pitfall 4: Sharing AsyncSession Across Concurrent Tasks
**What goes wrong:** Database state corruption, race conditions, wrong data returned
**Why it happens:** AsyncSession is not thread-safe; concurrent access causes internal state conflicts
**How to avoid:** Always use dependency injection pattern with `get_db()` yielding new session per request
**Warning signs:** Intermittent data inconsistencies, "object is already attached to session" errors

### Pitfall 5: Foreign Keys Without ON DELETE CASCADE
**What goes wrong:** Orphaned client records when user is deleted, or foreign key constraint violations preventing user deletion
**Why it happens:** PostgreSQL enforces referential integrity; without CASCADE, it protects against orphans by blocking deletes
**How to avoid:** Define foreign key with `ondelete="CASCADE"` in SQLAlchemy: `ForeignKey("users.id", ondelete="CASCADE")`
**Warning signs:** Cannot delete user errors, orphaned records in database, referential integrity violations

### Pitfall 6: Toast Notifications Before Redirect
**What goes wrong:** Toast message never shows because redirect happens before React can render it
**Why it happens:** Race condition between redirect execution and component lifecycle
**How to avoid:**
- Use cookie-based messaging: set cookie before redirect, read and display in destination page
- Or use `useActionState` to show message before programmatic navigation
- Return message in Server Action response instead of redirecting immediately
**Warning signs:** Success messages that never appear, users confused about whether action succeeded

### Pitfall 7: useOptimistic State Not Reverting
**What goes wrong:** Optimistic update stays even after server action completes, showing stale data
**Why it happens:** Parent component doesn't re-render with fresh server data after action completes
**How to avoid:**
- Call `router.refresh()` or revalidate path in Server Action
- Ensure parent passes updated data as new prop to trigger useOptimistic reset
- Use `useTransition` wrapper around Server Action call
**Warning signs:** UI shows "deleted" items that still exist, duplicate items after creation

## Code Examples

Verified patterns from official sources:

### CRUD Endpoint with Permission Check
```python
# Source: https://fastapi.tiangolo.com/tutorial/sql-databases/
# backend/app/routers/clients.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID

from app.database import get_db
from app.models.client import Client
from app.models.user import User
from app.dependencies.auth import get_current_user, require_admin
from app.schemas.client import ClientCreate, ClientUpdate, ClientPublic

router = APIRouter(prefix="/clients", tags=["clients"])

@router.get("/", response_model=list[ClientPublic])
async def list_clients(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all clients for current user."""
    result = await db.execute(
        select(Client)
        .where(Client.user_id == current_user.id)
        .options(selectinload(Client.user))
        .order_by(Client.brand_name)
    )
    return result.scalars().all()

@router.post("/", response_model=ClientPublic, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new client profile."""
    db_client = Client(**client_data.model_dump(), user_id=current_user.id)
    db.add(db_client)
    await db.commit()
    await db.refresh(db_client)
    return db_client

@router.patch("/{client_id}", response_model=ClientPublic)
async def update_client(
    client_id: UUID,
    client_data: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update client profile. Users can only update their own clients."""
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.user_id == current_user.id  # Security: users can only edit their own clients
        )
    )
    db_client = result.scalar_one_or_none()

    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Only update fields that were provided
    update_data = client_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_client, field, value)

    await db.commit()
    await db.refresh(db_client)
    return db_client

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)  # Admin only
):
    """Delete client profile. Admin only."""
    result = await db.execute(select(Client).where(Client.id == client_id))
    db_client = result.scalar_one_or_none()

    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")

    await db.delete(db_client)
    await db.commit()
```

### Client Selector Component with Badge
```typescript
// Source: https://ui.shadcn.com/docs/components/select
// frontend/src/components/client-selector.tsx
'use client'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { useSelectedClient } from '@/lib/client-context'

type Client = {
  id: string
  brand_name: string
  has_custom_prompts: boolean  // Backend should compute this
}

export function ClientSelector({ clients }: { clients: Client[] }) {
  const { selectedClientId, setSelectedClientId } = useSelectedClient()

  return (
    <Select value={selectedClientId || undefined} onValueChange={setSelectedClientId}>
      <SelectTrigger className="w-[200px]">
        <SelectValue placeholder="Select client" />
      </SelectTrigger>
      <SelectContent>
        {clients.map((client) => (
          <SelectItem key={client.id} value={client.id}>
            <div className="flex items-center gap-2">
              <span>{client.brand_name}</span>
              {client.has_custom_prompts && (
                <Badge variant="secondary" className="text-xs">Custom</Badge>
              )}
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
```

### Delete Confirmation with AlertDialog
```typescript
// Source: https://ui.shadcn.com/docs/components/alert-dialog
// frontend/src/components/delete-client-dialog.tsx
'use client'
import { useState } from 'react'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { deleteClient } from '@/actions/clients'

export function DeleteClientDialog({ clientId, clientName }: { clientId: string, clientName: string }) {
  const [open, setOpen] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  async function handleDelete() {
    setIsDeleting(true)
    try {
      await deleteClient(clientId)
      setOpen(false)
      // Parent component should handle optimistic update
    } catch (error) {
      console.error('Delete failed:', error)
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      <AlertDialogTrigger asChild>
        <Button variant="destructive" size="sm">Delete</Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
          <AlertDialogDescription>
            This will permanently delete the client profile for "{clientName}".
            This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
          <AlertDialogAction onClick={handleDelete} disabled={isDeleting}>
            {isDeleting ? 'Deleting...' : 'Delete Client'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| useFormState | useActionState | React 19 (2024) | Renamed hook, same functionality, better naming |
| SQLAlchemy sync | SQLAlchemy 2.0 async | 2023 | Must use eager loading, no implicit lazy loading |
| Manual optimistic updates | useOptimistic hook | React 19 (2024) | Automatic rollback, less boilerplate |
| Class-based dependencies | Function-based with Annotated | FastAPI 0.95+ (2023) | Cleaner syntax, better type hints |
| localStorage without SSR check | useEffect + window check | Next.js 13+ App Router | Prevents SSR hydration errors |

**Deprecated/outdated:**
- **useFormState**: Renamed to `useActionState` in React 19
- **SQLAlchemy expire_on_commit=True (default)**: With async, set to `False` to avoid lazy loading issues
- **lazy="select" (default)**: Use `lazy="raise"` or `lazy="selectin"` in async contexts
- **Dialog for destructive actions**: Use AlertDialog for proper UX and accessibility

## Open Questions

Things that couldn't be fully resolved:

1. **Default prompt storage location**
   - What we know: User decided on dedicated "Prompt Settings" page separate from main settings
   - What's unclear: Should prompts be in `app_settings` table (singleton) or new `prompt_settings` table?
   - Recommendation: Use existing `app_settings` table with new columns (system_prompt, task1_prompt, task2_prompt); simpler than new table

2. **Badge indicator implementation detail**
   - What we know: Show badge on clients with custom prompts
   - What's unclear: Should backend compute `has_custom_prompts` boolean or should frontend check if any prompt field is non-null?
   - Recommendation: Backend computes it; avoids sending large prompt text when just listing clients

3. **Client list sorting**
   - What we know: Context doc says "Claude's discretion"
   - What's unclear: Alphabetical by brand name, or most recently used?
   - Recommendation: Alphabetical (simpler), or add `last_used_at` timestamp if usage tracking is valuable

## Sources

### Primary (HIGH confidence)
- [FastAPI Tutorial: SQL Databases](https://fastapi.tiangolo.com/tutorial/sql-databases/) - CRUD patterns, dependency injection
- [SQLAlchemy 2.0 Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) - Async relationship loading, pitfalls
- [Next.js Forms Guide](https://nextjs.org/docs/app/guides/forms) - Server Actions, validation, error handling
- [React useOptimistic Reference](https://react.dev/reference/react/useOptimistic) - Optimistic UI updates
- [shadcn/ui Select Component](https://ui.shadcn.com/docs/components/select) - Dropdown implementation
- [shadcn/ui AlertDialog Component](https://ui.shadcn.com/docs/components/alert-dialog) - Delete confirmation
- [shadcn/ui Badge Component](https://ui.shadcn.com/docs/components/badge) - Status indicators

### Secondary (MEDIUM confidence)
- [Handling Forms in Next.js with Server Actions and Zod](https://medium.com/@sorayacantos/handling-forms-in-next-js-with-next-form-server-actions-useactionstate-and-zod-validation-15f9932b0a9e) - Form validation patterns
- [Postgres Foreign Keys Guide](https://medium.com/the-table-sql-and-devtalk/a-practical-guide-to-postgres-foreign-keys-59e663b10045) - ON DELETE CASCADE best practices
- [FastAPI Dependency Injection 2026 Playbook](https://thelinuxcode.com/dependency-injection-in-fastapi-2026-playbook-for-modular-testable-apis/) - Permission checks with Depends
- [Optimizing Next.js Lists with useOptimistic](https://kitemetric.com/blogs/optimizing-next-js-lists-with-the-useoptimistic-hook) - List management patterns
- [Next.js Context with localStorage](https://github.com/osehmathias/next-js-context) - State persistence pattern
- [React Server Actions with Toast Feedback](https://www.robinwieruch.de/react-server-actions-toast/) - Error handling patterns

### Tertiary (LOW confidence)
- [shadcn/ui Select Best Practices](https://shadcnstudio.com/docs/components/select) - Third-party documentation site, defer to official docs
- [Textarea MaxLength UX Guidelines](https://www.breck-mckye.com/blog/2012/05/character-count-design-some-guidelines/) - Older article (2012), principles still valid

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries are established, officially documented, in active use
- Architecture: HIGH - Patterns verified from official FastAPI, SQLAlchemy, Next.js, React documentation
- Pitfalls: HIGH - Multiple sources confirm async lazy loading issues, localStorage SSR issues, form handling gotchas

**Research date:** 2026-01-22
**Valid until:** 2026-02-22 (30 days - stack is stable, patterns are established)
