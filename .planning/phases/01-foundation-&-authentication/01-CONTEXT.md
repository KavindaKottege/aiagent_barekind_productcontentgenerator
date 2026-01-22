# Phase 1: Foundation & Authentication - Context

**Gathered:** 2026-01-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish production-ready Next.js + FastAPI architecture with secure user authentication and multi-tenant data isolation. This phase delivers the foundational infrastructure and auth system that all subsequent phases build upon.

</domain>

<decisions>
## Implementation Decisions

### Auth UX & flows
- Signup form captures: email, password, confirm password, and full name
- Successful signup auto-logs user into dashboard (no email verification required for v1)
- Forgot password functionality included with email reset link flow
- Validation error display: Claude's discretion (pick modern UX pattern)

### Session behavior
- Session duration: Claude's discretion (pick reasonable duration for team SaaS)
- Auto-refresh session tokens in background when possible to prevent interruption
- Logout affects current session only (other devices remain logged in)
- Multiple browser tabs share session state (logout in one tab logs out all tabs)

### OpenAI API key setup
- Application-wide setting (single API key shared by all users, configured at deployment level)
- First user to sign up gets prompted to enter API key in admin UI
- Only first registered user (admin) can view or change API key after setup
- API key displayed fully visible in admin UI (no masking)

### Dev environment
- Docker Compose for one-command PostgreSQL setup
- Database seed script creates sample clients and products for immediate testing
- Hardcoded dev credentials: admin@example.com / password123 created automatically in dev mode
- Environment variable management: Claude's discretion (pick standard approach)

### Claude's Discretion
- Validation error UI pattern (inline, toast, or summary)
- Session duration length (reasonable for team SaaS context)
- Environment variable convention (.env.example vs .env.local)
- Loading states and transitions during auth flows
- Exact password complexity requirements

</decisions>

<specifics>
## Specific Ideas

- First user becomes admin automatically - they control OpenAI API key
- Dev mode should "just work" with minimal setup (Docker Compose + seed data)
- Auth should feel modern and professional (SaaS-grade, not prototype)

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope

</deferred>

---

*Phase: 01-foundation-&-authentication*
*Context gathered: 2026-01-22*
