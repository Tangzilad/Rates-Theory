"""Capital shadow-cost engine for Chapter 18 decisions.

Pedagogical simplification:
- Uses a single capital hurdle and scalar funding charge.
- Does not model dynamic balance-sheet constraints or nonlinear capital rules.
"""

from __future__ import annotations


def capital_shadow_state(
    expected_pnl: float,
    capital_used: float,
    capital_hurdle: float,
    funding_charge: float,
) -> tuple[float, float, bool]:
    """Return (capital_charge, risk_adjusted_alpha, approval_flag)."""
    capital_charge = capital_used * capital_hurdle
    risk_adjusted_alpha = expected_pnl - capital_charge - funding_charge
    return capital_charge, risk_adjusted_alpha, risk_adjusted_alpha > 0
