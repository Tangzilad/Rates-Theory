from __future__ import annotations

import numpy as np
import streamlit as st

from core.types import BondResidualState, ChapterExportState, RelativeValueScreenState
from src.models.fitted_curves import constant_maturity_yields, fit_parametric_curve

from .base import ChapterBase


class Chapter08(ChapterBase):
    chapter_id = "8"

    def chapter_meta(self) -> dict[str, str]:
        return {
            "chapter": self.chapter_id,
            "title": "Chapter 8: Relative-value screens",
            "objective": "Fit a curve to a selected bond set, measure rich/cheap residuals, and export actionable trade-screen diagnostics for Chapter 9.",
        }

    def prerequisites(self) -> list[str]:
        return [
            "Curve representation and calibration diagnostics (Chapter 6)",
            "Risk governance thresholds and override policy (Chapter 7)",
            "Bond-yield conventions across maturities",
        ]

    def concept_map(self) -> dict[str, list[str]]:
        return {
            "nodes": [
                "Bond set",
                "Parametric curve",
                "Outlier control",
                "Residual diagnostics",
                "Benchmark/repo adjustment",
                "Rich/cheap flags",
                "Chapter 9 handoff",
            ],
            "edges": [
                "Bond set->Parametric curve",
                "Parametric curve->Residual diagnostics",
                "Residual diagnostics->Outlier control",
                "Outlier control->Rich/cheap flags",
                "Benchmark/repo adjustment->Rich/cheap flags",
                "Rich/cheap flags->Chapter 9 handoff",
            ],
        }

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Curve fit objective", "equation": "min_θ Σ_i w_i(y_i^obs - y_i^fit(θ))^2"},
            {"name": "Residual (bp)", "equation": "r_i^{bp}=100*(y_i^obs-y_i^fit)"},
            {
                "name": "Benchmark/repo adjusted residual",
                "equation": "r_i^{adj,bp}=r_i^{bp}-benchmark_spread_bp+repo_specialness_bp",
            },
            {"name": "Constant-maturity extraction", "equation": "CM(t)=y^fit(t; θ)"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Input a bond universe with maturities and observed yields.",
            "Calibrate a chosen parametric curve (Nelson-Siegel or Svensson).",
            "Apply optional outlier handling (exclude or down-weight) and refit.",
            "Compute per-bond rich/cheap residuals and adjusted residuals.",
            "Extract constant-maturity fitted yields and export diagnostics for Chapter 9 trade construction.",
        ]

    def interactive_lab(self) -> RelativeValueScreenState:
        st.subheader("Bond set controls")
        bond_count = st.slider("Number of bonds", min_value=5, max_value=16, value=8, step=1, key="ch8_bond_count")
        base_maturities = np.linspace(0.5, 30.0, bond_count)
        curve_shape = 3.0 + 0.8 * np.exp(-base_maturities / 2.0) + 0.4 * ((1.0 - np.exp(-base_maturities / 8.0)) / (base_maturities / 8.0) - np.exp(-base_maturities / 8.0))

        maturities: list[float] = []
        observed: list[float] = []
        labels: list[str] = []

        for idx in range(bond_count):
            c1, c2 = st.columns(2)
            mat = c1.number_input(
                f"Bond {idx + 1} maturity (years)",
                min_value=0.25,
                max_value=40.0,
                value=float(base_maturities[idx]),
                step=0.25,
                key=f"ch8_mat_{idx}",
            )
            default_yield = float(curve_shape[idx] + 0.03 * np.sin(idx))
            yld = c2.number_input(
                f"Bond {idx + 1} yield (%)",
                min_value=-2.0,
                max_value=20.0,
                value=default_yield,
                step=0.01,
                key=f"ch8_yld_{idx}",
            )
            maturities.append(float(mat))
            observed.append(float(yld))
            labels.append(f"B{idx + 1}")

        st.subheader("Fit and residual controls")
        fit_method = st.selectbox("Parametric fit method", options=["svensson", "nelson_siegel"], index=0, key="ch8_fit_method")
        outlier_mode = st.selectbox("Outlier handling", options=["none", "exclude", "down_weight"], index=0, key="ch8_outlier_mode")
        outlier_z_cutoff = st.slider("Outlier z-score threshold", min_value=1.0, max_value=4.0, value=2.0, step=0.1, key="ch8_outlier_cut")
        down_weight_factor = st.slider("Down-weight factor", min_value=0.05, max_value=0.95, value=0.30, step=0.05, key="ch8_dw")

        adjust_residuals = st.checkbox("Apply benchmark/repo residual adjustment", value=False, key="ch8_adj_toggle")
        benchmark_spread_bp = st.number_input("Benchmark spread (bp)", value=0.0, step=0.5, key="ch8_bench_spread")
        repo_specialness_bp = st.number_input("Repo specialness (bp)", value=0.0, step=0.5, key="ch8_repo")

        m = np.asarray(maturities, dtype=float)
        y = np.asarray(observed, dtype=float)

        initial_fit = fit_parametric_curve(m, y, method=fit_method)
        initial_residual_bp = initial_fit.residuals_pct * 100.0
        z = (initial_residual_bp - initial_residual_bp.mean()) / (initial_residual_bp.std(ddof=1) + 1e-8)

        weights = np.ones_like(y)
        include_mask = np.ones_like(y, dtype=bool)
        if outlier_mode == "exclude":
            include_mask = np.abs(z) <= outlier_z_cutoff
        elif outlier_mode == "down_weight":
            weights = np.where(np.abs(z) > outlier_z_cutoff, down_weight_factor, 1.0)

        if outlier_mode == "exclude" and np.count_nonzero(include_mask) >= 4:
            fit = fit_parametric_curve(m[include_mask], y[include_mask], method=fit_method)
            full_fitted = constant_maturity_yields(fit, m)
            residual_pct = y - full_fitted
            rmse_bp = float(np.sqrt(np.mean((residual_pct * 100.0) ** 2)))
            params = fit.params
        else:
            fit = fit_parametric_curve(m, y, method=fit_method, weights=weights)
            full_fitted = fit.fitted_yields_pct
            residual_pct = fit.residuals_pct
            rmse_bp = fit.rmse_bp
            params = fit.params

        residual_bp = residual_pct * 100.0
        if adjust_residuals:
            adjusted_residual_bp = residual_bp - float(benchmark_spread_bp) + float(repo_specialness_bp)
        else:
            adjusted_residual_bp = residual_bp.copy()

        residual_std = float(np.std(adjusted_residual_bp, ddof=1)) if adjusted_residual_bp.size > 1 else 0.0
        residual_z = (adjusted_residual_bp - adjusted_residual_bp.mean()) / (residual_std + 1e-8)

        st.subheader("Fitted curve and observed bond yields")
        dense_m = np.linspace(float(np.min(m)), float(np.max(m)), 120)
        dense_curve = constant_maturity_yields(
            fit_parametric_curve(m, y, method=fit_method, weights=weights if outlier_mode == "down_weight" else None)
            if outlier_mode != "exclude"
            else fit,
            dense_m,
        )
        st.line_chart(
            {
                "Fitted curve (%)": dense_curve,
            }
        )

        st.subheader("Per-bond residual panel")
        rows = []
        bond_states: list[BondResidualState] = []
        for i, (label, mt, obs, fit_y, res, adj, rz) in enumerate(
            zip(labels, m, y, full_fitted, residual_bp, adjusted_residual_bp, residual_z)
        ):
            flag = "cheap" if adj > 0.0 else "rich"
            rows.append(
                {
                    "Bond": label,
                    "Maturity (Y)": float(mt),
                    "Observed (%)": float(obs),
                    "Fitted (%)": float(fit_y),
                    "Residual (bp)": float(res),
                    "Adjusted residual (bp)": float(adj),
                    "Adj z-score": float(rz),
                    "Flag": flag,
                    "In fit": bool(include_mask[i]) if outlier_mode == "exclude" else True,
                    "Weight": float(weights[i]),
                }
            )
            bond_states.append(
                BondResidualState(
                    bond_id=label,
                    maturity_years=float(mt),
                    observed_yield_pct=float(obs),
                    fitted_yield_pct=float(fit_y),
                    residual_bp=float(res),
                    adjusted_residual_bp=float(adj),
                    rich_cheap_flag=flag,
                )
            )
        st.dataframe(rows, use_container_width=True)

        st.subheader("Fitted parameters")
        st.json({k: float(v) for k, v in params.items()})

        st.subheader("Constant-maturity yields")
        cm_tenors = np.array([2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0], dtype=float)
        cm_values = constant_maturity_yields(fit if outlier_mode == "exclude" else fit, cm_tenors)
        cm_dict = {f"{int(t)}Y": float(v) for t, v in zip(cm_tenors, cm_values)}
        st.dataframe([{"Tenor": tenor, "Yield (%)": val} for tenor, val in cm_dict.items()], use_container_width=True)

        st.subheader("Screen summary metrics")
        c1, c2, c3 = st.columns(3)
        c1.metric("Fit RMSE (bp)", f"{rmse_bp:.2f}")
        c2.metric("Max |adj residual| (bp)", f"{float(np.max(np.abs(adjusted_residual_bp))):.2f}")
        scenario_value = float(np.max(np.abs(adjusted_residual_bp)))
        c3.metric("Scenario value proxy", f"{scenario_value:.2f}")

        return RelativeValueScreenState(
            fit_method=fit_method,
            fitted_parameters={k: float(v) for k, v in params.items()},
            bonds=bond_states,
            constant_maturity_yields_pct=cm_dict,
            residual_rmse_bp=float(rmse_bp),
            benchmark_adjustment_bp=float(benchmark_spread_bp if adjust_residuals else 0.0),
            repo_specialness_bp=float(repo_specialness_bp if adjust_residuals else 0.0),
            outlier_mode=outlier_mode,
            scenario_value=scenario_value,
        )

    def case_studies(self) -> list[dict[str, str]]:
        return [
            {
                "name": "On-the-run vs off-the-run screening",
                "setup": "Curve fit indicates near-tenor off-the-run bonds look cheap after repo adjustment.",
                "takeaway": "Residual ranking and funding adjustment together determine whether a statistical cheap signal is tradeable.",
            }
        ]

    def failure_modes(self) -> list[dict[str, str]]:
        return [
            {
                "mode": "False rich/cheap flags from stale quotes or issue-specific liquidity",
                "mitigation": "Use outlier controls and benchmark/repo adjustment; require governance overrides for one-off dislocations.",
            },
            {
                "mode": "Overfitting curve factors to noisy tails",
                "mitigation": "Compare Nelson-Siegel and Svensson stability and cap leverage to unstable factor regimes.",
            },
        ]

    def assessment(self) -> list[dict[str, str]]:
        return [
            {
                "prompt": "When should a large raw residual not trigger a trade?",
                "expected": "When benchmark/repo adjustments, liquidity issues, or outlier diagnostics indicate the residual is non-structural.",
            }
        ]

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            signals=[
                "scenario_value",
                "fit_method",
                "fitted_parameters",
                "bond_residuals",
                "constant_maturity_yields",
                "adjusted_residuals",
                "residual_rmse_bp",
            ],
            usage="Feeds Chapter 9 trade construction with curve-based rich/cheap ranking, adjusted residual diagnostics, and scenario intensity proxy.",
            schema_name="RelativeValueScreenState",
        )
