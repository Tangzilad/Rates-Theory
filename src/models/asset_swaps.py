"""Asset-swap decomposition engine for Chapter 12.

Pedagogical simplification:
- Treats coupon mismatch and funding terms as additive bp adjustments.
- Omits full discount-curve/CSA-consistent package valuation and optionality.
"""

from __future__ import annotations

from core.types import AssetSwapState


SIMPLIFICATION_NOTES = [
    "Package fair value is represented as an additive bp identity.",
    "CSA-consistent discounting, collateral optionality, and convexity are not modeled.",
    "Funding sensitivity is linearized around the selected funding level.",
]


def coupon_mismatch_bp(
    bond_coupon_pct: float,
    benchmark_rate_pct: float,
) -> float:
    """Coupon mismatch in bp versus the selected floating benchmark."""
    return (bond_coupon_pct - benchmark_rate_pct) * 100.0


def asset_swap_spread_bp(
    z_spread_bp: float,
    coupon_mismatch_bp_value: float,
) -> float:
    """Asset-swap spread as z-spread net of coupon mismatch."""
    return z_spread_bp - coupon_mismatch_bp_value


def package_carry_bp(
    asset_swap_spread_bp_value: float,
    repo_funding_rate_pct: float,
    benchmark_rate_pct: float,
) -> float:
    """Carry of long-bond/receive-fixed package before mark-to-market effects."""
    funding_drag_bp = (repo_funding_rate_pct - benchmark_rate_pct) * 100.0
    return asset_swap_spread_bp_value - funding_drag_bp


def fair_package_level_bp(
    asset_swap_spread_bp_value: float,
    package_upfront_pct: float,
) -> float:
    """Fair package level under par/non-par simplification.

    Assumption: upfront premium/discount maps one-for-one to spread bp.
    """
    return asset_swap_spread_bp_value - package_upfront_pct * 100.0


def funding_sensitivity_bp_per_1bp() -> float:
    """Local sensitivity of package carry to a +1bp funding shift."""
    return -1.0


def decompose_asset_swap(
    z_spread_bp: float,
    bond_coupon_pct: float,
    benchmark_rate_pct: float,
    repo_funding_rate_pct: float,
    package_upfront_pct: float = 0.0,
    funding_shift_bp: float = 0.0,
    reference_rate_name: str = "Par swap",
    benchmark_type: str = "par",
) -> AssetSwapState:
    """Return a structured state for package anatomy and sensitivity."""
    coupon_bp = coupon_mismatch_bp(
        bond_coupon_pct=bond_coupon_pct,
        benchmark_rate_pct=benchmark_rate_pct,
    )
    asw_bp = asset_swap_spread_bp(
        z_spread_bp=z_spread_bp,
        coupon_mismatch_bp_value=coupon_bp,
    )
    carry_bp = package_carry_bp(
        asset_swap_spread_bp_value=asw_bp,
        repo_funding_rate_pct=repo_funding_rate_pct,
        benchmark_rate_pct=benchmark_rate_pct,
    )
    funding_beta = funding_sensitivity_bp_per_1bp()
    adjusted_carry_bp = carry_bp + funding_beta * funding_shift_bp

    return AssetSwapState(
        z_spread_bp=z_spread_bp,
        bond_coupon_pct=bond_coupon_pct,
        benchmark_rate_pct=benchmark_rate_pct,
        reference_rate_name=reference_rate_name,
        benchmark_type=benchmark_type,
        package_upfront_pct=package_upfront_pct,
        repo_funding_rate_pct=repo_funding_rate_pct,
        funding_shift_bp=funding_shift_bp,
        coupon_mismatch_bp=coupon_bp,
        asset_swap_spread_bp=asw_bp,
        package_carry_bp=adjusted_carry_bp,
        fair_package_level_bp=fair_package_level_bp(
            asset_swap_spread_bp_value=asw_bp,
            package_upfront_pct=package_upfront_pct,
        ),
        funding_sensitivity_bp_per_1bp=funding_beta,
        simplification_notes=SIMPLIFICATION_NOTES,
    )
