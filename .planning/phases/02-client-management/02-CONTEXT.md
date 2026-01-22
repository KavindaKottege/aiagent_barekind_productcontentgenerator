# Phase 2: Client Management - Context

**Gathered:** 2026-01-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can create and manage client profiles with brand-specific prompts and guidelines. Each user can create and edit clients; only admins can delete clients. App-level default prompts are configurable in admin settings, with optional per-client overrides.

</domain>

<decisions>
## Implementation Decisions

### Client list & navigation
- Dropdown/select menu in header or toolbar for client selection (space-efficient)
- Dropdown shows just client name (minimal, clean)
- Badge indicator on client names that have custom prompts
- Dedicated /clients management page for viewing all clients and creating new ones
- Available actions per client: Edit and Delete (Delete only visible to admins)

### Profile form structure
- Two-tab layout: "Brand & Guidelines" and "Custom Prompts (Optional)"
- **Brand & Guidelines tab** contains:
  - Brand Name (required, this is THE name field)
  - Story (optional textarea)
  - Tone (optional)
  - Language (optional)
  - Guidelines (optional textarea)
- **Custom Prompts tab** contains:
  - System prompt (optional override)
  - Task 1 prompt (optional override)
  - Task 2 prompt (optional override)
- Only Brand Name is required; all other fields are optional

### Prompt configuration
- App-level default prompts configured on dedicated "Prompt Settings" page (separate from main settings)
- Default prompts pre-filled with working templates (user can customize)
- Each prompt field has collapsible info sections with detailed examples and best practices
- Client-level custom prompts are optional overrides stored per client
- Badge on client name indicates when custom prompts are active

### Permissions model
- Full admin vs regular user permissions in Phase 2
- Regular users can: create clients, edit clients, select/switch clients
- Admin users can: everything regular users can + delete clients + manage app-level prompt settings
- Client creation, editing: available to all users
- Client deletion: admin-only (shows confirmation before delete)

### Client persistence & defaults
- Always remember last selected client across sessions
- When user first logs in with no clients: show empty state with "Create your first client" prompt and button
- Selected client persists in user session/local storage

### Claude's Discretion
- Exact dropdown styling and positioning
- Form validation error messages
- Loading states during save operations
- Client list sorting order on management page
- Empty state illustration/messaging details

</decisions>

<specifics>
## Specific Ideas

- User model is team-based: multiple users share the application, admins have elevated permissions for critical operations
- The "name" field in requirements actually refers to brand name (there's only one name field)
- Deletion is intentionally restricted to admins as it's a risky operation

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-client-management*
*Context gathered: 2026-01-22*
