"""Backward-compatible wrappers for risk measures.

Prefer importing from :mod:`src.models.risk_measures`.
"""

from .risk_measures import shock_adjusted_bond_state

__all__ = ["shock_adjusted_bond_state"]
