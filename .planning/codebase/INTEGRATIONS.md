# External Integrations

**Analysis Date:** 2026-01-22

## APIs & External Services

**AI/ML Services:**
- OpenAI API - Core LLM service for content generation and review
  - SDK/Client: `langchain-openai` (ChatOpenAI wrapper)
  - Models used: GPT-4o (content generation), GPT-5.2 (auto-review)
  - Auth: API key via `api_key` parameter in ChatOpenAI initialization
  - Temperature: 0.7 (generation), 0.1 (review)
  - Max tokens: 4096 (generation), 500 (review)
  - Usage tracking: Input/output tokens tracked for cost calculation
  - Pricing: $2.50 per 1M input tokens, $10.00 per 1M output tokens (GPT-4o rates in `Agent.py`)

**Vision API:**
- OpenAI Vision (GPT-4o/GPT-5.2 multimodal)
  - Image URLs passed via HumanMessage content array
  - Image format: `{"type": "image_url", "image_url": {"url": url}}`
  - Detail level: "high" for auto-review (`app.py:811`)
  - Up to 3 images per product review

## Data Storage

**Databases:**
- None (file-based storage only)

**File Storage:**
- Local filesystem for Excel files (.xlsx)
  - Input: `test_data.xlsx` (Products sheet, General Details sheet)
  - Output: `product_data_response.xlsx`
  - Handler: pandas + openpyxl

**Caching:**
- Streamlit session state for in-memory data
  - Session variables: `api_key`, `system_prompt`, `task1_prompt`, `task2_prompt`, product data
  - No persistent cache

## Authentication & Identity

**Auth Provider:**
- None (no user authentication)

**API Authentication:**
- OpenAI API key input via Streamlit text_input
  - Stored in: `st.session_state['api_key']`
  - Input field: `app.py:1644-1655` (Setup tab)
  - Usage: Passed to ChatOpenAI constructor as `api_key` parameter

## Monitoring & Observability

**Error Tracking:**
- None (basic try/except blocks only)

**Logs:**
- Console output via `print()` statements (`Agent.py`)
- Streamlit UI messages via `st.write()`, `st.success()`, `st.error()` (`app.py`)
- Progress tracking via `tqdm` in CLI script (`Agent.py`)

**Token Usage Tracking:**
- Manual tracking dictionary in `Agent.py:19-24`
- Metrics: total_input_tokens, total_output_tokens, total_cost
- Source: `response.usage_metadata` from LangChain responses

## CI/CD & Deployment

**Hosting:**
- Dev Containers (GitHub Codespaces compatible)
  - Base image: `mcr.microsoft.com/devcontainers/python:1-3.11-bookworm`
  - Port: 8501 (Streamlit default)
  - Auto-forward: openPreview on port 8501

**CI Pipeline:**
- None detected

**Deployment:**
- Manual via `streamlit run app.py`
- Dev container auto-starts: `postAttachCommand` runs streamlit server

## Environment Configuration

**Required env vars:**
- None (API key via UI, not environment)

**Secrets location:**
- In-memory only (Streamlit session state)
- Not persisted to disk or environment

**Configuration files:**
- `system_prompt.txt` - System message for LLM
- `main_prompt_task1.txt` - Title generation prompt
- `main_prompt_task2.txt` - Description generation prompt
- `test_data.xlsx` - Product data and brand details

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## Data Exchange Formats

**Input:**
- Excel (.xlsx) via pandas.read_excel()
  - Sheets: "Products", "General Details"
  - Image URLs: Space or newline separated strings in Images column

**Output:**
- Excel (.xlsx) via pandas.to_excel()
  - Columns: Product Token, Product Name, Product Title, Product Description, Review Images
- In-memory BytesIO for Streamlit download (`app.py`)

**API Communication:**
- LangChain message format: SystemMessage, HumanMessage
- Content types: text, image_url
- Response: AIMessage with content string and usage_metadata

---

*Integration audit: 2026-01-22*
