# Testing Patterns

**Analysis Date:** 2026-01-22

## Test Framework

**Runner:**
- None detected
- No test framework config files found (jest.config, vitest.config, pytest.ini)

**Assertion Library:**
- Not applicable

**Run Commands:**
```bash
# No test commands available
# Testing infrastructure not set up
```

## Test File Organization

**Location:**
- No test files detected (no `*.test.py`, `*.spec.py`, `test_*.py` files)

**Naming:**
- Not applicable (no test files)

**Structure:**
- No tests directory

## Test Structure

**Suite Organization:**
- Not implemented

**Patterns:**
- No testing patterns established

## Mocking

**Framework:** Not used

**Patterns:**
- No mocking infrastructure

**What to Mock:**
- If testing were implemented, candidates for mocking:
  - `ChatOpenAI` LLM API calls (expensive and external)
  - `st.session_state` (Streamlit state management)
  - File I/O operations (`pd.read_excel()`)
  - Image URL fetching

**What NOT to Mock:**
- Pure functions like `get_image_urls()`, `create_prompt_content()`
- String manipulation logic
- Character count validations

## Fixtures and Factories

**Test Data:**
- Production test data exists: `test_data.xlsx` (used for manual testing via UI)
- No test fixtures or factory functions

**Location:**
- Manual test data in project root: `/Users/kavinda/Github/langchain_test_barekind/test_data.xlsx`

## Coverage

**Requirements:** None enforced

**View Coverage:**
```bash
# No coverage tooling configured
```

## Test Types

**Unit Tests:**
- Not implemented
- Would benefit from unit tests for:
  - `get_image_urls()` in `app.py`
  - `create_prompt_content()` in `app.py` and `Agent.py`
  - `invoke_retry()` logic
  - Character limit validation

**Integration Tests:**
- Not implemented
- Would benefit from integration tests for:
  - Full product processing pipeline (`process_single_product()`)
  - LLM invocation with retry logic
  - Excel data loading and parsing

**E2E Tests:**
- Not implemented
- Streamlit UI testing not configured

## Manual Testing

**Approach:**
- "Use Test Data" button in UI loads `test_data.xlsx` for manual testing
- Located in `app.py` lines 1464-1479:
  ```python
  if st.button("🧪 Use Test Data", help="Load sample data for demo purposes", type="secondary"):
      try:
          import os
          test_file_path = os.path.join(os.path.dirname(__file__), 'test_data.xlsx')
          product_data = pd.read_excel(test_file_path, sheet_name="Products", engine='openpyxl')
          general_data = pd.read_excel(test_file_path, sheet_name="General Details", header=None, engine='openpyxl')
  ```

**Test Data Files:**
- `test_data.xlsx` - Sample product data with Products and General Details sheets
- `main_prompt_task1.txt` - Test prompt for title generation
- `main_prompt_task2.txt` - Test prompt for description generation
- `system_prompt.txt` - System prompt for testing

## Common Patterns

**Error Testing:**
- No automated error testing
- Production code includes error handling but no tests verify it works

**Async Testing:**
- Not applicable (no async code)

## Recommendations for Testing

**High Priority:**
1. Add pytest as test framework
2. Create unit tests for utility functions:
   - `get_image_urls()` - parse image URL strings
   - `create_prompt_content()` - format prompts correctly
   - Character limit validation logic
3. Mock LLM API calls to avoid costs during testing
4. Test error handling paths (image download failures, API errors)

**Medium Priority:**
1. Integration tests for `process_single_product()` workflow
2. Test session state management functions
3. Validate Excel parsing with fixture files

**Low Priority:**
1. Streamlit UI component testing
2. End-to-end tests with test data
3. Performance/load testing for batch processing

**Suggested Test Structure:**
```
tests/
├── unit/
│   ├── test_image_parsing.py
│   ├── test_prompt_formatting.py
│   └── test_character_limits.py
├── integration/
│   ├── test_product_processing.py
│   └── test_data_loading.py
└── fixtures/
    ├── sample_products.xlsx
    └── mock_responses.json
```

---

*Testing analysis: 2026-01-22*
