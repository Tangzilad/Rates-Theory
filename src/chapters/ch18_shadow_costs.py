from __future__ import annotations

import streamlit as st

from .base import SimpleChapter


class Chapter18(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(chapter_id="18", title="Chapter 18: Capital shadow costs", objective="Price capital usage and funding frictions into final trade acceptance decisions.")

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Capital charge", "equation": "capital_charge=capital_used*capital_hurdle"},
            {"name": "Risk-adjusted alpha", "equation": "raa=expected_pnl-capital_charge-funding_charge"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Estimate expected strategy P&L from execution and stress modules.",
            "Compute economic capital and funding shadow charges.",
            "Accept only trades with positive risk-adjusted alpha after charges.",
        ]

    def interactive_lab(self) -> dict[str, dict[str, float | bool]]:
        expected_pnl = st.number_input("Expected annual P&L ($)", value=1_250_000.0, step=50_000.0, key="pnl_18")
        capital_used = st.number_input("Allocated economic capital ($)", value=8_000_000.0, step=250_000.0, key="cap_18")
        capital_hurdle = st.slider("Capital hurdle rate", min_value=0.05, max_value=0.25, value=0.13, step=0.005, key="hurdle_18")
        funding_charge = st.number_input("Funding shadow charge ($)", value=220_000.0, step=10_000.0, key="fund_18")

        capital_charge = capital_used * capital_hurdle
        risk_adjusted_alpha = expected_pnl - capital_charge - funding_charge
        approval_flag = risk_adjusted_alpha > 0

        st.metric("Capital charge ($)", f"{capital_charge:,.0f}")
        st.metric("Risk-adjusted alpha ($)", f"{risk_adjusted_alpha:,.0f}")
        st.metric("Approve trade?", "Yes" if approval_flag else "No")

        return {"inputs": {"expected_pnl": expected_pnl, "capital_used": capital_used, "capital_hurdle": capital_hurdle, "funding_charge": funding_charge}, "outputs": {"capital_charge": capital_charge, "risk_adjusted_alpha": risk_adjusted_alpha, "approval_flag": approval_flag}}

    def exports_to_next_chapter(self) -> dict[str, object]:
        return {"schema_name": "ShadowCostState", "signals": ["capital_charge", "risk_adjusted_alpha", "approval_flag"], "usage": "Final chapter output for governance, audit trail, and portfolio allocation handoff."}
