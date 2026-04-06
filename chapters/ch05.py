from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from core.types import ChapterExportState, RiskMetricState
from src.models.risk_measures import shock_adjusted_bond_state

from .base import ChapterBase


class Chapter05(ChapterBase):
    chapter_id = "5"

    def chapter_meta(self) -> Dict[str, Any]:
        return {"chapter": self.chapter_id, "title": "Chapter 5: Duration and convexity diagnostics", "objective": "Translate curve shocks into price response."}

    def prerequisites(self) -> List[str]:
        return ["Yield curve points", "Duration and convexity definitions"]

    def concept_map(self) -> Dict[str, List[str]]:
        return {"nodes": ["Curve slope", "Duration", "Convexity", "Shock", "Fair price"], "edges": ["Shock+Greeks->Price change", "Price change->Fair price"]}

    def equation_set(self) -> List[Dict[str, str]]:
        return [{"name": "Price approximation", "equation": "dP/P≈-D*dy+0.5*C*dy^2"}]

    def derivation_steps(self) -> List[str]:
        return ["Choose dy shock in bp.", "Convert bp to decimal.", "Apply duration-convexity approximation."]

    def interactive_lab(self) -> RiskMetricState:
        st.caption("Pedagogical simplification: duration-convexity approximation assumes a parallel yield shock.")
        y2 = st.number_input("2Y yield (%)", value=3.70, step=0.01)
        y10 = st.number_input("10Y yield (%)", value=4.10, step=0.01)
        duration = st.number_input("Modified duration", value=7.2, step=0.1)
        convexity = st.number_input("Convexity", value=65.0, step=1.0)
        price = st.number_input("Bond price", value=100.0, step=0.1)
        dy_bp = st.slider("Yield shock (bp)", -100, 100, 10)

        slope, dp_pct, fair_price = shock_adjusted_bond_state(
            y2=y2,
            y10=y10,
            duration=duration,
            convexity=convexity,
            price=price,
            dy_bp=dy_bp,
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("2s10s slope (bp)", f"{slope:.1f}")
        c2.metric("Estimated price change (%)", f"{dp_pct * 100:.3f}")
        c3.metric("Shock-adjusted fair price", f"{fair_price:.3f}")

        return RiskMetricState(
            curve_slope_bp=slope,
            duration=duration,
            convexity=convexity,
            dy_bp=dy_bp,
            dp_pct=dp_pct,
            fair_price=fair_price,
        )

    def case_studies(self) -> List[Dict[str, str]]:
        return [{"name": "Bull steepener", "setup": "Front-end rallies more than long-end", "takeaway": "Curve slope and duration profile jointly drive PnL."}]

    def failure_modes(self) -> List[Dict[str, str]]:
        return [{"mode": "Large shock nonlinearity", "mitigation": "Reprice full cashflows beyond local approximation."}]

    def assessment(self) -> List[Dict[str, str]]:
        return [{"prompt": "What term dampens duration losses in big moves?", "expected": "Positive convexity term."}]

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            signals=["fair_price", "curve_slope_bp", "dp_pct"],
            usage="Compared with market pricing for rich/cheap screens.",
            schema_name="RiskMetricState",
        )
