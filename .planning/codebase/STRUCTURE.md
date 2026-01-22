# Codebase Structure

**Analysis Date:** 2026-01-22

## Directory Layout

```
langchain_test_barekind/
├── .planning/          # GSD planning documents
│   └── codebase/       # Codebase analysis outputs
├── .venv/              # Python virtual environment (gitignored)
├── __pycache__/        # Python bytecode cache
├── app.py              # Main Streamlit web application (2613 lines)
├── Agent.py            # Legacy CLI batch processing script (264 lines)
├── Agent copy.py       # Backup/experimental version of Agent.py
├── requirements.txt    # Python dependencies
├── test_data.xlsx      # Sample input data for testing
├── product_data_response.xlsx  # Example output file
├── main_prompt_task1.txt       # Product title generation prompt template
├── main_prompt_task2.txt       # Product description generation prompt template
└── system_prompt.txt           # System prompt for LLM
```

## Directory Purposes

**.planning/:**
- Purpose: GSD (Get Stuff Done) framework metadata
- Contains: Codebase analysis documents, architecture notes
- Key files: `codebase/ARCHITECTURE.md`, `codebase/STRUCTURE.md`

**.venv/:**
- Purpose: Isolated Python environment
- Contains: Installed packages from requirements.txt
- Key files: Python 3.11 site-packages

**Root directory:**
- Purpose: Application code and configuration
- Contains: Main application file, scripts, data files, prompts
- Key files: `app.py`, `Agent.py`, `requirements.txt`, `*.txt` prompts, `*.xlsx` data

## Key File Locations

**Entry Points:**
- `app.py`: Streamlit web application (primary interface)
- `Agent.py`: Command-line batch processing script (legacy/alternative)

**Configuration:**
- `requirements.txt`: Python package dependencies (streamlit, pandas, langchain-openai, langchain-core, openpyxl)
- `.gitignore`: Git exclusions (includes .venv, API keys)

**Core Logic:**
- `app.py` lines 655-884: Core functions (LLM invocation, retry logic, auto-review)
- `app.py` lines 886-1186: Generation orchestration and product processing
- `app.py` lines 1189-1381: UI rendering helpers (timeline, stats, progress ring)
- `app.py` lines 1383-2613: Main Streamlit UI (tabs, forms, review workflow)

**Testing:**
- `test_data.xlsx`: Sample product data with Products and General Details sheets
- No automated test files detected

**Prompt Templates:**
- `system_prompt.txt`: System-level LLM instructions
- `main_prompt_task1.txt`: Title generation instructions
- `main_prompt_task2.txt`: Description generation instructions (detailed format spec)

## Naming Conventions

**Files:**
- Python scripts: `lowercase.py` (e.g., `app.py`)
- Data files: `snake_case.xlsx` (e.g., `test_data.xlsx`, `product_data_response.xlsx`)
- Prompts: `snake_case.txt` (e.g., `main_prompt_task1.txt`)

**Directories:**
- Hidden config: `.lowercase` (e.g., `.venv`, `.planning`)
- Python cache: `__pycache__`

## Where to Add New Code

**New Feature:**
- Primary code: Add new tab in `app.py` main() function after line 1403
- Helper functions: Add to `app.py` between lines 650-880 (before UI rendering functions)
- Tests: Create new `tests/` directory with `test_*.py` files (not currently present)

**New LLM Integration:**
- Implementation: Add new `invoke_*` function in `app.py` around lines 740-885
- Follow pattern: Accept `llm`, return `(content, input_tokens, output_tokens, cost)`

**Utilities:**
- Shared helpers: Add to `app.py` after line 650 (utilities section)
- Data parsing: Near existing functions like `get_image_urls()` (line 655) or `create_prompt_content()` (line 669)

**New UI Component:**
- Rendering function: Add to `app.py` lines 1189-1381 (UI helpers section)
- Follow pattern: Return HTML string or SVG for injection via `st.markdown()` or `components.html()`

**New Prompt Template:**
- Create new `.txt` file in root directory
- Update `app.py` Tab 2 (Prompts section, lines 1552-1640) to include file uploader and text area

## Special Directories

**.planning/:**
- Purpose: GSD framework planning artifacts
- Generated: Manually by GSD commands
- Committed: Yes (contains architecture documentation)

**.venv/:**
- Purpose: Python virtual environment
- Generated: `python -m venv .venv`
- Committed: No (excluded via .gitignore)

**__pycache__/:**
- Purpose: Python bytecode cache
- Generated: Automatically by Python interpreter
- Committed: No (standard Python practice)

## File Dependencies

**app.py depends on:**
- External: streamlit, pandas, langchain_openai, langchain_core, openpyxl
- Data files: Uploaded Excel or `test_data.xlsx` (loaded dynamically)
- Prompts: User-provided via UI or defaults in code (DEFAULT_SYSTEM_PROMPT, DEFAULT_TASK1_PROMPT, DEFAULT_TASK2_PROMPT)

**Agent.py depends on:**
- External: pandas, langchain_openai, langchain_core, tqdm
- Data files: `test_data.xlsx` (hardcoded path line 35)
- Prompts: `main_prompt_task1.txt`, `main_prompt_task2.txt`, `system_prompt.txt` (lines 40-47)

## Code Organization Patterns

**Single-file architecture:**
- All application code in `app.py` (no separate modules)
- Organized by layers: utilities → business logic → UI rendering → main UI
- No class-based organization (functional programming style)

**Session state keys:**
- Generation: `gen_*` prefix (e.g., `gen_results`, `gen_state`, `gen_total_cost`)
- Review: `review_*` prefix (e.g., `review_data`, `review_statuses`)
- Data: Direct names (e.g., `product_data`, `general_info`, `openai_api_key`)

**UI organization:**
- Tab-based navigation (Upload → Prompts → Settings → Generate → Review)
- Each tab is self-contained `with` block in `main()` function
- Heavy use of `st.session_state` for cross-tab data sharing

---

*Structure analysis: 2026-01-22*
