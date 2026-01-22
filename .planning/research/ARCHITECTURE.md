# Architecture Research

**Domain:** AI-Powered SaaS Product Content Generator
**Researched:** 2026-01-22
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER (Next.js 14+)                       │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Pages/     │  │  Server      │  │   Client     │              │
│  │   Layouts    │  │  Components  │  │  Components  │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                       │
│         └─────────────────┴─────────────────┘                       │
│                           │                                         │
│  ┌────────────────────────┴────────────────────────┐               │
│  │         State Management Layer                   │               │
│  │  ┌──────────────┐    ┌────────────────────┐    │               │
│  │  │   Zustand    │    │  TanStack Query    │    │               │
│  │  │ (UI State)   │    │ (Server State)     │    │               │
│  │  └──────────────┘    └────────────────────┘    │               │
│  └─────────────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    HTTP/REST + WebSocket
                              │
┌─────────────────────────────────────────────────────────────────────┐
│                    API LAYER (FastAPI)                               │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │    Route     │  │  Background  │  │   WebSocket  │              │
│  │   Handlers   │  │   Workers    │  │   Handlers   │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                       │
│  ┌──────┴─────────────────┴─────────────────┴────────┐             │
│  │         Service Layer (Business Logic)             │             │
│  │  ┌──────────┐  ┌──────────┐  ┌─────────────────┐ │             │
│  │  │  Client  │  │  Excel   │  │  AI Generation  │ │             │
│  │  │ Service  │  │ Service  │  │    Service      │ │             │
│  │  └──────────┘  └──────────┘  └─────────────────┘ │             │
│  └────────────────────────────────────────────────────┘             │
│         │                 │                 │                       │
│  ┌──────┴─────────────────┴─────────────────┴────────┐             │
│  │         Repository Layer (Data Access)             │             │
│  └────────────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    SQLAlchemy Async ORM
                              │
┌─────────────────────────────────────────────────────────────────────┐
│                    DATA LAYER (PostgreSQL)                           │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │    users     │  │   clients    │  │  generations │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   products   │  │  job_queue   │  │ review_logs  │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    External APIs
                              │
┌─────────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                                 │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   OpenAI     │  │    Redis     │  │  S3/Storage  │              │
│  │   API        │  │  (Optional)  │  │  (Optional)  │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Next.js Frontend** | UI rendering, user interactions, client state | App Router, Server Components, Server Actions for mutations |
| **Server Components** | Initial data fetching, SEO, zero JS hydration | Next.js RSC with data fetching |
| **Client Components** | Interactive UI, forms, real-time updates | React with Zustand for UI state |
| **TanStack Query** | Server state caching, background refetching | Query/mutation hooks for API calls |
| **FastAPI Backend** | Business logic, data validation, orchestration | Async route handlers with Pydantic models |
| **Service Layer** | Domain logic, AI orchestration, Excel processing | Python classes with dependency injection |
| **Background Workers** | Long-running AI generation, async processing | FastAPI BackgroundTasks or ARQ/Redis |
| **Repository Layer** | Database operations, query abstraction | SQLAlchemy async sessions with repositories |
| **PostgreSQL** | Persistent data storage, relational queries | Multi-tenant schema with Row-Level Security |
| **WebSocket** | Real-time progress updates during generation | FastAPI WebSocket endpoints |

## Recommended Project Structure

### Frontend (Next.js)

```
frontend/
├── app/                        # Next.js App Router
│   ├── (auth)/                 # Auth route group
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/            # Authenticated routes
│   │   ├── layout.tsx          # Dashboard layout with nav
│   │   ├── clients/            # Client management
│   │   │   ├── page.tsx
│   │   │   ├── [id]/
│   │   │   │   └── page.tsx
│   │   │   └── new/
│   │   │       └── page.tsx
│   │   ├── generate/           # Content generation workflow
│   │   │   └── page.tsx
│   │   ├── review/             # Review interface
│   │   │   └── [batchId]/
│   │   │       └── page.tsx
│   │   └── settings/
│   │       └── page.tsx
│   ├── api/                    # API route handlers (minimal - mostly proxy)
│   │   └── auth/
│   │       └── [...nextauth]/
│   ├── layout.tsx              # Root layout
│   └── page.tsx                # Landing/home
├── components/
│   ├── ui/                     # Shadcn/UI components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   └── ...
│   ├── features/               # Feature-specific components
│   │   ├── client-form/
│   │   ├── excel-upload/
│   │   ├── product-review/
│   │   └── generation-progress/
│   └── shared/                 # Shared components
│       ├── header.tsx
│       └── sidebar.tsx
├── lib/
│   ├── api-client.ts           # FastAPI client (fetch wrapper)
│   ├── auth.ts                 # Auth configuration
│   ├── utils.ts                # Utilities
│   └── hooks/                  # Custom React hooks
│       ├── use-clients.ts
│       ├── use-generation.ts
│       └── use-websocket.ts
├── store/
│   ├── ui-store.ts             # Zustand UI state
│   └── auth-store.ts           # Auth state
├── types/
│   └── api.ts                  # TypeScript types for API
└── styles/
    └── globals.css             # Global styles (Tailwind)
```

### Backend (FastAPI)

