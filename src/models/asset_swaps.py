"""Asset-swap decomposition engine for Chapter 12.

Pedagogical simplification:
- Treats coupon mismatch and funding drag as additive bp adjustments.
- Omits full discount-curve/CSA-consistent package valuation.
"""

from __future__ import annotations


def decompose_asset_swap(
    z_spread_bp: float,
    bond_coupon_pct: float,
    swap_rate_pct: float,
    repo_drag_bp: float,
) -> tuple[float, float, float]:
    """Return (coupon_mismatch_bp, asset_swap_spread_bp, package_carry_bp)."""
    coupon_mismatch_bp = (bond_coupon_pct - swap_rate_pct) * 100.0
    asset_swap_spread_bp = z_spread_bp - coupon_mismatch_bp
    package_carry_bp = asset_swap_spread_bp - repo_drag_bp
    return coupon_mismatch_bp, asset_swap_spread_bp, package_carry_bp
