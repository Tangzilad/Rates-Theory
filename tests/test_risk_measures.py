from src.models.risk_diagnostics import shock_adjusted_bond_state


def test_shock_adjusted_bond_state_outputs_consistent_tuple():
    slope, dp_pct, fair_price = shock_adjusted_bond_state(
        y2=0.03,
        y10=0.04,
        duration=5.0,
        convexity=0.8,
        price=100.0,
        dy_bp=25,
    )

    assert isinstance(slope, float)
    assert isinstance(dp_pct, float)
    assert isinstance(fair_price, float)
    assert fair_price > 0.0
