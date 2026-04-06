from __future__ import annotations

import numpy as np
import streamlit as st

from core.types import ChapterExportState, CurvePoint, ResidualDiagnosticsState, YieldCurveModelState
from src.models.curve_representation import (
    evaluate_nss_curve,
    fit_nss_zero_curve,
    par_to_zero_bootstrap,
    piecewise_linear_curve,
    residual_diagnostics,
    zero_to_forward,
)

from .base import ChapterBase


class Chapter06(ChapterBase):
    chapter_id = "6"

    def chapter_meta(self) -> dict[str, str]:
        return {
            "chapter": self.chapter_id,
            "title": "Chapter 6: Yield curve models",
            "objective": "Show how identical market instruments can produce different zero/forward curves under different representations.",
        }

    def prerequisites(self) -> list[str]:
        return ["Par-swap / par-bond rates by tenor", "Discount factors and spot rates", "Forward-rate interpretation"]

    def concept_map(self) -> dict[str, list[str]]:
        return {
            "nodes": ["Par curve", "Bootstrap zero", "Forward curve", "Parametric fit", "Interpolation fit", "Residual diagnostics", "Risk interpretation"],
            "edges": [
                "Par curve->Bootstrap zero",
                "Bootstrap zero->Forward curve",
                "Bootstrap zero->Parametric fit",
                "Bootstrap zero->Interpolation fit",
                "Both fits->Residual diagnostics",
                "Residual diagnostics->Risk interpretation",
            ],
        }

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Par-to-zero bootstrap (annual pedagogical)", "equation": "1 = c*sum_{i=1}^{n-1} DF_i + (1+c)DF_n"},
            {"name": "Forward from zeros", "equation": "(1+z_n)^n = (1+z_{n-1})^{n-1}(1+f_{n-1,n})"},
            {"name": "NSS representation", "equation": "y(t)=β0+β1 L1(t,τ1)+β2 L2(t,τ1)+β3 L2(t,τ2)"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Input market par rates for standard maturities.",
            "Bootstrap pedagogical zero rates assuming annual coupon/pay frequencies.",
            "Derive forwards from adjacent zero nodes.",
            "Fit NSS parametric zero curve and build linear interpolation alternative.",
            "Compare residuals and risk diagnostics under same instrument set.",
        ]

    def interactive_lab(self) -> YieldCurveModelState:
        st.subheader("Market-rate inputs by maturity")
        maturities = np.array([1.0, 2.0, 3.0, 5.0, 7.0, 10.0], dtype=float)
        defaults = [4.10, 3.95, 3.82, 3.70, 3.66, 3.60]
        par_rates = np.array(
            [
                st.number_input(f"Par rate {int(mt)}Y (%)", value=default, step=0.01, key=f"ch6_par_{int(mt)}")
                for mt, default in zip(maturities, defaults)
            ],
            dtype=float,
        )

        st.subheader("Representation controls")
        interp_grid_density = st.slider("Interpolation display density", min_value=10, max_value=120, value=60, step=5, key="ch6_interp_density")

        zero_rates = par_to_zero_bootstrap(maturities=maturities, par_rates_pct=par_rates)
        forward_rates = zero_to_forward(maturities=maturities, zero_rates_pct=zero_rates)

        nss_params = fit_nss_zero_curve(maturities=maturities, zero_rates_pct=zero_rates)
        nss_at_nodes = evaluate_nss_curve(maturities=maturities, params=nss_params)
        interp_at_nodes = piecewise_linear_curve(maturities=maturities, rates_pct=zero_rates, target_maturities=maturities)

        diagnostics = residual_diagnostics(observed_pct=zero_rates, fitted_nss_pct=nss_at_nodes, fitted_interp_pct=interp_at_nodes)

        dense_maturities = np.linspace(float(maturities.min()), float(maturities.max()), interp_grid_density)
        dense_nss = evaluate_nss_curve(maturities=dense_maturities, params=nss_params)
        dense_interp = piecewise_linear_curve(maturities=maturities, rates_pct=zero_rates, target_maturities=dense_maturities)

        st.subheader("Par, zero, forward curves")
        curve_rows = [
            {
                "Maturity": float(mt),
                "Par (%)": float(pr),
                "Zero (%)": float(zr),
                "Forward (%)": float(fr),
            }
            for mt, pr, zr, fr in zip(maturities, par_rates, zero_rates, forward_rates)
        ]
        st.dataframe(curve_rows, use_container_width=True)

        st.subheader("Slope / curvature diagnostics")
        slope_2s10s = (zero_rates[-1] - zero_rates[1]) * 100.0
        belly_curvature = (2.0 * zero_rates[3] - zero_rates[1] - zero_rates[-1]) * 100.0
        c1, c2 = st.columns(2)
        c1.metric("2s10s slope (bp)", f"{slope_2s10s:.1f}")
        c2.metric("5Y belly curvature (bp)", f"{belly_curvature:.1f}")

        st.subheader("Side-by-side representation differences")
        diff_rows = [
            {
                "Maturity": float(mt),
                "NSS zero (%)": float(nss),
                "Linear interp zero (%)": float(interp),
                "NSS - interp (bp)": float((nss - interp) * 100.0),
            }
            for mt, nss, interp in zip(maturities, nss_at_nodes, interp_at_nodes)
        ]
        st.dataframe(diff_rows, use_container_width=True)

        st.subheader("Same instruments, different model: risk panel")
        one_year_roll = 1.0
        ten_to_nine_nss = float(np.interp(9.0, dense_maturities, dense_nss))
        ten_to_nine_interp = float(np.interp(9.0, dense_maturities, dense_interp))
        rolldown_nss_bp = (nss_at_nodes[-1] - ten_to_nine_nss) * 100.0 / one_year_roll
        rolldown_interp_bp = (interp_at_nodes[-1] - ten_to_nine_interp) * 100.0 / one_year_roll
        r1, r2 = st.columns(2)
        r1.metric("10Y→9Y roll-down (NSS, bp/yr)", f"{rolldown_nss_bp:.1f}")
        r2.metric("10Y→9Y roll-down (interp, bp/yr)", f"{rolldown_interp_bp:.1f}")
        st.caption("Interpretation: same market instruments, but model choice shifts derived carry/roll and hedge diagnostics.")

        st.subheader("Shadow-rate / lower-bound intuition (pedagogical simplification)")
        lb_rate = st.number_input("Effective lower bound (%)", value=0.00, step=0.05, key="ch6_lb")
        shadow_shift = st.number_input("Shadow-rate offset (%)", value=0.40, step=0.05, key="ch6_shadow_shift")
        shadow_zero = np.maximum(zero_rates, lb_rate) + shadow_shift
        st.caption("Pedagogical simplification: this panel uses a simple shifted-floor mapping, not a structural shadow-rate term-structure model.")
        st.line_chart(
            {
                "Observed zero": zero_rates,
                "Simplified shadow zero": shadow_zero,
            }
        )

        st.subheader("Residual diagnostics between fits")
        d1, d2, d3 = st.columns(3)
        d1.metric("NSS RMSE (bp)", f"{diagnostics.rmse_nss_bp:.3f}")
        d2.metric("Interp RMSE (bp)", f"{diagnostics.rmse_interp_bp:.3f}")
        d3.metric("RMSE gap (bp)", f"{diagnostics.rmse_nss_bp - diagnostics.rmse_interp_bp:.3f}")

        return YieldCurveModelState(
            par_curve=[CurvePoint(maturity_years=float(mt), rate_pct=float(rt)) for mt, rt in zip(maturities, par_rates)],
            zero_curve=[CurvePoint(maturity_years=float(mt), rate_pct=float(rt)) for mt, rt in zip(maturities, zero_rates)],
            forward_curve=[CurvePoint(maturity_years=float(mt), rate_pct=float(rt)) for mt, rt in zip(maturities, forward_rates)],
            fit_params={
                "beta0": float(nss_params.beta0),
                "beta1": float(nss_params.beta1),
                "beta2": float(nss_params.beta2),
                "beta3": float(nss_params.beta3),
                "tau1": float(nss_params.tau1),
                "tau2": float(nss_params.tau2),
            },
            interpolation_settings={
                "method": "piecewise_linear",
                "grid_density": float(interp_grid_density),
                "lower_bound_pct": float(lb_rate),
                "shadow_shift_pct": float(shadow_shift),
            },
            residual_diagnostics=ResidualDiagnosticsState(
                rmse_nss_bp=diagnostics.rmse_nss_bp,
                rmse_interp_bp=diagnostics.rmse_interp_bp,
                mean_abs_nss_bp=diagnostics.mean_abs_nss_bp,
                mean_abs_interp_bp=diagnostics.mean_abs_interp_bp,
                max_abs_nss_bp=diagnostics.max_abs_nss_bp,
                max_abs_interp_bp=diagnostics.max_abs_interp_bp,
            ),
        )

    def case_studies(self) -> list[dict[str, str]]:
        return [
            {
                "name": "Curve-strategy disagreement",
                "setup": "Two desks use NSS vs. piecewise-linear representations on the same par instruments.",
                "takeaway": "Carry/roll and hedge metrics diverge despite identical observed market quotes.",
            }
        ]

    def failure_modes(self) -> list[dict[str, str]]:
        return [
            {
                "mode": "Treating pedagogical bootstrap as production curve construction",
                "mitigation": "Use full instrument conventions (day-count, frequency, accrual, collateral) in production pricers.",
            }
        ]

    def assessment(self) -> list[dict[str, str]]:
        return [
            {
                "prompt": "Why can model choice alter risk even with unchanged market quotes?",
                "expected": "Derived zero/forward geometry changes hedges, carry/roll, and scenario sensitivities.",
            }
        ]

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            signals=["par_curve", "zero_curve", "forward_curve", "fit_params", "interpolation_settings", "residual_diagnostics"],
            usage="Provides curve-state and diagnostics for governance/risk discussions in Chapter 7.",
            schema_name="YieldCurveModelState",
        )
