from __future__ import annotations

import streamlit as st

from .base import SimpleChapter


class Chapter13(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(chapter_id="13", title="Chapter 13: Pure-credit extraction", objective="Isolate default-risk premium by stripping liquidity and technical basis effects.")

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Pure credit", "equation": "pure_credit_bp=observed_spread_bp-liquidity_bp-technical_bp"},
            {"name": "Default intensity", "equation": "hazard= pure_credit_bp / (10000*(1-recovery))"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Start from observed package spread and estimate non-default premia.",
            "Subtract liquidity and technical components to isolate pure-credit spread.",
            "Map pure-credit spread to a hazard-rate proxy using recovery assumptions.",
        ]

    def interactive_lab(self) -> dict[str, dict[str, float]]:
        observed_spread = st.number_input("Observed package spread (bp)", value=118.0, step=1.0, key="obs_13")
        liquidity_component = st.number_input("Liquidity premium (bp)", value=21.0, step=1.0, key="liq_13")
        technical_component = st.number_input("Technical basis (bp)", value=9.0, step=1.0, key="tech_13")
        recovery = st.slider("Recovery assumption", min_value=0.2, max_value=0.7, value=0.4, step=0.01, key="rec_13")

        pure_credit = observed_spread - liquidity_component - technical_component
        hazard = pure_credit / (10_000.0 * max(1e-6, 1.0 - recovery))

        st.metric("Pure-credit spread (bp)", f"{pure_credit:.2f}")
        st.metric("Implied hazard (annualized)", f"{hazard:.4%}")
        return {"inputs": {"observed_spread_bp": observed_spread, "liquidity_component_bp": liquidity_component, "technical_component_bp": technical_component, "recovery_rate": recovery}, "outputs": {"pure_credit_bp": pure_credit, "implied_hazard_rate": hazard}}

    def exports_to_next_chapter(self) -> dict[str, object]:
        return {"schema_name": "PureCreditState", "signals": ["pure_credit_bp", "implied_hazard_rate"], "usage": "Used by execution chapter to convert analytics into tradeable risk budgets."}
