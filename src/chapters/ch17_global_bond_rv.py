from __future__ import annotations

import streamlit as st

from .base import SimpleChapter


class Chapter17(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(
            chapter_id="17",
            title="Chapter 17: Global bond RV",
            objective="Rank relative-value bond packages across regions using hedge-adjusted spread carry and stress-aware downside filters.",
        )

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {
                "name": "Global RV spread P&L",
                "equation": "rv_spread_pnl=-(spread_shock_bp*portfolio_cs01 + rate_shock_bp*residual_dv01)",
            },
            {
                "name": "Stress-adjusted total",
                "equation": "total_stress_pnl=rv_spread_pnl-liquidity_haircut",
            },
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Project cross-market spread and rate shocks on a hedge-adjusted global RV basket.",
            "Apply CS01 and residual DV01 to estimate joint mark-to-market drawdown.",
            "Subtract liquidity haircut to form total_stress_pnl passed to chapter 18 shadow-cost governance.",
        ]

    def interactive_lab(self) -> dict[str, dict[str, float]]:
        spread_shock_bp = st.number_input("Global spread shock (bp)", value=65.0, step=5.0, key="spread_17")
        rate_shock_bp = st.number_input("Rates shock (bp)", value=35.0, step=5.0, key="rate_17")
        portfolio_cs01 = st.number_input("Portfolio CS01 ($/bp)", value=90_000.0, step=2_000.0, key="cs01_17")
        residual_dv01 = st.number_input("Residual DV01 from ch16 ($/bp)", value=22_000.0, step=1_000.0, key="dv01_17")
        liquidity_haircut = st.number_input("Liquidity haircut ($)", value=300_000.0, step=10_000.0, key="liq_17")

        rv_spread_pnl = -((spread_shock_bp * portfolio_cs01) + (rate_shock_bp * residual_dv01))
        total_stress_pnl = rv_spread_pnl - liquidity_haircut

        st.metric("Core RV stress P&L ($)", f"{rv_spread_pnl:,.0f}")
        st.metric("Total stress P&L ($)", f"{total_stress_pnl:,.0f}")

        return {
            "inputs": {
                "spread_shock_bp": spread_shock_bp,
                "rate_shock_bp": rate_shock_bp,
                "portfolio_cs01": portfolio_cs01,
                "residual_dv01": residual_dv01,
                "liquidity_haircut": liquidity_haircut,
            },
            "outputs": {
                "rv_spread_pnl": rv_spread_pnl,
                "total_stress_pnl": total_stress_pnl,
            },
        }

    def exports_to_next_chapter(self) -> dict[str, object]:
        return {
            "schema_name": "GlobalBondRVState",
            "signals": ["rv_spread_pnl", "total_stress_pnl"],
            "usage": "Transfers stress envelope into chapter 18 capital and shadow-pricing controls.",
        }
