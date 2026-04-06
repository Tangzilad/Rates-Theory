"""CDS and pure-credit extraction helpers for Chapter 13.

Pedagogical simplification:
- Uses a flat-hazard approximation from spread and recovery.
- Useful for teaching relative-value decomposition, not desk pricing.
"""

from __future__ import annotations


EPS = 1e-6


def pure_credit_spread(observed_spread_bp: float, liquidity_component_bp: float, technical_component_bp: float) -> float:
    """Strip non-default premia from observed spread (bp)."""
    return observed_spread_bp - liquidity_component_bp - technical_component_bp


def implied_hazard_rate(pure_credit_bp: float, recovery_rate: float) -> float:
    """Map pure credit spread (bp) to a flat annualized hazard proxy."""
    return pure_credit_bp / (10_000.0 * max(1.0 - recovery_rate, EPS))


def cds_bond_basis(cds_spread_bp: float, bond_implied_credit_bp: float) -> float:
    """Return CDS-bond basis in basis points."""
    return cds_spread_bp - bond_implied_credit_bp
