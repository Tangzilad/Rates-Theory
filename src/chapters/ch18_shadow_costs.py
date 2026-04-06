from __future__ import annotations

import streamlit as st

from core.types import ChapterExportState
from .base import SimpleChapter
from src.models.shadow_costs import capital_shadow_state


class Chapter18(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(
            chapter_id="18",
            title="Chapter 18: Other factors affecting swap spreads (executable realism)",
            objective="Bridge theoretical spread value to executable value by adding capital, leverage, repo stress, liquidity wedges, and non-monetisable blockers.",
        )

    def key_takeaway(self) -> str:
        return "A model can be right and still untradeable: execution value is theoretical value minus monetisable frictions, then filtered by non-monetisable constraints."

    def learn_focus(self) -> list[str]:
        return [
            "Leverage and capital constraints create shadow costs not visible in clean pricing formulas.",
            "Repo stress and liquidity wedges can dominate executable spread residuals.",
            "Non-monetisable blockers (mandate/legal/model governance) can veto otherwise attractive trades.",
        ]

    def derive_focus(self) -> list[str]:
        return [
            "Start from theoretical spread gap (observed - structural fair).",
            "Subtract monetisable wedges additively (funding, capital, liquidity, repo stress).",
            "Apply governance gate for non-monetisable blockers.",
        ]

    def trade_use_focus(self) -> list[str]:
        return [
            "Run execution residual before every go/no-go decision.",
            "Report monetisable and non-monetisable reasons separately for auditability.",
            "Use residual thresholds that reflect desk balance-sheet scarcity.",
        ]

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Theoretical spread gap", "equation": "spread_gap_bp=observed_spread_bp-structural_fair_spread_bp"},
            {"name": "Capital charge (bp)", "equation": "capital_charge_bp=(capital_used*capital_hurdle)/spread_bp_value_$perbp"},
            {
                "name": "Executable residual",
                "equation": "adj_residual_bp=spread_gap_bp-shadow_funding_cost_bp-capital_charge_bp-liquidity_wedge_bp-repo_stress_add_on_bp",
            },
            {"name": "Approval gate", "equation": "approve if adj_residual_bp>threshold_bp and no_non_monetisable_block"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Compute theoretical spread gap from structural fair value and observed market spread.",
            "Map leverage/capital usage into a bp-equivalent charge via desk conversion value.",
            "Subtract shadow funding, liquidity wedge, and repo stress to get executable residual.",
            "Compare residual to monetisable threshold set by desk hurdle.",
            "Override with non-monetisable blocker gate when constraints are hard.",
        ]

    def interactive_lab(self) -> dict[str, dict[str, float | bool | str]]:
        st.markdown("#### 1) Theoretical vs executable spread")
        structural_fair_spread_bp = st.number_input("Structural fair spread (bp)", value=38.0, step=0.5, key="fair_18")
        observed_spread_bp = st.number_input("Observed spread (bp)", value=52.0, step=0.5, key="obs_18")

        st.markdown("#### 2) Monetisable wedges")
        c1, c2, c3 = st.columns(3)
        shadow_funding_cost_bp = c1.number_input("Shadow funding cost (bp)", value=5.0, step=0.5, key="fund_18")
        liquidity_wedge_bp = c2.number_input("Liquidity wedge (bp)", value=3.0, step=0.5, key="liq_18")
        repo_stress_add_on_bp = c3.number_input("Repo stress add-on (bp)", value=2.0, step=0.5, key="repo_18")

        st.markdown("#### 3) Capital and leverage constraints")
        capital_used = st.number_input("Allocated economic capital ($)", value=8_000_000.0, step=250_000.0, key="cap_18")
        capital_hurdle = st.slider("Capital hurdle rate", min_value=0.05, max_value=0.25, value=0.13, step=0.005, key="hurdle_18")
        spread_bp_value_dollars = st.number_input("$ value per 1bp spread", value=25_000.0, step=1_000.0, key="bp_value_18")
        monetisable_threshold_bp = st.number_input("Minimum executable threshold (bp)", value=0.0, step=0.5, key="threshold_18")

        st.markdown("#### 4) Non-monetisable blockers")
        non_monetisable_block = st.checkbox(
            "Blocker present (mandate/legal/model-governance/ops)?",
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
        st.metric("Capital charge (bp)", f"{state.capital_charge_bp:,.2f}")
        st.metric("Adjusted executable residual (bp)", f"{state.adjusted_executable_spread_residual_bp:,.2f}")
        st.metric("Approval gate", state.approval_gate)

        st.dataframe(
            [
                {"component": "theoretical_gap", "bp": state.spread_gap_bp},
                {"component": "shadow_funding", "bp": -shadow_funding_cost_bp},
                {"component": "capital_charge", "bp": -state.capital_charge_bp},
                {"component": "liquidity_wedge", "bp": -liquidity_wedge_bp},
                {"component": "repo_stress", "bp": -repo_stress_add_on_bp},
                {"component": "executable_residual", "bp": state.adjusted_executable_spread_residual_bp},
            ],
            use_container_width=True,
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
            "outputs": {**state.model_dump()},
        }

    def failure_modes(self) -> list[dict[str, str]]:
        return [
            {"mode": "Confusing theoretical fair value with executable value", "mitigation": "Always run wedge-adjusted residual and approval gate."},
            {"mode": "Ignoring leverage/capital scarcity", "mitigation": "Convert capital usage into bp-equivalent before ranking trades."},
            {"mode": "Treating non-monetisable blockers as optional", "mitigation": "Use hard blocker override in governance process."},
        ]

    def assessment(self) -> list[dict[str, str]]:
        return [
            {
                "prompt": "Why can adjusted residual be positive yet trade be rejected?",
                "expected": "Because non-monetisable blockers can override monetisable economics in real execution governance.",
            }
        ]

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
            usage="Capstone output: explains theoretical-versus-executable gap and final governance gate.",
        )
