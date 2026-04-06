from __future__ import annotations

import streamlit as st

from .base import ChapterBase


class Chapter06(ChapterBase):
    chapter_id = "6"

    def chapter_meta(self) -> dict[str, str]:
        return {"chapter": self.chapter_id, "title": "Chapter 6: Portfolio construction", "objective": "Convert approved single-name signals into portfolio weights under constraints."}

    def prerequisites(self) -> list[str]:
        return ["Signal scores", "Risk budgets", "Liquidity limits"]

    def concept_map(self) -> dict[str, list[str]]:
        return {"nodes": ["Signal alpha", "Risk model", "Constraints", "Weights", "Expected P&L"], "edges": ["Alpha+Risk->Raw weights", "Raw weights+Constraints->Feasible weights", "Feasible weights->Portfolio P&L"]}

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Constrained objective", "equation": "max_w  alpha^T w - lambda w^T Sigma w"},
            {"name": "Budget constraint", "equation": "sum_i |w_i| <= gross_limit"},
            {"name": "Liquidity cap", "equation": "|w_i| <= ADV_i * participation_cap"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Map chapter signal scores to expected alpha inputs.",
            "Penalize concentration using covariance-driven risk term.",
            "Project unconstrained solution into implementable limits (gross, net, liquidity).",
        ]

    def interactive_lab(self) -> dict[str, float | bool]:
        alpha_bp = st.number_input("Average signal alpha (bp)", value=18.0, step=1.0, key="alpha_6")
        risk_penalty = st.slider("Risk penalty λ", min_value=0.1, max_value=5.0, value=1.5, step=0.1, key="lambda_6")
        gross_limit = st.slider("Gross exposure limit", min_value=0.5, max_value=5.0, value=2.0, step=0.1, key="gross_6")

        unconstrained = alpha_bp / max(risk_penalty, 1e-6)
        feasible_weight = min(unconstrained / 100.0, gross_limit)
        expected_edge = feasible_weight * alpha_bp

        st.metric("Unconstrained score", f"{unconstrained:.2f}")
        st.metric("Feasible portfolio weight", f"{feasible_weight:.2f}")
        st.metric("Expected weighted edge (bp)", f"{expected_edge:.2f}")
        st.info("TODO: add covariance matrix ingestion and optimizer-backed multi-asset allocation.")

        return {"unconstrained_score": unconstrained, "feasible_weight": feasible_weight, "expected_weighted_edge_bp": expected_edge, "within_limits": feasible_weight <= gross_limit}

    def case_studies(self) -> list[dict[str, str]]:
        return [{"name": "Signal crowding", "setup": "Many high-z signals arrive simultaneously", "takeaway": "Constraint-aware sizing prevents over-concentrated books."}]

    def failure_modes(self) -> list[dict[str, str]]:
        return [{"mode": "Ignoring liquidity caps", "mitigation": "Apply participation-rate limits before proposing notional sizes."}]

    def assessment(self) -> list[dict[str, str]]:
        return [{"prompt": "What is the effect of raising λ?", "expected": "Risk aversion rises, reducing unconstrained size and feasible weights."}]

    def exports_to_next_chapter(self) -> dict[str, object]:
        return {"signals": ["feasible_weight", "expected_weighted_edge_bp", "within_limits"], "usage": "Feeds Chapter 7 risk-budget and governance checks."}
