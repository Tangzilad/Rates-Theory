from __future__ import annotations

import streamlit as st

from core.types import ChapterExportState, ReferenceRateState
from src.models.reference_rates import (
    all_in_coupon_pct,
    curve_spread_bp,
    fallback_spread_bp,
    repo_reference_basis_bp,
    secured_unsecured_basis_bp,
    spread_term_structure_bp,
)

from .base import ChapterBase


class Chapter11(ChapterBase):
    chapter_id = "11"

    def chapter_meta(self) -> dict[str, str]:
        return {
            "chapter": self.chapter_id,
            "title": "Chapter 11: Reference-rate transition",
            "objective": "Compare benchmark curves, quantify secured-vs-unsecured and repo wedges, then embed fallback economics as a contract subsection.",
        }

    def prerequisites(self) -> list[str]:
        return ["Chapter 10 funding basis outputs", "Benchmark transition conventions", "Repo and money-market quoting basics"]

    def concept_map(self) -> dict[str, list[str]]:
        return {
            "nodes": ["Benchmark curves", "Tenor spread structure", "Secured/unsecured basis", "Repo-reference wedge", "Fallback transition"],
            "edges": [
                "Benchmark curves->Tenor spread structure",
                "Tenor spread structure->Secured/unsecured basis",
                "Secured/unsecured basis->Repo-reference wedge",
                "Repo-reference wedge->Fallback transition",
            ],
        }

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Benchmark curve spread", "equation": "curve_spread_bp=(curve_a-curve_b)*100"},
            {"name": "Secured-unsecured basis", "equation": "secured_unsecured_bp=(unsecured-secured)*100"},
            {"name": "Repo-reference basis", "equation": "repo_reference_bp=(repo_rate-reference_rate)*100"},
            {"name": "Fallback spread", "equation": "fallback_bp=(legacy_fixing-compounded_rfr)*100"},
            {"name": "All-in coupon", "equation": "all_in_coupon_pct=compounded_rfr+fallback_adj_bp/100"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Build two benchmark curves and compute level/tenor spreads to anchor transition economics.",
            "Separate structural liquidity premium via secured-versus-unsecured basis diagnostics.",
            "Measure repo wedge versus the benchmark reference to map financing drag.",
            "Preserve fallback math as a contract subsection for legacy-fallback coupon estimation.",
        ]

    def interactive_lab(self) -> ReferenceRateState:
        st.subheader("Benchmark curves panel")
        c1, c2 = st.columns(2)
        curve_a_name = c1.selectbox("Curve A", options=["SOFR", "EFFR", "ESTR", "SONIA"], index=0, key="curve_a_name_11")
        curve_b_name = c2.selectbox("Curve B", options=["SOFR", "EFFR", "ESTR", "SONIA"], index=1, key="curve_b_name_11")

        tenor_labels = ["1M", "3M", "6M", "12M"]
        curve_a_inputs: dict[str, float] = {}
        curve_b_inputs: dict[str, float] = {}

        t1, t2 = st.columns(2)
        for tenor in tenor_labels:
            curve_a_inputs[tenor] = t1.number_input(f"{curve_a_name} {tenor} (%)", value=4.80 + (0.03 * tenor_labels.index(tenor)), step=0.01, key=f"curve_a_{tenor}_11")
            curve_b_inputs[tenor] = t2.number_input(f"{curve_b_name} {tenor} (%)", value=4.70 + (0.03 * tenor_labels.index(tenor)), step=0.01, key=f"curve_b_{tenor}_11")

        selected_tenor = st.selectbox("Headline tenor for curve comparison", options=tenor_labels, index=1, key="headline_tenor_11")
        benchmark_rate_a = curve_a_inputs[selected_tenor]
        benchmark_rate_b = curve_b_inputs[selected_tenor]
        benchmark_curve_spread = curve_spread_bp(benchmark_rate_a, benchmark_rate_b)
        term_spreads = spread_term_structure_bp(curve_a_inputs, curve_b_inputs)

        st.metric(f"{curve_a_name}-{curve_b_name} spread at {selected_tenor} (bp)", f"{benchmark_curve_spread:.2f}")

        st.subheader("Spread term structure panel")
        st.dataframe(
            [{"tenor": tenor, "curve_a_pct": curve_a_inputs[tenor], "curve_b_pct": curve_b_inputs[tenor], "spread_bp": term_spreads[tenor]} for tenor in tenor_labels],
            use_container_width=True,
        )

        st.subheader("Secured / unsecured basis and repo-reference wedge")
        b1, b2, b3 = st.columns(3)
        secured_rate = b1.number_input("Secured funding rate (%)", value=4.74, step=0.01, key="secured_11")
        unsecured_rate = b2.number_input("Unsecured funding rate (%)", value=4.92, step=0.01, key="unsecured_11")
        repo_rate = b3.number_input("Repo rate (%)", value=4.68, step=0.01, key="repo_11")
        reference_rate = st.number_input("Chosen reference benchmark (%)", value=benchmark_rate_a, step=0.01, key="reference_11")

        secured_unsecured_basis = secured_unsecured_basis_bp(secured_rate, unsecured_rate)
        repo_reference_basis = repo_reference_basis_bp(repo_rate, reference_rate)
        st.metric("Secured-unsecured basis (bp)", f"{secured_unsecured_basis:.2f}")
        st.metric("Repo-reference basis (bp)", f"{repo_reference_basis:.2f}")

        st.subheader("Conventions notes panel")
        conventions = st.multiselect(
            "Select active market conventions",
            options=[
                "Compounded in arrears for RFR coupons",
                "Lookback without observation shift",
                "Two-day payment delay",
                "ACT/360 day-count for money-market legs",
                "Fallback spread fixed at ISDA historical median",
            ],
            default=["Compounded in arrears for RFR coupons", "Fallback spread fixed at ISDA historical median"],
            key="conventions_11",
        )
        if conventions:
            st.caption("Conventions guide curve alignment, fixing windows, and coupon comparability across legacy and RFR-linked contracts.")

        st.subheader("Fallback transition subsection")
        legacy_fixing = st.number_input("Legacy tenor fixing (%)", value=5.02, step=0.01, key="legacy_11")
        compounded_rfr = st.number_input("Compounded RFR (%)", value=4.71, step=0.01, key="rfr_11")
        contract_adjustment = st.number_input("Contract spread adjustment (bp)", value=26.0, step=1.0, key="adj_11")
        fallback_spread = fallback_spread_bp(legacy_fixing, compounded_rfr)
        all_in_coupon = all_in_coupon_pct(compounded_rfr, contract_adjustment)
        st.metric("Fallback spread (bp)", f"{fallback_spread:.2f}")
        st.metric("All-in reset coupon (%)", f"{all_in_coupon:.3f}")

        return ReferenceRateState(
            benchmark_curve_a=curve_a_name,
            benchmark_curve_b=curve_b_name,
            benchmark_rate_a_pct=benchmark_rate_a,
            benchmark_rate_b_pct=benchmark_rate_b,
            benchmark_curve_spread_bp=benchmark_curve_spread,
            spread_term_structure_bp=term_spreads,
            secured_rate_pct=secured_rate,
            unsecured_rate_pct=unsecured_rate,
            secured_unsecured_basis_bp=secured_unsecured_basis,
            repo_rate_pct=repo_rate,
            reference_rate_pct=reference_rate,
            repo_reference_basis_bp=repo_reference_basis,
            legacy_fixing_pct=legacy_fixing,
            compounded_rfr_pct=compounded_rfr,
            fallback_spread_bp=fallback_spread,
            contract_adjustment_bp=contract_adjustment,
            all_in_coupon_pct=all_in_coupon,
            conventions_notes=conventions,
        )

    def case_studies(self) -> list[dict[str, str]]:
        return [
            {
                "name": "RFR transition repricing",
                "setup": "Legacy floating notes roll into compounded RFR conventions with fixed fallback spreads.",
                "takeaway": "Curve and basis decomposition avoids attributing financing wedges to pure credit mispricing.",
            }
        ]

    def failure_modes(self) -> list[dict[str, str]]:
        return [
            {
                "mode": "Mixing day-count and observation conventions across curves",
                "mitigation": "Force explicit conventions metadata and re-run basis calculations under harmonized assumptions.",
            }
        ]

    def assessment(self) -> list[dict[str, str]]:
        return [
            {
                "prompt": "Why keep fallback analysis as a subsection rather than the chapter core?",
                "expected": "Fallback is one contractual overlay; chapter core is broader benchmark and funding-basis transition diagnostics.",
            }
        ]

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            signals=[
                "benchmark_curve_spread_bp",
                "spread_term_structure_bp",
                "secured_unsecured_basis_bp",
                "repo_reference_basis_bp",
                "fallback_spread_bp",
                "all_in_coupon_pct",
            ],
            usage="Feeds Chapter 12 asset-swap decomposition with benchmark transition, financing wedge, and fallback coupon assumptions.",
            schema_name="ReferenceRateState",
        )
