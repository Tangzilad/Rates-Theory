from __future__ import annotations

import streamlit as st

from core.types import ChapterExportState, CurveFairValueState

from .base import SimpleChapter


class Chapter08(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(chapter_id="8", title="Chapter 8: Relative-value screens", objective="Combine model and market spread views into actionable flags.")

    def interactive_lab(self) -> CurveFairValueState:
        model_fair_value = st.number_input("Model fair spread (bp)", value=68.0, step=1.0, key="model_8")
        market_observed = st.number_input("Market observed spread (bp)", value=81.0, step=1.0, key="market_8")
        residual_vol = st.number_input("Residual volatility (bp)", value=7.5, step=0.5, key="vol_8")

        residual_bp = market_observed - model_fair_value
        z_score = residual_bp / max(residual_vol, 0.01)

        if z_score >= 1.0:
            trade_signal = "short_spread"
        elif z_score <= -1.0:
            trade_signal = "long_spread"
        else:
            trade_signal = "hold"

        confidence = min(1.0, abs(z_score) / 3.0)

        st.metric("Residual (bp)", f"{residual_bp:.2f}")
        st.metric("Residual z-score", f"{z_score:.2f}")
        st.metric("Signal", trade_signal.replace("_", " ").title())

        return CurveFairValueState(
            model_fair_value_bp=model_fair_value,
            market_observed_bp=market_observed,
            residual_bp=residual_bp,
            z_score=z_score,
            trade_signal=trade_signal,
            confidence=confidence,
        )

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            signals=["model_fair_value_bp", "market_observed_bp", "residual_bp", "z_score", "trade_signal", "confidence"],
            usage="Supplies trade-construction inputs with residual magnitude and direction.",
            schema_name="CurveFairValueState",
        )
