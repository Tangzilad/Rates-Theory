from __future__ import annotations

import streamlit as st

from .base import SimpleChapter


class Chapter16(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(chapter_id="16", title="Chapter 16: Hedge calibration", objective="Size macro and idiosyncratic hedges to keep spread trades inside risk budgets.")

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Hedge ratio", "equation": "hedge_ratio=target_dv01/hedge_dv01"},
            {"name": "Residual DV01", "equation": "residual=trade_dv01-hedge_ratio*hedge_dv01"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Estimate trade DV01 and allowed residual risk budget.",
            "Compute hedge notional from instrument DV01 efficiency.",
            "Validate post-hedge residual against governance threshold.",
        ]

    def interactive_lab(self) -> dict[str, dict[str, float]]:
        trade_dv01 = st.number_input("Trade DV01 ($/bp)", value=145_000.0, step=5_000.0, key="tdv01_16")
        hedge_dv01 = st.number_input("Hedge instrument DV01 ($/bp per unit)", value=12_500.0, step=500.0, key="hdv01_16")
        target_residual = st.number_input("Target residual DV01 ($/bp)", value=20_000.0, step=2_500.0, key="res_16")

        target_hedged_dv01 = max(trade_dv01 - target_residual, 0.0)
        hedge_ratio = target_hedged_dv01 / max(hedge_dv01, 1.0)
        realized_residual = trade_dv01 - hedge_ratio * hedge_dv01

        st.metric("Hedge ratio (units)", f"{hedge_ratio:.2f}")
        st.metric("Realized residual DV01 ($/bp)", f"{realized_residual:,.0f}")

        return {"inputs": {"trade_dv01": trade_dv01, "hedge_dv01": hedge_dv01, "target_residual_dv01": target_residual}, "outputs": {"hedge_ratio_units": hedge_ratio, "realized_residual_dv01": realized_residual}}

    def exports_to_next_chapter(self) -> dict[str, object]:
        return {"schema_name": "HedgeCalibrationState", "signals": ["hedge_ratio_units", "realized_residual_dv01"], "usage": "Supplies scenario chapter with hedge-adjusted position sensitivities."}
