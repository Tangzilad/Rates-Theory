from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from .common import SimpleChapter
from .swap_basis import package_state
from src.models.integrated_rv import execution_signal


class Chapter14(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(
            chapter_id="14",
            title="Chapter 14: Executable trade design",
            objective="Convert spread signals into sized trades with slippage-aware entry filters.",
        )

    def equation_set(self) -> List[Dict[str, str]]:
        return [
            {"name": "Expected edge", "equation": "edge_bp=signal_bp-transaction_cost_bp"},
            {"name": "Execution confidence", "equation": "confidence=edge_bp/entry_threshold_bp"},
        ]

    def derivation_steps(self) -> List[str]:
        return [
            "Take modeled spread signal and estimate full execution cost stack.",
            "Compute net edge and compare against entry threshold.",
            "Scale conviction score to gate order release.",
        ]

    def interactive_lab(self) -> Dict[str, Any]:
        st.caption("Pedagogical simplification: execution confidence is a clipped linear function of edge vs threshold.")
        signal_bp = st.number_input("Signal edge before costs (bp)", value=37.0, step=1.0, key="sig_14")
        transaction_cost_bp = st.number_input("Estimated transaction costs (bp)", value=11.0, step=1.0, key="tc_14")
        entry_threshold_bp = st.number_input("Minimum entry threshold (bp)", value=20.0, step=1.0, key="th_14")

        edge_bp, confidence, execute_flag = execution_signal(signal_bp, transaction_cost_bp, entry_threshold_bp)

        st.metric("Net edge (bp)", f"{edge_bp:.2f}")
        st.metric("Execution confidence", f"{confidence:.2f}")
        st.metric("Release order?", "Yes" if execute_flag else "No")

        return {
            "inputs": {
                "signal_bp": signal_bp,
                "transaction_cost_bp": transaction_cost_bp,
                "entry_threshold_bp": entry_threshold_bp,
            },
            "outputs": {
                "net_edge_bp": edge_bp,
                "execution_confidence": confidence,
                "execute_flag": execute_flag,
            },
        }

    def failure_modes(self) -> List[Dict[str, str]]:
        return [
            {"mode": "Underestimated slippage", "mitigation": "Calibrate cost model to venue/size and stress by liquidity regime."},
            {"mode": "Threshold overfitting", "mitigation": "Backtest thresholds out-of-sample with turnover penalties."},
        ]

    def exports_to_next_chapter(self) -> Dict[str, Any]:
        return package_state(
            "ExecutableTradeState",
            {"net_edge_bp": 0.0, "execution_confidence": 0.0, "execute_flag": 0.0},
            "Passes executable opportunities into risk-capacity and carry projection modules.",
        )
