"""CDS and pure-credit extraction helpers for Chapter 13.

Pedagogical simplification:
- Uses a flat-hazard approximation from spread and recovery.
- Useful for teaching relative-value decomposition, not desk pricing.
"""

from __future__ import annotations

from core.types import PureCreditState, RecoverySensitivityPoint


EPS = 1e-6
DEFAULT_RECOVERY_SWEEP = (0.2, 0.3, 0.4, 0.5, 0.6)
SIMPLIFICATION_NOTES = [
    "Flat hazard proxy inferred from spread/(1-recovery).",
    "Constant recovery assumption over the CDS horizon.",
    "No accrual-on-default or premium/protection leg timing effects.",
]


def pure_credit_spread(observed_spread_bp: float, liquidity_component_bp: float, technical_component_bp: float) -> float:
    """Strip non-default premia from observed spread (bp)."""
    return observed_spread_bp - liquidity_component_bp - technical_component_bp


def implied_hazard_rate(pure_credit_bp: float, recovery_rate: float) -> float:
    """Map pure credit spread (bp) to a flat annualized hazard proxy.

    Pedagogical simplification:
    - Assumes a flat hazard term structure.
    - Uses a constant recovery rate.
    - Ignores accrual-on-default and detailed protection-leg timing.
    """
    return pure_credit_bp / (10_000.0 * max(1.0 - recovery_rate, EPS))


def hazard_proxy_pedagogical(purified_spread_bp: float, recovery_rate: float) -> float:
    """Pedagogical hazard helper under a flat-hazard/constant-recovery approximation."""
    return implied_hazard_rate(purified_spread_bp, recovery_rate)


def recovery_sensitivity_d_hazard_d_recovery(purified_spread_bp: float, recovery_rate: float) -> float:
    """Return d(hazard proxy)/d(recovery) under simplified Chapter 13 assumptions."""
    denominator = max(1.0 - recovery_rate, EPS)
    return purified_spread_bp / (10_000.0 * (denominator**2))


def recovery_sensitivity_scenarios(
    purified_spread_bp: float,
    recovery_grid: tuple[float, ...] = DEFAULT_RECOVERY_SWEEP,
) -> list[RecoverySensitivityPoint]:
    """Build a recovery scenario table of hazard proxy and local sensitivity."""
    return [
        RecoverySensitivityPoint(
            recovery_rate=recovery,
            hazard_proxy=hazard_proxy_pedagogical(
                purified_spread_bp=purified_spread_bp,
                recovery_rate=recovery,
            ),
            d_hazard_d_recovery=recovery_sensitivity_d_hazard_d_recovery(
                purified_spread_bp=purified_spread_bp,
                recovery_rate=recovery,
            ),
        )
        for recovery in recovery_grid
    ]


def compute_cds_state(
    observed_spread_bp: float,
    liquidity_component_bp: float,
    technical_component_bp: float,
    recovery_rate: float,
    recovery_grid: tuple[float, ...] = DEFAULT_RECOVERY_SWEEP,
) -> PureCreditState:
    """Compute chapter-facing pure-credit state for CDS decomposition.

    Simplified assumptions:
    - Flat hazard proxy inferred from a single purified spread level.
    - Constant recovery rate.
    - No accrual-on-default or protection-leg timing conventions.
    """
    purified_spread_bp = pure_credit_spread(
        observed_spread_bp=observed_spread_bp,
        liquidity_component_bp=liquidity_component_bp,
        technical_component_bp=technical_component_bp,
    )
    hazard_proxy = hazard_proxy_pedagogical(
        purified_spread_bp=purified_spread_bp,
        recovery_rate=recovery_rate,
    )
    local_sensitivity = recovery_sensitivity_d_hazard_d_recovery(
        purified_spread_bp=purified_spread_bp,
        recovery_rate=recovery_rate,
    )

    return PureCreditState(
        observed_spread_bp=observed_spread_bp,
        liquidity_component_bp=liquidity_component_bp,
        technical_component_bp=technical_component_bp,
        purified_spread_bp=purified_spread_bp,
        hazard_proxy=hazard_proxy,
        recovery_rate=recovery_rate,
        d_hazard_d_recovery=local_sensitivity,
        recovery_sensitivity_scenarios=recovery_sensitivity_scenarios(
            purified_spread_bp=purified_spread_bp,
            recovery_grid=recovery_grid,
        ),
        simplification_notes=SIMPLIFICATION_NOTES,
    )


def cds_bond_basis(cds_spread_bp: float, bond_implied_credit_bp: float) -> float:
    """Return CDS-bond basis in basis points."""
    return cds_spread_bp - bond_implied_credit_bp
