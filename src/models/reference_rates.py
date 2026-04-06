"""Reference-rate transition and basis utilities for Chapter 11."""

from __future__ import annotations


def curve_spread_bp(curve_a_rate_pct: float, curve_b_rate_pct: float) -> float:
    """Return curve A minus curve B in basis points."""
    return (curve_a_rate_pct - curve_b_rate_pct) * 100.0


def secured_unsecured_basis_bp(secured_rate_pct: float, unsecured_rate_pct: float) -> float:
    """Return unsecured minus secured funding basis in basis points."""
    return (unsecured_rate_pct - secured_rate_pct) * 100.0


def repo_reference_basis_bp(repo_rate_pct: float, reference_rate_pct: float) -> float:
    """Return repo minus benchmark reference basis in basis points."""
    return (repo_rate_pct - reference_rate_pct) * 100.0


def fallback_spread_bp(legacy_fixing_pct: float, compounded_rfr_pct: float) -> float:
    """Return legacy tenor minus compounded RFR fallback spread in basis points."""
    return (legacy_fixing_pct - compounded_rfr_pct) * 100.0


def all_in_coupon_pct(compounded_rfr_pct: float, fallback_adjustment_bp: float) -> float:
    """Return all-in floating coupon using compounded RFR + contractual fallback adjustment."""
    return compounded_rfr_pct + (fallback_adjustment_bp / 100.0)


def spread_term_structure_bp(
    curve_a_by_tenor_pct: dict[str, float],
    curve_b_by_tenor_pct: dict[str, float],
) -> dict[str, float]:
    """Return tenor-level curve A minus curve B spreads in basis points."""
    common_tenors = [tenor for tenor in curve_a_by_tenor_pct if tenor in curve_b_by_tenor_pct]
    return {tenor: curve_spread_bp(curve_a_by_tenor_pct[tenor], curve_b_by_tenor_pct[tenor]) for tenor in common_tenors}


def benchmark_spread_decomposition_bp(
    secured_unsecured_bp: float,
    repo_reference_bp: float,
    transition_overlay_bp: float,
) -> dict[str, float]:
    """Return additive benchmark spread decomposition."""
    total = secured_unsecured_bp + repo_reference_bp + transition_overlay_bp
    return {
        "secured_unsecured_basis_bp": secured_unsecured_bp,
        "repo_reference_basis_bp": repo_reference_bp,
        "transition_overlay_bp": transition_overlay_bp,
        "total_benchmark_spread_bp": total,
    }
