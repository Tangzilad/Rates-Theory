from __future__ import annotations

import pytest

from src.models.shadow_costs import capital_shadow_state


def test_shadow_cost_adjustment_and_approval_gate_positive_case() -> None:
    state = capital_shadow_state(
        structural_fair_spread_bp=40.0,
        observed_spread_bp=70.0,
        shadow_funding_cost_bp=4.0,
        capital_used=5_000_000.0,
        capital_hurdle=0.10,
        spread_bp_value_dollars=100_000.0,
        liquidity_wedge_bp=3.0,
        repo_stress_add_on_bp=2.0,
        monetisable_threshold_bp=5.0,
        non_monetisable_block=False,
    )

    assert state.spread_gap_bp == pytest.approx(30.0)
    assert state.capital_charge_bp == pytest.approx(5.0)
    assert state.adjusted_executable_spread_residual_bp == pytest.approx(16.0)
    assert state.approval_gate == "approve"


def test_shadow_cost_approval_blocker_overrides_positive_residual() -> None:
    state = capital_shadow_state(
        structural_fair_spread_bp=20.0,
        observed_spread_bp=45.0,
        shadow_funding_cost_bp=2.0,
        capital_used=1_000_000.0,
        capital_hurdle=0.10,
        spread_bp_value_dollars=100_000.0,
        liquidity_wedge_bp=1.0,
        repo_stress_add_on_bp=1.0,
        monetisable_threshold_bp=0.0,
        non_monetisable_block=True,
    )
    assert state.adjusted_executable_spread_residual_bp > 0.0
    assert state.approval_gate == "do_not_approve"
