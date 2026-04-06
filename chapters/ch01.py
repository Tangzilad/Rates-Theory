from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from core.types import ChapterExportState, ExecutableTradeState, ExecutionSignalState, JointSpreadState
from src.models.cash_carry import cash_carry_state

from .base import ChapterBase


class Chapter01(ChapterBase):
    chapter_id = "1"

    def chapter_meta(self) -> Dict[str, Any]:
        return {
            "chapter": self.chapter_id,
            "title": "Chapter 1: Cash-and-carry arbitrage",
            "objective": "Map mispricing into executable arbitrage direction.",
        }

    def prerequisites(self) -> List[str]:
        return ["Bond pricing basics", "Simple carry math", "Repo funding intuition"]

    def concept_map(self) -> Dict[str, List[str]]:
        return {
            "nodes": ["Spot", "Repo", "Fair futures", "Basis", "Trade direction"],
            "edges": ["Spot+Repo->Fair futures", "Observed-Fair->Basis", "Basis sign->Trade direction"],
        }

    def equation_set(self) -> List[Dict[str, str]]:
        return [
            {"name": "Fair futures", "equation": "F*=S*exp(r*T)"},
            {"name": "Basis", "equation": "basis=F_mkt-F*"},
        ]

    def derivation_steps(self) -> List[str]:
        return [
            "Start from spot purchase financed at repo.",
            "Compound financing to futures maturity.",
            "Compare observed and fair futures to extract basis.",
        ]

    def interactive_lab(self) -> ExecutableTradeState:
        c1, c2, c3, c4 = st.columns(4)
        spot = c1.number_input("Bond spot price", min_value=0.0, value=98.5, step=0.1)
        repo = c2.slider("Repo rate (%)", 0.0, 15.0, 4.5, 0.1) / 100
        t_years = c3.slider("Time to futures maturity (years)", 0.05, 2.0, 0.5, 0.05)
        fut_mkt = c4.number_input("Observed futures price", min_value=0.0, value=100.0, step=0.1)

        fair_fut, basis, direction = cash_carry_state(spot=spot, repo=repo, t_years=t_years, fut_mkt=fut_mkt)
        st.metric("Theoretical fair futures", f"{fair_fut:,.4f}")
        st.metric("Basis (Observed - Fair)", f"{basis:,.4f}")

        if basis > 0:
            st.success("Futures appears rich: consider cash-and-carry (buy bond, short futures).")
        elif basis < 0:
            st.success("Futures appears cheap: consider reverse cash-and-carry (short bond, long futures).")
        else:
            st.info("No arbitrage signal under current assumptions.")

        joint = JointSpreadState(fair_futures=fair_fut, basis=basis, direction=direction)
        signal = ExecutionSignalState(action=direction, confidence=min(abs(basis) / 2.0, 0.99), rationale="Basis sign maps directly to cash-and-carry direction.")
        return ExecutableTradeState(joint_spread=joint, signal=signal)

    def case_studies(self) -> List[Dict[str, str]]:
        return [{"name": "Funding squeeze", "setup": "Repo rises while futures unchanged", "takeaway": "Apparent mispricing can be funding-driven."}]

    def failure_modes(self) -> List[Dict[str, str]]:
        return [{"mode": "Ignoring transaction costs", "mitigation": "Apply conservative basis threshold net of costs."}]

    def assessment(self) -> List[Dict[str, str]]:
        return [{"prompt": "If basis is +40bp, what trade direction is implied?", "expected": "Cash-and-carry"}]

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            signals=["basis", "arbitrage_direction", "confidence"],
            usage="Used as spread state input for mean-reversion modeling.",
            schema_name="ExecutableTradeState",
        )
