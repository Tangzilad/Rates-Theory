# Comprehensive Code Review (2026-04-06)

## Scope and method
- Ran full and targeted test suites to surface contract/integration failures.
- Traced each failure to concrete module-level causes.
- Cross-checked chapter dependency metadata against actual chapter export contracts.

## Executive summary
The repository currently has **blocking integration regressions** that prevent a clean test run and break app importability. The highest-risk issues are:
1. Missing public API in Chapter 9 (`compose_gov_bond_trade_blueprint`) required by tests/integrations.
2. Infinite recursion in Chapter 1 compatibility aliases, causing `RecursionError` during Streamlit app import.
3. Widespread chapter dependency metadata drift (`CHAPTER_DEPENDENCIES`) vs actual chapter export signals, creating systemic contract validation failures.
4. `data/chapters.json` schema content drift for early chapters relative to enforced tests/contracts.

## Findings

### 1) Missing Chapter 9 composition API (blocking)
**Severity:** High (test collection blocker)

- `tests/test_chapters_7_12_workflows.py` imports `compose_gov_bond_trade_blueprint` from `src.chapters.ch09_trade_construction`.
- `src/chapters/ch09_trade_construction.py` currently exposes `Chapter09` and imported types, but has no `compose_gov_bond_trade_blueprint` function.
- Result: `ImportError` during pytest collection, which blocks the remainder of the suite.

**Evidence:**
- Test import expectation: `tests/test_chapters_7_12_workflows.py` lines 9-13.
- Missing implementation in `src/chapters/ch09_trade_construction.py` (module contains class implementation only).

**Recommendation:**
- Add a stable, module-level `compose_gov_bond_trade_blueprint(payload: Mapping[str, Any]) -> GovBondTradeBlueprint` helper (or update tests/contracts consistently).
- If the blueprint schema changed, provide an adapter for backward compatibility and deprecate old fields explicitly.

### 2) Infinite recursion in Chapter 1 method aliases (blocking runtime)
**Severity:** Critical (runtime crash)

- `ChapterBase.failure_modes_model_risk()` delegates to `self.failure_modes()`.
- `Chapter01.failure_modes()` delegates back to `self.failure_modes_model_risk()`.
- This creates an immediate recursion loop and raises `RecursionError` when the app renders contract sections.

**Evidence:**
- Base delegation: `src/chapters/base.py` line 79.
- Recursive alias in Chapter 1: `src/chapters/ch01_relative_value.py` line 213.
- Duplicate `assessment` alias has the same loop pattern at line 216 (`checkpoint()` -> `assessment()`).

**Recommendation:**
- Remove circular aliasing in `Chapter01`; keep one canonical implementation for `failure_modes` and `assessment`.
- If backward compatibility is needed, aliases must point to a non-aliased concrete helper method.

### 3) Dependency metadata drift vs chapter export contracts
**Severity:** High (system-wide contract validation failures)

- `CHAPTER_DEPENDENCIES` requires signals absent from provider chapter exports in multiple places.
- This causes repeated failures in dependency validation tests and undermines chapter wiring confidence.

**Observed mismatches:**
- `5 <= 4`: missing `regime_label`, `regime_score`.
- `6 <= 5`: missing `curve_slope_bp`, `fair_price`.
- `8 <= 7`: missing `approved`.
- `9 <= 8`: missing `curve_fit_residual_bp`, `residual_zscore`, `screen_signal`.
- `14 <= 13`: missing `pure_credit_bp`.
- `17 <= 16`: missing `realized_residual_dv01`.

**Evidence:**
- Dependency declarations: `src/chapters/registry.py` lines 29-53.
- Example provider exports lacking required keys:
  - Chapter 4 exports list: `src/chapters/ch04_multivariate_mean_reversion.py` lines 245-253.
  - Chapter 5 exports list: `src/chapters/ch05_duration_convexity.py` lines 200-206.
  - Chapter 7 exports list: `src/chapters/ch07_risk_governance.py` lines 220-226.

**Recommendation:**
- Choose one source of truth (dependency map or chapter export contracts) and reconcile all chapter interfaces in one pass.
- Add a CI gate that programmatically asserts dependency keys are subset of provider exports.

### 4) JSON chapter summary contract drift (chapters 1-6)
**Severity:** Medium (schema/content contract failure)

- Tests assert fixed `exports_to_next_chapter` arrays for chapters 1-6.
- `data/chapters.json` currently contains different export arrays (notably chapter 1 includes `fair_value`, `market_value`, etc. instead of expected basis/arbitrage fields).

**Evidence:**
- Data payload: `data/chapters.json` chapter objects.
- Assertion source: `tests/test_chapters_1_6_contracts.py` expected map in `test_chapters_json_chapters_1_to_6_required_content_and_export_alignment`.

**Recommendation:**
- Align `data/chapters.json` with the intended external contract or update tests/spec docs if the contract intentionally changed.
- Version the schema/contracts to avoid silent drift.

## Reproduction commands
- `pytest -q`
- `pytest -q tests/test_chapters_1_6_contracts.py tests/test_chapters_13_18_dependency_exports.py tests/test_chapter_registry_validation.py tests/test_ch14_icbs_calculations.py tests/test_ch15_ccbs_calculations.py tests/test_ch16_integrated_rv_consistency.py tests/test_ch17_global_ranking_logic.py tests/test_ch18_shadow_cost_adjustment.py tests/test_chapter_summary_schema.py tests/test_deterministic_system_contracts.py tests/test_pdf_parser.py`
- Contract drift probe script executed inline to compare dependency requirements with actual export signals.

## Suggested remediation order
1. Fix Chapter 1 recursion bug (unblocks app import/runtime).
2. Restore/implement Chapter 9 composition API expected by tests.
3. Reconcile `CHAPTER_DEPENDENCIES` with `exports_to_next_chapter` for all chapters.
4. Resolve `data/chapters.json` contract drift and lock schema versioning.
