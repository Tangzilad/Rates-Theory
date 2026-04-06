from __future__ import annotations

import streamlit as st

from core.types import ChapterExportState, FundingBasisState

from .base import ChapterBase


class Chapter10(ChapterBase):
    chapter_id = "10"

    def chapter_meta(self) -> dict[str, str]:
        return {"chapter": self.chapter_id, "title": "Chapter 10: Funding basis", "objective": "Bridge cash and derivatives funding assumptions into a unified basis adjustment."}

    def prerequisites(self) -> list[str]:
        return ["Swap spread conventions", "Repo/funding assumptions", "Cross-currency carry intuition"]

    def concept_map(self) -> dict[str, list[str]]:
        return {"nodes": ["Swap leg", "Cash funding", "FX hedge", "Basis wedge", "Adjusted fair value"], "edges": ["Swap-Cash->Basis wedge", "Basis+FX hedge->Funding adjustment", "Adjustment->Fair value"]}

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Funding basis", "equation": "basis_bp = (swap_float - cash_funding - hedge_cost) * 100"},
            {"name": "Adjusted fair spread", "equation": "fair_adj_bp = fair_raw_bp + basis_bp"},
            {"name": "Net carry", "equation": "carry_net_bp = carry_gross_bp - basis_bp"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Measure floating-leg carry from derivatives market quotes.",
            "Subtract cash funding and hedge costs to estimate persistent basis wedge.",
            "Apply basis wedge to fair spread and carry projections used downstream.",
        ]

    def interactive_lab(self) -> FundingBasisState:
        swap_float = st.number_input("Swap floating leg (%)", value=4.85, step=0.01, key="swap_10")
        cash_funding = st.number_input("Cash funding rate (%)", value=4.45, step=0.01, key="cash_10")
        hedge_cost = st.number_input("Hedge cost (%)", value=0.18, step=0.01, key="hedge_10")
        fair_raw_bp = st.number_input("Raw fair spread (bp)", value=62.0, step=1.0, key="raw_10")
        carry_gross_bp = st.number_input("Gross carry (bp)", value=31.0, step=1.0, key="carry_10")

        basis_bp = (swap_float - cash_funding - hedge_cost) * 100.0
        fair_adj_bp = fair_raw_bp + basis_bp
        carry_net_bp = carry_gross_bp - basis_bp

        st.metric("Funding basis (bp)", f"{basis_bp:.2f}")
        st.metric("Adjusted fair spread (bp)", f"{fair_adj_bp:.2f}")
        st.metric("Net carry after basis (bp)", f"{carry_net_bp:.2f}")
        st.info("TODO: add multi-currency basis term structure and collateral/CSA-aware funding analytics.")

        return FundingBasisState(
            funding_basis_bp=basis_bp,
            adjusted_fair_spread_bp=fair_adj_bp,
            net_carry_bp=carry_net_bp,
        )

    def case_studies(self) -> list[dict[str, str]]:
        return [{"name": "Funding dislocation", "setup": "Swap float detaches from cash funding", "takeaway": "Basis adjustments prevent false rich/cheap signals."}]

    def failure_modes(self) -> list[dict[str, str]]:
        return [{"mode": "Ignoring hedge-cost drift", "mitigation": "Refresh hedge costs and funding inputs per trade horizon."}]

    def assessment(self) -> list[dict[str, str]]:
        return [{"prompt": "What does positive basis_bp imply?", "expected": "Derivative funding is rich to cash, increasing adjusted fair spread."}]

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            signals=["funding_basis_bp", "adjusted_fair_spread_bp", "net_carry_bp"],
            usage="Feeds benchmark-transition and asset-swap decomposition chapters.",
            schema_name="FundingBasisState",
        )
