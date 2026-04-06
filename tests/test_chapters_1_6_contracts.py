from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from src.chapter_summary_schema import CHAPTER_REQUIRED_FIELDS, parse_chapters_map
from src.chapters.registry import CHAPTER_DEPENDENCIES, build_chapter_registry
from src.models.mvou import MVOUProcess
from src.models.ou import conditional_expectation, first_passage_time_approx, simulate_ou
from src.models.pca import factor_neutral_weights, run_pca
from src.models.risk_measures import (
    convexity,
    dv01,
    macaulay_duration,
    modified_duration,
    present_value,
    shock_adjusted_bond_state,
)
from src.models.yield_curve import (
    constant_maturity_interpolation,
    fit_nelson_siegel_svensson,
    nss_yield,
    rich_cheap_indicators,
)


def _export_signal_set(chapter_obj: object) -> set[str]:
    exports = chapter_obj.exports_to_next_chapter()
    if hasattr(exports, "model_dump"):
        exports = exports.model_dump()
    assert isinstance(exports, dict)
    assert isinstance(exports.get("usage", ""), str)
    signals = exports.get("signals")
    assert isinstance(signals, list)
    assert all(isinstance(sig, str) and sig for sig in signals)
    return set(signals)


def test_chapter_registry_contracts_for_chapters_1_to_6() -> None:
    registry = build_chapter_registry()
    assert list(registry.keys())[:6] == [str(i) for i in range(1, 7)]

    for key in map(str, range(1, 7)):
        chapter = registry[key]
        signal_set = _export_signal_set(chapter)

        dependency_requirements = CHAPTER_DEPENDENCIES.get(str(int(key) + 1), {}).get(key, [])
        assert set(dependency_requirements).issubset(signal_set)


def test_ou_conditional_expectation_term_structure_and_first_passage_fields() -> None:
    x_t = 2.0
    mu = 0.5
    theta = 0.7
    horizons = np.array([0.0, 0.25, 1.0, 2.0, 4.0])
    expectations = np.array([
        conditional_expectation(x_t=x_t, horizon=float(h), theta=theta, mu=mu) for h in horizons
    ])

    assert expectations[0] == x_t
    assert np.all(expectations[1:] < x_t)
    assert np.all(expectations[1:] > mu)
    assert np.all(np.diff(expectations) < 0)

    fpt_near = first_passage_time_approx(x0=0.2, level=0.0, theta=0.8, mu=0.0, sigma=0.3)
    fpt_far = first_passage_time_approx(x0=1.2, level=0.0, theta=0.8, mu=0.0, sigma=0.3)
    assert fpt_near < fpt_far

    paths = simulate_ou(
        x0=1.0,
        theta=1.0,
        mu=0.0,
        sigma=0.25,
        n_steps=252,
        n_paths=1000,
        dt=1.0 / 252.0,
        random_seed=123,
    )

    barrier = 0.8
    hit_mask = paths <= barrier
    first_hit_idx = np.argmax(hit_mask, axis=1)
    no_hit = ~hit_mask.any(axis=1)
    first_hit_idx[no_hit] = paths.shape[1]
    fpt_days = np.where(first_hit_idx < paths.shape[1], first_hit_idx, np.nan)

    hit_probability = float(np.nanmean(~np.isnan(fpt_days)))
    mean_fpt_days = float(np.nanmean(fpt_days)) if np.any(~np.isnan(fpt_days)) else None

    assert 0.0 < hit_probability <= 1.0
    assert mean_fpt_days is None or mean_fpt_days > 0.0


def test_pca_factor_scores_residualization_and_neutral_weights() -> None:
    rng = np.random.default_rng(9)
    x = rng.normal(size=(120, 5))
    x[:, 1] = 0.7 * x[:, 0] + 0.3 * x[:, 1]
    x[:, 2] = -0.2 * x[:, 0] + 0.6 * x[:, 2]

    result = run_pca(x)
    factor_scores = result.standardized_data @ result.eigenvectors

    assert factor_scores.shape == (120, 5)

    top_k = 2
    reconstruction_top = factor_scores[:, :top_k] @ result.eigenvectors[:, :top_k].T
    residual = result.standardized_data - reconstruction_top
    assert residual.shape == result.standardized_data.shape

    # Residuals should be orthogonal to the retained factor subspace.
    projection = residual @ result.eigenvectors[:, :top_k]
    assert np.all(np.abs(projection) < 1e-8)

    exposures = result.eigenvectors
    weights = factor_neutral_weights(exposures, target_notional=1.0, neutral_factors=(0, 1))
    assert weights.shape == (5,)
    assert np.isclose(np.sum(np.abs(weights)), 1.0, atol=1e-6)
    assert np.allclose(exposures[:, :2].T @ weights, 0.0, atol=1e-8)


