"""Duration/convexity risk measures for pedagogical bond diagnostics.

Pedagogical simplification:
- Uses fixed cashflow discounting with a flat yield assumption.
- Intended for intuition and screening, not full curve-consistent pricing.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np

from core.equations import curve_slope_bp, duration_convexity_price_change, shock_adjusted_price


def present_value(
    cashflows: Iterable[float],
    times_years: Iterable[float],
    yield_rate: float,
    compounding_frequency: int = 1,
) -> float:
    """Discount fixed cashflows under a flat yield and return PV."""
    cf = np.asarray(list(cashflows), dtype=float)
    t = np.asarray(list(times_years), dtype=float)
    if cf.size != t.size or cf.size == 0:
        raise ValueError("cashflows and times_years must have same non-zero length")
    if compounding_frequency <= 0:
        raise ValueError("compounding_frequency must be positive")

    discount = (1.0 + yield_rate / compounding_frequency) ** (-compounding_frequency * t)
    return float(np.sum(cf * discount))


def macaulay_duration(
    cashflows: Iterable[float],
    times_years: Iterable[float],
    yield_rate: float,
    compounding_frequency: int = 1,
) -> float:
    """Return Macaulay duration (years) for fixed cashflows."""
    cf = np.asarray(list(cashflows), dtype=float)
    t = np.asarray(list(times_years), dtype=float)
    if cf.size != t.size or cf.size == 0:
        raise ValueError("cashflows and times_years must have same non-zero length")

    pv = present_value(cf, t, yield_rate, compounding_frequency)
    if pv == 0.0:
        raise ValueError("present value is zero; duration is undefined")

    discount = (1.0 + yield_rate / compounding_frequency) ** (-compounding_frequency * t)
    weighted = np.sum(t * cf * discount)
    return float(weighted / pv)


def modified_duration(
    cashflows: Iterable[float],
    times_years: Iterable[float],
    yield_rate: float,
    compounding_frequency: int = 1,
) -> float:
    """Return modified duration (years) from Macaulay duration."""
    d_mac = macaulay_duration(cashflows, times_years, yield_rate, compounding_frequency)
    return float(d_mac / (1.0 + yield_rate / compounding_frequency))


def dv01(
    cashflows: Iterable[float],
    times_years: Iterable[float],
    yield_rate: float,
    compounding_frequency: int = 1,
) -> float:
    """Return dollar-value-of-a-basis-point under flat-yield approximation."""
    pv = present_value(cashflows, times_years, yield_rate, compounding_frequency)
    d_mod = modified_duration(cashflows, times_years, yield_rate, compounding_frequency)
    return float(abs(pv * d_mod * 1e-4))


def convexity(
    cashflows: Iterable[float],
    times_years: Iterable[float],
    yield_rate: float,
    compounding_frequency: int = 1,
) -> float:
    """Return standard bond convexity for periodic compounding."""
    cf = np.asarray(list(cashflows), dtype=float)
    t = np.asarray(list(times_years), dtype=float)
    if cf.size != t.size or cf.size == 0:
        raise ValueError("cashflows and times_years must have same non-zero length")
    if compounding_frequency <= 0:
        raise ValueError("compounding_frequency must be positive")

    m = float(compounding_frequency)
    pv = present_value(cf, t, yield_rate, compounding_frequency)
    if pv == 0.0:
        raise ValueError("present value is zero; convexity is undefined")

    n_periods = m * t
    base = 1.0 + yield_rate / m
    numerator = np.sum(cf * n_periods * (n_periods + 1.0) / (base ** (n_periods + 2.0)))
    return float(numerator / (pv * m**2))


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
