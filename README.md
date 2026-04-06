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
| 13 | Detailed implementation | Pure-credit extraction with liquidity/technical stripping and recovery-sensitive hazard proxy exports (`PureCreditState`). |
| 14 | Detailed implementation | Intra-currency basis edge decomposition, execution-confidence mapping, and deploy/no-deploy signaling (`ICBSState`). |
| 15 | Detailed implementation | Cross-currency basis carry + convergence package economics with expected total P&L exports (`CCBSState`). |
| 16 | Deep integrated study module | Multi-space signal normalization + dependency-graph shock propagation into a shared integrated state (`IntegratedRVState`). |
| 17 | Deep integrated study module | Global dual-ranking RV screen (curve + SOFR-ASW), disagreement diagnostics, attribution buckets, and stress-envelope handoff (`GlobalRVScreenState`). |
| 18 | Detailed implementation | Capital-shadow-cost approval gate with monetisable/non-monetisable blockers and governance-ready final state (`ShadowCostState`). |

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

## Chapters 13–18: True Late-Chapter Topics, Core Equations, and Export Contracts

| Chapter | True topic | Key equations | Exported structured state |
|---|---|---|---|
| 13 — CDS pure-credit extraction | Remove non-default contamination from observed CDS and infer a recovery-aware default-risk proxy. | `purified_credit_spread_bp = observed_spread_bp - liquidity_component_bp - technical_component_bp`<br>`hazard_proxy = purified_credit_spread_bp / (10000*(1-recovery_rate))` | `schema_name="PureCreditState"` with `signals=["observed_spread_bp", "purified_credit_spread_bp", "hazard_proxy", "recovery_sensitivity"]`. |
| 14 — Intra-currency basis swaps | Evaluate tenor-basis dislocations net of implementation drag and convert edge into execution confidence. | `basis_edge_bp = observed_basis_bp - fair_basis_bp - implementation_cost_bp`<br>`execution_confidence = min(1,max(0,basis_edge_bp/entry_hurdle_bp))` | `schema_name="ICBSState"` with `signals=["net_edge_bp", "execution_confidence", "execute_flag"]`. |
| 15 — Cross-currency basis swaps | Convert basis dislocation into carry-plus-convergence package economics. | `carry_pnl = notional*(annualized_basis_carry_bp/10000)*horizon_years`<br>`expected_total_pnl = carry_pnl + convergence_pnl - hedging_costs` | `schema_name="CCBSState"` with `signals=["carry_pnl", "convergence_pnl", "expected_total_pnl"]`. |
| 16 — Integrated asset-basis-CDS | Normalize bond/ASW/basis/CDS signals into common space and evaluate agreement + propagated shocks. | `normalized_signal_i_bp = transformed_signal_i_bp - sofr_anchor_bp`<br>`agreement_ratio = (count same-sign as mean)/(total signals)`<br>`shocked_signal_j = baseline_signal_j + shock_bp*beta(shocked_input,j)` | `schema_name="IntegratedRVState"` with `signals=["common_space_normalization.normalized_signals_bp", "agreement_divergence_diagnostics", "shock_propagation_results"]`. |
| 17 — Global bond RV | Run fitted-curve and SOFR-ASW residual rankings, diagnose disagreement, and project stress envelope. | `curve_residual_i^{bp} = 100*(y_i^{obs}-y_i^{fit})`<br>`rank_gap_i = |rank_i^{curve}-rank_i^{sofr_asw}|`<br>`total_stress_pnl = -(spread_shock_bp*portfolio_cs01+rate_shock_bp*residual_dv01)-liquidity_haircut` | `schema_name="GlobalRVScreenState"` with `signals=["curve_ranking", "sofr_asw_ranking", "disagreement_diagnostics", "attribution_buckets_bp", "portfolio_selection_signals", "rv_spread_pnl", "total_stress_pnl"]`. |
| 18 — Capital shadow costs | Convert monetisable and governance frictions into an executable residual and final approval gate. | `spread_gap_bp = observed_spread_bp - structural_fair_spread_bp`<br>`capital_charge_bp = (capital_used*capital_hurdle)/spread_bp_value_$perbp`<br>`adj_residual_bp = spread_gap_bp - shadow_funding_cost_bp - capital_charge_bp - liquidity_wedge_bp - repo_stress_add_on_bp` | `schema_name="ShadowCostState"` with `signals=["structural_fair_spread_bp", "observed_spread_bp", "shadow_funding_cost_bp", "capital_charge_bp", "liquidity_wedge_bp", "repo_stress_add_on_bp", "adjusted_executable_spread_residual_bp", "approval_gate"]`. |

## Why Chapters 16 and 17 Are Deep Integrated Study Modules

- **Chapter 16 is the integration bridge**: it unifies local-space signals from prior chapters (bond, asset-swap, intra/cross-basis, CDS) into a common SOFR-anchored frame, then applies dependency-graph shock propagation to expose cross-leg sensitivities before portfolio ranking.
- **Chapter 17 is the portfolio-scale integrator**: it lifts Chapter 16-style cross-space thinking into a multi-bond universe using two ranking systems (fitted-curve and SOFR-ASW), explicitly quantifies disagreement, and exports attribution + stress fields needed for Chapter 18 capital-aware approval.
- Together, **16 → 17 behaves as a two-stage lab**: (1) node-level integration and shock mechanics, then (2) universe-level ranking, attribution, and stress translation for final governance decisions.

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

Run tranche-3 contract checks (late-chapter integration and handoff coverage):

```bash
pytest tests/test_deterministic_system_contracts.py
pytest tests/test_chapter_registry_validation.py
pytest tests/test_chapters_7_12_workflows.py
```

Keep tranche-1 schema/parser + foundational model checks as fast smoke tests:

```bash
pytest tests/test_chapter_summary_schema.py
pytest tests/test_pdf_parser.py
pytest tests/test_chapters_1_6_contracts.py
```

### What each test group validates
- `tests/test_deterministic_system_contracts.py`
  - End-to-end deterministic contract checks across chapter registry wiring, app import behavior, and core model output shape/invariants.
- `tests/test_chapter_registry_validation.py`
  - Chapter dependency integrity and required export-key compatibility between adjacent chapters, including late-chapter state handoff validation through registry dependencies.
- `tests/test_chapters_7_12_workflows.py`
  - Mid-to-late pipeline deterministic workflow checks for curve/risk/funding primitives reused by Chapter 13+ integrations.
- `tests/test_chapter_summary_schema.py`
  - Canonical chapter summary schema validation, normalization, and error handling.
- `tests/test_pdf_parser.py`
  - PDF parser extraction behavior and summary JSON generation pathways.
- `tests/test_chapters_1_6_contracts.py`
  - Foundational contract checks for early chapter math/model invariants that upstream late-chapter modules still depend on.
