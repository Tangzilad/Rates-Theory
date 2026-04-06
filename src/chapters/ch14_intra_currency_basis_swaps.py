from __future__ import annotations

import streamlit as st

from core.types import ChapterExportState

from .base import SimpleChapter


def _clamp_confidence(raw: float) -> float:
    return max(0.0, min(1.0, raw))


class Chapter14(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(
            chapter_id="14",
            title="Chapter 14: Intra-currency basis swaps",
            objective="Measure and trade tenor-basis dislocations within one currency curve while accounting for funding frictions.",
        )

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {
                "name": "Tenor basis edge",
                "equation": "basis_edge_bp=observed_basis_bp-fair_basis_bp-implementation_cost_bp",
            },
            {
                "name": "Execution confidence",
                "equation": "execution_confidence=min(1,max(0,basis_edge_bp/entry_hurdle_bp))",
            },
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Estimate fair intra-currency basis from OIS-projected forwards and collateral assumptions.",
            "Compare observed quoted basis to fair basis and subtract execution and funding drag.",
            "Scale conviction into execution confidence used by the next chapter's basis-package allocator.",
        ]

    def interactive_lab(self) -> dict[str, dict[str, float | bool]]:
        observed_basis_bp = st.number_input("Observed 3s6s basis quote (bp)", value=12.0, step=0.5, key="obs_basis_14")
        fair_basis_bp = st.number_input("Model fair basis (bp)", value=8.5, step=0.5, key="fair_basis_14")
        implementation_cost_bp = st.number_input("All-in implementation cost (bp)", value=1.5, step=0.1, key="impl_14")
        entry_hurdle_bp = st.number_input("Entry hurdle (bp)", value=2.0, step=0.1, key="hurdle_14")

        net_edge_bp = observed_basis_bp - fair_basis_bp - implementation_cost_bp
        execution_confidence = _clamp_confidence(net_edge_bp / max(entry_hurdle_bp, 1e-6))
        execute_flag = net_edge_bp > 0

        st.metric("Net basis edge (bp)", f"{net_edge_bp:.2f}")
        st.metric("Execution confidence", f"{execution_confidence:.2f}")
        st.metric("Deploy trade?", "Yes" if execute_flag else "No")

        return {
            "inputs": {
                "observed_basis_bp": observed_basis_bp,
                "fair_basis_bp": fair_basis_bp,
                "implementation_cost_bp": implementation_cost_bp,
                "entry_hurdle_bp": entry_hurdle_bp,
            },
            "outputs": {
                "net_edge_bp": net_edge_bp,
                "execution_confidence": execution_confidence,
                "execute_flag": execute_flag,
            },
        }

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            schema_name="ICBSState",
            signals=["net_edge_bp", "execution_confidence", "execute_flag"],
            usage="Feeds cross-currency basis structuring with an executable confidence score.",
        )
