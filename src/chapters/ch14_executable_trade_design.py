from __future__ import annotations

import streamlit as st

from .base import SimpleChapter


def _clamp_confidence(raw: float) -> float:
    return max(0.0, min(1.0, raw))


class Chapter14(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(chapter_id="14", title="Chapter 14: Executable trade design", objective="Convert spread signals into sized trades with slippage-aware entry filters.")

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Expected edge", "equation": "edge_bp=signal_bp-transaction_cost_bp"},
            {"name": "Execution confidence", "equation": "confidence=edge_bp/entry_threshold_bp"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Take modeled spread signal and estimate full execution cost stack.",
            "Compute net edge and compare against entry threshold.",
            "Scale conviction score to gate order release.",
        ]

    def interactive_lab(self) -> dict[str, dict[str, float | bool]]:
        signal_bp = st.number_input("Signal edge before costs (bp)", value=37.0, step=1.0, key="sig_14")
        transaction_cost_bp = st.number_input("Estimated transaction costs (bp)", value=11.0, step=1.0, key="tc_14")
        entry_threshold_bp = st.number_input("Minimum entry threshold (bp)", value=20.0, step=1.0, key="th_14")

        edge_bp = signal_bp - transaction_cost_bp
        confidence = _clamp_confidence(edge_bp / max(entry_threshold_bp, 1.0))
        execute_flag = edge_bp >= entry_threshold_bp

        st.metric("Net edge (bp)", f"{edge_bp:.2f}")
        st.metric("Execution confidence", f"{confidence:.2f}")
        st.metric("Release order?", "Yes" if execute_flag else "No")

        return {"inputs": {"signal_bp": signal_bp, "transaction_cost_bp": transaction_cost_bp, "entry_threshold_bp": entry_threshold_bp}, "outputs": {"net_edge_bp": edge_bp, "execution_confidence": confidence, "execute_flag": execute_flag}}

    def exports_to_next_chapter(self) -> dict[str, object]:
        return {"schema_name": "ExecutableTradeState", "signals": ["net_edge_bp", "execution_confidence", "execute_flag"], "usage": "Passes executable opportunities into risk-capacity and carry projection modules."}
