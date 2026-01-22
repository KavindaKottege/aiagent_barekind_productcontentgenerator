# Phase 1: Foundation & Authentication - Research

**Researched:** 2026-01-22
**Domain:** Full-stack authentication with Next.js 15, FastAPI, PostgreSQL multi-tenancy
**Confidence:** HIGH

## Summary

This phase establishes a production-ready full-stack architecture with Next.js 15 (App Router) frontend, FastAPI backend, PostgreSQL database with Row-Level Security for multi-tenant isolation, and JWT-based authentication. The stack represents the current industry standard for building secure, scalable SaaS applications in 2026.

**Key architectural decisions:**
- Next.js 15 App Router with Server Actions for form handling (no client-side routing libraries needed)
- FastAPI with async SQLAlchemy 2.0 for high-concurrency database operations
- PostgreSQL Row-Level Security (RLS) for database-enforced tenant isolation
- JWT tokens in HTTP-only cookies for stateless authentication
- Docker Compose for local development with zero-configuration PostgreSQL

**Primary recommendation:** Use Server Actions for all authentication flows, implement RLS policies from day one (retrofitting is painful), configure async SQLAlchemy with proper connection pooling, and validate on both client and server using Zod schemas shared between Next.js and FastAPI's Pydantic models.

## Standard Stack

The established libraries/tools for this domain:

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 15.x | Frontend framework with App Router | Industry standard for React SSR/SSG, built-in Server Actions, official recommendation for 2026 |
| FastAPI | 0.115+ | Backend API framework | Fastest Python web framework, native async support, automatic OpenAPI docs |
| PostgreSQL | 16.x | Relational database | Most advanced open-source RDBMS, native RLS support for multi-tenancy |
| SQLAlchemy | 2.0+ | Python ORM with async support | Industry standard ORM, first-class async support in 2.0+, type-safe queries |
| Alembic | 1.13+ | Database migrations | Official SQLAlchemy migration tool, async support |
| Pydantic | 2.x | Data validation (Python) | Built into FastAPI, Rust-powered validation, 17x faster than v1 |
| Zod | 3.x | Data validation (TypeScript) | TypeScript-first validation, runtime type safety, Next.js recommended |
| jose (Python) | 3.x | JWT encoding/decoding | Official FastAPI recommendation for JWT operations |
| pwdlib | 0.2+ | Password hashing | Official FastAPI recommendation, supports Argon2 (most secure) |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| asyncpg | 0.29+ | Async PostgreSQL driver | Required for SQLAlchemy async with PostgreSQL |
| python-multipart | 0.0.6+ | Form data parsing | Required for FastAPI OAuth2PasswordRequestForm |
| uvicorn | 0.30+ | ASGI server | Production server for FastAPI |
| Docker Compose | 2.x | Local development orchestration | One-command PostgreSQL + pgAdmin setup |
| React Hook Form | 7.x | Client-side form state | Optional: better UX for complex forms, not required for simple auth |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| JWT in cookies | NextAuth.js/Auth.js | Auth libraries add complexity but provide OAuth/social login out of box; overkill for email/password only |
| PostgreSQL RLS | Application-level filtering | App-level filtering is fragile (one missing WHERE clause leaks data); RLS is enforced at DB level |
| Async SQLAlchemy | Sync SQLAlchemy | Sync is simpler but 2.3x slower (600 vs 1400 req/s); async essential for production scale |
| Alembic | Raw SQL migrations | Hand-written migrations error-prone; Alembic auto-generates from model changes |

**Installation:**

```bash
# Frontend (Next.js)
npx create-next-app@latest --typescript --tailwind --app
npm install zod react-hook-form @hookform/resolvers

# Backend (FastAPI)
pip install "fastapi[standard]" "sqlalchemy[asyncio]" asyncpg alembic "pwdlib[argon2]" pyjwt python-multipart uvicorn[standard]

# Development
docker-compose up -d  # PostgreSQL + pgAdmin
```

## Architecture Patterns

### Recommended Project Structure

