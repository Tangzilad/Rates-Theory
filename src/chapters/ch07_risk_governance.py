from __future__ import annotations

import streamlit as st

from core.types import ChapterExportState, FuturesBasisState

from .base import ChapterBase


class Chapter07(ChapterBase):
    chapter_id = "7"

    def chapter_meta(self) -> dict[str, str]:
        return {"chapter": self.chapter_id, "title": "Chapter 7: Risk governance", "objective": "Verify portfolio proposals against hard and soft risk limits before execution."}

    def prerequisites(self) -> list[str]:
        return ["Portfolio weights", "DV01/CS01 ladders", "Desk risk policy"]

    def concept_map(self) -> dict[str, list[str]]:
        return {"nodes": ["Proposed risk", "Limit ladder", "Breach ratio", "Escalation", "Approval"], "edges": ["Risk/Limit->Breach ratio", "Breach ratio->Escalation", "Escalation->Approval"]}

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Limit utilization", "equation": "utilization = proposed_risk / approved_limit"},
            {"name": "Headroom", "equation": "headroom = approved_limit - proposed_risk"},
            {"name": "Traffic-light rule", "equation": "status = green if utilization<0.8, amber if <1.0, red otherwise"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Aggregate proposed position sensitivities into policy risk buckets.",
            "Normalize by limit ladder to compute utilization and remaining headroom.",
            "Assign governance status and escalation path based on utilization bands.",
        ]

    def interactive_lab(self) -> FuturesBasisState:
        proposed = st.number_input("Proposed risk usage ($/bp)", value=140_000.0, step=5_000.0, key="prop_7")
        limit = st.number_input("Approved risk limit ($/bp)", value=180_000.0, step=5_000.0, key="limit_7")
        warn_band = st.slider("Warning threshold", min_value=0.5, max_value=0.95, value=0.8, step=0.05, key="warn_7")

        utilization = proposed / max(limit, 1.0)
        headroom = limit - proposed
        if utilization >= 1.0:
            status = "red"
        elif utilization >= warn_band:
            status = "amber"
        else:
            status = "green"

        st.metric("Limit utilization", f"{utilization:.2%}")
        st.metric("Headroom ($/bp)", f"{headroom:,.0f}")
        st.metric("Governance status", status.upper())
        st.info("TODO: add aggregated multi-factor breaches, exception workflow routing, and audit log integration.")

        return FuturesBasisState(utilization=utilization, headroom=headroom, status=status, approved=status != "red")

    def case_studies(self) -> list[dict[str, str]]:
        return [{"name": "Pre-trade check", "setup": "High-conviction signal with tight residual limit", "takeaway": "Governance traffic-lighting protects portfolio mandate consistency."}]

    def failure_modes(self) -> list[dict[str, str]]:
        return [{"mode": "Static limits in volatile regimes", "mitigation": "Re-tier risk limits by volatility regime and liquidity state."}]

    def assessment(self) -> list[dict[str, str]]:
        return [{"prompt": "When does amber status trigger?", "expected": "When utilization exceeds warning threshold but remains below hard limit."}]

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            signals=["utilization", "headroom", "status", "approved"],
            usage="Controls whether positions proceed into Chapter 8 implementation screens.",
            schema_name="FuturesBasisState",
        )