```
backend/
├── app/
│   ├── main.py                 # FastAPI app initialization
│   ├── config.py               # Configuration (env vars)
│   ├── database.py             # Database connection, session management
│   ├── dependencies.py         # Dependency injection helpers
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/                 # API version 1
│   │       ├── __init__.py
│   │       ├── routes/
│   │       │   ├── auth.py     # Authentication endpoints
│   │       │   ├── clients.py  # Client CRUD
│   │       │   ├── excel.py    # Upload, process, download
│   │       │   ├── generation.py # Generation orchestration
│   │       │   ├── review.py   # Review endpoints
│   │       │   └── websocket.py # WebSocket for real-time updates
│   │       └── schemas/
│   │           ├── client.py   # Pydantic models for clients
│   │           ├── product.py
│   │           ├── generation.py
│   │           └── user.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── client_service.py   # Client business logic
│   │   ├── excel_service.py    # Excel processing (openpyxl)
│   │   ├── ai_service.py       # LangChain + OpenAI orchestration
│   │   ├── generation_service.py # Generation workflow
│   │   └── review_service.py   # Review logic
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── client.py
│   │   ├── product.py
│   │   ├── generation.py
│   │   └── review.py
│   ├── repositories/           # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py             # Generic repository
│   │   ├── client_repository.py
│   │   ├── product_repository.py
│   │   └── generation_repository.py
│   ├── tasks/                  # Background tasks
│   │   ├── __init__.py
│   │   └── generation_tasks.py # Async generation jobs
│   └── utils/
│       ├── __init__.py
│       ├── auth.py             # JWT, password hashing
│       ├── langchain_helpers.py # LangChain utilities
│       └── validators.py       # Custom validators
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
├── tests/
│   ├── conftest.py
│   ├── test_clients.py
│   ├── test_generation.py
│   └── test_excel.py
└── requirements.txt
```

### Structure Rationale

**Frontend:**
- **App Router organization**: Route groups `(auth)` and `(dashboard)` enable different layouts without URL pollution
- **Feature-based components**: Components grouped by feature domain for better maintainability
- **API client abstraction**: Centralized FastAPI communication with type safety
- **Zustand for UI state**: Lightweight, minimal boilerplate vs Redux for simple UI state (modals, sidebar, etc.)
- **TanStack Query for server state**: Handles caching, background refetching, loading states automatically

**Backend:**
- **Layered architecture**: Clear separation of routes → services → repositories → models
- **Repository pattern**: Abstracts database operations, easier to test and swap implementations
- **Service layer**: Business logic isolated from HTTP concerns, reusable across endpoints
- **Pydantic schemas**: Request/response validation separate from ORM models
- **Async throughout**: FastAPI async handlers + SQLAlchemy async sessions for non-blocking I/O

## Architectural Patterns

### Pattern 1: Server Actions for Mutations, API Routes for Complex Operations

**What:** Use Next.js Server Actions for simple mutations (create client, update settings), but call FastAPI directly for complex workflows (generation, Excel processing).

**When to use:**
- Server Actions: Form submissions, CRUD operations, simple data updates
- API Routes: File uploads, streaming responses, WebSocket proxy
- Direct FastAPI calls: Complex AI workflows, batch operations

**Trade-offs:**
- PRO: Server Actions reduce boilerplate, automatic form handling, built-in revalidation
- PRO: FastAPI handles heavy lifting, keeps Next.js lightweight
- CON: Two places to manage API logic (Server Actions + FastAPI client)

**Example:**
```typescript
// Server Action for simple mutation
'use server'
export async function createClient(formData: FormData) {
  const data = {
    name: formData.get('name'),
    prompt: formData.get('prompt')
  }
  const response = await fetch(`${process.env.API_URL}/clients`, {
    method: 'POST',
    body: JSON.stringify(data)
  })
  revalidatePath('/clients')
  return response.json()
}

// Direct FastAPI call for complex operation
export async function generateContent(batchId: string) {
  const ws = new WebSocket(`${process.env.WS_URL}/generation/${batchId}`)
  // Handle streaming progress updates
}
```

### Pattern 2: Shared Schema Multi-Tenancy with Row-Level Security

**What:** Single PostgreSQL database with `tenant_id` (agency) and `user_id` columns on all tenant-scoped tables, enforced via Row-Level Security policies.

**When to use:** For SaaS with team-based access (5-20 users per agency, multiple clients per agency)

**Trade-offs:**
- PRO: Simple to manage, easy backups, cost-effective for < 1000 tenants
- PRO: PostgreSQL RLS automatically enforces isolation
- CON: Harder to scale to millions of tenants (but not needed here)
- CON: Requires careful query design to avoid N+1 problems

**Example:**
```sql
-- clients table with tenant isolation
CREATE TABLE clients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  created_by_user_id UUID NOT NULL REFERENCES users(id),
  name VARCHAR(255) NOT NULL,
  brand_prompt TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Row-Level Security policy
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_policy ON clients
  USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

### Pattern 3: Background Job Queue with Progress Tracking

**What:** For long-running AI generation, use FastAPI BackgroundTasks for simple jobs or ARQ+Redis for production-scale queuing, with WebSocket for real-time progress updates.

**When to use:**
- BackgroundTasks: MVP, low volume (< 100 jobs/hour), simple workflows
- ARQ+Redis: Production, high volume, job persistence, retries, distributed workers

**Trade-offs:**
- BackgroundTasks PRO: Zero additional infrastructure, simple
- BackgroundTasks CON: No persistence (server restart = lost jobs), no retries, single-worker
- ARQ PRO: Async-native, fast, persistent, retry logic, scalable
- ARQ CON: Requires Redis, more complexity

**Example:**
```python
# Simple approach - BackgroundTasks
from fastapi import BackgroundTasks

async def generate_content_task(batch_id: str, websocket: WebSocket):
    products = await get_products(batch_id)
    for i, product in enumerate(products):
        result = await ai_service.generate(product)
        await websocket.send_json({
            "progress": (i + 1) / len(products),
            "product_id": product.id
        })