def test_mvou_simulation_shapes_mean_reversion_and_covariance_effects() -> None:
    kappa_2d = np.array([[1.1, 0.0], [0.0, 0.8]])
    mu_2d = np.array([0.5, -0.25])
    cov_2d = np.array([[0.04, 0.0], [0.0, 0.09]])

    process_2d = MVOUProcess(kappa=kappa_2d, mu=mu_2d, covariance=cov_2d)
    paths_2d = process_2d.simulate(x0=np.array([2.0, -2.0]), n_steps=50, n_paths=128, random_seed=11)
    assert paths_2d.shape == (128, 51, 2)

    deterministic = MVOUProcess(
        kappa=np.diag([1.2, 1.0, 0.7]),
        mu=np.array([0.0, 0.5, -0.5]),
        covariance=np.diag([1e-14, 1e-14, 1e-14]),
    )
    paths_3d = deterministic.simulate(x0=np.array([2.0, -1.0, 1.5]), n_steps=80, n_paths=10, random_seed=1)
    assert paths_3d.shape == (10, 81, 3)

    terminal_mean = paths_3d[:, -1, :].mean(axis=0)
    initial_distance = np.linalg.norm(np.array([2.0, -1.0, 1.5]) - deterministic.mu)
    terminal_distance = np.linalg.norm(terminal_mean - deterministic.mu)
    assert terminal_distance < initial_distance

    high_corr_cov = np.array([[0.09, 0.08], [0.08, 0.09]])
    low_corr_cov = np.array([[0.09, 0.00], [0.00, 0.09]])
    corr_hi = MVOUProcess(kappa=kappa_2d, mu=np.zeros(2), covariance=high_corr_cov).simulate(
        x0=np.zeros(2), n_steps=120, n_paths=600, random_seed=2
    )[:, -1, :]
    corr_lo = MVOUProcess(kappa=kappa_2d, mu=np.zeros(2), covariance=low_corr_cov).simulate(
        x0=np.zeros(2), n_steps=120, n_paths=600, random_seed=2
    )[:, -1, :]

    terminal_corr_hi = np.corrcoef(corr_hi.T)[0, 1]
    terminal_corr_lo = np.corrcoef(corr_lo.T)[0, 1]
    assert terminal_corr_hi > terminal_corr_lo + 0.2


def test_risk_measures_duration_convexity_and_repricing_consistency() -> None:
    cashflows = np.array([2.0, 2.0, 2.0, 102.0])
    times = np.array([1.0, 2.0, 3.0, 4.0])
    ytm = 0.05

    pv = present_value(cashflows, times, ytm)
    d_mac = macaulay_duration(cashflows, times, ytm)
    d_mod = modified_duration(cashflows, times, ytm)
    dv01_val = dv01(cashflows, times, ytm)
    cx = convexity(cashflows, times, ytm)

    assert pv > 0.0
    assert d_mac > d_mod > 0.0
    assert dv01_val > 0.0
    assert cx > 0.0

    dy = 0.001  # 10 bp
    pv_up = present_value(cashflows, times, ytm + dy)
    repricing_pct = pv_up / pv - 1.0
    approx_pct = -d_mod * dy + 0.5 * cx * dy * dy
    assert math.isclose(approx_pct, repricing_pct, rel_tol=0.0, abs_tol=2e-4)

    slope_bp, dp_pct, fair_price = shock_adjusted_bond_state(
        y2=3.50, y10=4.20, duration=d_mod, convexity=cx, price=pv, dy_bp=10
    )
    assert math.isclose(slope_bp, 70.0, abs_tol=1e-12)
    assert dp_pct < 0.0
    assert fair_price < pv


def test_curve_representation_parametric_vs_interpolation_and_residual_diagnostics() -> None:
    maturities = np.array([1.0, 2.0, 3.0, 5.0, 7.0, 10.0])
    observed = np.array([2.10, 2.18, 2.24, 2.36, 2.45, 2.58])

    params = fit_nelson_siegel_svensson(
        maturities,
        observed,
        tau1_grid=[1.0, 1.5, 2.0],
        tau2_grid=[5.0, 8.0, 12.0],
    )

    zero_yields = np.array([nss_yield(float(t), params) for t in maturities])
    discounts = np.exp(-zero_yields * maturities / 100.0)
    fwd_1y = -np.diff(np.log(discounts)) / np.diff(maturities)

    roundtrip_discounts = np.empty_like(discounts)
    roundtrip_discounts[0] = np.exp(-zero_yields[0] * maturities[0] / 100.0)
    for i in range(1, len(maturities)):
        dt = maturities[i] - maturities[i - 1]
        roundtrip_discounts[i] = roundtrip_discounts[i - 1] * np.exp(-fwd_1y[i - 1] * dt)

    assert np.allclose(roundtrip_discounts, discounts, atol=1e-10)

    cm_4y = constant_maturity_interpolation(maturities, observed, target_maturity=4.0)
    nss_4y = nss_yield(4.0, params)
    assert abs(nss_4y - cm_4y) < 0.20

    diagnostics = rich_cheap_indicators(maturities, observed, params)
    assert diagnostics["fitted"].shape == observed.shape
    assert diagnostics["residual"].shape == observed.shape
    assert diagnostics["zscore"].shape == observed.shape
    assert abs(float(np.mean(diagnostics["zscore"]))) < 1e-8


def test_chapters_json_chapters_1_to_6_required_content_and_export_alignment() -> None:
    payload = json.loads(Path("data/chapters.json").read_text(encoding="utf-8"))
    chapters = parse_chapters_map(payload)

    expected_exports = {
        "1": ["basis", "arbitrage_direction", "confidence"],
        "2": ["half_life_days", "hit_probability", "terminal_sharpe"],
        "3": ["factor_scores", "explained_variance"],
        "4": ["residual_bp", "z_score", "rank_score", "signal_direction", "eligible"],
        "5": ["fair_price", "curve_slope_bp", "dp_pct"],
        "6": ["feasible_weight", "expected_weighted_edge_bp", "within_limits"],
    }

    for key in map(str, range(1, 7)):
        chapter = chapters[key]
        for field in CHAPTER_REQUIRED_FIELDS:
            assert field in chapter

        assert chapter["title"]
        assert chapter["learning_objective"]
        assert chapter["summary"]
        assert chapter["exports_to_next_chapter"] == expected_exports[key]
