"""Cross-currency basis swap (CCBS) engine for chapter-level analytics.

Pedagogical simplification:
- Computes basis from floating-leg differential and FX-forward implied rate.
- Treats credit/repo/reference frictions as additive bp penalties.
"""

from __future__ import annotations


def cross_currency_basis(
    domestic_float_rate_pct: float,
    foreign_float_rate_pct: float,
    fx_forward_implied_rate_pct: float,
    credit_adjustment_bp: float = 0.0,
    repo_adjustment_bp: float = 0.0,
    reference_rate_adjustment_bp: float = 0.0,
) -> float:
    """Compute CCBS spread in bp net of pedagogical adjustment terms."""
    raw_basis_bp = (domestic_float_rate_pct - (foreign_float_rate_pct + fx_forward_implied_rate_pct)) * 100.0
    return raw_basis_bp - credit_adjustment_bp - repo_adjustment_bp - reference_rate_adjustment_bp
