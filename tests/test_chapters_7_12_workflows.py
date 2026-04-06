from __future__ import annotations

import math

import numpy as np
import pytest

from src.chapter_summary_schema import ChapterSummarySchemaError, parse_chapters_map
from src.chapters.ch09_trade_construction import (
    GovBondTradeBlueprint,
    Chapter09,
    compose_gov_bond_trade_blueprint,
)
from src.chapters.ch07_risk_governance import Chapter07
from src.chapters.ch08_relative_value_screens import Chapter08
from src.chapters.ch10_funding_basis import Chapter10
from src.chapters.ch11_reference_rate_transition import Chapter11
from src.chapters.ch12_asset_swap_decomposition import Chapter12
from src.chapters.registry import CHAPTER_DEPENDENCIES, validate_chapter_dependencies
from src.models.asset_swaps import decompose_asset_swap
from src.models.ccbs import cross_currency_basis as ccbs_basis_bp
from src.models.swap_spreads import asset_swap_spread, cross_currency_basis, intra_currency_basis
from src.models.yield_curve import (
    constant_maturity_interpolation,
    fit_nelson_siegel_svensson,
    rich_cheap_indicators,
)


def _invoice_price(futures_price: float, conversion_factor: float, accrued_interest: float) -> float:
    return futures_price * conversion_factor + accrued_interest


def _implied_repo_rate(
    *,
    dirty_price: float,
    invoice_price: float,
    coupon_income: float,
    financing_days: int,
    day_count_basis: int = 360,
) -> float:
    gross_return = (invoice_price + coupon_income) / dirty_price
    return (gross_return - 1.0) * (day_count_basis / financing_days)


def _select_ctd_by_net_basis(candidates: list[dict[str, float]], futures_price: float) -> str:
    def net_basis(row: dict[str, float]) -> float:
        invoice = _invoice_price(futures_price, row["conversion_factor"], row["accrued_interest"])
        adjusted_dirty = row["dirty_price"] - row["repo_specialness_bp"] / 10000.0
        return adjusted_dirty - invoice

    return min(candidates, key=net_basis)["bond_id"]  # type: ignore[index]


def test_futures_invoice_implied_repo_and_ctd_switch_under_specialness_shift() -> None:
    invoice = _invoice_price(118.0, 0.8125, 1.75)
    assert invoice == pytest.approx(97.625)

    implied_repo = _implied_repo_rate(
        dirty_price=96.80,
        invoice_price=invoice,
        coupon_income=0.90,
        financing_days=90,
    )
    assert implied_repo == pytest.approx(0.07128099, rel=1e-6)

    candidates = [
        {"bond_id": "A", "dirty_price": 97.10, "conversion_factor": 0.8125, "accrued_interest": 1.75, "repo_specialness_bp": 0.0},
        {"bond_id": "B", "dirty_price": 95.80, "conversion_factor": 0.8000, "accrued_interest": 1.60, "repo_specialness_bp": 0.0},
    ]
    assert _select_ctd_by_net_basis(candidates, futures_price=118.0) == "A"

    shifted = [dict(row) for row in candidates]
    shifted[0]["repo_specialness_bp"] = -4000.0
    assert _select_ctd_by_net_basis(shifted, futures_price=118.0) == "B"


def test_fitted_curve_residuals_outlier_behavior_and_constant_maturity_output() -> None:
    maturities = np.array([1.0, 2.0, 3.0, 5.0, 7.0, 10.0], dtype=float)
    observed = np.array([2.00, 2.08, 2.18, 2.31, 2.44, 2.56], dtype=float)
    observed_with_outlier = observed.copy()
    observed_with_outlier[3] += 0.18

    params = fit_nelson_siegel_svensson(
        maturities,
        observed_with_outlier,
        tau1_grid=[1.0, 1.5, 2.0],
        tau2_grid=[5.0, 7.0, 10.0],
    )
    indicators = rich_cheap_indicators(maturities, observed_with_outlier, params)
    residual = indicators["residual"]
    zscore = indicators["zscore"]
    cm_4y = constant_maturity_interpolation(maturities, observed_with_outlier, 4.0)

    assert residual.shape == observed.shape
    assert zscore.shape == observed.shape
    assert residual[3] > 0
    assert abs(residual[3]) > np.median(np.abs(residual))
    assert np.isfinite(zscore).all()
    assert math.isfinite(cm_4y)
    assert observed_with_outlier[2] <= cm_4y <= observed_with_outlier[3]


