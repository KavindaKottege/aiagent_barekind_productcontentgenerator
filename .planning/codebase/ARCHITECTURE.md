# Architecture

**Analysis Date:** 2026-01-22

## Pattern Overview

**Overall:** Streamlit-based web application with LangChain integration

**Key Characteristics:**
- Event-driven UI with Streamlit's reactive state management
- LangChain abstraction for LLM interactions (OpenAI GPT models)
- Session-based state persistence for multi-step workflows
- Retry mechanism with cost optimization (lightweight retries without images)

## Layers

**Presentation Layer:**
- Purpose: User interface and interaction handling
- Location: `app.py` (lines 1-2613, Streamlit components)
- Contains: UI components, tabs, forms, file uploaders, styling, session state management
- Depends on: Application Logic layer, LangChain SDK
- Used by: End users through web browser

**Application Logic Layer:**
- Purpose: Core business logic for product content generation
- Location: `app.py` (helper functions lines 655-1380)
- Contains: Product processing functions (`process_single_product`, `run_generation`), prompt building, character limit validation, auto-review logic
- Depends on: LLM Integration layer
- Used by: Presentation layer event handlers

**LLM Integration Layer:**
- Purpose: Abstract LLM API calls and handle vision model interactions
- Location: `app.py` (`invoke_agent` lines 683-739, `invoke_retry` lines 742-768, `auto_review_product` lines 771-884)
- Contains: Message construction, image content parsing, token usage tracking, error handling with image fallback
- Depends on: LangChain SDK (`langchain_openai.ChatOpenAI`, `langchain_core.messages`)
- Used by: Application Logic layer

**Data Layer:**
- Purpose: Excel file parsing and DataFrame manipulation
- Location: `app.py` (file upload handlers, lines 1484-1540)
- Contains: Excel sheet reading (Products, General Details), DataFrame transformations, output Excel generation
- Depends on: pandas, openpyxl
- Used by: Application Logic layer

**Script Layer (Legacy):**
- Purpose: Command-line batch processing script
- Location: `Agent.py` (264 lines, standalone script)
- Contains: Similar logic to app.py but for non-interactive batch processing with progress bars
- Depends on: LangChain SDK, pandas
- Used by: Direct command-line execution (appears to be legacy/alternative to Streamlit app)

## Data Flow

**Product Generation Flow:**

1. User uploads Excel file via Streamlit file uploader (`app.py` lines 1428-1540)
2. Data parsed into `product_data` DataFrame and `general_info` dict, stored in `st.session_state`
3. User configures prompts, settings, API key in tabs (`app.py` lines 1552-1750)
4. User clicks "Start Generation" button triggering `run_generation()` (`app.py` lines 1056-1186)
5. For each product row:
   - `process_single_product()` calls `invoke_agent()` with task1 prompt (title generation)
   - If character count outside limits, `invoke_retry()` called up to 3 times
   - Same process repeats for task2 prompt (description generation)
   - Results appended to `st.session_state['gen_results']`
6. Progress displayed via live UI updates using `st.empty()` containers and HTML components
7. Completed results shown in Review tab with approve/reject workflow
8. Final approved results downloadable as Excel via `st.download_button`

**State Management:**
- All workflow state persists in `st.session_state` dictionary
- Key states: `product_data`, `general_info`, `gen_results`, `gen_state`, `review_data`, `review_statuses`
- State triggers UI re-renders through Streamlit's reactive model

## Key Abstractions

**Product Content Generator:**
- Purpose: Orchestrate multi-step AI content generation with validation
- Examples: `run_generation()` (`app.py` lines 1056-1186), `process_single_product()` (`app.py` lines 899-1053)
- Pattern: Generator with pause/resume capability via session state flags

**LLM Agent Invoker:**
- Purpose: Encapsulate LLM calls with retry logic and cost tracking
- Examples: `invoke_agent()` (`app.py` lines 683-739), `invoke_retry()` (`app.py` lines 742-768)
- Pattern: Wrapper with automatic image fallback on download errors, token usage metadata extraction

**Auto-Review Agent:**
- Purpose: AI-powered quality validation comparing generated content to product images
- Examples: `auto_review_product()` (`app.py` lines 771-884)
- Pattern: Structured output extraction using JSON mode (GPT-5.2 model)

**UI Renderer Functions:**
- Purpose: Generate dynamic HTML/SVG visualizations for progress tracking
- Examples: `render_timeline()` (`app.py` lines 1189-1209), `render_live_stats_html()` (`app.py` lines 1238-1280), `render_progress_ring()` (`app.py` lines 1351-1381)
- Pattern: HTML string builders injected via `st.markdown()` or `components.html()`

## Entry Points

**Web Application Entry:**
- Location: `app.py` - `main()` function (lines 1383-2613)
- Triggers: `streamlit run app.py` command
- Responsibilities: Initialize session state, render tab-based UI, handle file uploads, coordinate generation workflow, manage review process

**Script Entry (Legacy):**
- Location: `Agent.py` - module-level execution (lines 157-263)
- Triggers: `python Agent.py` command
- Responsibilities: Load test_data.xlsx, process all products in batch, save to product_data_response.xlsx, print token usage summary

## Error Handling

**Strategy:** Defensive with graceful degradation

**Patterns:**
- Image download failures trigger automatic retry without images (`invoke_agent` lines 714-726)
- Character limit violations handled via lightweight retry loops (max 3 attempts)
- Streamlit try-catch blocks around file operations with `st.error()` user feedback
- Session state corruption handled via existence checks (`if 'key' not in st.session_state`)

## Cross-Cutting Concerns

**Logging:** Streamlit UI feedback (`st.write()`, `st.success()`, `st.error()`) and tqdm progress bars in Agent.py

**Validation:** Character count validation for titles (30-60 chars) and descriptions (2000-3000 chars) with configurable limits

**Authentication:** API key stored in session state (`st.session_state['openai_api_key']`), passed to ChatOpenAI constructor

---

*Architecture analysis: 2026-01-22*
