from __future__ import annotations

import pytest

from src.models.fitted_curves import rank_residual_series, sofr_asw_residuals_bp


def test_global_ranking_logic_and_disagreement_attribution() -> None:
    labels = ["US_10Y", "DE_10Y", "JP_10Y", "UK_10Y"]
    curve_residuals = [12.0, -8.0, 5.0, -1.0]
    curve_ranked = rank_residual_series(labels=labels, residual_bp=curve_residuals)

    sofr_residuals = sofr_asw_residuals_bp(
        asset_swap_spread_bp=[20.0, 14.0, 16.0, 10.0],
        sofr_ois_spread_bp=[5.0, 4.0, 6.0, 3.0],
        funding_basis_bp=[2.0, 1.0, 5.0, 2.0],
        credit_difference_bp=[1.0, 2.0, 1.0, 2.0],
        benchmark_choice_bp=[1.0, 0.5, 2.0, 1.0],
    )
    sofr_ranked = rank_residual_series(labels=labels, residual_bp=sofr_residuals)

    curve_rank_map = {label: curve_ranked.rank_descending[i] for i, label in enumerate(labels)}
    sofr_rank_map = {label: sofr_ranked.rank_descending[i] for i, label in enumerate(labels)}

    disagreement_threshold = 2
    rank_gaps = {label: abs(curve_rank_map[label] - sofr_rank_map[label]) for label in labels}
    disagreement = {label: rank_gaps[label] >= disagreement_threshold for label in labels}

    assert curve_rank_map["US_10Y"] == 1
    assert sofr_rank_map["US_10Y"] == 1
    assert rank_gaps["US_10Y"] == 0
    assert disagreement["DE_10Y"] is True

    attribution_buckets = {
        "curve_mismatch": sum(abs(x) for x in curve_residuals) / len(curve_residuals),
        "funding_basis": (2.0 + 1.0 + 5.0 + 2.0) / 4.0,
        "credit_differences": (1.0 + 2.0 + 1.0 + 2.0) / 4.0,
        "benchmark_choice": (1.0 + 0.5 + 2.0 + 1.0) / 4.0,
    }

    assert attribution_buckets["funding_basis"] == pytest.approx(2.5)
    assert attribution_buckets["curve_mismatch"] == pytest.approx(6.5)
