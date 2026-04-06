from __future__ import annotations

import streamlit as st

from core.types import ChapterExportState, RegimeState

from .base import ChapterBase


class Chapter04(ChapterBase):
    chapter_id = "4"

    def chapter_meta(self) -> dict[str, str]:
        return {
            "chapter": self.chapter_id,
            "title": "Chapter 4: Factor interpretation and regime mapping",
            "objective": "Translate PCA factors into interpretable regime labels and signal gates.",
        }

    def prerequisites(self) -> list[str]:
        return ["Chapter 3 factor loadings", "Macro-rate regime intuition", "Signal gating discipline"]

    def core_claim(self) -> str:
        return "Named level/slope/curvature factors become tradable only after mapping them into stable, testable regime labels."

    def market_objects(self) -> list[str]:
        return ["factor loadings", "regime score", "regime label", "signal gate"]

    def concept_map(self) -> dict[str, list[str]]:
        return {
            "nodes": ["Factor loadings", "Economic labels", "Composite regime score", "Threshold bands", "Signal gate"],
            "edges": ["Loadings->Labels", "Labels->Regime score", "Regime score+Bands->Regime label", "Regime label->Signal gate"],
        }

    def technical_equations(self) -> list[dict[str, str]]:
        return [
            {"name": "Composite regime score", "equation": "regime_score = w_level*L + w_slope*S + w_curv*C"},
            {"name": "Confidence", "equation": "confidence = min(|regime_score|/threshold, 1.0)"},
        ]

    def equation_set(self) -> list[dict[str, str]]:
        return self.technical_equations()

    def derivation(self) -> list[str]:
        return [
            "Assign economic names to factor loadings (level/slope/curvature).",
            "Build a weighted composite regime score from those standardized factors.",
            "Map score bands into regime labels and attach confidence for signal gating.",
        ]

    def derivation_steps(self) -> list[str]:
        return self.derivation()

    def interactive_lab(self) -> RegimeState:
        c1, c2, c3 = st.columns(3)
        level = c1.slider("Level factor", -3.0, 3.0, 0.6, 0.1, key="lvl_4")
        slope = c2.slider("Slope factor", -3.0, 3.0, -0.2, 0.1, key="slp_4")
        curvature = c3.slider("Curvature factor", -3.0, 3.0, 0.1, 0.1, key="curv_4")

        w_level = st.slider("Weight: level", 0.0, 1.0, 0.5, 0.05, key="wl_4")
        w_slope = st.slider("Weight: slope", 0.0, 1.0, 0.3, 0.05, key="ws_4")
        w_curv = st.slider("Weight: curvature", 0.0, 1.0, 0.2, 0.05, key="wc_4")
        threshold = st.number_input("Regime threshold", min_value=0.1, value=1.0, step=0.1, key="thr_4")

        regime_score = w_level * level + w_slope * slope + w_curv * curvature
        if regime_score >= threshold:
            label = "bear_steepening"
        elif regime_score <= -threshold:
            label = "bull_flattening"
        else:
            label = "range_bound"

        confidence = min(abs(regime_score) / threshold, 1.0)

        st.metric("Regime score", f"{regime_score:.2f}")
        st.metric("Regime label", label)
        st.metric("Confidence", f"{confidence:.1%}")

        return RegimeState(
            level_loading=level,
            slope_loading=slope,
            curvature_loading=curvature,
            regime_score=regime_score,
            regime_label=label,
            regime_confidence=confidence,
        )

    def trade_interpretation(self) -> list[str]:
        return [
            "High positive regime scores support defensive (short-duration / wideners) bias.",
            "Near-zero score suggests neutral sizing and tighter entry thresholds due to weak macro tailwind.",
        ]

    def case_studies(self) -> list[dict[str, str]]:
        return [{"name": "Inflation shock", "setup": "Level and slope factors rise together", "takeaway": "Composite score flags bear-steepening pressure."}]

    def failure_modes_model_risk(self) -> list[dict[str, str]]:
        return [{"mode": "Overfit regime boundaries", "mitigation": "Use broad confidence bands and out-of-sample validation."}]

    def failure_modes(self) -> list[dict[str, str]]:
        return self.failure_modes_model_risk()

    def checkpoint(self) -> list[dict[str, str]]:
        return [{"prompt": "What should happen to confidence when score magnitude is below threshold?", "expected": "Confidence remains below 100% and signal gating should be conservative."}]

    def assessment(self) -> list[dict[str, str]]:
        return self.checkpoint()

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            signals=["regime_score", "regime_label", "regime_confidence"],
            usage="Used by Chapter 5 to condition shock diagnostics on macro regime context.",
            schema_name="RegimeState",
        )
