"""Capital shadow-cost engine for Chapter 18 decisions.

Pedagogical simplifications and boundaries:
- Uses a static fair spread estimate and one observed execution spread snapshot.
- Aggregates funding, liquidity, and repo stress frictions as additive wedges.
- Uses a single scalar capital hurdle (no nonlinear RWA/leverage interactions).
- Non-monetisable mispricings (legal constraints, mandate restrictions, model risk,
  operational bottlenecks) are represented as approval gates rather than dollars.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ApprovalGate = Literal["approve", "do_not_approve"]


@dataclass(frozen=True)
class ShadowCostState:
    structural_fair_spread_bp: float
    observed_spread_bp: float
    spread_gap_bp: float
    spread_bp_value_dollars: float
    shadow_funding_cost_bp: float
    capital_charge_dollars: float
    capital_charge_bp: float
    liquidity_wedge_bp: float
    repo_stress_add_on_bp: float
    adjusted_executable_spread_residual_bp: float
    approval_gate: ApprovalGate


def capital_shadow_state(
    structural_fair_spread_bp: float,
    observed_spread_bp: float,
    shadow_funding_cost_bp: float,
    capital_used: float,
    capital_hurdle: float,
    liquidity_wedge_bp: float,
    repo_stress_add_on_bp: float,
    spread_bp_value_dollars: float = 25_000.0,
    monetisable_threshold_bp: float = 0.0,
    non_monetisable_block: bool = False,
) -> ShadowCostState:
    """Compute a spread-space shadow-cost state and approval gate.

    The adjusted executable spread residual isolates the monetisable component:

      adjusted_residual =
          (observed_spread - structural_fair_spread)
          - shadow_funding_cost
          - capital_charge
          - liquidity_wedge
          - repo_stress_add_on

    If a non-monetisable block is present, the gate is forced to ``do_not_approve``
    even when the residual is positive.
    """
    if spread_bp_value_dollars <= 0:
        msg = "spread_bp_value_dollars must be positive."
        raise ValueError(msg)

    spread_gap_bp = observed_spread_bp - structural_fair_spread_bp
    capital_charge_dollars = capital_used * capital_hurdle
    capital_charge_bp = capital_charge_dollars / spread_bp_value_dollars
    adjusted_residual_bp = (
        spread_gap_bp
        - shadow_funding_cost_bp
        - capital_charge_bp
        - liquidity_wedge_bp
        - repo_stress_add_on_bp
    )
    monetisable_pass = adjusted_residual_bp > monetisable_threshold_bp
    approval_gate: ApprovalGate = (
        "approve" if (monetisable_pass and not non_monetisable_block) else "do_not_approve"
    )
    return ShadowCostState(
        structural_fair_spread_bp=structural_fair_spread_bp,
        observed_spread_bp=observed_spread_bp,
        spread_gap_bp=spread_gap_bp,
        spread_bp_value_dollars=spread_bp_value_dollars,
        shadow_funding_cost_bp=shadow_funding_cost_bp,
        capital_charge_dollars=capital_charge_dollars,
        capital_charge_bp=capital_charge_bp,
        liquidity_wedge_bp=liquidity_wedge_bp,
        repo_stress_add_on_bp=repo_stress_add_on_bp,
        adjusted_executable_spread_residual_bp=adjusted_residual_bp,
        approval_gate=approval_gate,
    )