@app.post("/generation/{batch_id}/start")
async def start_generation(
    batch_id: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(generate_content_task, batch_id)
    return {"status": "started"}

# Production approach - ARQ
from arq import create_pool
from arq.connections import RedisSettings

async def generate_batch(ctx, batch_id: str):
    """ARQ worker function"""
    products = await get_products(batch_id)
    for product in products:
        result = await ai_service.generate(product)
        await ctx['redis'].publish(
            f'progress:{batch_id}',
            json.dumps({"product_id": product.id})
        )

# Queue job
redis = await create_pool(RedisSettings())
await redis.enqueue_job('generate_batch', batch_id)
```

### Pattern 4: Streaming Excel Processing with Memory Optimization

**What:** Use openpyxl in read-only mode for uploads, process in chunks, stream directly to BytesIO for downloads without loading full file into memory.

**When to use:** Processing Excel files > 10MB or > 500 rows

**Trade-offs:**
- PRO: Minimal memory footprint (constant ~50MB regardless of file size)
- PRO: Faster processing, handles files up to 10K rows easily
- CON: Read-only mode means can't edit in-place (need to create new workbook)

**Example:**
```python
from openpyxl import load_workbook, Workbook
from io import BytesIO

async def process_excel_upload(file: UploadFile) -> List[Product]:
    """Stream read Excel without loading full file"""
    wb = load_workbook(file.file, read_only=True, data_only=True)
    ws = wb.active

    products = []
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if row_idx % 100 == 0:  # Process in chunks
            await asyncio.sleep(0)  # Yield to event loop

        products.append(Product(
            name=row[0],
            description=row[1],
            # ... map columns
        ))

    wb.close()
    return products

async def create_excel_download(products: List[Product]) -> BytesIO:
    """Stream write Excel output"""
    wb = Workbook(write_only=True)
    ws = wb.create_sheet()

    # Write header
    ws.append(['Product Name', 'Description', ...])

    # Write data in chunks
    for product in products:
        ws.append([product.name, product.description, ...])

    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output
```

### Pattern 5: Optimistic Mutations with TanStack Query

**What:** Update UI immediately (optimistic update) while mutation is in flight, rollback on error.

**When to use:** Review approval/rejection, client updates - actions where user expects immediate feedback

**Trade-offs:**
- PRO: Feels instant, better UX
- PRO: Works offline (UI updates even if network slow)
- CON: Must handle rollback on error
- CON: Requires careful cache invalidation strategy

**Example:**
```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query'

export function useApproveProduct() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (productId: string) => {
      return await api.post(`/products/${productId}/approve`)
    },
    onMutate: async (productId) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['products'] })

      // Snapshot previous value
      const previous = queryClient.getQueryData(['products'])

      // Optimistically update
      queryClient.setQueryData(['products'], (old: Product[]) =>
        old.map(p => p.id === productId
          ? { ...p, status: 'approved' }
          : p
        )
      )

      return { previous }
    },
    onError: (err, productId, context) => {
      // Rollback on error
      queryClient.setQueryData(['products'], context.previous)
    },
    onSettled: () => {
      // Refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: ['products'] })
    }
  })
}
```

### Pattern 6: Dynamic Prompt Building with Field Availability

**What:** Build AI prompts dynamically based on which product fields are actually present, warn users during review if key fields were missing.

**When to use:** When input data quality varies (Faire exports may have inconsistent fields)

**Trade-offs:**
- PRO: Graceful degradation, generates best content possible with available data
- PRO: Transparent to user what was used
- CON: More complex prompt logic
- CON: Results vary by input quality

**Example:**
```python
from typing import Optional, List
from pydantic import BaseModel

class Product(BaseModel):
    name: str
    type: Optional[str] = None
    description: Optional[str] = None
    images: Optional[List[str]] = None
    country: Optional[str] = None
    customization: Optional[str] = None
    sku: Optional[str] = None

    @property
    def available_fields(self) -> List[str]:
        """Track which fields have data"""
        return [
            field for field, value in self.dict().items()
            if value is not None and value != []
        ]

def build_prompt(product: Product, client: Client) -> str:
    """Dynamic prompt based on available data"""
    base = f"Generate a product title for: {product.name}\n\n"

    context = []
    if product.type:
        context.append(f"Product type: {product.type}")
    if product.description:
        context.append(f"Original description: {product.description}")
    if product.country:
        context.append(f"Made in: {product.country}")
    if product.customization:
        context.append(f"Customization: {product.customization}")

    if context:
        base += "Context:\n" + "\n".join(context) + "\n\n"

    base += f"Brand guidelines: {client.brand_prompt}\n"
    base += "Requirements: 30-60 characters"

    return base

# Store which fields were used for transparency
generation_record = Generation(
    product_id=product.id,
    fields_used=product.available_fields,
    prompt=build_prompt(product, client)
)
```

## Data Flow

### Upload → Generation → Review → Download Flow

```
[User uploads Excel]
        ↓
[Next.js] → POST /api/excel/upload
        ↓
[FastAPI] → ExcelService.parse_file()
        ↓ (stream read with openpyxl)
[PostgreSQL] ← Save products with batch_id
        ↓
[User selects fields & client]
        ↓
[Next.js] → POST /api/generation/start
        ↓
[FastAPI] → BackgroundTask or ARQ job
        ↓
[WebSocket] ← Real-time progress updates
        ↓
[For each product]
    ↓
    [AIService.generate()]
        ↓
        [Build dynamic prompt]
        ↓
        [LangChain → OpenAI API]
        ↓
        [Validate length, retry if needed]
        ↓
        [Save generation result]
        ↓
        [Send progress via WebSocket]
        ↓