```
# Frontend (Next.js)
src/
├── app/
│   ├── (auth)/              # Route group for auth pages
│   │   ├── login/
│   │   │   └── page.tsx
│   │   ├── signup/
│   │   │   └── page.tsx
│   │   └── reset-password/
│   │       └── page.tsx
│   ├── (dashboard)/         # Route group for authenticated pages
│   │   └── dashboard/
│   │       └── page.tsx
│   ├── actions/             # Server Actions
│   │   └── auth.ts
│   └── lib/
│       ├── dal.ts           # Data Access Layer (auth checks)
│       ├── session.ts       # Session encryption/decryption
│       └── schemas.ts       # Zod validation schemas
├── components/
│   ├── ui/                  # Reusable UI components
│   └── forms/               # Form components
└── middleware.ts            # Route protection (optimistic checks)

# Backend (FastAPI)
app/
├── main.py                  # FastAPI app + CORS
├── config.py                # Environment variables
├── database.py              # Async engine + session factory
├── models/                  # SQLAlchemy models
│   ├── __init__.py
│   ├── base.py              # Declarative Base
│   └── user.py
├── schemas/                 # Pydantic schemas
│   └── user.py
├── routers/                 # API routes
│   └── auth.py
├── utils/
│   ├── auth.py              # JWT + password hashing
│   └── dependencies.py      # get_current_user dependency
└── alembic/                 # Database migrations
    ├── env.py
    └── versions/
```

### Pattern 1: Server Actions for Authentication (Next.js)

**What:** Handle form submissions server-side using Next.js Server Actions with useActionState hook
**When to use:** All authentication flows (signup, login, logout, password reset)

**Example:**
```typescript
// Source: https://nextjs.org/docs/app/guides/authentication
// app/actions/auth.ts
'use server'

import { z } from 'zod'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

const signupSchema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
  password: z.string().min(8).regex(/[a-zA-Z]/).regex(/[0-9]/),
})

export async function signup(prevState: any, formData: FormData) {
  const validatedFields = signupSchema.safeParse({
    name: formData.get('name'),
    email: formData.get('email'),
    password: formData.get('password'),
  })

  if (!validatedFields.success) {
    return { errors: validatedFields.error.flatten().fieldErrors }
  }

  // Call FastAPI backend to create user
  const response = await fetch('http://localhost:8000/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(validatedFields.data),
  })

  if (!response.ok) {
    const error = await response.json()
    return { errors: { _form: [error.detail] } }
  }

  const { access_token } = await response.json()

  // Store JWT in HTTP-only cookie
  const cookieStore = await cookies()
  cookieStore.set('session', access_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 60 * 60 * 24 * 7, // 7 days
    path: '/',
  })

  redirect('/dashboard')
}
```

```tsx
// app/(auth)/signup/page.tsx
'use client'
import { useActionState } from 'react'
import { signup } from '@/app/actions/auth'

export default function SignupPage() {
  const [state, formAction, pending] = useActionState(signup, undefined)

  return (
    <form action={formAction}>
      <input name="name" type="text" required />
      {state?.errors?.name && <p>{state.errors.name}</p>}

      <input name="email" type="email" required />
      {state?.errors?.email && <p>{state.errors.email}</p>}

      <input name="password" type="password" required />
      {state?.errors?.password && <p>{state.errors.password}</p>}

      <button disabled={pending} type="submit">
        {pending ? 'Signing up...' : 'Sign up'}
      </button>
    </form>
  )
}
```

### Pattern 2: Data Access Layer (DAL) for Authorization

**What:** Centralize authentication checks using React's cache() to prevent duplicate requests
**When to use:** Every Server Component and Server Action that needs user data

**Example:**
```typescript
// Source: https://nextjs.org/docs/app/guides/authentication
// app/lib/dal.ts
import { cache } from 'react'
import { cookies } from 'next/headers'
import { jwtVerify } from 'jose'
import { redirect } from 'next/navigation'

const secretKey = new TextEncoder().encode(process.env.SESSION_SECRET)

export const verifySession = cache(async () => {
  const cookieStore = await cookies()
  const token = cookieStore.get('session')?.value

  if (!token) {
    redirect('/login')
  }

  try {
    const { payload } = await jwtVerify(token, secretKey)
    return { isAuth: true, userId: payload.sub as string }
  } catch (error) {
    redirect('/login')
  }
})

export const getUser = cache(async () => {
  const session = await verifySession()

  const response = await fetch(`http://localhost:8000/users/${session.userId}`, {
    headers: { Authorization: `Bearer ${session.userId}` }
  })

  return response.json()
})
```

### Pattern 3: FastAPI JWT Authentication with Async SQLAlchemy

**What:** OAuth2 password flow with JWT tokens, async database operations
**When to use:** All backend authentication endpoints

**Example:**
```python
# Source: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
# app/utils/auth.py
from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession

