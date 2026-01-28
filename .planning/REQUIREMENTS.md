# Requirements: Product Content Generator

**Defined:** 2026-01-22
**Core Value:** Generate professional, on-brand product content at scale with minimal friction - agencies can confidently use this with clients without worrying about workflow bottlenecks or unprofessional UX

## v1 Requirements

### Authentication

- [x] **AUTH-01**: User can sign up with email and password
- [x] **AUTH-02**: User can log in and stay logged in across sessions
- [x] **AUTH-03**: User can log out from any page
- [x] **AUTH-04**: User session persists across browser refresh
- [x] **AUTH-05**: OpenAI API key configuration stored per application (single agency)

### Client Profile Management

- [x] **CLNT-01**: User can create new client profile with name
- [x] **CLNT-02**: User can edit client profile (brand name, story, tone, language, guidelines)
- [x] **CLNT-03**: User can store AI prompts per client (system prompt, task1, task2)
- [x] **CLNT-04**: User can delete client profile
- [x] **CLNT-05**: User can switch between client profiles in UI
- [x] **CLNT-06**: Selected client profile persists across sessions
- [x] **CLNT-07**: User can view list of all client profiles

### Excel Upload & Processing

- [x] **EXCL-01**: User can upload Faire Excel template without pre-formatting
- [x] **EXCL-02**: App automatically detects and maps Faire columns
- [x] **EXCL-03**: User can select which product fields to use as AI inputs
- [x] **EXCL-04**: User can filter products by status (which statuses to generate for)
- [x] **EXCL-05**: App handles missing fields gracefully (prompts adapt)
- [ ] **EXCL-06**: App warns user during review if selected fields were missing (Phase 5)
- [x] **EXCL-07**: App uses streaming processing for large Excel files
- [x] **EXCL-08**: App detects when multiple rows have identical Product Name, Product Token, and SKU (indicating option variants)
- [x] **EXCL-09**: App groups option variant rows into single product for generation
- [ ] **EXCL-10**: System provides all option values to AI when generating content for grouped products (Phase 4)
- [x] **EXCL-11**: During review, grouped products appear as single item (not duplicated per option)
- [ ] **EXCL-12**: On export, generated title and description are copied to all original rows that belong to the product group (Phase 7)

### AI Content Generation

- [x] **GEN-01**: User can generate content for 5-10,000 products per upload
- [x] **GEN-02**: System builds prompts dynamically based on available product fields
- [x] **GEN-03**: System validates character limits (30-60 for titles, 2000-3000 for descriptions)
- [x] **GEN-04**: System retries generations that violate character limits
- [x] **GEN-05**: User sees real-time progress during generation (shows X of Y products completed, current cost)
- [x] **GEN-06**: System tracks OpenAI API costs per generation batch with running total
- [x] **GEN-07**: System handles OpenAI rate limits with exponential backoff and queuing
- [x] **GEN-08**: System retries failed generations automatically
- [x] **GEN-09**: System uses background job queue for long-running generation
- [x] **GEN-10**: User can pause generation in progress
- [x] **GEN-11**: User can resume paused or interrupted generation from where it stopped
- [x] **GEN-12**: System uses GPT-5.2 for content generation
- [x] **GEN-14**: System enforces soft cap at $500 per batch - prompts user with progress and costs when reached
- [x] **GEN-15**: User must explicitly choose to continue or stop when $500 soft cap is hit

### Review & Approval

- [x] **REV-01**: User can manually review each product (approve/reject)
- [x] **REV-02**: User can navigate products with keyboard shortcuts
- [x] **REV-03**: UI auto-advances to next product after approve/reject
- [x] **REV-04**: User can choose AI-assisted review mode (GPT-5.2 recommendations)
- [x] **REV-05**: User can choose AI-auto review mode (auto-approve with optional review)
- [x] **REV-06**: User can undo/redo review decisions during session
- [x] **REV-07**: Review shows warnings for products with missing selected fields
- [x] **REV-08**: User can start reviewing completed products while generation is still running
- [x] **REV-09**: Review UI updates in real-time as new products complete generation

### Smart Regeneration

- [ ] **REGEN-01**: User can provide rejection reason for rejected products
- [ ] **REGEN-02**: System stores previous generation attempts per product
- [ ] **REGEN-03**: System includes AI review feedback in regeneration context
- [ ] **REGEN-04**: User can regenerate only rejected products (not entire batch)

### Export

- [ ] **EXP-01**: User can download original Excel with updated Product Name and Description
- [ ] **EXP-02**: Downloaded Excel preserves all other columns and formatting
- [ ] **EXP-03**: Downloaded Excel only includes approved products

