"""Option pricing helpers: Black-Scholes, Black-76, implied volatility, and smiles."""

from __future__ import annotations

from math import erf, exp, log, pi, sqrt
from typing import Iterable

from constants import (
    DEFAULT_VOL_LOWER_BOUND,
    DEFAULT_VOL_UPPER_BOUND,
    EPSILON,
    MAX_NEWTON_ITERATIONS,
)


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))


def _norm_pdf(x: float) -> float:
    return exp(-0.5 * x * x) / sqrt(2.0 * pi)


def _d1_d2(forward_like: float, strike: float, vol: float, expiry: float) -> tuple[float, float]:
    vt = vol * sqrt(max(expiry, EPSILON))
    d1 = (log(max(forward_like, EPSILON) / max(strike, EPSILON)) + 0.5 * vt * vt) / max(vt, EPSILON)
    d2 = d1 - vt
    return d1, d2


def black_scholes_price(
    spot: float,
    strike: float,
    expiry: float,
    rate: float,
    volatility: float,
    option_type: str = "call",
    dividend_yield: float = 0.0,
) -> float:
    """Equity-style Black-Scholes price."""
    if expiry <= 0:
        intrinsic = max(spot - strike, 0.0) if option_type == "call" else max(strike - spot, 0.0)
        return intrinsic

    fwd_like = spot * exp((rate - dividend_yield) * expiry)
    d1, d2 = _d1_d2(fwd_like, strike, volatility, expiry)
    disc = exp(-rate * expiry)

    if option_type == "call":
        return disc * (fwd_like * _norm_cdf(d1) - strike * _norm_cdf(d2))
    if option_type == "put":
        return disc * (strike * _norm_cdf(-d2) - fwd_like * _norm_cdf(-d1))
    raise ValueError("option_type must be 'call' or 'put'")


def black_76_price(
    forward: float,
    strike: float,
    expiry: float,
    discount_factor: float,
    volatility: float,
    option_type: str = "call",
) -> float:
    """Black-76 option price (commonly used for rates options/swaptions)."""
    if expiry <= 0:
        intrinsic = max(forward - strike, 0.0) if option_type == "call" else max(strike - forward, 0.0)
        return discount_factor * intrinsic

    d1, d2 = _d1_d2(forward, strike, volatility, expiry)
    if option_type == "call":
        return discount_factor * (forward * _norm_cdf(d1) - strike * _norm_cdf(d2))
    if option_type == "put":
        return discount_factor * (strike * _norm_cdf(-d2) - forward * _norm_cdf(-d1))
    raise ValueError("option_type must be 'call' or 'put'")


def implied_volatility_black_76(
    price: float,
    forward: float,
    strike: float,
    expiry: float,
    discount_factor: float,
    option_type: str = "call",
    vol_lower: float = DEFAULT_VOL_LOWER_BOUND,
    vol_upper: float = DEFAULT_VOL_UPPER_BOUND,
) -> float:
    """Solve Black-76 implied volatility via bracketed bisection."""
    low, high = vol_lower, vol_upper
    for _ in range(MAX_NEWTON_ITERATIONS):
        mid = 0.5 * (low + high)
        mid_price = black_76_price(forward, strike, expiry, discount_factor, mid, option_type)
        if abs(mid_price - price) < 1.0e-10:
            return mid
        if mid_price > price:
            high = mid
        else:
            low = mid
    return 0.5 * (low + high)


def black_76_vega(forward: float, strike: float, expiry: float, discount_factor: float, volatility: float) -> float:
    """Black-76 vega used for smile and calibration diagnostics."""
    d1, _ = _d1_d2(forward, strike, volatility, expiry)
    return discount_factor * forward * _norm_pdf(d1) * sqrt(max(expiry, EPSILON))


def generate_smile_strikes(atm_forward: float, moneyness_offsets: Iterable[float]) -> list[float]:
    """Generate strike ladder from ATM forward and additive offsets."""
    return [atm_forward + off for off in moneyness_offsets]


def generate_vol_smile(
    atm_vol: float,
    strikes: Iterable[float],
    atm_forward: float,
    skew: float = -0.1,
    curvature: float = 0.2,
) -> list[float]:
    """Simple quadratic smile model around ATM."""
    vols: list[float] = []
    for k in strikes:
        x = (k - atm_forward) / max(atm_forward, EPSILON)
        vol = atm_vol + skew * x + curvature * x * x
        vols.append(max(vol, DEFAULT_VOL_LOWER_BOUND))
    return vols
