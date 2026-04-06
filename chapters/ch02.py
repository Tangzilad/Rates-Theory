from __future__ import annotations

from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from core.derivations import ou_half_life_days
from core.types import ChapterExportState, MeanReversionState
from src.models.ou import conditional_expectation, estimate_ou_parameters, sharpe_ratio, simulate_ou

from .base import ChapterBase


class Chapter02(ChapterBase):
    chapter_id = "2"

    def chapter_meta(self) -> Dict[str, Any]:
        return {"chapter": self.chapter_id, "title": "Chapter 2: OU mean reversion", "objective": "Quantify spread reversion and first-passage risk."}

    def prerequisites(self) -> List[str]:
        return ["Stochastic process notation", "Euler simulation", "Sharpe ratio basics"]

    def concept_map(self) -> Dict[str, List[str]]:
        return {"nodes": ["Theta", "Mu", "Sigma", "Path", "Barrier"], "edges": ["Theta+Mu->Drift", "Sigma->Noise", "Path+Barrier->First-passage"]}

    def equation_set(self) -> List[Dict[str, str]]:
        return [
            {"name": "OU SDE", "equation": "dX_t=\\theta(\\mu-X_t)dt+\\sigma dW_t"},
            {"name": "Conditional mean", "equation": "\\mathbb E[X_{t+h}|X_t]=\\mu+(X_t-\\mu)e^{-\\theta h}"},
            {"name": "Stationary variance", "equation": "\\mathrm{Var}[X_\\infty]=\\frac{\\sigma^2}{2\\theta}"},
            {"name": "Half-life", "equation": "t_{1/2}=\\frac{\\ln(2)}{\\theta}"},
        ]

    def derivation_steps(self) -> List[str]:
        return ["Discretize the SDE with Euler-Maruyama.", "Generate paths with Gaussian shocks.", "Compute barrier-hitting statistics."]

    def interactive_lab(self) -> MeanReversionState:
        st.caption("Pedagogical simplification: OU paths use Euler discretization and simplified barrier diagnostics.")
        c1, c2, c3, c4 = st.columns(4)
        theta = c1.slider("Mean reversion speed (theta)", 0.05, 3.0, 1.0, 0.05)
        mu = c2.number_input("Long-run mean (mu)", value=0.0, step=0.1)
        sigma = c3.slider("Volatility (sigma)", 0.01, 2.0, 0.4, 0.01)
        x0 = c4.number_input("Initial value", value=1.0, step=0.1)
        barrier = st.number_input("First-passage barrier", value=0.0, step=0.1)

        n_steps = 252
        n_paths = 400
        paths = simulate_ou(x0=x0, theta=theta, mu=mu, sigma=sigma, n_steps=n_steps - 1, n_paths=n_paths, random_seed=7)

        pnl = paths[:, -1] - paths[:, 0]
        sharpe = float(sharpe_ratio(pnl, annualize=False)) if np.std(pnl) > 0 else float("nan")

        hit_mask = paths <= barrier
        first_hit = np.argmax(hit_mask, axis=1)
        no_hit = ~hit_mask.any(axis=1)
        first_hit[no_hit] = n_steps
        fpt_days = np.where(first_hit < n_steps, first_hit, np.nan)

        fig, ax = plt.subplots(figsize=(8, 4))
        for i in range(min(40, n_paths)):
            ax.plot(paths[i], alpha=0.35, linewidth=0.8)
        ax.axhline(mu, color="black", linestyle="--", label="mu")
        ax.axhline(barrier, color="red", linestyle=":", label="barrier")
        ax.set_title("Simulated OU paths")
        ax.set_xlabel("Day")
        ax.set_ylabel("State")
        ax.legend()
        st.pyplot(fig)

        hit_prob = float(np.nanmean(~np.isnan(fpt_days)))
        mean_fpt_raw = np.nanmean(fpt_days)
        mean_fpt = float(mean_fpt_raw) if np.isfinite(mean_fpt_raw) else None
        half_life = ou_half_life_days(theta)
        stationary_std = float(np.sqrt((sigma**2) / (2.0 * theta))) if theta > 0 else np.nan
        current_z_score = float((x0 - mu) / stationary_std) if stationary_std > 0 else float("nan")

        sample_series = paths[0]
        est = estimate_ou_parameters(sample_series)
        st.caption(f"AR(1)→OU estimate: theta={est.theta:.3f}, mu={est.mu:.3f}, sigma={est.sigma:.3f}")

        horizon_days = np.array([1, 5, 10, 21, 42, 63, 126, 252], dtype=float)
        expected_path = [float(conditional_expectation(x_t=x0, horizon=h / 252.0, theta=theta, mu=mu)) for h in horizon_days]
        term_df = {"horizon_days": horizon_days.tolist(), "conditional_expectation": expected_path}

        st.metric("Current z-score", f"{current_z_score:.2f}" if np.isfinite(current_z_score) else "N/A")
        st.metric("Estimated first-passage probability", f"{hit_prob:.2%}")
        st.metric("Mean first-passage time (days)", f"{mean_fpt:.1f}" if mean_fpt is not None else "No hits")
        st.metric("Terminal Sharpe (simulated)", f"{sharpe:.3f}" if np.isfinite(sharpe) else "N/A")
        st.metric("Half-life estimate (days)", f"{half_life:.1f}" if half_life is not None else "N/A")

        return MeanReversionState(
            theta=theta,
            mu=mu,
            sigma=sigma,
            x0=x0,
            current_z_score=current_z_score,
            half_life=half_life,
            first_passage_probability=hit_prob,
            mean_first_passage_time=mean_fpt,
            terminal_sharpe=sharpe,
            conditional_expectation_term_structure=term_df,
        )

    def case_studies(self) -> List[Dict[str, str]]:
        return [{"name": "Spread convergence trade", "setup": "Entry on 2-sigma deviation", "takeaway": "Half-life should match expected holding window."}]

    def failure_modes(self) -> List[Dict[str, str]]:
        return [{"mode": "Regime shift", "mitigation": "Re-estimate theta and mu with rolling windows and break tests."}]

    def assessment(self) -> List[Dict[str, str]]:
        return [{"prompt": "What happens to first-passage time as theta increases?", "expected": "Barrier is generally hit faster when mean is on the barrier side."}]

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            signals=[
                "theta",
                "mu",
                "sigma",
                "x0",
                "current_z_score",
                "half_life",
                "first_passage_probability",
                "mean_first_passage_time",
                "terminal_sharpe",
                "conditional_expectation_term_structure",
            ],
            usage="Inputs for PCA-based factor-aware signal timing.",
            schema_name="MeanReversionState",
        )
