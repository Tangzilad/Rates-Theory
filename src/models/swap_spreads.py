"""Swap spread and basis calculation utilities."""

from __future__ import annotations


def asset_swap_spread(
    par_swap_rate: float,
    bond_yield: float,
    credit_adjustment: float = 0.0,
    repo_adjustment: float = 0.0,
) -> float:
    """Compute asset swap spread with optional credit/repo adjustments."""
    return par_swap_rate - bond_yield - credit_adjustment - repo_adjustment


def intra_currency_basis(
    float_leg_a: float,
    float_leg_b: float,
    reference_rate_adjustment: float = 0.0,
) -> float:
    """Compute basis between two floating-rate indices in same currency."""
    return float_leg_a - float_leg_b - reference_rate_adjustment


def cross_currency_basis(
    domestic_float_rate: float,
    foreign_float_rate: float,
    fx_forward_implied_rate: float,
    credit_adjustment: float = 0.0,
    repo_adjustment: float = 0.0,
    reference_rate_adjustment: float = 0.0,
) -> float:
    """Compute cross-currency basis net of credit/repo/reference-rate adjustments."""
    raw_basis = domestic_float_rate - (foreign_float_rate + fx_forward_implied_rate)
    total_adj = credit_adjustment + repo_adjustment + reference_rate_adjustment
    return raw_basis - total_adj
