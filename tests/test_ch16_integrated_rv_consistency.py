from __future__ import annotations

import pytest

from src.models.integrated_rv import integrated_rv_state


def test_integrated_rv_normalization_consistency_and_no_divergence() -> None:
    state = integrated_rv_state(
        bond_local_space_signal_bp=20.0,
        asset_swap_transformed_signal_bp=22.0,
        intra_basis_transformed_signal_bp=21.0,
        cross_currency_basis_transformed_signal_bp=19.0,
        cds_pure_credit_signal_bp=20.0,
        sofr_anchor_bp=20.0,
        divergence_threshold_bp=3.0,
        shocked_input="bond",
        shock_bp=0.0,
    )

    normalized = state.common_space_normalization.normalized_signals_bp
    assert normalized == {
        "bond_local": 0.0,
        "asset_swap": 2.0,
        "basis_intra": 1.0,
        "basis_cross": -1.0,
        "cds_pure_credit": 0.0,
    }
    assert state.agreement_divergence_diagnostics.divergence_flag is False


def test_integrated_rv_divergence_flag_and_shock_propagation() -> None:
    state = integrated_rv_state(
        bond_local_space_signal_bp=30.0,
        asset_swap_transformed_signal_bp=10.0,
        intra_basis_transformed_signal_bp=-5.0,
        cross_currency_basis_transformed_signal_bp=25.0,
        cds_pure_credit_signal_bp=-10.0,
        sofr_anchor_bp=0.0,
        divergence_threshold_bp=8.0,
        shocked_input="asset_swap",
        shock_bp=20.0,
    )

    diag = state.agreement_divergence_diagnostics
    assert diag.divergence_flag is True
    assert diag.max_deviation_bp > 8.0

    shocked = state.shock_propagation_results.shocked_signals_bp
    assert shocked["asset_swap"] == pytest.approx(30.0)
    assert shocked["basis_cross"] == pytest.approx(33.0)
    assert shocked["bond_local"] == pytest.approx(36.0)