[Next.js] → Listen on WebSocket, update UI
        ↓
[All products complete]
        ↓
[User reviews products]
        ↓
[Next.js] → PATCH /api/products/{id}/approve
        ↓ (optimistic update)
[FastAPI] → Update product status
        ↓
[PostgreSQL] ← Save approval
        ↓
[User downloads results]
        ↓
[Next.js] → GET /api/excel/download/{batch_id}
        ↓
[FastAPI] → ExcelService.create_output()
        ↓ (stream write with openpyxl)
[Return Excel file with only approved products]
```

### Authentication Flow

```
[User logs in]
    ↓
[Next.js] → POST /api/auth/login (Server Action or API route)
    ↓
[FastAPI] → Validate credentials
    ↓
[PostgreSQL] → Query user, verify password hash
    ↓
[FastAPI] ← Generate JWT token with tenant_id, user_id
    ↓
[Next.js] ← Store token (httpOnly cookie)
    ↓
[Subsequent requests include JWT]
    ↓
[FastAPI middleware] → Verify JWT, extract tenant_id
    ↓
[PostgreSQL RLS] → Set session variable: app.current_tenant_id
    ↓
[All queries automatically filtered by tenant_id]
```

### Real-Time Progress Updates (WebSocket)

```
[Client connects WebSocket]
    ↓
    ws://api/generation/{batch_id}/progress
    ↓
[FastAPI WebSocketEndpoint]
    ↓
    Authenticate connection (JWT in query param)
    ↓
    Subscribe to Redis pub/sub channel: `progress:{batch_id}`
    ↓
[Background Worker generates content]
    ↓
    For each product:
        ↓
        Generate content
        ↓
        Publish to Redis: `progress:{batch_id}`
        ↓
[FastAPI WebSocket] ← Receive from Redis
    ↓
    ws.send_json({
        "type": "progress",
        "product_id": "...",
        "current": 45,
        "total": 100,
        "status": "completed"
    })
    ↓
[Next.js Client] ← Update progress bar in real-time
```

## State Management Strategy

### Client-Side State Architecture

```
┌─────────────────────────────────────────────────────┐
│              CLIENT STATE LAYERS                     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │   URL State (Next.js router)               │    │
│  │   - Current page                           │    │
│  │   - Query params (filters, sorting)        │    │
│  │   - Batch ID, product ID in review         │    │
│  └────────────────────────────────────────────┘    │
│                       ↕                             │
│  ┌────────────────────────────────────────────┐    │
│  │   Server State (TanStack Query)            │    │
│  │   - Clients list (cached)                  │    │
│  │   - Products in batch (cached)             │    │
│  │   - Generation status (refetch on focus)   │    │
│  │   - User profile (rarely changes)          │    │
│  └────────────────────────────────────────────┘    │
│                       ↕                             │
│  ┌────────────────────────────────────────────┐    │
│  │   UI State (Zustand)                       │    │
│  │   - Sidebar open/closed                    │    │
│  │   - Modals (create client, confirm)        │    │
│  │   - Selected fields for generation         │    │
│  │   - Review keyboard shortcuts enabled      │    │
│  └────────────────────────────────────────────┘    │
│                       ↕                             │
│  ┌────────────────────────────────────────────┐    │
│  │   Form State (React Hook Form)            │    │
│  │   - Client creation form                   │    │
│  │   - Excel upload form                      │    │
│  │   - Settings form                          │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**State Management Rules:**
1. **URL State**: Source of truth for navigation, filters, current item
2. **Server State (TanStack Query)**: Any data from API, automatic caching and revalidation
3. **UI State (Zustand)**: Ephemeral UI state not derived from server (modals, sidebar)
4. **Form State**: Uncontrolled with React Hook Form, validation with Zod

### Server-Side State Architecture

```
┌─────────────────────────────────────────────────────┐
│              SERVER STATE LAYERS                     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │   Session State (JWT)                      │    │
│  │   - user_id, tenant_id                     │    │
│  │   - roles/permissions                      │    │
│  │   - expires_at                             │    │
│  └────────────────────────────────────────────┘    │
│                       ↓                             │
│  ┌────────────────────────────────────────────┐    │
│  │   Request Context (Dependency Injection)   │    │
│  │   - Current user (from JWT)                │    │
│  │   - Database session (scoped to request)   │    │
│  │   - Tenant isolation (RLS context)         │    │
│  └────────────────────────────────────────────┘    │
│                       ↓                             │
│  ┌────────────────────────────────────────────┐    │
│  │   Application State (PostgreSQL)           │    │
│  │   - Persistent data (clients, products)    │    │
│  │   - Job queue status                       │    │
│  │   - Generation history                     │    │
│  └────────────────────────────────────────────┘    │
│                       ↓                             │
│  ┌────────────────────────────────────────────┐    │
│  │   Background Job State (Redis - optional)  │    │
│  │   - Job queue (ARQ)                        │    │
│  │   - Real-time progress pub/sub             │    │
│  │   - Rate limiting counters                 │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| **0-10 agencies (MVP)** | Monolith FastAPI on single Railway instance, PostgreSQL managed DB, Next.js on Vercel, BackgroundTasks for jobs. Cost: ~$20-50/mo |
| **10-50 agencies** | Add Redis + ARQ for job queue, horizontal scaling of FastAPI workers (2-3 instances), connection pooling (pgbouncer), CDN for static assets. Cost: ~$100-200/mo |
| **50-200 agencies** | Separate worker processes for AI generation, Celery or ARQ with dedicated workers, PostgreSQL read replicas for queries, API response caching (Redis), rate limiting per tenant. Cost: ~$300-500/mo |
| **200+ agencies** | Consider Citus for PostgreSQL sharding (shard on tenant_id), separate microservices for Excel processing and AI generation, dedicated queue infrastructure, horizontal autoscaling. Cost: $1000+/mo |

### Scaling Priorities

1. **First bottleneck (50-100 concurrent generations):** OpenAI API rate limits
   - **Solution:** Implement queue with concurrency control (max 5-10 concurrent AI requests), batch requests where possible using OpenAI Batch API (50% cost savings), cache prompt embeddings

2. **Second bottleneck (500+ products/day):** PostgreSQL write contention during generation
   - **Solution:** Batch inserts (save generation results in bulk), use UNLOGGED tables for temporary staging data, connection pooling with pgbouncer, async commit for non-critical writes

3. **Third bottleneck (1000+ concurrent users):** FastAPI single-worker limits
   - **Solution:** Horizontal scaling (2-5 Gunicorn workers), load balancer (Railway handles this), stateless design (no session state in memory), use Redis for shared session storage if needed

## Anti-Patterns

### Anti-Pattern 1: Loading Full Excel File into Memory

**What people do:** Read entire Excel with pandas `pd.read_excel()` or openpyxl without read-only mode, store all rows in memory before processing

**Why it's wrong:**
- Files > 10MB crash with OOM errors
- Slow processing (wait for full file load before starting)
- Can't handle files with 5K+ rows in production

**Do this instead:**
```python
# ❌ BAD - Loads entire file
df = pd.read_excel(file)
for row in df.iterrows():
    process(row)

