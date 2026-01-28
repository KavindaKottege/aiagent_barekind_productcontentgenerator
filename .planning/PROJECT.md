# Candid Founders Content Generator

## What This Is

A professional AI-powered product content generator for marketing agencies. Teams upload raw product Excel files (Faire format), select which product fields to use, and generate optimized titles and descriptions using client-specific brand guidelines and prompts. The app handles client profiles, smart regeneration with feedback, and multi-mode review (manual, AI-assisted, or auto). Built for agencies managing multiple clients with different brand voices.

## Core Value

Generate professional, on-brand product content at scale with minimal friction - agencies can confidently use this with clients without worrying about workflow bottlenecks or unprofessional UX.

## Requirements

### Validated

<!-- Existing capabilities from current Streamlit app -->

- ✓ Upload Excel file with product data — existing
- ✓ AI-powered content generation (titles and descriptions) using OpenAI GPT models — existing
- ✓ Character limit validation with retry logic (30-60 chars for titles, 2000-3000 for descriptions) — existing
- ✓ Auto-review feature using GPT-5.2 with image analysis — existing
- ✓ Manual review workflow with approve/reject functionality — existing
- ✓ Token usage tracking and cost monitoring — existing
- ✓ Download generated content as Excel — existing
- ✓ Configurable AI prompts (system, task-specific) — existing

### Active

<!-- New requirements for commercial-grade rebuild -->

**Architecture & Foundation**
- [ ] Next.js frontend with modern, professional UI
- [ ] Python/FastAPI backend API (separation from UI)
- [ ] PostgreSQL database for persistent storage
- [ ] Team authentication and user management
- [ ] Cloud deployment ready (Vercel frontend, Railway/similar backend)

**Client Management**
- [ ] Client profile creation and management
- [ ] Store client-specific prompts, brand guidelines, tone, and language
- [ ] Switch between client profiles easily
- [ ] Client profile selection persists across sessions

**Excel Processing**
- [ ] Upload raw Faire Excel files without pre-formatting
- [ ] Automatic column detection and mapping
- [ ] User selects which product fields feed into AI (e.g., product name, type, description, images, country, customization, SKU)
- [ ] Product status filtering (generate only for selected statuses)
- [ ] Dynamic prompt building based on available fields
- [ ] Warn user in review if selected fields were missing for specific products

**Content Generation**
- [ ] Dynamic prompt optimization based on available product data
- [ ] Progress tracking during batch generation
- [ ] Handle missing fields gracefully (prompts adapt to what's available)

**Review System**
- [ ] Three review modes: Manual only, AI-assisted (recommendations), AI-auto (with optional user review)
- [ ] Side-by-side comparison (original vs generated)
- [ ] Keyboard shortcuts for rapid review (approve/reject/navigate)
- [ ] Auto-advance to next product after approve/reject
- [ ] Undo/redo functionality during review
- [ ] Display warnings for missing selected fields

**Smart Regeneration**
- [ ] Track rejection reasons per product
- [ ] Store previous generation attempts
- [ ] Include optional AI review feedback in regeneration context
- [ ] Regenerate only rejected products with enhanced prompts

**Output**
- [ ] Download original Excel with updated Product Name and Description columns
- [ ] Preserve all other Excel columns and formatting
- [ ] Only include approved products in output

**User Experience**
- [ ] Clean, modern SaaS-style dashboard interface
- [ ] Professional visual design (white-label ready)
- [ ] Minimal friction workflow (upload → select → generate → review → download)
- [ ] Robust error handling with clear user feedback
- [ ] Responsive design for different screen sizes

### Out of Scope

- Client-facing access (clients logging in to review) — team-only for v1, defer to future
- Multi-language content generation — English only for v1
- Product catalog storage in client profiles — only store brand/prompt settings, not products
- Alternative LLM providers — OpenAI only (cost optimization via model selection)
- Real-time collaboration — single-user workflow for v1
- Custom Excel templates beyond Faire format — Faire only for v1
- Bulk prompt testing/A-B testing — defer to future
- Analytics dashboard (content performance tracking) — defer to future

## Context

**Current State:**
- Existing Streamlit prototype (2600-line monolith in app.py)
- Already has core AI generation logic with LangChain + OpenAI
- Auto-review feature using GPT-5.2 with vision
- Basic retry and validation logic
- Session-based state management

**User:**
- Marketing agency serving multiple clients
- Need to manage different brand voices and guidelines per client
- Current workflow requires manual Excel formatting before upload
- Cost-sensitive (optimize API usage)

**Technical Environment:**
- Python backend with LangChain already working
- Familiar with OpenAI API (GPT-4o for generation, GPT-5.2 for review)
- Ready to move to modern frontend (React/Next.js)
- Targeting cloud deployment

**Known Issues to Address:**
- Current UI is cluttered and unprofessional
- No client management - settings must be re-entered per session
- Excel format requires manual preprocessing
- Editing prompts is cumbersome
- Review workflow is not efficient (no keyboard shortcuts, manual navigation)
- Regeneration doesn't learn from previous attempts or rejection feedback

## Constraints

- **Tech Stack**: Next.js frontend + Python/FastAPI backend + PostgreSQL database — required for professional architecture
- **LLM Provider**: OpenAI only — existing integration, proven models
- **Cost**: Optimize for minimal infrastructure and API costs — use appropriate models (GPT-4o for generation, GPT-5.2 only for review)
- **Excel Format**: Faire bulk upload template format — target use case
- **Deployment**: Cloud platform (Vercel/Railway) — managed hosting for simplicity

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Rebuild frontend in Next.js instead of enhancing Streamlit | Need full design control for professional, white-label ready UI; Streamlit limitations prevent modern UX | — Pending |
| Separate frontend/backend architecture | Better separation of concerns, testability, scalability; allows independent deployment | — Pending |
| PostgreSQL for persistence | Industry standard, robust, supports complex queries for client profiles and generation history | — Pending |
| Keep existing AI logic/prompts | Core generation logic works; optimize dynamically but don't rebuild from scratch | — Pending |
| Team-only auth for v1 | Simpler scope; client access can come later after core workflow is solid | — Pending |

---
*Last updated: 2026-01-22 after initialization*
