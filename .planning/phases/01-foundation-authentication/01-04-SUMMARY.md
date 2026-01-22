---
phase: 01-foundation-authentication
plan: 04
subsystem: admin
tags: [settings, admin, api-configuration, nextjs, fastapi, dev-tooling]

# Dependency graph
requires:
  - phase: 01-02
    provides: Backend authentication, get_current_admin dependency
  - phase: 01-03
    provides: Frontend authentication UI, getAdmin() DAL function
provides:
  - Admin-only settings API endpoints for OpenAI API key configuration
  - Settings page in frontend for admin configuration
  - Dev environment seeding script for one-command setup
  - AppSettings database model with singleton pattern
affects:
  - 02-* (AI generation will use stored API key from settings)
  - All future plans (dev seed script provides instant dev environment)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Singleton database pattern for app-wide settings (id=1 row)
    - Admin-only routes with get_current_admin dependency
    - Public endpoint for setup status checking
    - Idempotent seeding scripts for dev environments

key-files:
  created:
    - backend/app/models/settings.py
    - backend/app/schemas/settings.py
    - backend/app/routers/settings.py
    - backend/alembic/versions/002_create_settings_table.py
    - frontend/src/app/actions/settings.ts
    - frontend/src/components/forms/api-key-form.tsx
    - frontend/src/app/(dashboard)/settings/page.tsx
    - backend/scripts/__init__.py
    - backend/scripts/seed_dev.py
  modified:
    - backend/app/models/__init__.py
    - backend/app/schemas/__init__.py
    - backend/app/main.py
    - frontend/src/lib/dal.ts

key-decisions:
  - "Singleton pattern for app_settings table (single row with id=1)"
  - "Public endpoint for has-api-key check (enables frontend setup flow)"
  - "API key stored plaintext for v1 (encryption deferred to future)"
  - "Idempotent seed script that skips existing data"
  - "getAdmin() DAL function redirects non-admins to dashboard with error"

patterns-established:
  - "Pattern 1: Admin-only endpoints use get_current_admin dependency"
  - "Pattern 2: Settings retrieved via singleton pattern (id=1)"
  - "Pattern 3: Dev seeding with friendly emoji output and next steps"

# Metrics
duration: 4min
completed: 2026-01-22
---

# Phase 1 Plan 4: API Foundation Summary

**Admin settings page with OpenAI API key configuration, dev seeding script for one-command setup (admin@example.com / password123), and complete AUTH-05 requirement**

## Performance

- **Duration:** 4 minutes
- **Started:** 2026-01-22T08:22:25Z
- **Completed:** 2026-01-22T08:26:30Z
- **Tasks:** 3
- **Files created:** 9
- **Files modified:** 4

## Accomplishments

- Complete admin settings system for OpenAI API key configuration
- Backend API endpoints with admin-only access control
- Frontend settings page with form validation and success feedback
- Dev environment seeding script that creates admin user in one command
- All AUTH-05 requirements fulfilled

## Task Commits

Each task was committed atomically:

1. **Task 1: Create AppSettings model and API endpoints** - `f75f2ae` (feat)
2. **Task 2: Create admin settings page in frontend** - `ac0c405` (feat)
3. **Task 3: Create dev environment seeding script** - `75e5101` (feat)

## Files Created/Modified

**Backend Models:**
- `backend/app/models/settings.py` - AppSettings model with singleton pattern (id=1)
- `backend/app/models/__init__.py` - Export AppSettings

**Backend Schemas:**
- `backend/app/schemas/settings.py` - SettingsUpdate, SettingsResponse, HasApiKeyResponse
- `backend/app/schemas/__init__.py` - Export settings schemas

**Backend Routes:**
- `backend/app/routers/settings.py` - Admin settings endpoints (GET/PUT /settings, GET /settings/has-api-key)
- `backend/app/main.py` - Include settings router

**Backend Migration:**
- `backend/alembic/versions/002_create_settings_table.py` - Create app_settings table with initial row

**Backend Scripts:**
- `backend/scripts/__init__.py` - Scripts package marker
- `backend/scripts/seed_dev.py` - Dev environment seeding with admin user creation

**Frontend Actions:**
- `frontend/src/app/actions/settings.ts` - Server Actions for getSettings() and updateSettings()

**Frontend Components:**
- `frontend/src/components/forms/api-key-form.tsx` - API key form with validation and success feedback

**Frontend Pages:**
- `frontend/src/app/(dashboard)/settings/page.tsx` - Admin settings page