## v2 Requirements

### Multi-Agency Support

- **MULTI-01**: Multiple agencies can use the app with isolated data
- **MULTI-02**: Each agency has its own workspace and API key configuration
- **MULTI-03**: Organization management (create/invite team members)
- **MULTI-04**: PostgreSQL Row Level Security for multi-tenant isolation

### Advanced Features

- **ADV-01**: Analytics dashboard (acceptance rates, cost per client, quality metrics)
- **ADV-02**: Template library for common product types
- **ADV-03**: Bulk prompt testing (A/B test different prompts)
- **ADV-04**: API access for programmatic content generation
- **ADV-05**: Shopify/WooCommerce platform integrations
- **ADV-06**: Multi-level approval workflows (designer → manager → client)
- **ADV-07**: White-label UI customization

### Multi-Language

- **LANG-01**: Generate content in multiple languages
- **LANG-02**: Language selection per client profile
- **LANG-03**: Multi-language output in single batch

## Out of Scope

| Feature | Reason |
|---------|--------|
| Client-facing login | Team-only for v1, clients don't need app access yet |
| Product catalog storage | Profiles store prompts/brand only, not product data |
| Alternative LLM providers | OpenAI only - proven quality, existing integration |
| Real-time collaboration | Single-user workflow sufficient for v1 |
| Custom Excel templates | Faire format only - known format, specific use case |
| Built-in image generation | Use existing product images, don't generate new ones |
| Auto-publish to platforms | Manual export workflow maintains control |
| Version history for content | Regeneration stores attempts, but no full versioning system |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Complete |
| AUTH-02 | Phase 1 | Complete |
| AUTH-03 | Phase 1 | Complete |
| AUTH-04 | Phase 1 | Complete |
| AUTH-05 | Phase 1 | Complete |
| CLNT-01 | Phase 2 | Complete |
| CLNT-02 | Phase 2 | Complete |
| CLNT-03 | Phase 2 | Complete |
| CLNT-04 | Phase 2 | Complete |
| CLNT-05 | Phase 2 | Complete |
| CLNT-06 | Phase 2 | Complete |
| CLNT-07 | Phase 2 | Complete |
| EXCL-01 | Phase 3 | Pending |
| EXCL-02 | Phase 3 | Pending |
| EXCL-03 | Phase 3 | Pending |
| EXCL-04 | Phase 3 | Pending |
| EXCL-05 | Phase 3 | Pending |
| EXCL-06 | Phase 3 | Pending |
| EXCL-07 | Phase 3 | Pending |
| EXCL-08 | Phase 3 | Pending |
| EXCL-09 | Phase 3 | Pending |
| EXCL-10 | Phase 3 | Pending |
| EXCL-11 | Phase 3 | Pending |
| EXCL-12 | Phase 3 | Pending |
| GEN-01 | Phase 4 | Complete |
| GEN-02 | Phase 4 | Complete |
| GEN-03 | Phase 4 | Complete |
| GEN-04 | Phase 4 | Complete |
| GEN-05 | Phase 4 | Complete |
| GEN-06 | Phase 4 | Complete |
| GEN-07 | Phase 4 | Complete |
| GEN-08 | Phase 4 | Complete |
| GEN-09 | Phase 4 | Complete |
| GEN-10 | Phase 4 | Complete |
| GEN-11 | Phase 4 | Complete |
| GEN-12 | Phase 4 | Complete |
| GEN-14 | Phase 4 | Complete |
| GEN-15 | Phase 4 | Complete |
| REV-01 | Phase 5 | Complete |
| REV-02 | Phase 5 | Complete |
| REV-03 | Phase 5 | Complete |
| REV-04 | Phase 5 | Complete |
| REV-05 | Phase 5 | Complete |
| REV-06 | Phase 5 | Complete |
| REV-07 | Phase 5 | Complete |
| REV-08 | Phase 5 | Complete |
| REV-09 | Phase 5 | Complete |
| REGEN-01 | Phase 6 | Pending |
| REGEN-02 | Phase 6 | Pending |
| REGEN-03 | Phase 6 | Pending |
| REGEN-04 | Phase 6 | Pending |
| EXP-01 | Phase 7 | Pending |
| EXP-02 | Phase 7 | Pending |
| EXP-03 | Phase 7 | Pending |

**Coverage:**
- v1 requirements: 51 total (GEN-13 removed - Batch API has 24hr latency, incompatible with real-time UX)
- Mapped to phases: 51
- Unmapped: 0

---
*Requirements defined: 2026-01-22*
*Last updated: 2026-01-29 (Phase 5 complete)*
