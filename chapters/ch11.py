from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from .common import SimpleChapter
from .swap_basis import package_state, spread_bp


class Chapter11(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(
            chapter_id="11",
            title="Chapter 11: Reference-rate transition",
            objective="Measure fallback economics moving from LIBOR-style fixings into RFR compounding.",
        )

    def equation_set(self) -> List[Dict[str, str]]:
        return [
            {"name": "Fallback spread", "equation": "fallback_bp=(legacy_fixing-rfr_compounded)*100"},
            {"name": "All-in coupon", "equation": "all_in_pct=rfr_compounded+fallback_adj/100"},
        ]

    def derivation_steps(self) -> List[str]:
        return [
            "Collect legacy tenor fixing and compounded RFR observations.",
            "Translate the difference into fallback basis points.",
            "Apply contractual spread adjustment to estimate all-in reset coupon.",
        ]

    def interactive_lab(self) -> Dict[str, Any]:
        legacy_fixing = st.number_input("Legacy tenor fixing (%)", value=5.02, step=0.01, key="legacy_11")
        rfr_compounded = st.number_input("Compounded RFR (%)", value=4.71, step=0.01, key="rfr_11")
        contract_adj = st.number_input("Contract spread adjustment (bp)", value=26.0, step=1.0, key="adj_11")

        fallback_bp = spread_bp(legacy_fixing, rfr_compounded)
        all_in_coupon = rfr_compounded + (contract_adj / 100.0)
        delta_to_legacy_bp = spread_bp(all_in_coupon, legacy_fixing)

        st.metric("Fallback spread (bp)", f"{fallback_bp:.2f}")
        st.metric("All-in reset coupon (%)", f"{all_in_coupon:.3f}")
        st.metric("Coupon vs legacy (bp)", f"{delta_to_legacy_bp:.2f}")

        return {
            "inputs": {
                "legacy_fixing_pct": legacy_fixing,
                "rfr_compounded_pct": rfr_compounded,
                "contract_adjustment_bp": contract_adj,
            },
            "outputs": {
                "fallback_spread_bp": fallback_bp,
                "all_in_coupon_pct": all_in_coupon,
                "coupon_vs_legacy_bp": delta_to_legacy_bp,
            },
        }

    def failure_modes(self) -> List[Dict[str, str]]:
        return [
            {"mode": "Mismatched day-count conventions", "mitigation": "Normalize accrual basis before comparing term and compounded fixings."},
            {"mode": "Stale fallback adjustment", "mitigation": "Validate adjustment source against contract annex and effective date."},
        ]

    def exports_to_next_chapter(self) -> Dict[str, Any]:
        return package_state(
            "ReferenceRateState",
            {
                "fallback_spread_bp": 0.0,
                "all_in_coupon_pct": 0.0,
                "coupon_vs_legacy_bp": 0.0,
            },
            "Feeds asset-swap decomposition with standardized floating benchmark assumptions.",
        )
