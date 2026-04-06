from __future__ import annotations

import pytest

from src.models.icbs import (
    carry_estimate,
    current_same_currency_basis_from_benchmarks,
    icbs_chapter_payload,
)


def test_icbs_current_basis_term_structure_carry_and_rolldown() -> None:
    payload = icbs_chapter_payload(
        benchmark_a_name="SOFR-3M",
        benchmark_b_name="SOFR-6M",
        benchmark_a_pct=5.10,
        benchmark_b_pct=4.95,
        maturity_years=[1.0, 2.0, 3.0, 5.0],
        benchmark_a_curve_pct=[5.05, 5.00, 4.95, 4.80],
        benchmark_b_curve_pct=[4.95, 4.90, 4.86, 4.74],
        current_maturity_years=3.0,
        roll_horizon_years=1.0,
        expected_basis_bp=10.0,
        carry_horizon_years=0.5,
        reference_rate_adjustment_bp=1.0,
    )

    assert payload.current_basis_bp == pytest.approx(14.0)
    assert len(payload.term_structure) == 4
    assert payload.term_structure[2].basis_bp == pytest.approx(8.0)

    expected_carry = carry_estimate(current_basis_bp=14.0, expected_basis_bp=10.0, horizon_years=0.5)
    assert payload.carry_estimate_bp == pytest.approx(expected_carry)
    assert payload.rolldown_estimate_bp == pytest.approx(1.0)


def test_icbs_current_basis_helper_matches_formula() -> None:
    basis_bp = current_same_currency_basis_from_benchmarks(
        benchmark_a_pct=4.80,
        benchmark_b_pct=4.72,
        reference_rate_adjustment_bp=0.5,
    )
    assert basis_bp == pytest.approx((4.80 - 4.72) * 100.0 - 0.5)