# ✅ GOOD - Stream with openpyxl read-only mode
wb = load_workbook(file, read_only=True, data_only=True)
ws = wb.active
for row in ws.iter_rows(min_row=2, values_only=True):
    process(row)
wb.close()
```

### Anti-Pattern 2: Synchronous AI Calls in Request Handler

**What people do:** Call OpenAI API directly in route handler, wait for response, block request thread

**Why it's wrong:**
- Request timeout after 30-60s (typical proxy limits)
- Can't handle batch of 100+ products (would take 10+ minutes)
- Server can't handle concurrent requests (all workers blocked)
- No progress tracking, user has no feedback

**Do this instead:**
```python
# ❌ BAD - Blocks request
@app.post("/generate")
async def generate(batch_id: str):
    products = get_products(batch_id)
    for product in products:
        result = await openai_call(product)  # 2-5s each = minutes total
    return {"status": "done"}

# ✅ GOOD - Background job with progress
@app.post("/generate")
async def generate(batch_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(generate_batch, batch_id)
    return {"status": "started", "batch_id": batch_id}

# Client polls /generation/{batch_id}/status or uses WebSocket
```

### Anti-Pattern 3: Storing AI Responses Without Validation

**What people do:** Save LLM output directly to database without checking length, format, or content

**Why it's wrong:**
- LLM sometimes ignores length constraints (generates 150 char title when max is 60)
- May return error messages or refusals as content
- Downstream Excel export fails or corrupts
- User discovers issues during final review (too late)

**Do this instead:**
```python
# ❌ BAD - No validation
result = await llm.ainvoke(prompt)
await db.save_product(text=result.content)

# ✅ GOOD - Validate and retry
from pydantic import BaseModel, validator

class GeneratedContent(BaseModel):
    title: str
    description: str

    @validator('title')
    def validate_title_length(cls, v):
        if not (30 <= len(v) <= 60):
            raise ValueError(f"Title length {len(v)} not in range 30-60")
        return v

async def generate_with_retry(product, max_retries=3):
    for attempt in range(max_retries):
        result = await llm.ainvoke(prompt)
        try:
            validated = GeneratedContent(
                title=extract_title(result),
                description=extract_description(result)
            )
            return validated
        except ValueError as e:
            if attempt == max_retries - 1:
                raise
            # Retry with stricter prompt
            prompt = add_constraint(prompt, "MUST be 30-60 characters")
```

### Anti-Pattern 4: N+1 Queries from Client-Side Data Fetching

**What people do:** Fetch list of products, then fetch client details for each product individually from client

**Why it's wrong:**
- 100 products = 101 database queries (1 for list + 100 for clients)
- Slow page load (100+ round trips)
- Database connection exhaustion under load

**Do this instead:**
```python
# ❌ BAD - N+1 queries
@app.get("/products")
async def get_products():
    products = await db.query(Product).all()
    return products  # Frontend fetches client for each

# Frontend does N queries
for product in products:
    client = await fetch(`/clients/${product.client_id}`)

# ✅ GOOD - Eager loading with join
@app.get("/products")
async def get_products(db: AsyncSession):
    result = await db.execute(
        select(Product)
        .options(joinedload(Product.client))  # Eager load
        .where(Product.tenant_id == current_tenant_id)
    )
    products = result.scalars().all()
    return products  # Includes client data, single query
```

### Anti-Pattern 5: Storing OpenAI API Keys in Frontend

**What people do:** Pass API key to Next.js client to call OpenAI directly from browser

**Why it's wrong:**
- API key exposed in browser (view source, network tab)
- Anyone can steal key and rack up charges
- Can't enforce rate limits or audit usage
- Security nightmare

**Do this instead:**
```typescript
// ❌ BAD - API key in client
const openai = new OpenAI({
  apiKey: process.env.NEXT_PUBLIC_OPENAI_KEY  // NEVER do this
})

// ✅ GOOD - API calls proxied through backend
// Frontend
const result = await fetch('/api/generate', {
  method: 'POST',
  body: JSON.stringify({ product })
})

// Backend (FastAPI) - API key stays server-side
@app.post("/generate")
async def generate(product: Product):
    llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY)  # Server only
    return await llm.ainvoke(product)
