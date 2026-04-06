from __future__ import annotations

import streamlit as st

from core.types import ChapterExportState
from .base import SimpleChapter
from src.models.shadow_costs import capital_shadow_state


class Chapter18(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(chapter_id="18", title="Chapter 18: Capital shadow costs", objective="Price capital usage and funding frictions into final trade acceptance decisions.")

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Spread gap", "equation": "spread_gap_bp=observed_spread_bp-structural_fair_spread_bp"},
            {"name": "Capital charge ($)", "equation": "capital_charge_$=capital_used*capital_hurdle"},
            {"name": "Capital charge (bp)", "equation": "capital_charge_bp=capital_charge_$/spread_bp_value_$perbp"},
            {
                "name": "Adjusted executable spread residual",
                "equation": "adj_residual_bp=spread_gap_bp-shadow_funding_cost_bp-capital_charge_bp-liquidity_wedge_bp-repo_stress_add_on_bp",
            },
            {"name": "Approval gate", "equation": "approve if (adj_residual_bp>threshold_bp) and (not non_monetisable_block) else do_not_approve"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Estimate structural fair spread from cross-chapter decomposition and collect observed executable spread.",
            "Translate monetisable frictions into additive wedges: shadow funding cost, capital charge, liquidity wedge, and repo stress add-on.",
            "Compute adjusted executable spread residual and compare it versus a minimum monetisable threshold.",
            "Apply approval gate: any non-monetisable mispricing blocker (mandate, legal, model-governance, ops constraints) overrides positive residuals.",
            "Boundary reminder: this chapter is a first-pass additive approximation, not a full balance-sheet optimizer.",
        ]

    def interactive_lab(self) -> dict[str, dict[str, float | bool | str]]:
        structural_fair_spread_bp = st.number_input("Structural fair spread (bp)", value=38.0, step=0.5, key="fair_18")
        observed_spread_bp = st.number_input("Observed spread (bp)", value=52.0, step=0.5, key="obs_18")
        shadow_funding_cost_bp = st.number_input("Shadow funding cost (bp)", value=5.0, step=0.5, key="fund_18")
        capital_used = st.number_input("Allocated economic capital ($)", value=8_000_000.0, step=250_000.0, key="cap_18")
        capital_hurdle = st.slider("Capital hurdle rate", min_value=0.05, max_value=0.25, value=0.13, step=0.005, key="hurdle_18")
        spread_bp_value_dollars = st.number_input("Annualized $ value per 1bp spread (risk conversion)", value=25_000.0, step=1_000.0, key="bp_value_18")
        liquidity_wedge_bp = st.number_input("Liquidity wedge (bp)", value=3.0, step=0.5, key="liq_18")
        repo_stress_add_on_bp = st.number_input("Repo stress add-on (bp)", value=2.0, step=0.5, key="repo_18")
        monetisable_threshold_bp = st.number_input("Minimum monetisable residual threshold (bp)", value=0.0, step=0.5, key="threshold_18")
        non_monetisable_block = st.checkbox(
            "Non-monetisable blocker present (mandate/legal/model risk/operational)?",
            value=False,
            key="block_18",
        )

        state = capital_shadow_state(
            structural_fair_spread_bp=structural_fair_spread_bp,
            observed_spread_bp=observed_spread_bp,
            shadow_funding_cost_bp=shadow_funding_cost_bp,
            capital_used=capital_used,
            capital_hurdle=capital_hurdle,
            liquidity_wedge_bp=liquidity_wedge_bp,
            repo_stress_add_on_bp=repo_stress_add_on_bp,
            spread_bp_value_dollars=spread_bp_value_dollars,
            monetisable_threshold_bp=monetisable_threshold_bp,
            non_monetisable_block=non_monetisable_block,
        )

        st.metric("Spread gap (bp)", f"{state.spread_gap_bp:,.2f}")
        st.metric("Capital charge ($)", f"{state.capital_charge_dollars:,.0f}")
        st.metric("Capital charge (bp)", f"{state.capital_charge_bp:,.2f}")
        st.metric("Adjusted executable spread residual (bp)", f"{state.adjusted_executable_spread_residual_bp:,.2f}")
        st.metric("Approval gate", state.approval_gate)

        st.caption(
            "Teaching note: positive residual does not guarantee approval when mispricing is non-monetisable "
            "(e.g., documentation constraints, hard mandate exclusions, unresolved model-governance findings)."
        )
        st.info(
            "Simplification boundary: this additive wedge framework is pedagogical. Real desks often apply "
            "nonlinear capital interactions, inventory state-dependence, and scenario-dependent execution penalties."
        )

        return {
            "inputs": {
                "structural_fair_spread_bp": structural_fair_spread_bp,
                "observed_spread_bp": observed_spread_bp,
                "shadow_funding_cost_bp": shadow_funding_cost_bp,
                "capital_used": capital_used,
                "capital_hurdle": capital_hurdle,
                "spread_bp_value_dollars": spread_bp_value_dollars,
                "liquidity_wedge_bp": liquidity_wedge_bp,
                "repo_stress_add_on_bp": repo_stress_add_on_bp,
                "monetisable_threshold_bp": monetisable_threshold_bp,
                "non_monetisable_block": non_monetisable_block,
            },
            "outputs": {
                **state.model_dump(),
            },
        }

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            schema_name="ShadowCostState",
            signals=[
                "structural_fair_spread_bp",
                "observed_spread_bp",
                "shadow_funding_cost_bp",
                "capital_charge_bp",
                "liquidity_wedge_bp",
                "repo_stress_add_on_bp",
                "adjusted_executable_spread_residual_bp",
                "approval_gate",
            ],
            usage="Final chapter output for governance, audit trail, and portfolio allocation handoff.",
        )
