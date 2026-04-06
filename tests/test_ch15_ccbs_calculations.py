from __future__ import annotations

import pytest

from src.models.ccbs import (
    ccbs_chapter_payload,
    implied_cross_currency_basis,
    synthetic_domestic_hedged_yield,
)


def test_ccbs_basis_synthetic_hedged_yield_and_sensitivity() -> None:
    payload = ccbs_chapter_payload(
        domestic_float_rate_pct=5.10,
        foreign_float_rate_pct=3.90,
        fx_forward_implied_rate_pct=0.95,
        foreign_leg_yield_pct=4.20,
        fx_hedge_cost_pct=0.35,
        shocks_bp=[-10.0, 0.0, 15.0],
        credit_adjustment_bp=2.0,
        repo_adjustment_bp=1.0,
        reference_rate_adjustment_bp=3.0,
    )

    assert payload.basis_bp == pytest.approx(19.0)
    assert payload.synthetic_domestic_hedged_yield_pct == pytest.approx(4.74)
    assert [point.shocked_basis_bp for point in payload.sensitivity_table] == [9.0, 19.0, 34.0]


def test_ccbs_quote_convention_sign_flip() -> None:
    basis_domestic = implied_cross_currency_basis(
        domestic_float_rate_pct=4.90,
        foreign_float_rate_pct=4.20,
        fx_forward_implied_rate_pct=0.50,
        quote_convention="domestic_minus_hedged_foreign",
    )
    basis_foreign = implied_cross_currency_basis(
        domestic_float_rate_pct=4.90,
        foreign_float_rate_pct=4.20,
        fx_forward_implied_rate_pct=0.50,
        quote_convention="hedged_foreign_minus_domestic",
    )

    assert basis_foreign == pytest.approx(-basis_domestic)

    synthetic = synthetic_domestic_hedged_yield(
        foreign_leg_yield_pct=3.80,
        fx_hedge_cost_pct=0.20,
        basis_bp=basis_foreign,
        quote_convention="hedged_foreign_minus_domestic",
    )
    assert synthetic == pytest.approx(3.80 + 0.20 - basis_foreign / 100.0)
