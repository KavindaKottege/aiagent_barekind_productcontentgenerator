---
phase: 02-client-management
plan: 05
subsystem: admin-ui
tags: [nextjs, react, shadcn-ui, prompts, admin, settings]

dependency-graph:
  requires:
    - 02-02  # Default prompts in app_settings table
    - 01-03  # Frontend auth infrastructure
    - 01-04  # Admin DAL functions
  provides:
    - Admin UI for configuring default AI prompts
    - Collapsible info sections with examples
    - Prompt settings form with validation
  affects:
    - Future plans using default prompts for generation

tech-stack:
  added:
    - "@radix-ui/react-collapsible": "Headless UI for collapsible sections"
    - "lucide-react": "Icon library for UI components"
  patterns:
    - "Collapsible UI pattern": "Toggle-able info sections for better UX"
    - "Domain-specific examples": "Product content examples in UI"
    - "Monospace textarea": "Code-like formatting for prompts"

key-files:
  created:
    - frontend/src/app/(dashboard)/settings/prompts/page.tsx: "Admin-only Prompt Settings page"
    - frontend/src/components/forms/prompt-settings-form.tsx: "Form with collapsible info sections"
    - frontend/src/components/ui/collapsible.tsx: "Radix UI collapsible wrapper"
    - frontend/src/components/ui/textarea.tsx: "Textarea component"
  modified:
    - frontend/src/app/(dashboard)/settings/page.tsx: "Added Prompt Settings navigation card"
    - frontend/src/app/actions/settings.ts: "Added prompt settings actions, fixed auth pattern"
    - frontend/src/components/ui/card.tsx: "Added CardDescription component"
    - frontend/src/components/forms/login-form.tsx: "Fixed Button isLoading prop"
    - frontend/src/components/forms/signup-form.tsx: "Fixed Button isLoading prop"

decisions:
  - id: CLNT-05-01
    decision: "Use Radix UI collapsible for expandable info sections"
    rationale: "Keeps UI clean by hiding examples/tips by default while making them easily accessible"
    alternatives:
      - "Always show examples": "Would clutter the UI"
      - "Tooltips": "Too limited for long examples"

  - id: CLNT-05-02
    decision: "Provide domain-specific examples for product content generation"
    rationale: "Helps users understand effective prompt engineering for e-commerce use case"
    alternatives:
      - "Generic examples": "Less helpful for specific domain"

  - id: CLNT-05-03
    decision: "Use monospace font for prompt textareas"
    rationale: "Prompts are code-like text with placeholders - monospace improves readability"
    alternatives:
      - "Regular font": "Harder to distinguish placeholders from prose"

metrics:
  duration: 6
  completed: 2026-01-22
---

# Phase 2 Plan 5: Prompt Settings Admin UI Summary

**One-liner:** Admin UI for configuring default AI prompts with collapsible examples and product content-specific guidance

## What Was Built

Created a complete admin interface for managing default AI prompts:

1. **Prompt Settings Page** (`/settings/prompts`)
   - Admin-only access with getAdmin check
   - Three prompt fields: system, task1 (title generation), task2 (description generation)
   - Collapsible info sections for each prompt
   - Product content-specific examples and tips
   - Success/error feedback

2. **Form Components**
   - PromptSettingsForm with useActionState pattern
   - Collapsible UI component from Radix UI
   - Textarea component for multi-line input
   - CardDescription added to card component

3. **Server Actions**
   - getPromptSettings: Fetch current prompt settings
   - updatePromptSettings: Save prompt changes
   - Fixed auth pattern: migrated from session cookie to access_token cookie

4. **Navigation**
   - Added Prompt Settings card to /settings page
   - Admin-only visibility
   - "Manage Prompts" button link

## Technical Implementation

**UI Components:**
```typescript
- Collapsible sections hide examples/tips by default
- Monospace font for prompt textareas (better for code-like text)
- Each prompt has: title, description, examples, tips, textarea
- Success message shows after save
- Form uses useActionState for optimistic UI
```

**Server Actions:**
```typescript
- getPromptSettings: GET /settings/ with access_token auth
- updatePromptSettings: PUT /settings/ with access_token auth
- Empty strings converted to null for clearing prompts
- 401/403 redirects handled appropriately
```

**Admin Access Control:**
```typescript
- /settings/prompts uses getAdmin() check
- Non-admins redirected to /dashboard?error=admin_required
- Settings page shows Prompt Settings card only if user.is_admin
```

## Domain-Specific Examples

**System Prompt Example:**
```
You are an expert product copywriter for e-commerce brands...
- Highlight key product benefits
- Use natural, conversational language
- Include relevant keywords without keyword stuffing
```

