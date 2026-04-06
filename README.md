# Rates-Theory

## Project Overview
Rates-Theory is a fixed-income analytics app that turns chapter-level concepts from *Fixed Income Relative Value Analysis* into interactive workflows. The project is designed to:
- Parse and organize chapter content from a source PDF.
- Generate reusable chapter summaries for app features.
- Expose quantitative model modules in a Streamlit interface.

### Chapter-to-Feature Mapping
| Chapter | Core topic (example) | App feature |
|---|---|---|
| Chapter 1 | Relative value foundations | Overview dashboard and terminology glossary |
| Chapter 2 | Curve structure and carry | Curve analytics panel and carry/roll-down views |
| Chapter 3 | Risk decomposition | Duration, DV01, and key-rate risk explorer |
| Chapter 4 | Spread/value signals | Spread monitor and ranking views |
| Chapter 5 | Statistical relative value | Signal generation and z-score diagnostics |
| Chapter 6 | Portfolio construction | Position sizing and portfolio what-if tools |

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

## Generate Chapter Summaries
Run your parser/summarizer step to create:

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
- `load_chapter_summaries()` validates the same schema and provides graceful fallback messages for malformed JSON.

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

## Model Modules (and chapter/page usage)
Use this as a reference map for model files. Replace page ranges with parsed metadata once available.

| Module | Purpose | Chapters/pages used |
|---|---|---|
| `models/duration_model.py` | Computes Macaulay/modified duration and sensitivity metrics. | Chapters on interest-rate risk (e.g., Ch. 3, risk pages). |
| `models/curve_model.py` | Fits/parses term-structure views and carry/roll-down metrics. | Curve chapters (e.g., Ch. 2, term-structure pages). |
| `models/spread_model.py` | Builds spread signals and relative value comparisons. | Spread/value chapters (e.g., Ch. 4). |
| `models/stat_arb_model.py` | Runs z-score/mean-reversion style statistical screens. | Statistical RV chapters (e.g., Ch. 5). |
| `models/portfolio_model.py` | Position sizing, risk budgeting, and scenario aggregation. | Portfolio construction chapters (e.g., Ch. 6). |
