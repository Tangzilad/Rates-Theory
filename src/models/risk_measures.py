"""Duration/convexity risk measures for pedagogical bond diagnostics.

Pedagogical simplification:
- Uses first/second-order price approximation and parallel yield shocks.
- Intended for intuition and screening, not full cashflow repricing.
"""

from __future__ import annotations

from core.equations import curve_slope_bp, duration_convexity_price_change, shock_adjusted_price


def shock_adjusted_bond_state(
    y2: float,
    y10: float,
    duration: float,
    convexity: float,
    price: float,
    dy_bp: int,
) -> tuple[float, float, float]:
    """Return curve slope, approximate % price change, and shock-adjusted price."""
    slope = curve_slope_bp(y2, y10)
    dp_pct = duration_convexity_price_change(duration, convexity, dy_bp)
    fair_price = shock_adjusted_price(price, dp_pct)
    return slope, dp_pct, fair_price