SECRET_KEY = "your-secret-key-here"  # From env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080  # 7 days

password_hash = PasswordHash.recommended()  # Uses Argon2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "sub": str(data["user_id"])})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    # Fetch user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user
```

```python
# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup")
async def signup(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password
    hashed_password = password_hash.hash(user_data.password)

    # Create user
    new_user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Return JWT
    access_token = create_access_token({"user_id": new_user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
):
    # Get user
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    # Verify password
    if not user or not password_hash.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Return JWT
    access_token = create_access_token({"user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}
```

### Pattern 4: PostgreSQL Row-Level Security (RLS)

**What:** Database-enforced tenant isolation using policies that filter rows based on session context
**When to use:** All multi-tenant tables from the start (retrofitting is extremely difficult)

**Example:**
```sql
-- Source: https://www.postgresql.org/docs/current/ddl-rowsecurity.html
-- Migration: Create users table with RLS
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    hashed_password TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own record
CREATE POLICY user_isolation_policy ON users
    FOR ALL
    USING (id::text = current_setting('app.current_user_id', true))
    WITH CHECK (id::text = current_setting('app.current_user_id', true));

-- Policy: Admins bypass RLS (use sparingly!)
CREATE POLICY admin_all_access ON users
    FOR ALL
    TO admin_role
    USING (true);
```

```python
# Set tenant context before each query
# app/database.py (in get_db dependency)
async def get_db():
    async with async_session_maker() as session:
        # Set session variable for RLS
        user_id = get_user_id_from_jwt()  # Extract from current request
        await session.execute(text(f"SET app.current_user_id = '{user_id}'"))
        yield session
```

### Pattern 5: Async SQLAlchemy Session Management

**What:** Dependency injection pattern with proper session lifecycle and connection pooling
**When to use:** All database operations in FastAPI

**Example:**
```python
# Source: https://medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/dbname"

# Create async engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set False in production
    pool_size=10,  # Number of persistent connections
    max_overflow=20,  # Additional connections when pool exhausted
    pool_pre_ping=True,  # Test connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Session factory with expire_on_commit=False for async
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Critical for async to avoid extra queries
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

# Dependency for route handlers
async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
```

### Pattern 6: CORS Configuration for Production

**What:** Allow Next.js frontend to make requests to FastAPI backend with credentials
**When to use:** Always configure CORS explicitly for security

**Example:**
```python
# Source: https://fastapi.tiangolo.com/tutorial/cors/
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# IMPORTANT: Set specific origins in production, never "*"
origins = [
    "http://localhost:3000",  # Next.js dev
    "https://yourdomain.com",  # Production frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # DO NOT use ["*"] in production
    allow_credentials=True,  # Required for cookies
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### Anti-Patterns to Avoid

- **Storing JWTs in localStorage**: Vulnerable to XSS attacks; always use HTTP-only cookies
- **Returning null in layouts for unauthorized users**: Next.js has multiple entry points; use middleware + DAL pattern instead
- **Forgetting tenant_id in INSERT queries**: RLS only filters reads/updates, not inserts; must explicitly set tenant_id
- **Reusing async sessions across requests**: Each request must get fresh session from pool
- **Using sync SQLAlchemy with async FastAPI**: 2.3x slower than full async stack (600 vs 1400 req/s)
- **Missing CORS credentials flag**: Frontend cookies won't be sent without `allow_credentials=True`
- **Hardcoding secrets in code**: Use environment variables for JWT secret, database credentials, API keys

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Password hashing | Custom hash function | pwdlib with Argon2 | Argon2 is GPU-resistant; bcrypt/pbkdf2 are outdated; custom crypto always breaks |
| JWT encoding/decoding | Manual base64 + HMAC | PyJWT (Python) or jose (Next.js) | JWT has specific timing attack protections, claim validation, algorithm negotiation |
| Form validation | Manual regex checks | Zod (TypeScript) + Pydantic (Python) | Type safety, reusable schemas, automatic error messages, async validators |
| Database migrations | Hand-written SQL scripts | Alembic | Auto-generates migrations from model changes, rollback support, handles dependencies |
| Connection pooling | Manual connection reuse | SQLAlchemy's built-in pooling | Handles connection lifecycle, health checks, overflow, pre-ping for stale connections |
| Password reset tokens | Random strings in DB | JWT with short expiry | Self-contained, stateless, automatic expiration, can't be reused after use |
| Session management | Custom cookie encryption | iron-session or jose | Proper encryption (AES-256-GCM), signature verification, automatic rotation |
| Email validation | Regex patterns | Zod's .email() + server-side SMTP check | Handles all edge cases (internationalized domains, plus addressing, etc.) |

**Key insight:** Authentication and database operations are security-critical. The cost of a bug (leaked data, account takeover) far exceeds the time saved by custom solutions. Use battle-tested libraries.

## Common Pitfalls

### Pitfall 1: RLS Policies Don't Auto-Populate tenant_id on INSERT

**What goes wrong:** Developers enable RLS, test SELECT queries (which correctly filter), then INSERT fails or inserts NULL tenant_id because RLS doesn't auto-populate fields.

**Why it happens:** RLS WITH CHECK clause only validates that the inserted row matches the policy; it doesn't set the value. Common misconception from "RLS handles multi-tenancy" tutorials.

**How to avoid:**
```python
# WRONG: Assumes RLS will set tenant_id
new_client = Client(name="Acme Corp")  # tenant_id is NULL!

# CORRECT: Explicitly set tenant_id
current_user = await get_current_user(token, db)
new_client = Client(name="Acme Corp", tenant_id=current_user.id)
```

**Warning signs:**
- INSERT succeeds but SELECT returns nothing
- RLS policies fail on WITH CHECK clause
- Queries work in pgAdmin but fail from application

### Pitfall 2: Connection Pool Reusing Wrong Tenant Context

**What goes wrong:** Connection pooling can reuse a connection that still has `SET app.current_user_id = 'user1'` from previous request, causing user2's request to see user1's data.

**Why it happens:** PostgreSQL session variables persist for the connection lifetime. Connection pools reuse connections across requests to save overhead.

**How to avoid:**
```python
# CORRECT: Set tenant context at start of EVERY request
async def get_db():
    async with async_session_maker() as session:
        # Always reset tenant context
        user_id = get_user_id_from_jwt()
        await session.execute(text(f"SET app.current_user_id = '{user_id}'"))
        yield session
        # Connection returns to pool with this user_id still set
```

**Alternative:** Use `pool_pre_ping=True` and reset variables on checkout.

**Warning signs:**
- Intermittent data leakage in production (works in dev)
- Wrong user's data appears randomly
- Happens more under high load (more connection reuse)

### Pitfall 3: Async SQLAlchemy with expire_on_commit=True (default)

**What goes wrong:** After `await session.commit()`, accessing any attribute of a committed object triggers a new SELECT query to refresh it, even for simple fields like `user.id`.

**Why it happens:** SQLAlchemy's default `expire_on_commit=True` assumes sync operations. In async, you can't lazily load attributes, so it raises errors or makes unexpected queries.

**How to avoid:**
```python
# WRONG (default)
async_session_maker = async_sessionmaker(engine)  # expire_on_commit defaults to True

user = User(email="test@example.com")
session.add(user)
await session.commit()
print(user.id)  # Triggers: SELECT id FROM users WHERE id = ?

# CORRECT
async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,  # Keep objects accessible after commit
)
```

**Warning signs:**
- "Object is not bound to a session" errors in async code
- Extra SELECT queries after every commit
- Performance degradation (N+1 queries for simple operations)

### Pitfall 4: Next.js Middleware Redirects Creating Infinite Loops

**What goes wrong:** Protected route middleware redirects to `/login`, but `/login` is also protected by middleware, creating infinite redirect loop.

**Why it happens:** Middleware runs on ALL requests by default, including the login page itself.

**How to avoid:**
```typescript
// WRONG
export async function middleware(req: NextRequest) {
  const session = await getSession()
  if (!session) return NextResponse.redirect(new URL('/login', req.url))
}

// CORRECT
export async function middleware(req: NextRequest) {
  const publicPaths = ['/login', '/signup', '/reset-password']
  if (publicPaths.some(path => req.nextUrl.pathname.startsWith(path))) {
    return NextResponse.next()
  }

  const session = await getSession()
  if (!session) return NextResponse.redirect(new URL('/login', req.url))
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)']
}
```

**Warning signs:**
- Browser shows "too many redirects" error
- Network tab shows hundreds of 307 redirects
- Login page never loads

### Pitfall 5: Leaking Secrets to Client Components

**What goes wrong:** Passing environment variables or API responses containing secrets to Client Components exposes them in browser bundle.

**Why it happens:** Next.js bundles Client Components for browser; all props are serialized and visible in page source.

**How to avoid:**
```typescript
// WRONG: app/admin/settings/page.tsx
'use client'
export default function Settings({ apiKey }: { apiKey: string }) {
  return <input value={apiKey} />  // API key now in browser JS bundle!
}

// CORRECT: Keep secrets in Server Components/Actions
'use server'
import { getApiKey } from '@/lib/secrets'  // Server-only import

export default async function Settings() {
  const apiKey = await getApiKey()  // Never sent to client

  async function updateApiKey(formData: FormData) {
    'use server'
    // Update logic runs on server, key never exposed
  }

  return (
    <form action={updateApiKey}>
      <input name="apiKey" type="password" defaultValue={maskApiKey(apiKey)} />
    </form>
  )
}
```

**Warning signs:**
- API keys visible in browser DevTools → Sources tab
- "use client" directive in files that access secrets
- Environment variables without `NEXT_PUBLIC_` prefix used in Client Components

### Pitfall 6: Forgetting Password Reset Token Expiration

**What goes wrong:** Password reset tokens remain valid indefinitely, allowing attackers to use old tokens from compromised email accounts.

**Why it happens:** Developers generate random tokens stored in DB without expiration timestamp.

**How to avoid:**
```python
# WRONG: Token in DB without expiration
reset_token = secrets.token_urlsafe(32)
user.reset_token = reset_token  # Valid forever!

# CORRECT: Use JWT with expiration
def create_password_reset_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    token_data = {"sub": user_id, "exp": expire, "type": "password_reset"}
    return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

# Verify token
try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("type") != "password_reset":
        raise ValueError("Invalid token type")
    return payload["sub"]
except jwt.ExpiredSignatureError:
    raise HTTPException(status_code=400, detail="Token expired")
```

**Warning signs:**
- Old reset emails still work after hours/days
- No expiration logic in password reset flow
- Tokens stored as random strings in database

## Code Examples

Verified patterns from official sources:

### Docker Compose for PostgreSQL Development

```yaml
# Source: https://www.docker.com/blog/how-to-use-the-postgres-docker-official-image/
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16
    container_name: dev_postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: devuser
      POSTGRES_PASSWORD: devpassword
      POSTGRES_DB: saas_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql  # Seed data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U devuser"]
      interval: 10s
      timeout: 5s
      retries: 5

  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: dev_pgadmin
    restart: unless-stopped
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@example.com
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
    depends_on:
      - postgres

volumes:
  postgres_data:
```

```sql
-- init.sql: Seed data for development
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create dev admin user (hardcoded credentials for dev only)
INSERT INTO users (id, email, name, hashed_password, is_admin)
VALUES (
    uuid_generate_v4(),
    'admin@example.com',
    'Dev Admin',
    '$argon2id$v=19$m=65536,t=3,p=4$...',  -- Hash of 'password123'
    true
) ON CONFLICT (email) DO NOTHING;

-- Seed sample data
INSERT INTO clients (name, email, tenant_id)
VALUES
    ('Sample Client 1', 'client1@example.com', (SELECT id FROM users WHERE email = 'admin@example.com')),
    ('Sample Client 2', 'client2@example.com', (SELECT id FROM users WHERE email = 'admin@example.com'));
```

### Environment Variables Pattern

```bash
# .env.local (Next.js) - Never commit!
# Database
DATABASE_URL="postgresql+asyncpg://devuser:devpassword@localhost:5432/saas_dev"

# Auth
SESSION_SECRET="generate-with-openssl-rand-hex-32"

# Backend API (dev)
NEXT_PUBLIC_API_URL="http://localhost:8000"

# Optional: OpenAI API key (stored in database in production)
OPENAI_API_KEY="sk-..."
```

```python
# .env (FastAPI) - Never commit!
DATABASE_URL=postgresql+asyncpg://devuser:devpassword@localhost:5432/saas_dev
SECRET_KEY=your-secret-key-generate-with-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# CORS
FRONTEND_URL=http://localhost:3000
FRONTEND_PROD_URL=https://yourdomain.com

# Environment
ENVIRONMENT=development
```

```bash
# .env.example (commit this)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
SECRET_KEY=generate-with-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
FRONTEND_URL=http://localhost:3000
```

### Alembic Migration Setup

```python
# Source: https://testdriven.io/blog/fastapi-sqlmodel/
# alembic/env.py (async configuration)
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from app.models.base import Base  # Import your Base
import app.models  # Import all models to register with Base

config = context.config

# Override with environment variable
config.set_main_option('sqlalchemy.url', os.getenv('DATABASE_URL'))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # No pooling for migrations
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio
    asyncio.run(run_migrations_online())
```

```bash
# Initialize Alembic with async template
alembic init -t async alembic

# Generate migration from model changes
alembic revision --autogenerate -m "create users table"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Next.js Pages Router | Next.js App Router | Next.js 13 (2023) | Server Components default, built-in data fetching, layouts |
| NextAuth.js v4 | Auth.js v5 (or custom JWT) | 2024 | Renamed to Auth.js, better edge runtime support; but custom JWT simpler for email/password only |
| Pydantic v1 | Pydantic v2 | June 2023 | 17x faster (Rust core), breaking API changes, required FastAPI 0.100+ |
| SQLAlchemy 1.4 | SQLAlchemy 2.0 | Jan 2023 | Native async, new query API, type hints, no more "lazy" joins in async |
| bcrypt for passwords | Argon2 (via pwdlib) | 2024 | GPU-resistant, official FastAPI recommendation, replaces passlib |
| python-jose | PyJWT directly | 2024 | python-jose less maintained, PyJWT is reference implementation |
| Client-side form libs (Formik) | React Server Actions | React 19 (2024) | No client JS for simple forms, progressive enhancement, built-in pending states |

**Deprecated/outdated:**
- **passlib**: Replaced by pwdlib (FastAPI docs updated 2024); passlib maintenance stopped
- **NextAuth.js**: Renamed to Auth.js; old tutorials use v4, current is v5 with breaking changes
- **SQLAlchemy 1.4**: End of life; async support was provisional, 2.0 is required for production async
- **Storing JWTs in localStorage**: Never recommended but common in old tutorials; XSS vulnerability

## Open Questions

Things that couldn't be fully resolved:

1. **Optimal session duration for team SaaS**
   - What we know: Enterprise SaaS typically uses 7-30 days with background refresh
   - What's unclear: Whether to implement refresh token rotation or single long-lived token for v1
   - Recommendation: Start with 7-day token, no refresh rotation (simpler). Add refresh tokens in v2 if needed for security compliance.

2. **Exact password complexity requirements**
   - What we know: NIST recommends minimum 8 characters, no max length, check against breach databases
   - What's unclear: Whether to enforce uppercase/lowercase/special chars (NIST says optional)
   - Recommendation: Minimum 8 characters + at least one letter + one number. No special char requirement (users hate it). Consider have-i-been-pwned API in v2.

3. **Connection pool sizing for production**
   - What we know: pool_size=10, max_overflow=20 are common defaults; depends on request concurrency
   - What's unclear: Formula to calculate optimal pool size for specific traffic patterns
   - Recommendation: Start with defaults (10/20), monitor with Prometheus. Formula: `pool_size = (concurrent_requests * avg_query_time) / avg_response_time`

4. **NextAuth.js vs custom JWT for this specific use case**
   - What we know: NextAuth.js (Auth.js v5) provides OAuth, database sessions, callbacks; custom JWT is simpler but manual
   - What's unclear: Whether single email/password auth justifies custom implementation or if Auth.js future-proofs for OAuth
   - Recommendation: Use custom JWT for v1 (less complexity, no OAuth needed). Migrate to Auth.js in v2 if adding social login.

## Sources

### Primary (HIGH confidence)

- [Next.js App Router Authentication Guide](https://nextjs.org/docs/app/guides/authentication) - Official Next.js documentation on authentication patterns
- [FastAPI OAuth2 with JWT Tokens](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) - Official FastAPI security tutorial
- [PostgreSQL Row Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) - Official PostgreSQL documentation
- [Docker Official Image: PostgreSQL](https://www.docker.com/blog/how-to-use-the-postgres-docker-official-image/) - Official Docker usage guide
- [FastAPI CORS Tutorial](https://fastapi.tiangolo.com/tutorial/cors/) - Official FastAPI CORS documentation

### Secondary (MEDIUM confidence)

- [Next.js 15 App Router Complete Guide (Medium, Jan 2026)](https://medium.com/@livenapps/next-js-15-app-router-a-complete-senior-level-guide-0554a2b820f7) - Senior-level patterns
- [FastAPI JWT Authentication (TestDriven.io)](https://testdriven.io/blog/fastapi-jwt-auth/) - Production patterns
- [SQLAlchemy 2.0 with FastAPI (Medium, 2024)](https://medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308) - Async setup patterns
- [PostgreSQL RLS Multi-Tenant SaaS (TechBuddies, Jan 2026)](https://www.techbuddies.io/2026/01/01/how-to-implement-postgresql-row-level-security-for-multi-tenant-saas/) - Recent RLS patterns
- [PostgreSQL Connection Pooling FastAPI (Medium, Jan 2026)](https://medium.com/write-a-catalyst/how-to-handle-millions-of-postgresql-connections-in-fastapi-using-async-and-connection-pooling-8d63b24f4e43) - High-concurrency patterns
- [Postgres RLS Implementation Guide (Permit.io)](https://www.permit.io/blog/postgres-rls-implementation-guide) - Common pitfalls
- [Next.js Security Guide 2025 (TurboStarter)](https://www.turbostarter.dev/blog/complete-nextjs-security-guide-2025-authentication-api-protection-and-best-practices) - Security best practices

### Tertiary (LOW confidence - marked for validation)

- [Next.js Best Practices 2025 (DEV Community)](https://dev.to/bajrayejoon/best-practices-for-organizing-your-nextjs-15-2025-53ji) - Project structure ideas
- [FastAPI at Scale 2026 (Medium)](https://medium.com/@kaushalsinh73/fastapi-at-scale-in-2026-pydantic-v2-uvloop-http-3-which-knob-moves-latency-vs-throughput-cd0a601179de) - Performance benchmarks
- WebSearch results on Docker Compose patterns - Multiple community examples, need official docs verification

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified from official FastAPI/Next.js docs and Context7 (if available)
- Architecture: HIGH - Patterns from official Next.js authentication guide and FastAPI security tutorial
- Pitfalls: MEDIUM-HIGH - Mix of official docs (RLS, async SQLAlchemy) and community experiences (WebSearch)

**Research date:** 2026-01-22
**Valid until:** 2026-02-22 (30 days - frameworks stable, libraries update monthly)

**Next steps for planner:**
- Break down into tasks: Docker setup, database models + migrations, FastAPI auth routes, Next.js auth flows, RLS policies
- Consider parallel work: Frontend and backend can be developed simultaneously using API contract (Pydantic schemas)
- Testing strategy: Unit tests for password hashing, integration tests for auth flows, manual testing for RLS isolation
