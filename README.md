# Rates-Theory

## Project Purpose
Rates-Theory is a **chapter-driven learning platform** for Chapters **1–18** of *Fixed Income Relative Value Analysis*. The app combines:
- chapter metadata and summaries,
- contract-based chapter modules,
- reusable rates models,
- and a Streamlit UI for guided, chapter-by-chapter exploration.

The primary goal is to let learners move through fixed-income relative value concepts in sequence, while inspecting structured outputs at each chapter boundary.

## Repository Layout (Current)

```text
streamlit_app/
  app.py

src/
  __init__.py
  chapter_summary_schema.py
  cli.py
  pdf_parser.py
  chapters/
    base.py
    registry.py
    ch01_relative_value.py
    ...
    ch18_shadow_costs.py
  models/
    __init__.py
    asset_swaps.py
    cash_carry.py
    ccbs.py
    cds.py
    curve_representation.py
    fitted_curves.py
    futures.py
    icbs.py
    integrated_rv.py
    mean_reversion.py
    mvou.py
    options.py
    ou.py
    pca.py
    pca_module.py
    reference_rates.py
    risk_diagnostics.py
    risk_measures.py
    shadow_costs.py
    swap_spreads.py
    yield_curve.py
  ui/
    components.py
    diagnostics_panel.py
    derivation_panel.py
    equation_cards.py
    quiz_panel.py

data/
  Fixed Income Relative Value Analysis.pdf
  chapter_summaries.json
  chapters.json
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

## Chapter Implementation Matrix (Chapters 1–18)

| Chapter(s) | Status | Notes |
|---|---|---|
| 1–18 | Implemented | All chapters are wired in `build_chapter_registry()` and validated by dependency/export contract checks. |
| 4, 6, 8, 9 | Refactored scaffold pattern | These chapters use the `SimpleChapter` contract for deterministic baseline behavior while preserving full registry participation and export contracts. |
| 7, 10, 11, 12 | Tranche-2 detailed implementations | These chapters expose chapter-specific equations, deterministic labs, and explicit structured state exports consumed downstream. |

## Chapters 7–12: Core Relation + Exported Structured State

| Chapter | Core relation | Exported structured state |
|---|---|---|
| 7 — Risk governance | `utilization = proposed_risk / approved_limit` drives governance status (`green/amber/red`) and approval routing. | `signals=["utilization", "status", "approved"]` used to gate progression into implementation screens. |
| 8 — Relative-value screens | Deterministic screen relation is represented by the shared `Inputs → Model → Diagnostics → Decision` pipeline from `SimpleChapter`. | `schema_name="RiskMetricState"` with `signals=["scenario_value"]` for downstream trade construction. |
| 9 — Trade construction | Deterministic construction relation inherits the same `SimpleChapter` scenario mapping for reproducible sizing inputs. | `schema_name="RiskMetricState"` with `signals=["scenario_value"]` feeding funding-basis attribution. |
| 10 — Funding basis | `basis_bp = (swap_float - cash_funding - hedge_cost) * 100` and `fair_adj_bp = fair_raw_bp + basis_bp` bridge derivatives and cash funding assumptions. | `signals=["funding_basis_bp", "adjusted_fair_spread_bp", "net_carry_bp"]` for benchmark transition and carry alignment. |
| 11 — Reference-rate transition | `fallback_bp = (legacy_fixing - rfr_compounded) * 100` quantifies fallback economics and all-in reset coupon impact. | `schema_name="ReferenceRateState"` with `signals=["fallback_spread_bp", "all_in_coupon_pct", "coupon_vs_legacy_bp"]`. |
| 12 — Asset-swap decomposition | `asset_swap_spread_bp = z_spread_bp - (bond_coupon - swap_rate) * 100`, then funding drag isolates package carry. | `schema_name="AssetSwapState"` with `signals=["asset_swap_spread_bp", "package_carry_bp", "coupon_mismatch_bp"]` for pure-credit extraction. |

## Model Modules Feeding Chapters 10–13

- `src/models/futures.py`
  - Futures-versus-cash carry transformations used for pre-funding normalization in trade construction workflows (Chapters 9–10).
- `src/models/fitted_curves.py`
  - Parametric curve-fit and residual extraction utilities used to separate curve shape from spread/funding effects before basis and credit decomposition (Chapters 10–12).
- `src/models/reference_rates.py`
  - Legacy-vs-RFR transition helpers for fallback spread and all-in coupon state propagation into package analytics (Chapters 11–12).
- `src/models/asset_swaps.py` (updated)
  - Canonical decomposition entry point returning `(coupon_mismatch_bp, asset_swap_spread_bp, package_carry_bp)` and feeding clean spread inputs into Chapter 13 pure-credit extraction.

## Data and Chapter Assets
Place the source book/PDF at:

```text
data/Fixed Income Relative Value Analysis.pdf
```

Generate chapter summary artifacts to:

Implementation note:
- `BookParser.save_summaries_json()` transforms parser-native fields (`chapter_number`, `summary_sentences`, `quote_candidates`) into this canonical contract.
- Parser summaries are merged into chapter records as optional helper metadata and are not the sole source for equations or derivations.

## Testing
Run the full test suite:

```bash
pytest
```

Run tranche-2 contract checks (chapters 7–12 and integrated deterministic pathways):

```bash
pytest tests/test_deterministic_system_contracts.py
pytest tests/test_chapter_registry_validation.py
```

Keep tranche-1 schema/parser checks as fast smoke tests:

```bash
pytest tests/test_chapter_summary_schema.py
pytest tests/test_pdf_parser.py
```

### What each test group validates
- `tests/test_deterministic_system_contracts.py`
  - End-to-end deterministic contract checks across chapter registry wiring, app import behavior, and core model output shape/invariants.
- `tests/test_chapter_registry_validation.py`
  - Chapter dependency integrity and required export-key compatibility between adjacent chapters.
- `tests/test_chapter_summary_schema.py`
  - Canonical chapter summary schema validation, normalization, and error handling.
- `tests/test_pdf_parser.py`
  - PDF parser extraction behavior and summary JSON generation pathways.