def test_chapter9_blueprint_composition_happy_path_and_malformed_payload() -> None:
    payload = {
        "trade_id": "UST-9Y-RV-001",
        "instrument": "UST 9Y cash vs TY future",
        "direction": "long_cash_short_future",
        "target_notional": 25_000_000.0,
        "entry_level": 102.125,
        "stop_level": 101.250,
        "take_profit_level": 103.000,
        "governance_status": "amber",
        "approved": True,
        "scenario_value": 102.42,
        "notes": ["sizing from scenario ladder", "risk review complete"],
    }

    blueprint = compose_gov_bond_trade_blueprint(payload)

    assert isinstance(blueprint, GovBondTradeBlueprint)
    assert blueprint.trade_id == "UST-9Y-RV-001"
    assert blueprint.approved is True
    assert blueprint.notes == ("sizing from scenario ladder", "risk review complete")

    malformed = dict(payload)
    malformed.pop("entry_level")
    with pytest.raises(ValueError, match="Missing required blueprint fields"):
        compose_gov_bond_trade_blueprint(malformed)


def test_reference_rate_transform_and_basis_comparisons() -> None:
    fallback_spread_bp = (5.05 - 4.72) * 100.0
    all_in_coupon_pct = 4.72 + 0.28
    assert fallback_spread_bp == pytest.approx(33.0)
    assert all_in_coupon_pct == pytest.approx(5.0)

    secured_unsecured_bp = intra_currency_basis(float_leg_a=4.76, float_leg_b=4.66, reference_rate_adjustment=0.02)
    repo_reference_bp = cross_currency_basis(
        domestic_float_rate=4.90,
        foreign_float_rate=4.35,
        fx_forward_implied_rate=0.30,
        credit_adjustment=0.02,
        repo_adjustment=0.01,
        reference_rate_adjustment=0.01,
    )
    repo_reference_ccbs_bp = ccbs_basis_bp(
        domestic_float_rate_pct=4.90,
        foreign_float_rate_pct=4.35,
        fx_forward_implied_rate_pct=0.30,
        credit_adjustment_bp=2.0,
        repo_adjustment_bp=1.0,
        reference_rate_adjustment_bp=1.0,
    )

    assert secured_unsecured_bp == pytest.approx(0.08)
    assert repo_reference_bp == pytest.approx(0.21)
    assert repo_reference_ccbs_bp == pytest.approx(21.0)


def test_asset_swap_decomposition_funding_sensitivity_and_benchmark_toggles() -> None:
    mismatch_bp, ass_bp, carry_bp = decompose_asset_swap(
        z_spread_bp=94.0,
        bond_coupon_pct=4.25,
        swap_rate_pct=3.95,
        repo_drag_bp=12.0,
    )
    assert mismatch_bp == pytest.approx(30.0)
    assert ass_bp == pytest.approx(64.0)
    assert carry_bp == pytest.approx(52.0)

    mismatch_bp_alt, ass_bp_alt, carry_bp_alt = decompose_asset_swap(
        z_spread_bp=94.0,
        bond_coupon_pct=4.25,
        swap_rate_pct=3.95,
        repo_drag_bp=20.0,
    )
    assert mismatch_bp_alt == pytest.approx(mismatch_bp)
    assert ass_bp_alt == pytest.approx(ass_bp)
    assert carry_bp_alt == pytest.approx(carry_bp - 8.0)

    benchmark_ois = asset_swap_spread(par_swap_rate=0.0400, bond_yield=0.0350, credit_adjustment=0.0005, repo_adjustment=0.0003)
    benchmark_libor = asset_swap_spread(par_swap_rate=0.0412, bond_yield=0.0350, credit_adjustment=0.0005, repo_adjustment=0.0003)
    assert benchmark_libor > benchmark_ois


def test_registry_dependency_validation_for_chapters_7_to_12_and_missing_exports_failure() -> None:
    registry = {
        "7": Chapter07(),
        "8": Chapter08(),
        "9": Chapter09(),
        "10": Chapter10(),
        "11": Chapter11(),
        "12": Chapter12(),
    }
    scoped_dependencies = {
        "7": {},
        "8": CHAPTER_DEPENDENCIES["8"],
        "9": CHAPTER_DEPENDENCIES["9"],
        "10": CHAPTER_DEPENDENCIES["10"],
        "11": CHAPTER_DEPENDENCIES["11"],
        "12": CHAPTER_DEPENDENCIES["12"],
    }

    clean_result = validate_chapter_dependencies(registry, dependency_map=scoped_dependencies)
    assert clean_result.has_errors is False

    failing_dependencies = dict(scoped_dependencies)
    failing_dependencies["12"] = {"11": ["fallback_spread_bp", "secured_unsecured_basis_bp"]}
    failing_result = validate_chapter_dependencies(registry, dependency_map=failing_dependencies)
    assert failing_result.has_errors is True
    assert any("secured_unsecured_basis_bp" in issue.message for issue in failing_result.issues)


def test_parse_chapters_map_rejects_malformed_payload_type() -> None:
    with pytest.raises(ChapterSummarySchemaError, match="Top-level chapter content JSON must be an object"):
        parse_chapters_map(["not", "an", "object"])
