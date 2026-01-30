# Requirements: Product Content Generator

**Defined:** 2026-01-22
**Core Value:** Generate professional, on-brand product content at scale with minimal friction - agencies can confidently use this with clients without worrying about workflow bottlenecks or unprofessional UX

## v1.0 Requirements (Complete)

All 51 v1.0 requirements complete. See MILESTONES.md for details.

## v2.0 Requirements — Platform Deployment

Requirements for deploying to MadeByKav platform. Each maps to roadmap phases.

### Auth Migration

- [ ] **AUTH2-01**: App uses @madebykav/auth getAuthContext() for all server component auth checks
- [ ] **AUTH2-02**: App uses @madebykav/auth requireAuth() for all API route auth checks
- [ ] **AUTH2-03**: Login, signup, and logout pages are removed (platform handles user lifecycle)
- [ ] **AUTH2-04**: All data queries are scoped by tenant_id from platform session context
- [ ] **AUTH2-05**: Python backend validates requests via x-tenant-id and x-user-id internal headers from Next.js
- [ ] **AUTH2-06**: Unauthenticated users are redirected to platform login (not an in-app login page)

### Database Migration

- [ ] **DB-01**: All database tables include tenant_id column (uuid, not null)
- [ ] **DB-02**: Drizzle ORM schema exists for all tables, usable from Next.js server components and API routes
- [ ] **DB-03**: SQLAlchemy models updated with tenant_id column replacing user_id
- [ ] **DB-04**: All Next.js database queries use withTenant() wrapper for RLS enforcement
- [ ] **DB-05**: All Python backend queries set tenant context via set_config('app.current_tenant_id', ...) for RLS
- [ ] **DB-06**: RLS policies applied to all app tables using platform's tenant isolation pattern
- [ ] **DB-07**: Alembic migrations updated for tenant_id schema (runnable on shared database)
- [ ] **DB-08**: Table names prefixed with app slug to avoid collisions in shared database

### UI Migration

- [ ] **UI-01**: All UI components import from @madebykav/ui instead of local shadcn/ui
- [ ] **UI-02**: Auth-related pages (login, signup) are removed from the app
- [ ] **UI-03**: App layout works within platform embedding (tenant subdomain, /app/ path)
- [ ] **UI-04**: Navigation and header adapted for platform context (no standalone app chrome for auth)

### Backend Containerization

- [ ] **DOCK-01**: Production Dockerfile exists for FastAPI backend service
- [ ] **DOCK-02**: Production Dockerfile exists for ARQ worker service
- [ ] **DOCK-03**: Redis service is configured for production use
- [ ] **DOCK-04**: Docker Compose file orchestrates all backend services (FastAPI + ARQ + Redis)
- [ ] **DOCK-05**: Backend services are on internal network only (not exposed to public internet)
- [ ] **DOCK-06**: Health check endpoints exist for container orchestration

### API Proxy Layer

- [ ] **PROXY-01**: Next.js API routes forward requests to Python backend with tenant context headers
- [ ] **PROXY-02**: SSE streams from Python backend are proxied through Next.js to the browser
- [ ] **PROXY-03**: Excel file uploads are proxied through Next.js to Python backend (up to 10MB)
- [ ] **PROXY-04**: Error responses from Python backend are properly forwarded to the frontend

### Per-Tenant Configuration

- [ ] **CFG-01**: OpenAI API key is stored per tenant in the database
- [ ] **CFG-02**: Settings page allows tenant to configure their OpenAI API key
- [ ] **CFG-03**: Python backend reads the tenant's API key when running AI generation
- [ ] **CFG-04**: App gracefully handles missing API key (shows setup prompt, blocks generation)

### Platform Brief

- [ ] **BRIEF-01**: Infrastructure requirements document describes all services needed on the platform
- [ ] **BRIEF-02**: Document includes Docker container specifications (images, ports, volumes, env vars)
- [ ] **BRIEF-03**: Document includes networking requirements (internal service communication)
- [ ] **BRIEF-04**: Document includes environment variable configuration for all services

## Future Requirements

Deferred beyond v2.0.

### Multi-Agency Support

- **MULTI-01**: Multiple agencies can use the app with isolated data
- **MULTI-02**: Organization management (invite team members)

### Advanced Features

- **ADV-01**: Analytics dashboard (acceptance rates, cost per client, quality metrics)
- **ADV-02**: Template library for common product types
- **ADV-03**: Bulk prompt testing (A/B test different prompts)
- **ADV-04**: API access for programmatic content generation
- **ADV-05**: Platform integrations (Shopify, WooCommerce)
- **ADV-06**: Multi-language content generation

## Out of Scope

| Feature | Reason |
|---------|--------|
| Using @madebykav/ai SDK for generation | App needs LangChain structured output, direct OpenAI API access required |
| Automated data migration from dev DB | Manual initial setup; production starts fresh |
| Custom domain per tenant | Platform handles subdomain routing |
| Alternative LLM providers | OpenAI only for now |
| Real-time collaboration | Single-user workflow per tenant |
| Custom Excel templates | Faire format only |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH2-01 | TBD | Pending |
| AUTH2-02 | TBD | Pending |
| AUTH2-03 | TBD | Pending |
| AUTH2-04 | TBD | Pending |
| AUTH2-05 | TBD | Pending |
| AUTH2-06 | TBD | Pending |
| DB-01 | TBD | Pending |
| DB-02 | TBD | Pending |
| DB-03 | TBD | Pending |
| DB-04 | TBD | Pending |
| DB-05 | TBD | Pending |
| DB-06 | TBD | Pending |
| DB-07 | TBD | Pending |
| DB-08 | TBD | Pending |
| UI-01 | TBD | Pending |
| UI-02 | TBD | Pending |
| UI-03 | TBD | Pending |
| UI-04 | TBD | Pending |
| DOCK-01 | TBD | Pending |
| DOCK-02 | TBD | Pending |
| DOCK-03 | TBD | Pending |
| DOCK-04 | TBD | Pending |
| DOCK-05 | TBD | Pending |
| DOCK-06 | TBD | Pending |
| PROXY-01 | TBD | Pending |
| PROXY-02 | TBD | Pending |
| PROXY-03 | TBD | Pending |
| PROXY-04 | TBD | Pending |
| CFG-01 | TBD | Pending |
| CFG-02 | TBD | Pending |
| CFG-03 | TBD | Pending |
| CFG-04 | TBD | Pending |
| BRIEF-01 | TBD | Pending |
| BRIEF-02 | TBD | Pending |
| BRIEF-03 | TBD | Pending |
| BRIEF-04 | TBD | Pending |

**Coverage:**
- v2.0 requirements: 36 total
- Mapped to phases: 0 (pending roadmap creation)
- Unmapped: 36

---
*Requirements defined: 2026-01-22 (v1.0), updated 2026-01-30 (v2.0)*
*Last updated: 2026-01-30 (v2.0 requirements defined)*
