"""Reference-rate transition helpers for fallback spread analytics."""

from __future__ import annotations


def fallback_spread_bp(legacy_fixing_pct: float, compounded_rfr_pct: float) -> float:
    """Return fallback spread in basis points."""
    return (legacy_fixing_pct - compounded_rfr_pct) * 100.0


def all_in_coupon_pct(compounded_rfr_pct: float, contractual_adjustment_bp: float) -> float:
    """Return all-in coupon percentage after contractual fallback adjustment."""
    return compounded_rfr_pct + contractual_adjustment_bp / 100.0
