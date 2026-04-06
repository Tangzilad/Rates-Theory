from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from core.types import ChapterExportState, MVOUState
from src.models.mvou import MVOUProcess, compare_independent_vs_joint, non_monotonic_expected_path_example, simulate_mvou_2d, simulate_mvou_3d

from .base import ChapterBase


class Chapter04(ChapterBase):
    chapter_id = "4"

    def chapter_meta(self) -> dict[str, str]:
        return {
            "chapter": self.chapter_id,
            "title": "Chapter 4: Multivariate mean reversion",
            "objective": "Core claim: joint matrix-OU dynamics are materially better than isolated single-leg OU for spread baskets.",
        }

    def prerequisites(self) -> list[str]:
        return [
            "Market objects: tradable spread legs (2D/3D basket)",
            "Market objects: hedge ratios and co-movement intuition",
            "Matrix notation for K, mu, and covariance",
        ]

    def concept_map(self) -> dict[str, list[str]]:
        return {
            "nodes": ["K diagonal", "K off-diagonal", "Long-run mean", "Covariance", "Expected path", "Hedge design"],
            "edges": [
                "K diagonal->Self mean reversion",
                "K off-diagonal->Cross-coupling",
                "Covariance->Co-movement",
                "Expected path+Simulation->Trade interpretation",
                "Trade interpretation->Hedge design",
            ],
        }

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Matrix OU", "equation": "dX_t = K(mu - X_t)dt + L dW_t, with Sigma = L L^T"},
            {"name": "Expected path", "equation": "E[X_t] = mu + exp(-K t)(X_0 - mu)"},
            {"name": "Independent baseline", "equation": "K_ind = diag(K), Sigma_ind = diag(Sigma)"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Start from matrix OU dynamics and isolate deterministic expectation by removing Brownian shocks.",
            "Apply the matrix exponential solution to obtain E[X_t] and visualize diagonal vs off-diagonal K effects.",
            "Compare joint and independent dynamics, then map covariance into hedge suggestions for basket construction.",
        ]

    def interactive_lab(self) -> MVOUState:
        dim = st.radio("System dimension", options=[2, 3], horizontal=True, index=0, format_func=lambda x: f"{x}D basket")

        st.subheader("K matrix and long-run mean")
        c1, c2, c3 = st.columns(3)
        k11 = c1.slider("K[1,1] self-reversion", 0.05, 3.0, 1.10, 0.05)
        k22 = c2.slider("K[2,2] self-reversion", 0.05, 3.0, 0.90, 0.05)
        k33 = c3.slider("K[3,3] self-reversion", 0.05, 3.0, 0.70, 0.05, disabled=dim == 2)

        c4, c5, c6 = st.columns(3)
        mu1 = c4.number_input("mu[1]", value=0.0, step=0.1)
        mu2 = c5.number_input("mu[2]", value=0.0, step=0.1)
        mu3 = c6.number_input("mu[3]", value=0.0, step=0.1, disabled=dim == 2)

        st.caption("Off-diagonal K terms control cross-coupling between legs.")
        o1, o2, o3 = st.columns(3)
        k12 = o1.slider("K[1,2]", -2.0, 2.0, -0.40, 0.05)
        k21 = o2.slider("K[2,1]", -2.0, 2.0, 0.35, 0.05)
        k13 = o3.slider("K[1,3]", -2.0, 2.0, 0.10, 0.05, disabled=dim == 2)
        o4, o5, o6 = st.columns(3)
        k31 = o4.slider("K[3,1]", -2.0, 2.0, -0.05, 0.05, disabled=dim == 2)
        k23 = o5.slider("K[2,3]", -2.0, 2.0, 0.15, 0.05, disabled=dim == 2)
        k32 = o6.slider("K[3,2]", -2.0, 2.0, -0.10, 0.05, disabled=dim == 2)

        if dim == 2:
            kappa = np.array([[k11, k12], [k21, k22]], dtype=float)
            mu = np.array([mu1, mu2], dtype=float)
        else:
            kappa = np.array([[k11, k12, k13], [k21, k22, k23], [k31, k32, k33]], dtype=float)
            mu = np.array([mu1, mu2, mu3], dtype=float)

        st.subheader("Covariance and initial state")
        v1, v2, v3 = st.columns(3)
        vol1 = v1.slider("vol[1]", 0.05, 2.0, 0.60, 0.05)
        vol2 = v2.slider("vol[2]", 0.05, 2.0, 0.45, 0.05)
        vol3 = v3.slider("vol[3]", 0.05, 2.0, 0.40, 0.05, disabled=dim == 2)

        r1, r2, r3 = st.columns(3)
        corr12 = r1.slider("corr(1,2)", -0.95, 0.95, 0.35, 0.05)
        corr13 = r2.slider("corr(1,3)", -0.95, 0.95, 0.25, 0.05, disabled=dim == 2)
        corr23 = r3.slider("corr(2,3)", -0.95, 0.95, 0.15, 0.05, disabled=dim == 2)

        if dim == 2:
            covariance = np.array(
                [
                    [vol1**2, corr12 * vol1 * vol2],
                    [corr12 * vol1 * vol2, vol2**2],
                ],
                dtype=float,
            )
        else:
            covariance = np.array(
                [
                    [vol1**2, corr12 * vol1 * vol2, corr13 * vol1 * vol3],
                    [corr12 * vol1 * vol2, vol2**2, corr23 * vol2 * vol3],
                    [corr13 * vol1 * vol3, corr23 * vol2 * vol3, vol3**2],
                ],
                dtype=float,
            )

        s1, s2, s3 = st.columns(3)
        x1 = s1.number_input("x0[1]", value=1.2, step=0.1)
        x2 = s2.number_input("x0[2]", value=-0.6, step=0.1)
        x3 = s3.number_input("x0[3]", value=0.4, step=0.1, disabled=dim == 2)
        x0 = np.array([x1, x2] if dim == 2 else [x1, x2, x3], dtype=float)

        g1, g2 = st.columns(2)
        horizon = g1.slider("Horizon (trading days)", min_value=20, max_value=252, value=126, step=2)
        n_paths = g2.slider("Simulation paths", min_value=100, max_value=1200, value=400, step=100)

        process = MVOUProcess(kappa=kappa, mu=mu, covariance=covariance)
        expected = process.expected_path(x0=x0, n_steps=horizon)
        if dim == 2:
            paths = simulate_mvou_2d(kappa=kappa, mu=mu, covariance=covariance, x0=x0, n_steps=horizon, n_paths=n_paths, random_seed=17)
        else:
            paths = simulate_mvou_3d(kappa=kappa, mu=mu, covariance=covariance, x0=x0, n_steps=horizon, n_paths=n_paths, random_seed=17)

        fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
        for leg in range(dim):
            axes[0].plot(expected[:, leg], linewidth=2.0, label=f"E[Leg {leg + 1}]")
            for sample_idx in range(min(18, n_paths)):
                axes[0].plot(paths[sample_idx, :, leg], alpha=0.08, linewidth=0.7, color=f"C{leg}")
        axes[0].set_title("Expected path + sample joint paths")
        axes[0].set_xlabel("Day")
        axes[0].set_ylabel("Spread state")
        axes[0].legend(loc="best")

        term = paths[:, -1, :]
        if dim == 2:
            axes[1].scatter(term[:, 0], term[:, 1], alpha=0.35, s=14)
            axes[1].set_xlabel("Terminal leg 1")
            axes[1].set_ylabel("Terminal leg 2")
            axes[1].set_title("Terminal co-movement")
        else:
            axes[1].scatter(term[:, 0], term[:, 1], alpha=0.35, s=14, label="(1,2)")
            axes[1].scatter(term[:, 0], term[:, 2], alpha=0.35, s=14, label="(1,3)")
            axes[1].set_xlabel("Terminal leg 1")
            axes[1].set_ylabel("Terminal other legs")
            axes[1].set_title("Projected terminal co-movement")
            axes[1].legend(loc="best")
        st.pyplot(fig)

        diag_effect = np.diag(kappa)
        off_diag_strength = float(np.sum(np.abs(kappa - np.diag(diag_effect))))
        corr_matrix = covariance / np.sqrt(np.outer(np.diag(covariance), np.diag(covariance)))
        avg_abs_corr = float(np.mean(np.abs(corr_matrix[np.triu_indices(dim, k=1)]))) if dim > 1 else 0.0

        comp = compare_independent_vs_joint(
            kappa=kappa,
            mu=mu,
            covariance=covariance,
            x0=x0,
            n_steps=horizon,
            n_paths=min(600, n_paths),
            random_seed=99,
        )

        cdiag, coff, ccov = st.columns(3)
        cdiag.metric("K diagonal avg", f"{float(np.mean(diag_effect)):.3f}")
        coff.metric("K off-diagonal L1", f"{off_diag_strength:.3f}")
        ccov.metric("Average |corr|", f"{avg_abs_corr:.3f}")

        st.markdown(
            "\n".join(
                [
                    f"- **Diagonal K effects:** average self-reversion speed is **{float(np.mean(diag_effect)):.2f}**; larger values pull each leg to its own mean faster.",
                    f"- **Off-diagonal K effects:** cross-coupling magnitude is **{off_diag_strength:.2f}**, so one leg's dislocation propagates into others.",
                    f"- **Covariance impact on co-movement:** average absolute correlation is **{avg_abs_corr:.2f}**; this sets how tightly shocks arrive together.",
                    f"- **Joint vs independent comparison:** terminal corr (joint) **{comp['joint_terminal_corr']:.2f}** vs independent **{comp['independent_terminal_corr']:.2f}**, path RMSE **{comp['mean_path_rmse']:.3f}**.",
                ]
            )
        )

        show_non_monotonic = st.checkbox("Show optional non-monotonic expected-path example", value=False)
        if show_non_monotonic:
            _, _, _, _, special_expected = non_monotonic_expected_path_example(n_steps=horizon)
            fig2, ax2 = plt.subplots(figsize=(7, 3.5))
            ax2.plot(special_expected[:, 0], label="Example leg 1")
            ax2.plot(special_expected[:, 1], label="Example leg 2")
            ax2.set_title("Damped non-monotonic expected path")
            ax2.legend(loc="best")
            st.pyplot(fig2)
            st.caption("This example uses rotational cross-coupling so expected values can overshoot before converging.")

        hedge_suggestions: list[str] = []
        for idx in range(1, dim):
            if covariance[idx, idx] > 0:
                beta = covariance[0, idx] / covariance[idx, idx]
                hedge_suggestions.append(f"Hedge leg 1 with {-beta:.2f} units of leg {idx + 1} (covariance beta hedge).")

        spread_norm = float(np.linalg.norm(x0 - mu))
        stationary_scale = float(np.sqrt(np.trace(covariance)))
        z_score = spread_norm / stationary_scale if stationary_scale > 0 else 0.0
        st.metric("Basket z-score proxy", f"{z_score:.2f}")

        return MVOUState(
            k_matrix=kappa.tolist(),
            mu_vector=mu.tolist(),
            covariance_matrix=covariance.tolist(),
            expected_path=expected.tolist(),
            simulated_joint_paths=paths[: min(40, n_paths)].tolist(),
            hedge_suggestions=hedge_suggestions,
        )

    def case_studies(self) -> list[dict[str, str]]:
        return [
            {
                "name": "Trade interpretation",
                "setup": "Use expected-path speed and joint terminal correlation to choose entry size and hedge mix.",
                "takeaway": "A strongly coupled K matrix argues for basket-level risk limits rather than single-leg stop rules.",
            }
        ]

    def failure_modes(self) -> list[dict[str, str]]:
        return [
            {"mode": "Unstable or misspecified K", "mitigation": "Constrain eigenvalues to positive real parts and re-estimate on rolling windows."},
            {"mode": "Covariance regime break", "mitigation": "Stress-test low/high-correlation regimes before using hedge ratios."},
        ]

    def assessment(self) -> list[dict[str, str]]:
        return [
            {
                "prompt": "Checkpoint: if K off-diagonal entries increase while diagonal terms stay fixed, what changes first?",
                "expected": "Cross-leg transmission rises, making joint path shape and hedge ratios more sensitive to one-leg shocks.",
            }
        ]

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            signals=[
                "k_matrix",
                "mu_vector",
                "covariance_matrix",
                "expected_path",
                "simulated_joint_paths",
                "hedge_suggestions",
                "z_score",
            ],
            usage="Feeds Chapter 5 diagnostics with joint spread state and z-score-style dislocation context.",
            schema_name="MVOUState",
        )
