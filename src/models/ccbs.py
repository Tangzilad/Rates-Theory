"""Cross-currency basis swap (CCBS) engine for chapter-level analytics.

Pedagogical simplification:
- Computes basis from floating-leg differential and FX-forward implied rate.
- Treats credit/repo/reference frictions as additive bp penalties.
"""

from __future__ import annotations

from dataclasses import dataclass


SIMPLIFICATION_NOTES = [
    "Convention handling is sign-based and does not replicate full dealer quote sheets.",
    "Synthetic domestic hedged yield uses additive decomposition of foreign yield, FX hedge, and basis.",
    "Shock sensitivity assumes linear pass-through from basis shocks into synthetic yield.",
]


@dataclass(frozen=True)
class CCBSSensitivityPoint:
    basis_shock_bp: float
    shocked_basis_bp: float
    shocked_synthetic_domestic_yield_pct: float


@dataclass(frozen=True)
class CCBSChapterPayload:
    quote_convention: str
    basis_bp: float
    synthetic_domestic_hedged_yield_pct: float
    sensitivity_table: list[CCBSSensitivityPoint]
    simplification_notes: list[str]



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



def implied_cross_currency_basis(
    domestic_float_rate_pct: float,
    foreign_float_rate_pct: float,
    fx_forward_implied_rate_pct: float,
    quote_convention: str = "domestic_minus_hedged_foreign",
    credit_adjustment_bp: float = 0.0,
    repo_adjustment_bp: float = 0.0,
    reference_rate_adjustment_bp: float = 0.0,
) -> float:
    """Return implied cross-currency basis (bp) with explicit quote-convention handling.

    Supported conventions:
    - ``domestic_minus_hedged_foreign``: positive = domestic leg richer.
    - ``hedged_foreign_minus_domestic``: sign-flipped market alternative.

    Simplification note:
    - Convention logic is implemented as deterministic sign mapping.
    """
    basis_bp = cross_currency_basis(
        domestic_float_rate_pct=domestic_float_rate_pct,
        foreign_float_rate_pct=foreign_float_rate_pct,
        fx_forward_implied_rate_pct=fx_forward_implied_rate_pct,
        credit_adjustment_bp=credit_adjustment_bp,
        repo_adjustment_bp=repo_adjustment_bp,
        reference_rate_adjustment_bp=reference_rate_adjustment_bp,
    )

    if quote_convention == "domestic_minus_hedged_foreign":
        return basis_bp
    if quote_convention == "hedged_foreign_minus_domestic":
        return -basis_bp
    raise ValueError(f"Unsupported quote_convention: {quote_convention}")



def synthetic_domestic_hedged_yield(
    foreign_leg_yield_pct: float,
    fx_hedge_cost_pct: float,
    basis_bp: float,
    quote_convention: str = "domestic_minus_hedged_foreign",
) -> float:
    """Compute synthetic domestic hedged yield from foreign carry, FX hedge, and basis.

    Simplification notes:
    - Basis contribution is converted linearly from bp to percent.
    - Sign follows selected convention.
    """
    basis_sign = 1.0
    if quote_convention == "hedged_foreign_minus_domestic":
        basis_sign = -1.0
    elif quote_convention != "domestic_minus_hedged_foreign":
        raise ValueError(f"Unsupported quote_convention: {quote_convention}")

    return foreign_leg_yield_pct + fx_hedge_cost_pct + basis_sign * (basis_bp / 100.0)



def basis_shock_sensitivity(
    base_basis_bp: float,
    foreign_leg_yield_pct: float,
    fx_hedge_cost_pct: float,
    shocks_bp: list[float],
    quote_convention: str = "domestic_minus_hedged_foreign",
) -> list[CCBSSensitivityPoint]:
    """Return sensitivity table under basis widening/narrowing shocks.

    Simplification note:
    - Assumes one-for-one passthrough from basis shocks to synthetic hedged yield.
    """
    points: list[CCBSSensitivityPoint] = []
    for shock in shocks_bp:
        shocked_basis = base_basis_bp + shock
        points.append(
            CCBSSensitivityPoint(
                basis_shock_bp=shock,
                shocked_basis_bp=shocked_basis,
                shocked_synthetic_domestic_yield_pct=synthetic_domestic_hedged_yield(
                    foreign_leg_yield_pct=foreign_leg_yield_pct,
                    fx_hedge_cost_pct=fx_hedge_cost_pct,
                    basis_bp=shocked_basis,
                    quote_convention=quote_convention,
                ),
            )
        )
    return points



def ccbs_chapter_payload(
    domestic_float_rate_pct: float,
    foreign_float_rate_pct: float,
    fx_forward_implied_rate_pct: float,
    foreign_leg_yield_pct: float,
    fx_hedge_cost_pct: float,
    shocks_bp: list[float],
    quote_convention: str = "domestic_minus_hedged_foreign",
    credit_adjustment_bp: float = 0.0,
    repo_adjustment_bp: float = 0.0,
    reference_rate_adjustment_bp: float = 0.0,
) -> CCBSChapterPayload:
    """Return chapter-ready CCBS payload as a typed dataclass.

    Payload contains convention-aware implied basis, synthetic domestic hedged
    yield, and stress sensitivity under basis widening/narrowing shocks.
    """
    basis_bp = implied_cross_currency_basis(
        domestic_float_rate_pct=domestic_float_rate_pct,
        foreign_float_rate_pct=foreign_float_rate_pct,
        fx_forward_implied_rate_pct=fx_forward_implied_rate_pct,
        quote_convention=quote_convention,
        credit_adjustment_bp=credit_adjustment_bp,
        repo_adjustment_bp=repo_adjustment_bp,
        reference_rate_adjustment_bp=reference_rate_adjustment_bp,
    )
    synthetic_yield = synthetic_domestic_hedged_yield(
        foreign_leg_yield_pct=foreign_leg_yield_pct,
        fx_hedge_cost_pct=fx_hedge_cost_pct,
        basis_bp=basis_bp,
        quote_convention=quote_convention,
    )
    sensitivity = basis_shock_sensitivity(
        base_basis_bp=basis_bp,
        foreign_leg_yield_pct=foreign_leg_yield_pct,
        fx_hedge_cost_pct=fx_hedge_cost_pct,
        shocks_bp=shocks_bp,
        quote_convention=quote_convention,
    )

    return CCBSChapterPayload(
        quote_convention=quote_convention,
        basis_bp=basis_bp,
        synthetic_domestic_hedged_yield_pct=synthetic_yield,
        sensitivity_table=sensitivity,
        simplification_notes=SIMPLIFICATION_NOTES,
    )
