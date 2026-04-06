# Rates-Theory

## Project Overview
Rates-Theory is a fixed-income analytics app that turns chapter-level concepts from *Fixed Income Relative Value Analysis* into interactive workflows. The project is designed to:
- Parse and organize chapter content from a source PDF.
- Generate reusable chapter summaries for app features.
- Expose quantitative model modules in a Streamlit interface.

### Chapter-to-Feature Mapping
| Chapter | Core topic | App feature |
|---|---|---|
| Chapter 1 | Relative-value foundations and cash-and-carry | Financed fair-futures and basis-direction lab |
| Chapter 2 | OU mean reversion | Half-life and first-passage simulation lab |
| Chapter 3 | PCA factor extraction | Explained-variance and loading diagnostics |
| Chapter 4 | Factor interpretation and regime mapping | Regime scoring, labels, and confidence gating |
| Chapter 5 | Duration-convexity diagnostics | Shock-to-price approximation and fair-value panel |
| Chapter 6 | Multi-curve construction | OIS/IBOR discount-forward and basis diagnostics |

> Update this table as your parser indexes exact chapter titles and page spans.

## Installation
1. Create and activate a virtual environment (recommended).
2. Install project dependencies:

```bash
pip install -r requirements.txt
```

## Data and PDF Location
Place the source book/PDF at:

```text
data/Fixed Income Relative Value Analysis.pdf
```

If the file currently lives in the repository root, move it into `data/` before running parsing/summarization steps.

## Curated Chapter Data (Primary Source)
The Streamlit app now reads chapter content from:

```text
data/chapters.json
```

This file is keyed by `"1"` through `"18"` and each chapter includes:
- `title`
- `learning_objective`
- `summary`
- `quotes`
- `market_objects`
- `equations`
- `derivation_steps`
- `failure_modes`
- `prerequisites`
- `exports_to_next_chapter`

## Generate Chapter Summaries (Optional Helper Metadata)
Parser/summarizer output is optional helper metadata and should be written to:

```text
data/chapter_summaries.json
```

### Chapter Summary JSON Schema Contract (v1.0)
All chapter summaries are persisted in a **single canonical schema** so the parser and Streamlit UI use the same contract.

```json
{
  "schema_version": "1.0",
  "chapters": [
    {
      "key": "1",
      "title": "Chapter 1",
      "summary": "Short chapter summary text.",
      "quotes": ["Optional quote 1", "Optional quote 2"]
    }
  ]
}
```

Field rules:
- `schema_version` *(string, required)*: must be `"1.0"`.
- `chapters` *(array, required)*: list of chapter objects.
- `chapters[].key` *(string, required)*: chapter key used by the UI selector (for example `"1"` or `"final"`).
- `chapters[].title` *(string, required)*: display title.
- `chapters[].summary` *(string, required)*: compact prose summary.
- `chapters[].quotes` *(array[string], required)*: key quote/excerpt list (duplicates/empty values removed at load/save time).

Implementation note:
- `BookParser.save_summaries_json()` transforms parser-native fields (`chapter_number`, `summary_sentences`, `quote_candidates`) into this canonical contract.
- Parser summaries are merged into chapter records as optional helper metadata and are not the sole source for equations or derivations.

Example invocation (adjust to your parser entrypoint):

```bash
python -m parser.generate_chapter_summaries \
  --input "data/Fixed Income Relative Value Analysis.pdf" \
  --output data/chapter_summaries.json
```

## Launch the Streamlit App
```bash
streamlit run streamlit_app/app.py
```

## Model Modules (Chapter 1–6 implementation map)
| Module | Purpose | Used in |
|---|---|---|
| `src/models/cash_carry.py` | Computes financed fair futures, basis, and direction for cash-and-carry decisions. | Chapter 1 |
| `src/models/mean_reversion.py` | Simulates OU paths and computes risk-adjusted convergence diagnostics. | Chapter 2 |
| `src/models/pca_module.py` | Runs covariance eigendecomposition and factor loading extraction. | Chapter 3 |
| `src/chapters/ch04_factor_regime_mapping.py` | Converts factors into regime score/label/confidence outputs for gating. | Chapter 4 |
| `src/models/risk_diagnostics.py` | Applies duration-convexity shock approximation and fair-price estimation. | Chapter 5 |
| `src/chapters/ch06_multi_curve_construction.py` | Builds simple OIS discount / IBOR projection diagnostics and basis outputs. | Chapter 6 |
