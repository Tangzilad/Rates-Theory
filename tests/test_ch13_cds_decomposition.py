from __future__ import annotations

import pytest

from src.models.cds import (
    compute_cds_state,
    hazard_proxy_pedagogical,
    pure_credit_spread,
    recovery_sensitivity_d_hazard_d_recovery,
)


def test_cds_decomposition_and_hazard_proxy_with_recovery_sensitivity() -> None:
    purified = pure_credit_spread(
        observed_spread_bp=145.0,
        liquidity_component_bp=20.0,
        technical_component_bp=15.0,
    )
    assert purified == pytest.approx(110.0)

    hazard = hazard_proxy_pedagogical(purified_spread_bp=purified, recovery_rate=0.40)
    sensitivity = recovery_sensitivity_d_hazard_d_recovery(
        purified_spread_bp=purified,
        recovery_rate=0.40,
    )

    assert hazard == pytest.approx(110.0 / (10_000.0 * 0.60))
    assert sensitivity == pytest.approx(110.0 / (10_000.0 * 0.60**2))


def test_compute_cds_state_recovery_grid_monotonicity() -> None:
    state = compute_cds_state(
        observed_spread_bp=130.0,
        liquidity_component_bp=12.0,
        technical_component_bp=8.0,
        recovery_rate=0.40,
        recovery_grid=(0.20, 0.40, 0.60),
    )

    assert state.purified_spread_bp == pytest.approx(110.0)
    assert state.hazard_proxy == pytest.approx(110.0 / (10_000.0 * 0.60))

    scenario_hazards = [point.hazard_proxy for point in state.recovery_sensitivity_scenarios]
    scenario_slopes = [point.d_hazard_d_recovery for point in state.recovery_sensitivity_scenarios]

    assert scenario_hazards[0] < scenario_hazards[1] < scenario_hazards[2]
    assert scenario_slopes[0] < scenario_slopes[1] < scenario_slopes[2]