```

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **OpenAI API** | LangChain abstraction, async client | Use `ChatOpenAI` with async, implement retry with exponential backoff, track token usage per request |
| **Vercel (Frontend)** | Git-based deployment | Auto-deploy on push to main, preview deployments for PRs, environment variables via dashboard |
| **Railway (Backend)** | Dockerfile or Nixpacks | Auto-deploy FastAPI, managed PostgreSQL add-on, environment variables, health check endpoint required |
| **PostgreSQL** | SQLAlchemy async ORM | Connection pooling (max 20 connections), use `asyncpg` driver, enable RLS for tenant isolation |
| **Redis (Optional)** | ARQ for jobs, pub/sub for WebSocket | Not required for MVP, add when scaling to 50+ agencies or need job persistence |
| **S3/Storage (Optional)** | Boto3 for uploaded files | Not required for MVP (store Excel temporarily), add for long-term file storage or large files |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **Next.js ↔ FastAPI** | REST API over HTTPS | JWT in Authorization header, CORS configured, API versioning (/api/v1) |
| **Next.js ↔ WebSocket** | WebSocket (ws://) | JWT in connection query param, heartbeat every 30s, auto-reconnect on disconnect |
| **FastAPI Routes ↔ Services** | Direct function calls (DI) | Services injected via Depends(), async functions, no HTTP |
| **Services ↔ Repositories** | Direct function calls | Repositories receive AsyncSession via DI, return domain models not ORM objects |
| **Repositories ↔ Database** | SQLAlchemy ORM | Async sessions, context managers for transaction scope, RLS enforced automatically |
| **FastAPI ↔ Background Jobs** | BackgroundTasks or ARQ | BackgroundTasks for MVP (in-process), ARQ via Redis for production (separate worker) |

## Deployment Architecture

### Development
```
┌──────────────────────────────────────────────┐
│  Developer Machine                           │
├──────────────────────────────────────────────┤
│  Next.js dev server (localhost:3000)         │
│      ↓                                       │
│  FastAPI dev server (localhost:8000)         │
│      ↓                                       │
│  PostgreSQL local (Docker or .app)           │
└──────────────────────────────────────────────┘
```

### Production (Recommended for MVP)
```
┌──────────────────────────────────────────────┐
│  Vercel                                      │
│  - Next.js SSR + static assets               │
│  - Edge functions (middleware)               │
│  - Auto-scaling                              │
└────────────┬─────────────────────────────────┘
             │ HTTPS
             ↓
┌──────────────────────────────────────────────┐
│  Railway                                     │
│  - FastAPI app (Gunicorn + Uvicorn)          │
│  - Background workers (same process for MVP) │
│  - WebSocket support                         │
└────────────┬─────────────────────────────────┘
             │ asyncpg
             ↓
