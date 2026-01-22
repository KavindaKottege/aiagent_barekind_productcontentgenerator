# Technology Stack

**Analysis Date:** 2026-01-22

## Languages

**Primary:**
- Python 3.11+ - Core application language (uses venv with Python 3.11, dev environment uses Python 3.11)

**Secondary:**
- HTML/CSS - Embedded in Streamlit UI components (`app.py`)
- Markdown - Documentation and prompt templates

## Runtime

**Environment:**
- Python 3.11+ (devcontainer specifies Python 3.11-bookworm base image)
- Virtual environment (.venv) for dependency isolation

**Package Manager:**
- pip (Python package installer)
- Lockfile: Not present (requirements.txt only)

## Frameworks

**Core:**
- Streamlit >=1.28.0 - Web UI framework for the product content generator application
- LangChain OpenAI >=0.1.0 - OpenAI model integration and chat interface
- LangChain Core >=0.1.0 - Core LangChain abstractions and message types

**Data Processing:**
- Pandas >=2.0.0 - Excel data processing and DataFrame operations
- OpenPyXL >=3.1.5 - Excel file reading/writing (.xlsx format)

**Development:**
- tqdm 4.67.1 - Progress bars for CLI scripts (`Agent.py`)

## Key Dependencies

**Critical:**
- langchain-openai >=0.1.0 - OpenAI GPT-4o and GPT-5.2 model integration via ChatOpenAI interface
- streamlit >=1.28.0 - Entire web UI built on Streamlit framework
- pandas >=2.0.0 - All Excel data import/export operations
- openpyxl >=3.1.0 - Required for pandas Excel file support

**Infrastructure:**
- tiktoken 0.12.0 - Token counting for OpenAI models (transitive dependency)
- httpx 0.28.1 - HTTP client (transitive via openai/langchain)
- openai 2.14.0 - OpenAI Python SDK (via langchain-openai)
- requests 2.32.5 - HTTP library for API calls
- numpy 2.4.0 - Data structure support (transitive via pandas)

**UI/UX:**
- Pillow 12.1.0 - Image handling (transitive)
- pydeck 0.9.1 - Deck.gl integration for Streamlit (transitive)
- Jinja2 3.1.6 - Template rendering (transitive)

## Configuration

**Environment:**
- API keys managed via session state in Streamlit UI (`st.session_state['api_key']`)
- No .env file detected in root (API keys entered via UI)
- Configuration via text files: `system_prompt.txt`, `main_prompt_task1.txt`, `main_prompt_task2.txt`

**Build:**
- No build configuration (Python interpreted)
- requirements.txt at `/Users/kavinda/Github/langchain_test_barekind/requirements.txt`
- Devcontainer config at `/Users/kavinda/Github/langchain_test_barekind/.devcontainer/devcontainer.json`

## Platform Requirements

**Development:**
- Python 3.11+
- VS Code with Python extensions (ms-python.python, ms-python.vscode-pylance)
- Docker/Dev Containers support (devcontainer.json present)
- Port 8501 for Streamlit server

**Production:**
- Streamlit Cloud or similar Python hosting
- Access to OpenAI API (requires API key)
- Runs via: `streamlit run app.py --server.enableCORS false --server.enableXsrfProtection false`

---

*Stack analysis: 2026-01-22*
