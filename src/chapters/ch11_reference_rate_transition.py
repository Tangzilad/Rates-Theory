from __future__ import annotations

import streamlit as st

from core.types import ChapterExportState, ReferenceRateState

from .base import SimpleChapter


def _spread_bp(lhs: float, rhs: float) -> float:
    return (lhs - rhs) * 100.0


class Chapter11(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(chapter_id="11", title="Chapter 11: Reference-rate transition", objective="Measure fallback economics moving from LIBOR-style fixings into RFR compounding.")

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Fallback spread", "equation": "fallback_bp=(legacy_fixing-rfr_compounded)*100"},
            {"name": "All-in coupon", "equation": "all_in_pct=rfr_compounded+fallback_adj/100"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Collect legacy tenor fixing and compounded RFR observations.",
            "Translate the difference into fallback basis points.",
            "Apply contractual spread adjustment to estimate all-in reset coupon.",
        ]

    def interactive_lab(self) -> ReferenceRateState:
        legacy_fixing = st.number_input("Legacy tenor fixing (%)", value=5.02, step=0.01, key="legacy_11")
        rfr_compounded = st.number_input("Compounded RFR (%)", value=4.71, step=0.01, key="rfr_11")
        contract_adj = st.number_input("Contract spread adjustment (bp)", value=26.0, step=1.0, key="adj_11")

        fallback_bp = _spread_bp(legacy_fixing, rfr_compounded)
        all_in_coupon = rfr_compounded + (contract_adj / 100.0)
        delta_to_legacy_bp = _spread_bp(all_in_coupon, legacy_fixing)

        st.metric("Fallback spread (bp)", f"{fallback_bp:.2f}")
        st.metric("All-in reset coupon (%)", f"{all_in_coupon:.3f}")
        st.metric("Coupon vs legacy (bp)", f"{delta_to_legacy_bp:.2f}")

        return ReferenceRateState(
            legacy_fixing_pct=legacy_fixing,
            rfr_compounded_pct=rfr_compounded,
            contract_adjustment_bp=contract_adj,
            fallback_spread_bp=fallback_bp,
            all_in_coupon_pct=all_in_coupon,
            coupon_vs_legacy_bp=delta_to_legacy_bp,
        )

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            schema_name="ReferenceRateState",
            signals=[
                "legacy_fixing_pct",
                "rfr_compounded_pct",
                "contract_adjustment_bp",
                "fallback_spread_bp",
                "all_in_coupon_pct",
                "coupon_vs_legacy_bp",
            ],
            usage="Feeds asset-swap decomposition with standardized floating benchmark assumptions.",
        )
