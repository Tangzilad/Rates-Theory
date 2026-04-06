from __future__ import annotations

import streamlit as st

from .base import ChapterBase


class Chapter04(ChapterBase):
    chapter_id = "4"

    def chapter_meta(self) -> dict[str, str]:
        return {"chapter": self.chapter_id, "title": "Chapter 4: Spread/value signals", "objective": "Build ranked spread signals from model-vs-market dislocations."}

    def prerequisites(self) -> list[str]:
        return ["Chapter 1 basis output", "Chapter 2 reversion speed", "Chapter 3 factor diagnostics"]

    def concept_map(self) -> dict[str, list[str]]:
        return {
            "nodes": ["Model fair spread", "Observed spread", "Residual", "Z-score", "Signal rank"],
            "edges": ["Fair-Observed->Residual", "Residual/Vol->Z-score", "Z-score+Filters->Rank"],
        }

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Residual spread", "equation": "residual_t = spread_mkt,t - spread_fair,t"},
            {"name": "Standardized signal", "equation": "z_t = (residual_t - mu_res) / sigma_res"},
            {"name": "Priority score", "equation": "score_t = |z_t| * liquidity_weight * conviction"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Compute fair spread from carry/curve/factor controls.",
            "Subtract market spread to obtain residual mispricing.",
            "Standardize residuals and rank by absolute conviction adjusted for tradability.",
        ]

    def interactive_lab(self) -> dict[str, float | str | bool]:
        c1, c2, c3 = st.columns(3)
        spread_mkt = c1.number_input("Observed spread (bp)", value=84.0, step=1.0, key="mkt_4")
        spread_fair = c2.number_input("Model fair spread (bp)", value=70.0, step=1.0, key="fair_4")
        residual_vol = c3.number_input("Residual volatility (bp)", min_value=0.1, value=10.0, step=0.5, key="vol_4")
        liquidity_weight = st.slider("Liquidity weight", min_value=0.2, max_value=1.0, value=0.8, step=0.05, key="liq_4")

        residual = spread_mkt - spread_fair
        z_score = residual / residual_vol
        score = abs(z_score) * liquidity_weight
        signal = "short_spread" if residual > 0 else "long_spread"

        st.metric("Residual (bp)", f"{residual:.2f}")
        st.metric("Signal z-score", f"{z_score:.2f}")
        st.metric("Rank score", f"{score:.2f}")
        st.info("TODO: add cross-sectional ranking, decay controls, and multi-horizon signal blending.")

        return {"residual_bp": residual, "z_score": z_score, "rank_score": score, "signal_direction": signal, "eligible": score >= 1.0}

    def case_studies(self) -> list[dict[str, str]]:
        return [{"name": "Dislocation basket", "setup": "Sort spreads by normalized residual", "takeaway": "Ranked spreads support disciplined entry sequencing."}]

    def failure_modes(self) -> list[dict[str, str]]:
        return [{"mode": "Volatility regime shift", "mitigation": "Recompute residual sigma with rolling windows and cap stale z-scores."}]

    def assessment(self) -> list[dict[str, str]]:
        return [{"prompt": "What happens when residual volatility doubles?", "expected": "Absolute z-score and rank score fall for the same raw residual."}]

    def exports_to_next_chapter(self) -> dict[str, object]:
        return {"signals": ["residual_bp", "z_score", "rank_score", "signal_direction", "eligible"], "usage": "Feeds Chapter 5 diagnostics and Chapter 6 portfolio construction."}
