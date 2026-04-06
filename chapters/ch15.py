from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from .common import SimpleChapter
from .swap_basis import carry_pnl, package_state


class Chapter15(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(
            chapter_id="15",
            title="Chapter 15: Carry and rolldown budgeting",
            objective="Project forward P&L from carry and curve roll under realistic holding windows.",
        )

    def equation_set(self) -> List[Dict[str, str]]:
        return [
            {"name": "Carry P&L", "equation": "carry_pnl=notional*(carry_bp/10000)*horizon"},
            {"name": "Total expected P&L", "equation": "total=carry_pnl+rolldown_pnl-costs"},
        ]

    def derivation_steps(self) -> List[str]:
        return [
            "Set holding horizon and spread-carry assumption.",
            "Estimate rolldown contribution from curve migration.",
            "Subtract implementation costs to derive expected net return.",
        ]

    def interactive_lab(self) -> Dict[str, Any]:
        notional = st.number_input("Notional ($)", value=25_000_000.0, step=500_000.0, key="notional_15")
        carry_bp = st.number_input("Carry (bp/year)", value=42.0, step=1.0, key="carry_15")
        rolldown_bp = st.number_input("Rolldown (bp/year)", value=18.0, step=1.0, key="roll_15")
        horizon_years = st.slider("Holding horizon (years)", min_value=0.1, max_value=2.0, value=0.5, step=0.1, key="h_15")
        costs = st.number_input("Estimated implementation costs ($)", value=60_000.0, step=5_000.0, key="cost_15")

        carry = carry_pnl(notional, carry_bp, horizon_years)
        rolldown = carry_pnl(notional, rolldown_bp, horizon_years)
        total = carry + rolldown - costs

        st.metric("Carry P&L ($)", f"{carry:,.0f}")
        st.metric("Rolldown P&L ($)", f"{rolldown:,.0f}")
        st.metric("Expected net P&L ($)", f"{total:,.0f}")

        return {
            "inputs": {
                "notional": notional,
                "carry_bp": carry_bp,
                "rolldown_bp": rolldown_bp,
                "horizon_years": horizon_years,
                "costs": costs,
            },
            "outputs": {"carry_pnl": carry, "rolldown_pnl": rolldown, "expected_total_pnl": total},
        }

    def failure_modes(self) -> List[Dict[str, str]]:
        return [
            {"mode": "Assuming static curve", "mitigation": "Run multi-scenario rate shifts and convexity-aware carry projections."},
            {"mode": "Ignoring turnover costs", "mitigation": "Apply realistic unwind and rebalance fees in budgeting."},
        ]

    def exports_to_next_chapter(self) -> Dict[str, Any]:
        return package_state(
            "CarryBudgetState",
            {"carry_pnl": 0.0, "rolldown_pnl": 0.0, "expected_total_pnl": 0.0},
            "Feeds hedge calibration with projected return and cost contribution.",
        )