┌──────────────────────────────────────────────┐
│  Railway Managed PostgreSQL                  │
│  - Auto backups                              │
│  - Connection pooling                        │
│  - Metrics                                   │
└──────────────────────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────┐
│  External: OpenAI API                        │
│  - Rate limited (tier-based)                 │
│  - Track usage via callbacks                 │
└──────────────────────────────────────────────┘
```

### Production (Scaled - 50+ agencies)
```
┌──────────────────────────────────────────────┐
│  Vercel (Frontend)                           │
└────────────┬─────────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────┐
│  Railway API Instances (2-3 replicas)        │
│  - Load balanced                             │
│  - Stateless (no session state)              │
└────────────┬─────────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────┐
│  Redis (Upstash or Railway)                  │
│  - ARQ job queue                             │
│  - WebSocket pub/sub                         │
│  - Rate limiting                             │
└──────────────────────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────┐
│  Railway Worker Instances (2-4 replicas)     │
│  - ARQ workers consume from Redis queue      │
│  - Independent scaling                       │
└────────────┬─────────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────┐
│  PostgreSQL (Crunchy Data or Railway)        │
│  - Read replicas for queries                 │
│  - Connection pooler (pgbouncer)             │
└──────────────────────────────────────────────┘
```

## Build Order Recommendations

Based on dependencies and risk, suggested implementation order:

### Phase 1: Foundation (Week 1-2)
**Why first:** Everything depends on auth and data persistence

1. FastAPI project setup + PostgreSQL + Alembic migrations
2. User model + authentication (JWT) + registration/login endpoints
3. Tenant model + Row-Level Security policies
4. Next.js project setup + API client + auth integration
5. Protected route layout + login/register pages

**Dependencies:** None
**Risk:** Low (standard patterns)
**Blocker for:** Everything else

### Phase 2: Client Management (Week 2-3)
**Why second:** Need client profiles before generation can work

1. Client model (tenant-scoped) + migrations
2. Client CRUD endpoints (FastAPI)
3. Client repository + service layer
4. Client management UI (Next.js)
5. Client form with prompt editor

**Dependencies:** Phase 1 (auth, tenant isolation)
**Risk:** Low (standard CRUD)
**Blocker for:** Generation (needs client prompts)

### Phase 3: Excel Processing (Week 3-4)
**Why third:** Core workflow starts here, but no AI yet (can test with mock data)

1. Excel upload endpoint (FastAPI) with streaming
2. Product model + migrations
3. Excel parsing service (openpyxl read-only)
4. Column detection and field mapping
5. Upload UI (Next.js) with field selection
6. Product table display

**Dependencies:** Phase 2 (client selection)
**Risk:** Medium (file processing edge cases)
**Blocker for:** Generation

### Phase 4: AI Generation (Week 4-6)
**Why fourth:** Core value, but depends on client profiles and products

1. AI service (LangChain + OpenAI integration)
2. Dynamic prompt building based on available fields
3. Generation endpoint with BackgroundTasks
4. Validation + retry logic
5. Generation status polling endpoint
6. Generation UI with progress bar

**Dependencies:** Phase 3 (products uploaded)
**Risk:** High (AI reliability, rate limits, cost)
**Blocker for:** Review

### Phase 5: Real-Time Progress (Week 5-6 - Parallel with Phase 4)
**Why fifth:** UX enhancement, not critical for MVP but important for production feel

1. WebSocket endpoint (FastAPI)
2. Progress pub/sub (in-memory for MVP, Redis for production)
3. WebSocket React hook
4. Real-time progress UI updates

**Dependencies:** Phase 4 (generation running)
**Risk:** Medium (WebSocket connection handling)
**Blocker for:** None (nice-to-have)

### Phase 6: Review System (Week 6-7)
**Why sixth:** Depends on generated content existing

1. Review status model + migrations
2. Approve/reject endpoints
3. Review UI with side-by-side comparison
4. Keyboard shortcuts (approve=A, reject=R, next=→)
5. Optimistic updates with TanStack Query
6. Missing fields warnings

**Dependencies:** Phase 4 (generation complete)
**Risk:** Low (standard CRUD with UI polish)
**Blocker for:** Download

### Phase 7: Smart Regeneration (Week 7-8)
**Why seventh:** Enhancement to core generation

1. Track rejection reasons
2. Store generation history (attempts)
3. Enhanced prompt for regeneration
4. Regenerate rejected products endpoint
5. Regeneration UI

**Dependencies:** Phase 6 (rejection tracking)
**Risk:** Medium (prompt engineering complexity)
**Blocker for:** None (enhancement)

### Phase 8: Excel Download (Week 8)
**Why eighth:** Last step in workflow

1. Download endpoint (FastAPI) with streaming write
2. Filter approved products only
3. Preserve original Excel structure
4. Download UI button

**Dependencies:** Phase 6 (review complete)
**Risk:** Low (reverse of upload)
**Blocker for:** None

### Phase 9: Polish & Production (Week 9-10)
**Why last:** Refinement after core workflow proven

1. Error handling and user feedback
2. Loading states and skeletons
3. Responsive design
4. Performance optimization
5. Deployment configuration
6. Monitoring and logging

**Dependencies:** All previous phases
**Risk:** Low
**Blocker for:** Launch

## Cost Optimization Opportunities

Based on the architecture, key areas for cost optimization:

### 1. OpenAI API Costs (Biggest expense)

**Optimization strategies:**
- Use GPT-4o-mini for title generation (10x cheaper), GPT-4o only for descriptions
- Batch API for non-urgent regenerations (50% cost reduction)
- Cache embeddings for client prompts (reuse across products)
- Implement character-level streaming to detect length early (abort if over limit)
- Smart retry logic (increase temperature instead of regenerating from scratch)

**Estimated savings:** 40-60% of AI costs

### 2. Database Connection Pooling

**Optimization strategies:**
- Use pgbouncer for connection pooling (max 20 connections vs 100+)
- Close sessions immediately after query (async context managers)
- Use read replicas for heavy queries (product list, review)

**Estimated savings:** Enables same DB tier to handle 5x more traffic

### 3. Reduce API Response Size

**Optimization strategies:**
- Pagination for product lists (20-50 per page)
- Field selection (only return needed fields)
- Compression (gzip middleware for JSON > 1KB)

**Estimated savings:** 60-80% bandwidth reduction

### 4. Background Job Efficiency

**Optimization strategies:**
- Process products in batches of 10 (batch embedding, shared context)
- Use ARQ instead of Celery (async-native, ~50% faster)
- Concurrency limit (5-10 concurrent OpenAI calls to avoid rate limit penalties)

**Estimated savings:** 30-40% faster processing = lower worker costs

### 5. Caching Strategy

**Optimization strategies:**
- TanStack Query stale time: 5 minutes for client list, 1 minute for products
- HTTP cache headers for static API responses (client details)
- Redis cache for expensive queries (product counts, statistics)

**Estimated savings:** 70-90% reduction in repeated queries

## Sources

**Next.js + FastAPI + PostgreSQL Architecture:**
- [Next.js FastAPI PostgreSQL Boilerplate Tutorial](https://www.travisluong.com/how-to-build-a-full-stack-next-js-fastapi-postgresql-boilerplate-tutorial/)
- [Building Scalable Full-Stack App with Next.js and FastAPI](https://medium.com/@pottavijay/creating-a-scalable-full-stack-web-app-with-next-js-and-fastapi-eb4db44f4f4e)
- [Modern Full Stack Architecture Using Next.js 15+](https://softwaremill.com/modern-full-stack-application-architecture-using-next-js-15/)

**SaaS Architecture Patterns:**
- [SaaS Architecture Patterns with Next.js](https://vladimirsiedykh.com/blog/saas-architecture-patterns-nextjs)
- [Building SaaS Product with Next.js 14: Architecture Overview](https://medium.com/@mateogalic112/building-saas-product-with-next-js-14-architecture-overview-947371e78d46)
- [Next.js for SaaS Dashboards: Best Practices](https://www.ksolves.com/blog/next-js/best-practices-for-saas-dashboards)

**FastAPI Background Tasks & Job Queues:**
- [FastAPI Background Tasks - Official Docs](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Managing Background Tasks in FastAPI: ARQ vs Built-in](https://davidmuraya.com/blog/fastapi-background-tasks-arq-vs-built-in/)
- [How I Handled 100K Daily Jobs in FastAPI Using Task Queues](https://medium.com/@connect.hashblock/how-i-handled-100k-daily-jobs-in-fastapi-using-task-queues-and-async-retries-62bbcdd8240d)

**PostgreSQL Multi-Tenant Design:**
- [Designing Your Postgres Database for Multi-tenancy](https://www.crunchydata.com/blog/designing-your-postgres-database-for-multi-tenancy)
- [Multi-Tenant Database Architecture Patterns Explained](https://www.bytebase.com/blog/multi-tenant-database-architecture-patterns-explained/)
- [Multi-tenancy Implementation with PostgreSQL](https://blog.logto.io/implement-multi-tenancy)

**FastAPI SQLAlchemy Async Patterns:**
- [Asynchronous Database Sessions in FastAPI with SQLAlchemy](https://dev.to/akarshan/asynchronous-database-sessions-in-fastapi-with-sqlalchemy-1o7e)
- [Building High-Performance Async APIs with FastAPI & SQLAlchemy 2.0](https://leapcell.io/blog/building-high-performance-async-apis-with-fastapi-sqlalchemy-2-0-and-asyncpg)
- [Patterns and Practices for SQLAlchemy 2.0 with FastAPI](https://chaoticengineer.hashnode.dev/fastapi-sqlalchemy)

**Excel Processing Best Practices:**
- [Using pandas to Read Large Excel Files in Python](https://realpython.com/working-with-large-excel-files-in-pandas/)
- [Handle Large Excel Files Efficiently with openpyxl](https://pytutorial.com/handle-large-excel-files-efficiently-python-openpyxl/)
- [FastAPI File Uploads - Handling Gigabyte-Scale Data](https://medium.com/@connect.hashblock/async-file-uploads-in-fastapi-handling-gigabyte-scale-data-smoothly-aec421335680)

**LangChain Production Architecture:**
- [Deploy LangChain Applications to Production in 2026](https://langchain-tutorials.github.io/deploy-langchain-production-2026/)
- [LangChain in Production: Enterprise Scale](https://www.nexastack.ai/blog/langchain-production)
- [LangChain Performance Tuning 2026](https://langchain-tutorials.github.io/langchain-performance-tuning-2026/)

**State Management in Next.js:**
- [TanStack Query with Next.js - Seamless Server State Management](https://leapcell.io/blog/seamless-server-state-management-in-next-js-with-tanstack-query)
- [React Server Components + TanStack Query: 2026 Data-Fetching Power Duo](https://dev.to/krish_kakadiya_5f0eaf6342/react-server-components-tanstack-query-the-2026-data-fetching-power-duo-you-cant-ignore-21fj)
- [State Management in 2025: Context vs Redux vs Zustand vs Jotai](https://dev.to/hijazi313/state-management-in-2025-when-to-use-context-redux-zustand-or-jotai-2d2k)
- [Zustand vs Redux Toolkit: Which to Use in 2026?](https://medium.com/@sangramkumarp530/zustand-vs-redux-toolkit-which-should-you-use-in-2026-903304495e84)

**Next.js Server Actions vs API Routes:**
- [Next.js Server Actions vs API Routes: Don't Build Until You Read This](https://dev.to/myogeshchavan97/nextjs-server-actions-vs-api-routes-dont-build-your-app-until-you-read-this-4kb9)
- [Server Actions vs Route Handlers in Next.js](https://makerkit.dev/blog/tutorials/server-actions-vs-route-handlers)
- [Should I Use Server Actions Or APIs?](https://www.pronextjs.dev/should-i-use-server-actions-or-apis)

**Authentication in Next.js:**
- [Clerk vs Supabase Auth vs NextAuth.js: The Production Reality](https://medium.com/better-dev-nextjs-react/clerk-vs-supabase-auth-vs-nextauth-js-the-production-reality-nobody-tells-you-a4b8f0993e1b)
- [Complete Authentication Guide for Next.js App Router in 2025](https://clerk.com/articles/complete-authentication-guide-for-nextjs-app-router)
- [User Authentication for Next.js: Top Tools for 2025](https://clerk.com/articles/user-authentication-for-nextjs-top-tools-and-recommendations-for-2025)

**WebSocket with FastAPI + Next.js:**
- [FastAPI + WebSockets + React: Real-Time Features](https://medium.com/@suganthi2496/fastapi-websockets-react-real-time-features-for-your-modern-apps-b8042a10fd90)
- [Advanced WebSocket Architectures in FastAPI](https://hexshift.medium.com/how-to-incorporate-advanced-websocket-architectures-in-fastapi-for-high-performance-real-time-b48ac992f401)
- [Developing Real-time Dashboard with FastAPI & WebSockets](https://testdriven.io/blog/fastapi-postgres-websockets/)

**Cost Optimization for AI APIs:**
- [LangChain Cost Management & Token Tracking](https://apxml.com/courses/langchain-production-llm/chapter-6-optimizing-scaling-langchain/cost-management-token-tracking)
- [Efficient Batch Processing with LangChain and OpenAI](https://medium.com/@hey_16878/efficient-batch-processing-with-langchain-and-openai-overcoming-ratelimiterror-daa9de4bbd8b)
- [How to Make LangChain Apps 10x Faster and 5x Cheaper](https://medium.com/@vinodkrane/langchain-in-production-performance-security-and-cost-optimization-d5e0b44a26fd)

---
*Architecture research for: AI-Powered SaaS Product Content Generator*
*Researched: 2026-01-22*
