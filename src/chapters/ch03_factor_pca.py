from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from core.market_data import synthetic_tenor_matrix
from core.types import ChapterExportState, FactorState
from src.models.pca_module import run_pca

from .base import ChapterBase


class Chapter03(ChapterBase):
    chapter_id = "3"

    def chapter_meta(self) -> dict[str, str]:
        return {"chapter": self.chapter_id, "title": "Chapter 3: PCA factor extraction", "objective": "Extract orthogonal curve factors for diagnostics."}

    def prerequisites(self) -> list[str]:
        return ["Covariance matrix", "Eigenvectors/eigenvalues", "Yield curve tenors"]

    def core_claim(self) -> str:
        return "A small orthogonal factor set explains most curve-variation and creates stable state variables for downstream signals."

    def market_objects(self) -> list[str]:
        return ["tenor return matrix", "covariance matrix", "eigenvectors", "factor scores"]

    def concept_map(self) -> dict[str, list[str]]:
        return {"nodes": ["Returns", "Standardization", "Covariance", "Eigenpairs", "Factors"], "edges": ["Returns->Standardization", "Standardization->Covariance", "Covariance->Eigenpairs", "Eigenpairs->Factors"]}

    def technical_equations(self) -> list[dict[str, str]]:
        return [{"name": "Explained variance", "equation": "EV_i=lambda_i/sum(lambda)"}]

    def derivation(self) -> list[str]:
        return ["Standardize numeric columns.", "Compute covariance matrix.", "Sort eigenpairs descending by eigenvalue."]

    def interactive_lab(self) -> FactorState:
        source = st.radio("Data source", ["Synthetic sample", "Upload CSV"], horizontal=True)
        df = None
        if source == "Upload CSV":
            up = st.file_uploader("Upload CSV (columns = tenors/factors)", type=["csv"])
            if up is not None:
                df = pd.read_csv(up)

        if df is None:
            df = synthetic_tenor_matrix()

        x = df.select_dtypes(include=[np.number]).dropna()
        if x.shape[1] < 2:
            st.warning("Need at least 2 numeric columns for PCA.")
            return FactorState(columns=[], explained_variance=[], top_loadings={})

        pca_result = run_pca(x.to_numpy())
        explained = pca_result.explained_variance_ratio
        evecs = pca_result.eigenvectors
        cols = list(x.columns)

        exp_df = pd.DataFrame({"PC": [f"PC{i + 1}" for i in range(len(explained))], "Explained Var": explained})
        st.dataframe(exp_df, use_container_width=True)

        fig1, ax1 = plt.subplots(figsize=(8, 4))
        ax1.bar(exp_df["PC"], exp_df["Explained Var"])
        ax1.set_title("Explained variance by factor")
        st.pyplot(fig1)

        fig2, ax2 = plt.subplots(figsize=(8, 4))
        max_factors = min(3, evecs.shape[1])
        for i in range(max_factors):
            ax2.plot(cols, evecs[:, i], marker="o", label=f"PC{i + 1}")
        ax2.axhline(0, color="black", linewidth=0.8)
        ax2.set_title("Eigenvector loadings")
        ax2.legend()
        st.pyplot(fig2)

        return FactorState(columns=cols, explained_variance=explained.tolist(), top_loadings={f"PC{i + 1}": evecs[:, i].tolist() for i in range(max_factors)})

    def trade_interpretation(self) -> list[str]:
        return [
            "Level/slope/curvature tilts reveal where RV bets are concentrated along the curve.",
            "Falling explained variance concentration can signal unstable factor regimes and lower sizing confidence.",
        ]

    def case_studies(self) -> list[dict[str, str]]:
        return [{"name": "Level/slope/curvature decomposition", "setup": "Daily curve changes", "takeaway": "First factors usually explain most variance."}]

    def failure_modes_model_risk(self) -> list[dict[str, str]]:
        return [{"mode": "Using raw non-stationary levels", "mitigation": "Use changes/returns and monitor factor stability."}]

    def checkpoint(self) -> list[dict[str, str]]:
        return [{"prompt": "Why standardize before PCA?", "expected": "To avoid scale-dominated factors."}]

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            signals=["factor_scores", "explained_variance"],
            usage="Feed multi-asset spread construction and hedge design.",
            schema_name="FactorState",
        )

    def equation_set(self) -> list[dict[str, str]]:
        return self.technical_equations()

    def derivation_steps(self) -> list[str]:
        return self.derivation()

    def failure_modes(self) -> list[dict[str, str]]:
        return self.failure_modes_model_risk()

    def assessment(self) -> list[dict[str, str]]:
        return self.checkpoint()
