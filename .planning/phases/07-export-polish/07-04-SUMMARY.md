---
phase: 07-export-polish
plan: 04
subsystem: frontend-dashboard
tags: [dashboard, empty-state, onboarding, css-transitions, animations, notion-style]
depends_on:
  requires:
    - "07-02 (skeleton/toast infrastructure)"
  provides:
    - "Guided 3-step onboarding for new users (0 clients)"
    - "Quick-action overview grid for returning users"
    - "Global CSS transitions: card-hover, animate-fade-in, skeleton-pulse"
    - "150ms smooth transitions on all interactive elements"
  affects:
    - "07-05 (final polish pass can build on dashboard and transitions)"
tech-stack:
  added: []
  patterns:
    - "Conditional rendering based on data state (empty state vs populated)"
    - "Server component data fetching with getClients for state detection"
    - "CSS utility classes for reusable hover/animation effects"
    - "Notion-style aesthetic: warm, spacious, content-first"
key-files:
  created: []
  modified:
    - frontend/src/app/(dashboard)/dashboard/page.tsx
    - frontend/src/app/globals.css
decisions:
  - "New user detection via clients.length === 0 (simplest meaningful signal)"
  - "Settings quick-action card only shown to admin users (is_admin check)"
  - "card-hover CSS class for reusable hover lift effect across app"
  - "animate-fade-in applied at page wrapper level for entrance animation"
metrics:
  duration: "2 minutes"
  completed: "2026-01-29"
---

# Phase 7 Plan 4: Dashboard Redesign & CSS Transitions Summary

**One-liner:** Guided 3-step onboarding for new users + quick-action overview grid for returning users + global CSS transitions (card hover, fade-in, skeleton pulse)

## What Was Done

### Task 1: Dashboard redesign with guided empty state
Complete rewrite of `frontend/src/app/(dashboard)/dashboard/page.tsx`:

**Data fetching:** Server component fetches both `getUser()` and `getClients()` to determine user state (new vs returning) based on `clients.length === 0`.

**New user state (0 clients):**
- Centered welcome heading: "Welcome to SEO Content Generator, {name}"
- Subtitle: "Get started in three simple steps"
- 3-column grid of step cards:
  1. **Create a Client** (active) -- Users icon, blue ring highlight, "Create Client" CTA button linking to /clients
  2. **Upload Products** (muted, opacity-50) -- Upload icon, greyed out
  3. **Generate Content** (muted, opacity-50) -- Sparkles icon, greyed out
- Each step has numbered badge (1, 2, 3), icon, title, description
- Active step prominent with ring-2 ring-brand-blue; future steps dimmed

**Returning user state (has clients):**
- Greeting: "Welcome back, {userName}" with "Pick up where you left off" subtitle
- 2-column responsive grid of quick-action cards:
  - **Products** (Package icon) -- "View and manage your product catalog"
  - **Review** (CheckCircle icon) -- "Review and approve generated content"
  - **Clients** (Users icon) -- "Manage client profiles and brand settings"
  - **Settings** (Settings icon, admin only) -- "Configure AI generation settings"
- Each card: card-hover class for shadow lift, group hover transitions on icon/arrow, ArrowRight indicator
- Removed all old placeholder content (Account Information, Getting Started, "features will be available" text)

**Design:** Notion-style warm spacious aesthetic -- rounded-xl cards, generous padding, gray-900/500/400 text hierarchy, space-y-8 between sections, animate-fade-in page entrance.

### Task 2: Global CSS transitions and consistency pass
Appended new CSS rules to `frontend/src/app/globals.css` (all additive, no existing styles removed):

1. **Smooth interactive transitions:** `button, a, [role="button"]` get `transition: all 0.15s ease`
2. **Card hover effect:** `.card-hover` class with `box-shadow 0.2s ease, transform 0.2s ease` -- hover lifts card 1px with soft shadow
3. **Fade-in animation:** `@keyframes fadeIn` from opacity 0 + translateY(4px) to full -- `.animate-fade-in` class
4. **Skeleton pulse:** `.skeleton-pulse` with 1.5s cubic-bezier infinite pulse for consistent loading skeleton timing

All existing Tailwind directives, brand color variables, and utility classes preserved intact.

## Deviations from Plan

None -- plan executed exactly as written.

## Verification

- [x] `frontend/src/app/(dashboard)/dashboard/page.tsx` fully redesigned
- [x] No old placeholder content ("Product content generation features will be available...")
- [x] Conditional rendering based on `clients.length` for empty state detection
- [x] `npx tsc --noEmit` passes with zero errors
- [x] `frontend/src/app/globals.css` contains new transition and animation rules
- [x] Existing CSS rules preserved (Tailwind directives intact)
- [x] `npm run build` succeeds with clean output

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| 7ae696d | feat | (07-04) Dashboard redesign with guided empty state |
| 8dd08dc | feat | (07-04) Global CSS transitions and consistency pass |

## Next Plan Readiness

Ready for 07-05 (final polish pass). The dashboard is redesigned with guided onboarding and returning-user overview. CSS transitions (card-hover, animate-fade-in) are globally available for use across all pages.
