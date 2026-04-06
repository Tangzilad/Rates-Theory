from __future__ import annotations

import streamlit as st

from core.types import ChapterExportState, GovBondTradeBlueprint

from .base import SimpleChapter


class Chapter09(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(chapter_id="9", title="Chapter 9: Trade construction", objective="Convert valuation signals into position sizing and implementation checks.")

    def interactive_lab(self) -> GovBondTradeBlueprint:
        trade_name = st.text_input("Trade name", value="UST 10Y RV switch", key="trade_name_9")
        entry_leg = st.text_input("Entry leg", value="Long UST 10Y cash", key="entry_leg_9")
        hedge_leg = st.text_input("Hedge leg", value="Short TY futures", key="hedge_leg_9")
        target_notional_mm = st.number_input("Target notional ($mm)", value=25.0, step=1.0, key="notional_9")
        hedge_ratio = st.number_input("Hedge ratio", value=0.92, step=0.01, key="hedge_ratio_9")
        expected_edge_bp = st.number_input("Expected edge (bp)", value=11.0, step=1.0, key="edge_9")
        dv01_gap = st.number_input("DV01 neutrality gap ($/bp)", value=2_500.0, step=100.0, key="dv01_gap_9")
        stop_loss_bp = st.number_input("Stop loss (bp)", value=-8.0, step=1.0, key="stop_9")
        take_profit_bp = st.number_input("Take profit (bp)", value=14.0, step=1.0, key="take_9")

        approved = expected_edge_bp > 0 and abs(dv01_gap) <= 5_000

        st.metric("Expected edge (bp)", f"{expected_edge_bp:.2f}")
        st.metric("DV01 gap ($/bp)", f"{dv01_gap:,.0f}")
        st.metric("Blueprint status", "APPROVED" if approved else "REVIEW")

        return GovBondTradeBlueprint(
            trade_name=trade_name,
            entry_leg=entry_leg,
            hedge_leg=hedge_leg,
            target_notional_mm=target_notional_mm,
            hedge_ratio=hedge_ratio,
            expected_edge_bp=expected_edge_bp,
            dv01_neutrality_gap_usd_per_bp=dv01_gap,
            stop_loss_bp=stop_loss_bp,
            take_profit_bp=take_profit_bp,
            approved=approved,
        )

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            signals=[
                "trade_name",
                "entry_leg",
                "hedge_leg",
                "target_notional_mm",
                "hedge_ratio",
                "expected_edge_bp",
                "dv01_neutrality_gap_usd_per_bp",
                "stop_loss_bp",
                "take_profit_bp",
                "approved",
            ],
            usage="Passes implementation blueprint and risk checks into funding-basis analysis.",
            schema_name="GovBondTradeBlueprint",
        )
