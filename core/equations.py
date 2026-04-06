from __future__ import annotations

import numpy as np


def fair_futures_price(spot: float, repo_rate: float, t_years: float) -> float:
    return float(spot * np.exp(repo_rate * t_years))


def basis_from_market(observed_futures: float, fair_futures: float) -> float:
    return float(observed_futures - fair_futures)


def arbitrage_direction(basis: float) -> str:
    if basis > 0:
        return "cash_and_carry"
    if basis < 0:
        return "reverse_cash_and_carry"
    return "neutral"


def duration_convexity_price_change(duration: float, convexity: float, dy_bp: int) -> float:
    dy = dy_bp / 10_000
    return float(-duration * dy + 0.5 * convexity * (dy**2))


def curve_slope_bp(short_yield_pct: float, long_yield_pct: float) -> float:
    return float((long_yield_pct - short_yield_pct) * 100)


def shock_adjusted_price(price: float, dp_pct: float) -> float:
    return float(price * (1 + dp_pct))
