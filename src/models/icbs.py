"""Intra-currency basis swap (ICBS) engine for teaching Chapter workflows.

Pedagogical simplification:
- Uses simple spread differences between floating indices.
- Ignores convexity and collateral optionality adjustments.
"""

from __future__ import annotations

from core.types import ICBSState, ICBSTermPoint


SIMPLIFICATION_NOTES = [
    "Basis is represented as a simple difference between two floating benchmarks.",
    "Term structure interpolation/bootstrapping is omitted; each maturity is handled pointwise.",
    "Carry and rolldown are linearized and exclude convexity, day-count, and collateral effects.",
]



def intra_currency_basis(
    float_leg_a_pct: float,
    float_leg_b_pct: float,
    reference_rate_adjustment_bp: float = 0.0,
) -> float:
    """Compute ICBS level in bp from two floating legs and reference adjustment."""
    return (float_leg_a_pct - float_leg_b_pct) * 100.0 - reference_rate_adjustment_bp



def current_same_currency_basis_from_benchmarks(
    benchmark_a_pct: float,
    benchmark_b_pct: float,
    reference_rate_adjustment_bp: float = 0.0,
) -> float:
    """Return the current same-currency basis (bp) from two floating benchmarks.

    Simplification note:
    - Treats the observed benchmark differential as the tradable basis level.
    """
    return intra_currency_basis(
        float_leg_a_pct=benchmark_a_pct,
        float_leg_b_pct=benchmark_b_pct,
        reference_rate_adjustment_bp=reference_rate_adjustment_bp,
    )



def basis_term_structure_from_maturity_grid(
    maturity_years: list[float],
    benchmark_a_curve_pct: list[float],
    benchmark_b_curve_pct: list[float],
    reference_rate_adjustment_bp: float = 0.0,
) -> list[ICBSTermPoint]:
    """Build a basis term structure over a maturity grid.

    Simplification notes:
    - Each grid point is treated independently.
    - No smoothing/curve fitting is applied.
    """
    if not (len(maturity_years) == len(benchmark_a_curve_pct) == len(benchmark_b_curve_pct)):
        raise ValueError("Maturity and benchmark curves must have identical lengths.")

    return [
        ICBSTermPoint(
            maturity_years=maturity,
            benchmark_a_pct=curve_a,
            benchmark_b_pct=curve_b,
            basis_bp=current_same_currency_basis_from_benchmarks(
                benchmark_a_pct=curve_a,
                benchmark_b_pct=curve_b,
                reference_rate_adjustment_bp=reference_rate_adjustment_bp,
            ),
        )
        for maturity, curve_a, curve_b in zip(
            maturity_years,
            benchmark_a_curve_pct,
            benchmark_b_curve_pct,
            strict=True,
        )
    ]



def carry_estimate(
    current_basis_bp: float,
    expected_basis_bp: float,
    horizon_years: float,
) -> float:
    """Estimate carry (bp over horizon) from basis accrual and expected convergence.

    Simplification notes:
    - Carry is linearized as current basis accrual plus convergence to expected basis.
    - Timing of coupon resets and compounding conventions are ignored.
    """
    return current_basis_bp * horizon_years + (expected_basis_bp - current_basis_bp)



def rolldown_estimate(
    current_maturity_years: float,
    roll_horizon_years: float,
    term_structure: list[ICBSTermPoint],
) -> float:
    """Estimate basis rolldown (bp) by moving along the observed term structure.

    Simplification notes:
    - Uses nearest available maturity points (no interpolation).
    - Assumes the term structure shape is unchanged over the roll horizon.
    """
    if roll_horizon_years < 0.0:
        raise ValueError("roll_horizon_years must be non-negative.")

    rolled_maturity = max(current_maturity_years - roll_horizon_years, 0.0)

    current_point = min(term_structure, key=lambda p: abs(p.maturity_years - current_maturity_years))
    rolled_point = min(term_structure, key=lambda p: abs(p.maturity_years - rolled_maturity))
    return rolled_point.basis_bp - current_point.basis_bp



def icbs_chapter_payload(
    benchmark_a_name: str,
    benchmark_b_name: str,
    benchmark_a_pct: float,
    benchmark_b_pct: float,
    maturity_years: list[float],
    benchmark_a_curve_pct: list[float],
    benchmark_b_curve_pct: list[float],
    current_maturity_years: float,
    roll_horizon_years: float,
    expected_basis_bp: float,
    carry_horizon_years: float,
    reference_rate_adjustment_bp: float = 0.0,
) -> ICBSState:
    """Return chapter-ready ICBS payload as a typed dataclass.

    The payload bundles current basis, term structure, carry estimate, and rolldown
    using a teaching-friendly linear approximation framework.
    """
    current_basis = current_same_currency_basis_from_benchmarks(
        benchmark_a_pct=benchmark_a_pct,
        benchmark_b_pct=benchmark_b_pct,
        reference_rate_adjustment_bp=reference_rate_adjustment_bp,
    )
    structure = basis_term_structure_from_maturity_grid(
        maturity_years=maturity_years,
        benchmark_a_curve_pct=benchmark_a_curve_pct,
        benchmark_b_curve_pct=benchmark_b_curve_pct,
        reference_rate_adjustment_bp=reference_rate_adjustment_bp,
    )

    return ICBSState(
        benchmark_a_name=benchmark_a_name,
        benchmark_b_name=benchmark_b_name,
        current_basis_bp=current_basis,
        term_structure=structure,
        carry_estimate_bp=carry_estimate(
            current_basis_bp=current_basis,
            expected_basis_bp=expected_basis_bp,
            horizon_years=carry_horizon_years,
        ),
        rolldown_estimate_bp=rolldown_estimate(
            current_maturity_years=current_maturity_years,
            roll_horizon_years=roll_horizon_years,
            term_structure=structure,
        ),
        simplification_notes=SIMPLIFICATION_NOTES,
    )
