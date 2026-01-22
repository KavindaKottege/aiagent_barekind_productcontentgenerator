# Coding Conventions

**Analysis Date:** 2026-01-22

## Naming Patterns

**Files:**
- Python scripts use lowercase with underscores: `Agent.py` (though capitalized), `app.py`
- Uppercase for constants in filenames: `Agent copy.py`
- Configuration/data files use lowercase: `requirements.txt`, `test_data.xlsx`

**Functions:**
- snake_case for all function names: `create_image_content()`, `invoke_agent()`, `auto_review_product()`
- Descriptive, action-oriented names: `get_image_urls()`, `update_live_stats_ui()`, `process_single_product()`

**Variables:**
- snake_case for local variables: `product_name`, `image_urls_str`, `char_count`
- UPPER_SNAKE_CASE for module-level constants: `TITLE_CHAR_MIN`, `INPUT_TOKEN_COST`, `DEFAULT_TASK1_PROMPT`
- Descriptive names with type hints in context: `total_in_tokens`, `had_retries`, `review_statuses`

**Types:**
- No custom classes defined in codebase
- Type hints not used extensively (Python 3.11 runtime without explicit typing)

## Code Style

**Formatting:**
- No formatter config detected (.prettierrc, .black.toml not present)
- 4-space indentation (standard Python)
- Line length varies (no enforced limit, some lines in app.py exceed 150 characters)

**Linting:**
- No linter config detected (.eslintrc, .flake8, .pylintrc not present)
- No automated code quality enforcement

## Import Organization

**Order:**
1. Standard library imports (grouped at top)
2. Third-party packages (streamlit, pandas, langchain)
3. Relative/local imports (not used)

**Pattern in `app.py`:**
```python
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import time
import openpyxl
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from io import BytesIO
```

**Pattern in `Agent.py`:**
```python
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from tqdm import tqdm
```

**Path Aliases:**
- Not used (no complex package structure)

## Error Handling

**Patterns:**
- Try-except blocks for external API calls and image processing
- Graceful fallback: if image download fails, retry without images
- JSON parsing with JSONDecodeError handling in `auto_review_product()` in `app.py`
- Exception messages include context: `f"Error during review: {str(e)}"`

**Example from `app.py`:**
```python
try:
    response = llm.invoke(messages)
    image_status = "success" if images_used > 0 else ("no_images" if total_available == 0 else "skipped")
except Exception as e:
    error_str = str(e).lower()
    if include_images and ('image' in error_str or 'timeout' in error_str or 'download' in error_str):
        result = invoke_agent(llm, row, task_prompt, system_prompt, general_info, include_images=False)
        # Update image info to show failure
        result_list = list(result)
        result_list[4] = {'available': total_available, 'used': 0, 'status': 'failed'}
        return tuple(result_list)
    raise
```

## Logging

**Framework:** Console output via `tqdm.write()` and `print()`

**Patterns:**
- Progress bars for batch operations: `tqdm(product_data.iterrows(), total=len(product_data))`
- Structured console output with visual separators: `print(f"\n{'='*60}")`
- Detailed per-product logging in `Agent.py`:
  ```python
  tqdm.write(f"\n[{idx + 1}/{len(product_data)}] Processing: {product_name}")
  tqdm.write("  ├─ Generating product title...")
  tqdm.write(f"  │  Tokens: {in_tok} in / {out_tok} out | Cost: ${cost:.4f}")
  ```
- No logging framework (logging, loguru) used
- Streamlit uses `st.markdown()`, `st.success()`, `st.error()` for UI feedback

## Comments

**When to Comment:**
- Section headers in large files (e.g., `# =============================================================================`)
- Complex logic explanations (e.g., `# Clean quotation marks from title`)
- Function purposes via docstrings (sparse usage)

**Docstrings:**
- Used inconsistently
- Present in complex functions like `invoke_agent()` and `process_single_product()`
- Format: Multi-line strings with Args/Returns sections:
  ```python
  def invoke_agent(llm, row, task_prompt, system_prompt, general_info, include_images=True):
      """Invoke the agent with text and images. Retries without images if image download fails.

      Returns: (content, input_tokens, output_tokens, cost, image_info)
      where image_info is a dict with 'available', 'used', and 'status' keys.
      """
  ```

**Inline Comments:**
- Used to explain data transformations: `# Replace newlines with spaces, then split by space`
- Used for tracking state: `# Track token usage`

## Function Design

**Size:**
- Functions range from 5 lines (`get_image_urls()`) to 150+ lines (`process_single_product()`, `run_generation()`)
- Main UI function `main()` in `app.py` is 1200+ lines
- No enforced size limit

**Parameters:**
- Functions with many parameters use descriptive names
- Complex functions accept dictionaries for grouped data: `general_info`, `char_limits`, `ui_containers`
- Optional parameters with defaults: `include_images=True`, `start_index=0`

**Return Values:**
- Single values or tuples for multiple returns: `return response.content, input_tokens, output_tokens, cost, image_info`
- No named tuples or dataclasses used
- Functions return status dicts: `{'available': total_available, 'used': images_used, 'status': image_status}`

## Module Design

**Exports:**
- No explicit `__all__` declarations
- Functions defined at module level in `app.py` and `Agent.py`
- No class-based organization

**Barrel Files:**
- Not used (single-file modules)

## Session State Management (Streamlit-specific)

**Pattern:**
- Check before access: `if 'key' not in st.session_state:`
- Initialize with defaults: `st.session_state['gen_results'] = []`
- Get with fallback: `st.session_state.get('gen_start_time', time.time())`
- Direct assignment for updates: `st.session_state['gen_total_cost'] = value`

**Example:**
```python
if 'review_data' not in st.session_state:
    st.session_state['review_data'] = None
if 'review_statuses' not in st.session_state:
    st.session_state['review_statuses'] = {}
```

## String Formatting

**Patterns:**
- f-strings for all string interpolation: `f"Processing: {product_name}"`
- Multi-line f-strings for complex content:
  ```python
  text_content = f"""Input English Language to be used: {language}
  Brand Name: {brand_name}
  Product Name: {row['Product Name']}"""
  ```
- String methods for cleaning: `.strip().strip('"').strip("'")`

## Data Handling

**Patterns:**
- pandas DataFrames for tabular data: `pd.read_excel()`, `pd.DataFrame()`
- Dictionary comprehensions for transformations: `dict(zip(general_data[0], general_data[1]))`
- Null checking with pandas: `if pd.isna(image_urls_str) or not image_urls_str:`
- List comprehensions for filtering: `[url.strip() for url in text.split() if url.strip().startswith("http")]`

---

*Convention analysis: 2026-01-22*
