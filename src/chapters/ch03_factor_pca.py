from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from core.market_data import synthetic_tenor_matrix
from core.types import ChapterExportState, FactorState
from src.models.pca import factor_neutral_weights, run_pca

from .base import ChapterBase


class Chapter03(ChapterBase):
    chapter_id = "3"

    def chapter_meta(self) -> dict[str, str]:
        return {"chapter": self.chapter_id, "title": "Chapter 3: PCA factor extraction", "objective": "Extract orthogonal curve factors for diagnostics."}

    def prerequisites(self) -> list[str]:
        return ["Covariance matrix", "Eigenvectors/eigenvalues", "Yield curve tenors"]

    def concept_map(self) -> dict[str, list[str]]:
        return {"nodes": ["Returns", "Standardization", "Covariance", "Eigenpairs", "Factors"], "edges": ["Returns->Standardization", "Standardization->Covariance", "Covariance->Eigenpairs", "Eigenpairs->Factors"]}

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Explained variance", "equation": "EV_i=lambda_i/sum(lambda)"},
            {"name": "Factor score", "equation": "F=ZV"},
            {"name": "Residualized series", "equation": "R=Z-F_kV_k^T"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Standardize numeric columns into Z-scores matrix Z.",
            "Compute covariance matrix and sort eigenpairs descending by eigenvalue.",
            "Construct factor scores through time F = Z @ eigenvectors.",
            "Reconstruct selected component panel and compute residualized series after removing those PCs.",
            "Solve candidate factor-neutral hedge weights from selected factor exposures.",
        ]

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
            return FactorState(
                columns=[],
                explained_variance=[],
                eigenvectors={},
                factor_scores={},
                residualized_series={},
                candidate_neutral_hedge_weights={},
            )

        pca_result = run_pca(x.to_numpy())
        explained = pca_result.explained_variance_ratio
        evecs = pca_result.eigenvectors
        cols = list(x.columns)
        z = pca_result.standardized_data
        scores = z @ evecs

        exp_df = pd.DataFrame({"PC": [f"PC{i + 1}" for i in range(len(explained))], "Explained Var": explained})
        st.dataframe(exp_df, use_container_width=True)

        max_pc_for_controls = min(5, evecs.shape[1])
        selected_pc_count = st.slider(
            "Reconstruction / residualization PCs",
            min_value=1,
            max_value=max_pc_for_controls,
            value=min(2, max_pc_for_controls),
            help="1=PC1 only, 2=PC1+PC2, etc.",
        )
        selected_evecs = evecs[:, :selected_pc_count]
        selected_scores = scores[:, :selected_pc_count]
        reconstructed = selected_scores @ selected_evecs.T
        residualized = z - reconstructed

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

        fig3, ax3 = plt.subplots(figsize=(8, 4))
        for i in range(min(3, scores.shape[1])):
            ax3.plot(scores[:, i], label=f"PC{i + 1} score")
        ax3.axhline(0, color="black", linewidth=0.8)
        ax3.set_title("Factor scores through time (Z @ eigenvectors)")
        ax3.legend()
        st.pyplot(fig3)

        recon_df = pd.DataFrame(reconstructed, columns=cols)
        resid_df = pd.DataFrame(residualized, columns=cols)
        st.markdown(f"**Reconstruction preview (first 10 rows, using PC1..PC{selected_pc_count})**")
        st.dataframe(recon_df.head(10), use_container_width=True)
        st.markdown("**Residualized panel (first 10 rows)**")
        st.dataframe(resid_df.head(10), use_container_width=True)

        neutral_pc_count = st.slider(
            "Neutral hedge to first N PCs",
            min_value=1,
            max_value=max_pc_for_controls,
            value=min(2, max_pc_for_controls),
            help="Construct candidate weights neutral to the selected leading factors.",
        )
        try:
            hedge_weights = factor_neutral_weights(evecs, neutral_factors=tuple(range(neutral_pc_count)))
            hedge_weights_map = {c: float(w) for c, w in zip(cols, hedge_weights)}
            st.dataframe(
                pd.DataFrame(
                    {"Column": cols, "Candidate neutral hedge weight": [hedge_weights_map[c] for c in cols]}
                ),
                use_container_width=True,
            )
        except ValueError as err:
            st.warning(f"Could not construct candidate neutral weights: {err}")
            hedge_weights_map = {}

        st.markdown("### Factor interpretation panel")
        interp_rows = []
        for i in range(min(3, evecs.shape[1])):
            vec = evecs[:, i]
            left_mean = float(np.mean(vec[: max(1, len(vec) // 3)]))
            right_mean = float(np.mean(vec[-max(1, len(vec) // 3) :]))
            sign_changes = int(np.sum(np.sign(vec[:-1]) != np.sign(vec[1:])))
            if sign_changes == 0:
                likely = "Level"
            elif sign_changes == 1:
                likely = "Slope"
            else:
                likely = "Curvature"
            interp_rows.append(
                {
                    "Factor": f"PC{i + 1}",
                    "Likely interpretation": likely,
                    "Front avg loading": left_mean,
                    "Back avg loading": right_mean,
                    "Sign changes": sign_changes,
                }
            )
        st.dataframe(pd.DataFrame(interp_rows), use_container_width=True)
        st.warning(
            "Interpretations such as level/slope/curvature are heuristics: PCA factors are statistical objects, "
            "not guaranteed economic truths."
        )

        return FactorState(
            columns=cols,
            explained_variance=explained.tolist(),
            eigenvectors={f"PC{i + 1}": evecs[:, i].tolist() for i in range(evecs.shape[1])},
            factor_scores={f"PC{i + 1}": scores[:, i].tolist() for i in range(scores.shape[1])},
            residualized_series={c: resid_df[c].tolist() for c in cols},
            candidate_neutral_hedge_weights=hedge_weights_map,
        )

    def case_studies(self) -> list[dict[str, str]]:
        return [{"name": "Level/slope/curvature decomposition", "setup": "Daily curve changes", "takeaway": "First factors usually explain most variance."}]

    def failure_modes(self) -> list[dict[str, str]]:
        return [{"mode": "Using raw non-stationary levels", "mitigation": "Use changes/returns and monitor factor stability."}]

    def assessment(self) -> list[dict[str, str]]:
        return [{"prompt": "Why standardize before PCA?", "expected": "To avoid scale-dominated factors."}]

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            signals=["factor_scores", "explained_variance", "residualized_series", "candidate_neutral_hedge_weights"],
            usage="Feed spread diagnostics, residualized monitoring, and candidate hedge design.",
            schema_name="FactorState",
        )
