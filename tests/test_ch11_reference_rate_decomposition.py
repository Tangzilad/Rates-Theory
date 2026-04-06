from __future__ import annotations

import pytest

from src.models.reference_rates import (
    all_in_coupon_pct,
    benchmark_spread_decomposition_bp,
    curve_spread_bp,
    fallback_spread_bp,
    repo_reference_basis_bp,
    secured_unsecured_basis_bp,
    spread_term_structure_bp,
)


def test_reference_rate_wedges_and_transition_math() -> None:
    assert curve_spread_bp(4.80, 4.65) == pytest.approx(15.0)
    assert secured_unsecured_basis_bp(4.60, 4.85) == pytest.approx(25.0)
    assert repo_reference_basis_bp(4.55, 4.70) == pytest.approx(-15.0)
    assert fallback_spread_bp(5.02, 4.71) == pytest.approx(31.0)
    assert all_in_coupon_pct(4.71, 26.0) == pytest.approx(4.97)


def test_term_structure_and_decomposition_consistency() -> None:
    term = spread_term_structure_bp(
        {"1M": 4.50, "3M": 4.60, "6M": 4.70},
        {"1M": 4.72, "3M": 4.79, "6M": 4.83},
    )
    assert term == {"1M": pytest.approx(-22.0), "3M": pytest.approx(-19.0), "6M": pytest.approx(-13.0)}

    decomposition = benchmark_spread_decomposition_bp(
        secured_unsecured_bp=24.0,
        repo_reference_bp=-8.0,
        transition_overlay_bp=27.0,
    )
    assert decomposition["total_benchmark_spread_bp"] == pytest.approx(43.0)
