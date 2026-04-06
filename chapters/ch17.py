from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from .common import SimpleChapter
from .swap_basis import package_state


class Chapter17(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(
            chapter_id="17",
            title="Chapter 17: Scenario and stress engine",
            objective="Quantify trade robustness under spread, rates, and liquidity shock combinations.",
        )

    def equation_set(self) -> List[Dict[str, str]]:
        return [
            {"name": "Stress P&L", "equation": "stress_pnl=-(spread_shock_bp*cs01 + rate_shock_bp*dv01)"},
            {"name": "Liquidity add-on", "equation": "total_stress=stress_pnl-liquidity_penalty"},
        ]

    def derivation_steps(self) -> List[str]:
        return [
            "Specify spread and rate shocks for coherent stress scenarios.",
            "Apply CS01 and DV01 sensitivities to compute mark-to-market hit.",
            "Add liquidity liquidation penalty for full stressed-loss estimate.",
        ]

    def interactive_lab(self) -> Dict[str, Any]:
        spread_shock = st.number_input("Spread shock (bp)", value=75.0, step=5.0, key="ss_17")
        rate_shock = st.number_input("Rate shock (bp)", value=40.0, step=5.0, key="rs_17")
        cs01 = st.number_input("CS01 ($/bp)", value=82_000.0, step=2_000.0, key="cs01_17")
        dv01 = st.number_input("DV01 ($/bp)", value=31_000.0, step=1_000.0, key="dv01_17")
        liquidity_penalty = st.number_input("Liquidity liquidation penalty ($)", value=350_000.0, step=25_000.0, key="liq_17")

        core_stress = -((spread_shock * cs01) + (rate_shock * dv01))
        total_stress = core_stress - liquidity_penalty

        st.metric("Core stress P&L ($)", f"{core_stress:,.0f}")
        st.metric("Total stressed P&L ($)", f"{total_stress:,.0f}")

        return {
            "inputs": {
                "spread_shock_bp": spread_shock,
                "rate_shock_bp": rate_shock,
                "cs01": cs01,
                "dv01": dv01,
                "liquidity_penalty": liquidity_penalty,
            },
            "outputs": {"core_stress_pnl": core_stress, "total_stress_pnl": total_stress},
        }

    def failure_modes(self) -> List[Dict[str, str]]:
        return [
            {"mode": "Single-factor stress design", "mitigation": "Combine correlated spread-rate-liquidity shocks for realism."},
            {"mode": "Static liquidity penalty", "mitigation": "Scale liquidation cost with position size and regime volatility."},
        ]

    def exports_to_next_chapter(self) -> Dict[str, Any]:
        return package_state(
            "StressScenarioState",
            {"core_stress_pnl": 0.0, "total_stress_pnl": 0.0},
            "Transfers downside envelope into capital and shadow-cost analysis.",
        )
