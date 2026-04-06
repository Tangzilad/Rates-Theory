from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from .common import SimpleChapter
from .swap_basis import package_state
from src.models.cds import implied_hazard_rate, pure_credit_spread


class Chapter13(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(
            chapter_id="13",
            title="Chapter 13: Pure-credit extraction",
            objective="Isolate default-risk premium by stripping liquidity and technical basis effects.",
        )

    def equation_set(self) -> List[Dict[str, str]]:
        return [
            {"name": "Pure credit", "equation": "pure_credit_bp=observed_spread_bp-liquidity_bp-technical_bp"},
            {"name": "Default intensity", "equation": "hazard= pure_credit_bp / (10000*(1-recovery))"},
        ]

    def derivation_steps(self) -> List[str]:
        return [
            "Start from observed package spread and estimate non-default premia.",
            "Subtract liquidity and technical components to isolate pure-credit spread.",
            "Map pure-credit spread to a hazard-rate proxy using recovery assumptions.",
        ]

    def interactive_lab(self) -> Dict[str, Any]:
        st.caption("Pedagogical simplification: pure-credit spread and hazard mapping use a flat-intensity approximation.")
        observed_spread = st.number_input("Observed package spread (bp)", value=118.0, step=1.0, key="obs_13")
        liquidity_component = st.number_input("Liquidity premium (bp)", value=21.0, step=1.0, key="liq_13")
        technical_component = st.number_input("Technical basis (bp)", value=9.0, step=1.0, key="tech_13")
        recovery = st.slider("Recovery assumption", min_value=0.2, max_value=0.7, value=0.4, step=0.01, key="rec_13")

        pure_credit = pure_credit_spread(observed_spread, liquidity_component, technical_component)
        hazard = implied_hazard_rate(pure_credit, recovery)

        st.metric("Pure-credit spread (bp)", f"{pure_credit:.2f}")
        st.metric("Implied hazard (annualized)", f"{hazard:.4%}")

        return {
            "inputs": {
                "observed_spread_bp": observed_spread,
                "liquidity_component_bp": liquidity_component,
                "technical_component_bp": technical_component,
                "recovery_rate": recovery,
            },
            "outputs": {"pure_credit_bp": pure_credit, "implied_hazard_rate": hazard},
        }

    def failure_modes(self) -> List[Dict[str, str]]:
        return [
            {"mode": "Double-counted liquidity premium", "mitigation": "Use orthogonal liquidity proxies and enforce additivity checks."},
            {"mode": "Unstable recovery assumptions", "mitigation": "Run scenario bands and propagate uncertainty into hazard estimates."},
        ]

    def exports_to_next_chapter(self) -> Dict[str, Any]:
        return package_state(
            "PureCreditState",
            {"pure_credit_bp": 0.0, "implied_hazard_rate": 0.0},
            "Used by execution chapter to convert analytics into tradeable risk budgets.",
        )
