from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from core.equations import curve_slope_bp, duration_convexity_price_change
from core.types import ChapterExportState, RiskMetricState
from src.models.risk_measures import convexity, dv01, macaulay_duration, modified_duration, present_value

from .base import ChapterBase


class Chapter05(ChapterBase):
    chapter_id = "5"

    def chapter_meta(self) -> dict[str, str]:
        return {"chapter": self.chapter_id, "title": "Chapter 5: Duration and convexity diagnostics", "objective": "Translate curve shocks into price response."}

    def prerequisites(self) -> list[str]:
        return ["Yield curve points", "Duration and convexity definitions"]

    def concept_map(self) -> dict[str, list[str]]:
        return {"nodes": ["Curve slope", "Duration", "Convexity", "Shock", "Fair price"], "edges": ["Shock+Greeks->Price change", "Price change->Fair price"]}

    def equation_set(self) -> list[dict[str, str]]:
        return [{"name": "Price approximation", "equation": "dP/P≈-D*dy+0.5*C*dy^2"}]

    def derivation_steps(self) -> list[str]:
        return ["Choose dy shock in bp.", "Convert bp to decimal.", "Apply duration-convexity approximation."]

    def _cashflow_inputs(self) -> tuple[np.ndarray, np.ndarray, float, int]:
        builder = st.radio("Cash-flow input mode", ["Synthetic coupon bond", "Custom cash-flow schedule"], horizontal=True)

        if builder == "Synthetic coupon bond":
            face = st.number_input("Face value", min_value=1.0, value=100.0, step=1.0)
            coupon_pct = st.number_input("Annual coupon (%)", min_value=0.0, value=4.5, step=0.1)
            maturity_years = st.number_input("Maturity (years)", min_value=0.5, value=5.0, step=0.5)
            freq = st.selectbox("Coupon frequency", options=[1, 2, 4], index=1)

            periods = max(1, int(round(maturity_years * freq)))
            times = np.arange(1, periods + 1, dtype=float) / float(freq)
            coupon_cashflow = face * (coupon_pct / 100.0) / float(freq)
            cashflows = np.full(periods, coupon_cashflow, dtype=float)
            cashflows[-1] += face
            return cashflows, times, face, int(freq)

        default_times = "0.5,1.0,1.5,2.0,2.5,3.0"
        default_cashflows = "2.0,2.0,2.0,2.0,2.0,102.0"
        times_raw = st.text_input("Times in years (comma-separated)", value=default_times)
        cashflows_raw = st.text_input("Cash flows (comma-separated)", value=default_cashflows)
        freq = st.selectbox("Compounding frequency", options=[1, 2, 4], index=1)

        times = np.array([float(x.strip()) for x in times_raw.split(",") if x.strip()], dtype=float)
        cashflows = np.array([float(x.strip()) for x in cashflows_raw.split(",") if x.strip()], dtype=float)
        if times.size != cashflows.size or times.size == 0:
            raise ValueError("Custom schedule must have the same non-zero number of times and cash flows.")

        notional_guess = float(np.max(cashflows))
        return cashflows, times, notional_guess, int(freq)

    def interactive_lab(self) -> RiskMetricState:
        y2 = st.number_input("2Y yield (%)", value=3.70, step=0.01)
        y10 = st.number_input("10Y yield (%)", value=4.10, step=0.01)
        ytm_pct = st.number_input("Flat valuation yield (%)", value=4.00, step=0.01)

        try:
            cashflows, times, notional, freq = self._cashflow_inputs()
        except ValueError as exc:
            st.error(str(exc))
            return RiskMetricState()

        ytm = ytm_pct / 100.0
        pv = present_value(cashflows, times, ytm, freq)
        d_mac = macaulay_duration(cashflows, times, ytm, freq)
        d_mod = modified_duration(cashflows, times, ytm, freq)
        dv01_value = dv01(cashflows, times, ytm, freq)
        conv = convexity(cashflows, times, ytm, freq)
        slope = curve_slope_bp(y2, y10)

        discount_factors = (1.0 + ytm / float(freq)) ** (-float(freq) * times)
        pv_contrib = cashflows * discount_factors
        pv_weights = pv_contrib / pv if pv else np.zeros_like(pv_contrib)

        table = pd.DataFrame(
            {
                "time_years": times,
                "cashflow": cashflows,
                "discount_factor": discount_factors,
                "pv_contribution": pv_contrib,
                "pv_weight": pv_weights,
            }
        )

        st.subheader("Cash-flow valuation table")
        st.dataframe(table.style.format({"time_years": "{:.3f}", "cashflow": "{:.4f}", "discount_factor": "{:.6f}", "pv_contribution": "{:.6f}", "pv_weight": "{:.6%}"}), use_container_width=True)

        metric_cols = st.columns(3)
        metric_cols[0].metric("PV", f"{pv:.6f}")
        metric_cols[1].metric("Macaulay duration (yrs)", f"{d_mac:.6f}")
        metric_cols[2].metric("Modified duration (yrs)", f"{d_mod:.6f}")
        metric_cols = st.columns(3)
        metric_cols[0].metric("DV01", f"{dv01_value:.6f}")
        metric_cols[1].metric("Convexity", f"{conv:.6f}")
        metric_cols[2].metric("2s10s slope (bp)", f"{slope:.2f}")

        st.subheader("Shock analysis")
        small_shock_bp = st.slider("Small yield shock (bp)", -50, 50, 10, 1)
        large_shock_bp = st.slider("Large yield shock (bp)", -300, 300, 100, 5)

        def analyze_shock(dy_bp: int) -> dict[str, float]:
            approx_dp_pct = duration_convexity_price_change(d_mod, conv, dy_bp)
            approx_price = pv * (1.0 + approx_dp_pct)
            shocked_ytm = ytm + (dy_bp / 10_000.0)
            full_price = present_value(cashflows, times, shocked_ytm, freq)
            error = approx_price - full_price
            return {
                "shock_bp": float(dy_bp),
                "approx_dp_pct": approx_dp_pct,
                "approx_price": approx_price,
                "full_reprice": full_price,
                "approx_error": error,
            }

        small = analyze_shock(small_shock_bp)
        large = analyze_shock(large_shock_bp)
        shock_df = pd.DataFrame([small, large], index=["Small shock", "Large shock"])
        st.dataframe(
            shock_df.style.format(
                {
                    "shock_bp": "{:.0f}",
                    "approx_dp_pct": "{:.4%}",
                    "approx_price": "{:.6f}",
                    "full_reprice": "{:.6f}",
                    "approx_error": "{:.6f}",
                }
            ),
            use_container_width=True,
        )

        fair_price = large["full_reprice"]
        approximation_error = large["approx_error"]

        st.caption(f"Using large shock ({large_shock_bp:+.0f} bp) for exported fair price and approximation error. Notional reference: {notional:.2f}.")

        return RiskMetricState(
            curve_slope_bp=slope,
            slope=slope,
            duration=d_mod,
            macaulay_duration=d_mac,
            modified_duration=d_mod,
            dv01=dv01_value,
            convexity=conv,
            pv=pv,
            dy_bp=large_shock_bp,
            dp_pct=large["approx_dp_pct"],
            fair_price=fair_price,
            fair_price_under_shock=fair_price,
            approximation_error=approximation_error,
        )

    def case_studies(self) -> list[dict[str, str]]:
        return [{"name": "Bull steepener", "setup": "Front-end rallies more than long-end", "takeaway": "Curve slope and duration profile jointly drive PnL."}]

    def failure_modes(self) -> list[dict[str, str]]:
        return [{"mode": "Large shock nonlinearity", "mitigation": "Reprice full cashflows beyond local approximation."}]

    def assessment(self) -> list[dict[str, str]]:
        return [{"prompt": "What term dampens duration losses in big moves?", "expected": "Positive convexity term."}]

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            signals=[
                "pv",
                "macaulay_duration",
                "modified_duration",
                "dv01",
                "convexity",
                "slope",
                "fair_price_under_shock",
                "approximation_error",
            ],
            usage="Compared with market pricing for rich/cheap screens.",
            schema_name="RiskMetricState",
        )
