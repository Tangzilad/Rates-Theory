"""Risk diagnostic helpers for duration-convexity approximations."""

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
    slope = curve_slope_bp(y2, y10)
    dp_pct = duration_convexity_price_change(duration, convexity, dy_bp)
    fair_price = shock_adjusted_price(price, dp_pct)
    return slope, dp_pct, fair_price