**Task 1 (Title) Example:**
```
Generate a product title for the following product:
Product Name: {product_name}
Requirements:
- Length: 30-60 characters
- Make it descriptive and searchable
```

**Task 2 (Description) Example:**
```
Generate a product description...
Requirements:
- Length: 2000-3000 characters
- Start with a hook that captures attention
- End with a call to action
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed Button component incompatibility**
- **Found during:** Task 1 build verification
- **Issue:** Button component was replaced with shadcn/ui version that doesn't support isLoading prop, causing compilation errors in login-form.tsx and signup-form.tsx
- **Fix:** Changed `isLoading={isPending}` to `disabled={isPending}` in both forms
- **Files modified:** login-form.tsx, signup-form.tsx
- **Commit:** 163f889

**2. [Rule 1 - Bug] Fixed incorrect auth pattern in settings actions**
- **Found during:** Task 1 implementation
- **Issue:** settings.ts was using session cookie instead of access_token cookie (violates 01-05 dual-cookie architecture decision)
- **Fix:** Migrated getSettings and updateSettings to use getAccessToken() and access_token cookie
- **Files modified:** app/actions/settings.ts
- **Commit:** 163f889

**3. [Rule 2 - Missing Critical] Added CardDescription component**
- **Found during:** Task 2 build verification
- **Issue:** PromptSettingsForm uses CardDescription but it wasn't exported from card.tsx
- **Fix:** Added CardDescription export to card.tsx
- **Files modified:** components/ui/card.tsx
- **Commit:** b539d6b

## Files Changed

**Created (4 files):**
- frontend/src/app/(dashboard)/settings/prompts/page.tsx
- frontend/src/components/forms/prompt-settings-form.tsx
- frontend/src/components/ui/collapsible.tsx
- frontend/src/components/ui/textarea.tsx

**Modified (7 files):**
- frontend/src/app/(dashboard)/settings/page.tsx
- frontend/src/app/actions/settings.ts
- frontend/src/components/ui/card.tsx
- frontend/src/components/forms/login-form.tsx
- frontend/src/components/forms/signup-form.tsx
- frontend/package.json
- frontend/package-lock.json

## Testing Notes

**Automated verification completed:**
- ✅ Dependencies installed (@radix-ui/react-collapsible, lucide-react)
- ✅ npm run build passes without errors
- ✅ TypeScript compilation successful
- ✅ New route /settings/prompts appears in build output

**Manual verification required:**
- Admin can access /settings/prompts
- Non-admin redirected from /settings/prompts
- All three prompt fields display correctly
- Collapsible sections expand/collapse
- Examples and tips are helpful and domain-specific
- Saving prompts shows success message
- Saved prompts persist after refresh
- Empty prompt clears to null
- /settings page shows Prompt Settings link

## Integration Points

**Backend:**
- Uses existing /settings/ endpoint from Plan 02-02
- AppSettings model already has default_*_prompt fields
- SettingsResponse schema includes prompt fields

**Frontend:**
- Integrates with getAdmin from Plan 01-04
- Uses access_token auth pattern from Plan 01-05
- Follows existing settings page pattern
- Uses shadcn/ui component architecture

## Next Phase Readiness

**Phase 2 (Client Management) progress: 2/5 plans complete**

**Remaining plans:**
- Client form for create/edit (in progress from other commits)
- Client selector for switching context
- Integration testing

**Ready for:**
- AI content generation with configurable prompts
- Per-client prompt overrides (future enhancement)

## Success Criteria

✅ Admin-only Prompt Settings page at /settings/prompts
✅ Three editable prompt fields (system, task1, task2)
✅ Collapsible info sections with examples and tips
✅ Success feedback after save
✅ Empty fields clear prompts (stored as null)
✅ Navigation from /settings to /settings/prompts
✅ Non-admin users cannot access page

## Commits

1. **163f889** - feat(02-05): add prompt settings actions and UI components
   - Install collapsible and lucide-react dependencies
   - Create Collapsible and Textarea UI components
   - Add getPromptSettings and updatePromptSettings actions
   - Fix auth pattern: use access_token instead of session cookie
   - Fix Button isLoading prop usage

2. **b539d6b** - feat(02-05): create PromptSettingsForm component
   - Form with three prompt fields
   - Collapsible info sections with examples
   - Product content-specific guidance
   - Success/error feedback

3. **5fc938b** - feat(02-05): create Prompt Settings page and update navigation
   - /settings/prompts admin-only page
   - Update /settings with Prompt Settings card
   - Admin-only access control

---

**Plan completed:** 2026-01-22
**Duration:** 6 minutes
**Tasks completed:** 3/3
**Deviations:** 3 auto-fixes (blocking Button incompatibility, auth pattern bug, missing CardDescription)