**Frontend DAL:**
- `frontend/src/lib/dal.ts` - Added getAdmin() function for admin verification

## Decisions Made

1. **Singleton pattern for AppSettings** - Single row (id=1) for app-wide settings, simpler than key-value table
2. **Public has-api-key endpoint** - Allows frontend to check setup status without authentication
3. **Plaintext API key storage** - Deferred encryption to future, v1 focuses on functionality
4. **Idempotent seed script** - Safe to run multiple times, checks existing data before creation
5. **Frontend validation** - API key must start with "sk-" to catch common mistakes early
6. **getAdmin() redirect pattern** - Non-admin users redirected to dashboard with error parameter

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**TypeScript initial state type error** - useActionState required non-null initial state
- **Resolution:** Changed initial state from `null` to `{}` in ApiKeyForm component
- **Files modified:** frontend/src/components/forms/api-key-form.tsx, frontend/src/app/actions/settings.ts
- **Verification:** Frontend builds successfully without type errors

## Technical Implementation

### AppSettings Model

Singleton pattern with single row (id=1):

```python
class AppSettings(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    openai_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

### API Endpoints

**GET /settings/** - Admin only, returns current configuration
**PUT /settings/** - Admin only, updates configuration
**GET /settings/has-api-key** - Public, returns boolean for setup check

### Dev Seeding Script

```bash
python -m scripts.seed_dev
```

Creates:
- Admin user: admin@example.com / password123
- Settings row (id=1)
- Idempotent (safe to re-run)

## Verification Results

All success criteria met:

✅ GET /settings returns current API key for admin
✅ PUT /settings updates API key (admin only)
✅ GET /settings/has-api-key returns boolean (public)
✅ Non-admin gets 403 on /settings endpoints
✅ Admin can view /settings page in frontend
✅ Admin can save OpenAI API key via form
✅ API key displays fully visible (not masked)
✅ python -m scripts.seed_dev creates admin user
✅ Seed script is idempotent (safe to run multiple times)
✅ Dev environment works with single docker-compose up + seed

**Manual testing performed:**

```bash
# Admin can get settings
TOKEN=$(curl -s -X POST 'http://localhost:8000/auth/login' -d 'username=admin@example.com&password=password123' | jq -r '.access_token')
curl 'http://localhost:8000/settings/' -H "Authorization: Bearer $TOKEN"
# Returns: {"openai_api_key":"sk-test123","has_api_key":true}

# Admin can update API key
curl -X PUT 'http://localhost:8000/settings/' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"openai_api_key": "sk-prod-test-key-123"}'
# Returns: {"openai_api_key":"sk-prod-test-key-123","has_api_key":true}

# Public endpoint works
curl 'http://localhost:8000/settings/has-api-key'
# Returns: {"has_api_key":true}

# Non-admin gets 403
USER_TOKEN=$(curl -s -X POST 'http://localhost:8000/auth/login' -d 'username=user@example.com&password=password123' | jq -r '.access_token')
curl 'http://localhost:8000/settings/' -H "Authorization: Bearer $USER_TOKEN"
# Returns: {"detail":"Not enough permissions. Admin access required."}

# Seed script is idempotent
python -m scripts.seed_dev
# Shows: ℹ Admin user already exists
```

## User Setup Required

None - no external service configuration required.

Dev environment setup is fully automated:

```bash
# One-time setup
docker-compose up -d
cd backend && alembic upgrade head
python -m scripts.seed_dev

# Daily workflow
uvicorn app.main:app --reload  # Backend on :8000
cd frontend && npm run dev      # Frontend on :3000
# Login: admin@example.com / password123
```

## Next Phase Readiness

**Phase 1 (Foundation & Authentication) is COMPLETE:**
- ✅ AUTH-01: PostgreSQL database setup
- ✅ AUTH-02: Backend authentication with JWT
- ✅ AUTH-03: Frontend authentication UI
- ✅ AUTH-04: Session management
- ✅ AUTH-05: OpenAI API key configuration

**Phase 2 (Product Import) is ready to execute:**
- Backend API infrastructure complete
- Admin authentication and authorization working
- Settings storage available for API keys
- Dev environment provides instant testing capability

**No blockers for Phase 2.**

**Considerations for future phases:**
- API key stored in plaintext - consider encryption middleware in Phase 6 or 7
- Settings page could expand with additional configuration (models, temperature, etc.)
- Seed script could be enhanced with sample product data for Phase 2 testing

---
*Phase: 01-foundation-authentication*
*Completed: 2026-01-22*
