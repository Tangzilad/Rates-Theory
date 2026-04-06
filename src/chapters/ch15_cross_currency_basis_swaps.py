from __future__ import annotations

import streamlit as st

from .base import SimpleChapter


class Chapter15(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(
            chapter_id="15",
            title="Chapter 15: Cross-currency basis swaps",
            objective="Translate cross-currency basis dislocations into expected carry-plus-convergence P&L for hedge-funded packages.",
        )

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {
                "name": "Carry from basis",
                "equation": "carry_pnl=notional*(annualized_basis_carry_bp/10000)*horizon_years",
            },
            {
                "name": "Expected package P&L",
                "equation": "expected_total_pnl=carry_pnl+convergence_pnl-hedging_costs",
            },
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Map quoted cross-currency basis into annualized carry after collateral and funding conventions.",
            "Add expected convergence of off-fair basis toward equilibrium over the holding horizon.",
            "Deduct hedge and balance-sheet costs to compute expected_total_pnl for integrated asset-basis trade calibration.",
        ]

    def interactive_lab(self) -> dict[str, dict[str, float]]:
        notional = st.number_input("Swap notional ($)", value=40_000_000.0, step=1_000_000.0, key="notional_15")
        annualized_basis_carry_bp = st.number_input("Annualized basis carry (bp)", value=28.0, step=1.0, key="basis_carry_15")
        convergence_bp = st.number_input("Expected convergence gain (bp)", value=16.0, step=1.0, key="conv_15")
        horizon_years = st.slider("Holding horizon (years)", min_value=0.1, max_value=2.0, value=0.75, step=0.05, key="h_15")
        hedging_costs = st.number_input("FX hedge + balance-sheet costs ($)", value=95_000.0, step=5_000.0, key="hedge_cost_15")

        carry_pnl = notional * (annualized_basis_carry_bp / 10_000.0) * horizon_years
        convergence_pnl = notional * (convergence_bp / 10_000.0) * horizon_years
        expected_total_pnl = carry_pnl + convergence_pnl - hedging_costs

        st.metric("Carry P&L ($)", f"{carry_pnl:,.0f}")
        st.metric("Convergence P&L ($)", f"{convergence_pnl:,.0f}")
        st.metric("Expected total P&L ($)", f"{expected_total_pnl:,.0f}")

        return {
            "inputs": {
                "notional": notional,
                "annualized_basis_carry_bp": annualized_basis_carry_bp,
                "convergence_bp": convergence_bp,
                "horizon_years": horizon_years,
                "hedging_costs": hedging_costs,
            },
            "outputs": {
                "carry_pnl": carry_pnl,
                "convergence_pnl": convergence_pnl,
                "expected_total_pnl": expected_total_pnl,
            },
        }

    def exports_to_next_chapter(self) -> dict[str, object]:
        return {
            "schema_name": "CrossCurrencyBasisState",
            "signals": ["carry_pnl", "convergence_pnl", "expected_total_pnl"],
            "usage": "Supplies expected package economics for integrated asset-basis-CDS construction.",
        }
