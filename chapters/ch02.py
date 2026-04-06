from __future__ import annotations

from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

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
        return [{"name": "OU SDE", "equation": "dX_t=theta(mu-X_t)dt+sigma dW_t"}]

    def derivation_steps(self) -> List[str]:
        return ["Discretize the SDE with Euler-Maruyama.", "Generate paths with Gaussian shocks.", "Compute barrier-hitting statistics."]

    def interactive_lab(self) -> Dict[str, Any]:
        c1, c2, c3, c4 = st.columns(4)
        theta = c1.slider("Mean reversion speed (theta)", 0.05, 3.0, 1.0, 0.05)
        mu = c2.number_input("Long-run mean (mu)", value=0.0, step=0.1)
        sigma = c3.slider("Volatility (sigma)", 0.01, 2.0, 0.4, 0.01)
        x0 = c4.number_input("Initial value", value=1.0, step=0.1)
        barrier = st.number_input("First-passage barrier", value=0.0, step=0.1)

        n_steps = 252
        n_paths = 400
        dt = 1 / 252
        rng = np.random.default_rng(7)
        x = np.full((n_paths, n_steps), x0, dtype=float)
        for t in range(1, n_steps):
            x[:, t] = x[:, t - 1] + theta * (mu - x[:, t - 1]) * dt + sigma * np.sqrt(dt) * rng.standard_normal(n_paths)

        pnl = x[:, -1] - x[:, 0]
        sharpe = float(np.mean(pnl) / np.std(pnl)) if np.std(pnl) > 0 else float("nan")

        hit_mask = x <= barrier
        first_hit = np.argmax(hit_mask, axis=1)
        no_hit = ~hit_mask.any(axis=1)
        first_hit[no_hit] = n_steps
        fpt_days = np.where(first_hit < n_steps, first_hit, np.nan)

        fig, ax = plt.subplots(figsize=(8, 4))
        for i in range(min(40, n_paths)):
            ax.plot(x[i], alpha=0.35, linewidth=0.8)
        ax.axhline(mu, color="black", linestyle="--", label="mu")
        ax.axhline(barrier, color="red", linestyle=":", label="barrier")
        ax.set_title("Simulated OU paths")
        ax.set_xlabel("Day")
        ax.set_ylabel("State")
        ax.legend()
        st.pyplot(fig)

        hit_prob = float(np.nanmean(~np.isnan(fpt_days)))
        mean_fpt = float(np.nanmean(fpt_days)) if np.isfinite(np.nanmean(fpt_days)) else None
        st.metric("Estimated first-passage probability", f"{hit_prob:.2%}")
        st.metric("Mean first-passage time (days)", f"{mean_fpt:.1f}" if mean_fpt is not None else "No hits")
        st.metric("Terminal Sharpe (simulated)", f"{sharpe:.3f}" if np.isfinite(sharpe) else "N/A")

        return {"inputs": {"theta": theta, "mu": mu, "sigma": sigma, "x0": x0, "barrier": barrier}, "outputs": {"hit_probability": hit_prob, "mean_fpt_days": mean_fpt, "terminal_sharpe": sharpe}}

    def case_studies(self) -> List[Dict[str, str]]:
        return [{"name": "Spread convergence trade", "setup": "Entry on 2-sigma deviation", "takeaway": "Half-life should match expected holding window."}]

    def failure_modes(self) -> List[Dict[str, str]]:
        return [{"mode": "Regime shift", "mitigation": "Re-estimate theta and mu with rolling windows and break tests."}]

    def assessment(self) -> List[Dict[str, str]]:
        return [{"prompt": "What happens to first-passage time as theta increases?", "expected": "Barrier is generally hit faster when mean is on the barrier side."}]

    def exports_to_next_chapter(self) -> Dict[str, Any]:
        return {"signals": ["half_life_proxy", "hit_probability"], "usage": "Inputs for PCA-based factor-aware signal timing."}
