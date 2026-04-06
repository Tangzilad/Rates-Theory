from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from .common import SimpleChapter
from .swap_basis import package_state
from src.models.shadow_costs import capital_shadow_state


class Chapter18(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(
            chapter_id="18",
            title="Chapter 18: Capital shadow costs",
            objective="Price capital usage and funding frictions into final trade acceptance decisions.",
        )

    def equation_set(self) -> List[Dict[str, str]]:
        return [
            {"name": "Capital charge", "equation": "capital_charge=capital_used*capital_hurdle"},
            {"name": "Risk-adjusted alpha", "equation": "raa=expected_pnl-capital_charge-funding_charge"},
        ]

    def derivation_steps(self) -> List[str]:
        return [
            "Estimate expected strategy P&L from execution and stress modules.",
            "Compute economic capital and funding shadow charges.",
            "Accept only trades with positive risk-adjusted alpha after charges.",
        ]

    def interactive_lab(self) -> Dict[str, Any]:
        st.caption("Pedagogical simplification: capital and funding shadow costs are represented with scalar annual charges.")
        expected_pnl = st.number_input("Expected annual P&L ($)", value=1_250_000.0, step=50_000.0, key="pnl_18")
        capital_used = st.number_input("Allocated economic capital ($)", value=8_000_000.0, step=250_000.0, key="cap_18")
        capital_hurdle = st.slider("Capital hurdle rate", min_value=0.05, max_value=0.25, value=0.13, step=0.005, key="hurdle_18")
        funding_charge = st.number_input("Funding shadow charge ($)", value=220_000.0, step=10_000.0, key="fund_18")

        capital_charge, risk_adjusted_alpha, approval_flag = capital_shadow_state(
            expected_pnl,
            capital_used,
            capital_hurdle,
            funding_charge,
        )

        st.metric("Capital charge ($)", f"{capital_charge:,.0f}")
        st.metric("Risk-adjusted alpha ($)", f"{risk_adjusted_alpha:,.0f}")
        st.metric("Approve trade?", "Yes" if approval_flag else "No")

        return {
            "inputs": {
                "expected_pnl": expected_pnl,
                "capital_used": capital_used,
                "capital_hurdle": capital_hurdle,
                "funding_charge": funding_charge,
            },
            "outputs": {
                "capital_charge": capital_charge,
                "risk_adjusted_alpha": risk_adjusted_alpha,
                "approval_flag": approval_flag,
            },
        }

    def failure_modes(self) -> List[Dict[str, str]]:
        return [
            {"mode": "Underpriced capital", "mitigation": "Align hurdle rates with current treasury transfer-pricing assumptions."},
            {"mode": "Ignoring stress losses", "mitigation": "Reduce expected alpha by tail-loss envelope before approval."},
        ]

    def exports_to_next_chapter(self) -> Dict[str, Any]:
        return package_state(
            "ShadowCostState",
            {"capital_charge": 0.0, "risk_adjusted_alpha": 0.0, "approval_flag": 0.0},
            "Final chapter output for governance, audit trail, and portfolio allocation handoff.",
        )
