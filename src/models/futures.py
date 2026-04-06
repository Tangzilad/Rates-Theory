"""Futures/cash carry helpers used by downstream chapter workflows."""

from __future__ import annotations


def fair_futures_from_cash_carry(spot_price: float, funding_rate_pct: float, maturity_years: float) -> float:
    """Return fair futures price from spot financed at simple carry."""
    return spot_price * (1.0 + funding_rate_pct / 100.0 * maturity_years)


def basis_bp(observed_futures: float, fair_futures: float) -> float:
    """Return futures basis in basis points relative to fair futures."""
    if fair_futures == 0.0:
        return 0.0
    return (observed_futures / fair_futures - 1.0) * 10_000.0
