# Rates-Theory

## Project Purpose
Rates-Theory is a **chapter-driven learning platform** for Chapters **1–18** of *Fixed Income Relative Value Analysis*. The app combines:
- chapter metadata and summaries,
- contract-based chapter modules,
- reusable rates models,
- and a Streamlit UI for guided, chapter-by-chapter exploration.

The primary goal is to let learners move through fixed-income relative value concepts in sequence, while inspecting structured outputs at each chapter boundary.

## Repository Layout (Current)

> Note: chapter implementation modules currently live in top-level `chapters/`. The `src/chapters/` and `src/ui/` paths below are documented as target/organizational paths and are currently scaffold scope.

```text
streamlit_app/
  app.py

src/
  __init__.py
  chapter_summary_schema.py
  cli.py
  pdf_parser.py
  models/
    __init__.py
    cash_carry.py
    mean_reversion.py
    mvou.py
    options.py
    pca_module.py
    risk_diagnostics.py
    swap_spreads.py
    yield_curve.py

src/chapters/
  (scaffold scope; active chapter modules currently live in /chapters)

src/ui/
  (scaffold scope; Streamlit entrypoint currently in /streamlit_app/app.py)

data/
  Fixed Income Relative Value Analysis.pdf
  chapter_summaries.json
  chapters.json (chapter metadata path expected by project docs/workflow)
```

## Running the App
Install dependencies:

```bash
pip install -r requirements.txt
```

Run the Streamlit app:

```bash
streamlit run streamlit_app/app.py
```

Chapter metadata loading path (project convention):

```text
data/chapters.json
```

Current chapter summary/schema loader in app runtime:

```text
data/chapter_summaries.json
```

## Chapter Implementation Matrix (Chapters 1–18)

| Chapter(s) | Status | Notes |
|---|---|---|
| 1, 2, 3, 5, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18 | Fully implemented | Registered in chapter registry and backed by concrete chapter modules. |
| 4, 6, 7, 10 | Scaffolded (scoped) | Explicitly in scope as scaffold chapters; currently resolved via placeholder/not-implemented behavior in registry lookup path. |

## Data and Chapter Assets
Place the source book/PDF at:

```text
data/Fixed Income Relative Value Analysis.pdf
```

Generate chapter summary artifacts to:

```text
data/chapter_summaries.json
```

## Testing
Run the full test suite:

```bash
pytest
```

Or run grouped checks explicitly:

```bash
pytest tests/test_chapter_summary_schema.py
pytest tests/test_chapter_registry_validation.py
pytest tests/test_pdf_parser.py
```

### What each test group validates
- `tests/test_chapter_summary_schema.py`
  - Canonical chapter summary schema validation, normalization, and error handling.
- `tests/test_chapter_registry_validation.py`
  - Chapter registry integrity and dependency/export contract validation.
- `tests/test_pdf_parser.py`
  - PDF parser extraction behavior and summary JSON generation pathways.
