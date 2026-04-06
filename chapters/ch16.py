from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from .common import SimpleChapter
from .swap_basis import package_state
from src.models.integrated_rv import hedge_ratio


class Chapter16(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(
            chapter_id="16",
            title="Chapter 16: Hedge calibration",
            objective="Size macro and idiosyncratic hedges to keep spread trades inside risk budgets.",
        )

    def equation_set(self) -> List[Dict[str, str]]:
        return [
            {"name": "Hedge ratio", "equation": "hedge_ratio=target_dv01/hedge_dv01"},
            {"name": "Residual DV01", "equation": "residual=trade_dv01-hedge_ratio*hedge_dv01"},
        ]

    def derivation_steps(self) -> List[str]:
        return [
            "Estimate trade DV01 and allowed residual risk budget.",
            "Compute hedge notional from instrument DV01 efficiency.",
            "Validate post-hedge residual against governance threshold.",
        ]

    def interactive_lab(self) -> Dict[str, Any]:
        st.caption("Pedagogical simplification: hedge sizing assumes static DV01 and a one-instrument linear hedge.")
        trade_dv01 = st.number_input("Trade DV01 ($/bp)", value=145_000.0, step=5_000.0, key="tdv01_16")
        hedge_dv01 = st.number_input("Hedge instrument DV01 ($/bp per unit)", value=12_500.0, step=500.0, key="hdv01_16")
        target_residual = st.number_input("Target residual DV01 ($/bp)", value=20_000.0, step=2_500.0, key="res_16")

        hedge_ratio_units, realized_residual = hedge_ratio(trade_dv01, hedge_dv01, target_residual)

        st.metric("Hedge ratio (units)", f"{hedge_ratio_units:.2f}")
        st.metric("Realized residual DV01 ($/bp)", f"{realized_residual:,.0f}")

        return {
            "inputs": {
                "trade_dv01": trade_dv01,
                "hedge_dv01": hedge_dv01,
                "target_residual_dv01": target_residual,
            },
            "outputs": {"hedge_ratio_units": hedge_ratio_units, "realized_residual_dv01": realized_residual},
        }

    def failure_modes(self) -> List[Dict[str, str]]:
        return [
            {"mode": "Basis mismatch in hedge proxy", "mitigation": "Use multi-factor hedge basket to capture curve and spread beta."},
            {"mode": "Outdated risk sensitivities", "mitigation": "Refresh DV01 measures intraday for volatile market regimes."},
        ]

    def exports_to_next_chapter(self) -> Dict[str, Any]:
        return package_state(
            "HedgeCalibrationState",
            {"hedge_ratio_units": 0.0, "realized_residual_dv01": 0.0},
            "Supplies scenario chapter with hedge-adjusted position sensitivities.",
        )
