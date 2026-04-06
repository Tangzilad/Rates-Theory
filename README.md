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

