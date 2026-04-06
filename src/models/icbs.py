"""Intra-currency basis swap (ICBS) engine for teaching Chapter workflows.

Pedagogical simplification:
- Uses simple spread differences between floating indices.
- Ignores convexity and collateral optionality adjustments.
"""

from __future__ import annotations


def intra_currency_basis(
    float_leg_a_pct: float,
    float_leg_b_pct: float,
    reference_rate_adjustment_bp: float = 0.0,
) -> float:
    """Compute ICBS level in bp from two floating legs and reference adjustment."""
    return (float_leg_a_pct - float_leg_b_pct) * 100.0 - reference_rate_adjustment_bp
