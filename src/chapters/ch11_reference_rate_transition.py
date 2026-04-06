from __future__ import annotations

import streamlit as st

from core.types import ChapterExportState, ReferenceRateState
from src.models.reference_rates import (
    all_in_coupon_pct,
    benchmark_spread_decomposition_bp,
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
            "title": "Chapter 11: Reference rates, benchmark wedges, and transition",
            "objective": "Decompose benchmark choice into secured/unsecured structure, repo wedge, and transition overlays so valuation changes are attributed correctly.",
        }

    def key_takeaway(self) -> str:
        return "Benchmark choice is a valuation input: if your benchmark, collateral, and repo anchors mismatch, your spread signal is contaminated before trading begins."

    def learn_focus(self) -> list[str]:
        return [
            "A bond can look rich/cheap purely because you changed the benchmark family (secured vs unsecured), not because fundamentals moved.",
            "Repo vs reference-rate wedges separate financing pressure from benchmark-level economics.",
            "Fallback transition mechanics matter, but only as one contractual overlay on a broader benchmark decomposition.",
        ]

    def derive_focus(self) -> list[str]:
        return [
            "Start from two benchmark curves and compute tenor-by-tenor spreads.",
            "Split the spread into secured/unsecured structure and repo wedge.",
            "Only then layer contract fallback to estimate coupon resets for legacy references.",
        ]

    def trade_use_focus(self) -> list[str]:
        return [
            "Use curve comparison to avoid false RV calls caused by benchmark mismatch.",
            "Use repo wedge to identify trades that are funding-sensitive versus truly benchmark-mispriced.",
            "Carry fallback terms into asset-swap packaging so coupon expectations are realistic.",
        ]

    def prerequisites(self) -> list[str]:
        return ["Chapter 10 dependency map", "Money-market benchmark conventions", "Repo funding interpretation"]

    def concept_map(self) -> dict[str, list[str]]:
        return {
            "nodes": [
                "Secured benchmark curve",
                "Unsecured benchmark curve",
                "Repo curve",
                "Benchmark spread decomposition",
                "Fallback transition overlay",
                "Valuation impact",
            ],
            "edges": [
                "Secured benchmark curve->Benchmark spread decomposition",
                "Unsecured benchmark curve->Benchmark spread decomposition",
                "Repo curve->Benchmark spread decomposition",
                "Benchmark spread decomposition->Valuation impact",
                "Fallback transition overlay->Valuation impact",
            ],
        }

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Curve spread", "equation": "curve_spread_bp=(curve_a-curve_b)*100"},
            {"name": "Secured-unsecured basis", "equation": "secured_unsecured_basis_bp=(unsecured-secured)*100"},
            {"name": "Repo-reference wedge", "equation": "repo_reference_basis_bp=(repo-reference)*100"},
            {
                "name": "Benchmark decomposition",
                "equation": "benchmark_spread_bp = secured_unsecured_basis_bp + repo_reference_basis_bp + transition_overlay_bp",
            },
            {"name": "Fallback spread", "equation": "fallback_spread_bp=(legacy_fixing-compounded_rfr)*100"},
            {"name": "All-in coupon", "equation": "all_in_coupon_pct=compounded_rfr+contract_adjustment_bp/100"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Observe two benchmark curves (e.g., secured RFR curve and unsecured term curve) and compute tenor-level spreads.",
            "Estimate secured-vs-unsecured structural premium and repo-vs-reference financing wedge.",
            "Combine these terms into a benchmark spread decomposition that maps to valuation basis points.",
            "Add transition overlay through fallback spread and contract adjustment where legacy documentation applies.",
            "Use the final decomposition to distinguish true RV signals from benchmark-convention artifacts.",
        ]

    def interactive_lab(self) -> ReferenceRateState:
        st.subheader("1) Benchmark curve comparison")
        c1, c2 = st.columns(2)
        curve_a_name = c1.selectbox("Curve A (typically secured)", options=["SOFR", "ESTR", "SONIA", "TONA"], index=0, key="curve_a_name_11")
        curve_b_name = c2.selectbox("Curve B (typically unsecured/term)", options=["LIBOR legacy", "Bank CP", "EFFR", "SOFR"], index=0, key="curve_b_name_11")

        tenor_labels = ["1M", "3M", "6M", "12M"]
        curve_a_inputs: dict[str, float] = {}
        curve_b_inputs: dict[str, float] = {}

        left, right = st.columns(2)
        for tenor in tenor_labels:
            curve_a_inputs[tenor] = left.number_input(f"{curve_a_name} {tenor} (%)", value=4.55 + (0.04 * tenor_labels.index(tenor)), step=0.01, key=f"curve_a_{tenor}_11")
            curve_b_inputs[tenor] = right.number_input(f"{curve_b_name} {tenor} (%)", value=4.75 + (0.03 * tenor_labels.index(tenor)), step=0.01, key=f"curve_b_{tenor}_11")

        chart_rows = {
            curve_a_name: [curve_a_inputs[t] for t in tenor_labels],
            curve_b_name: [curve_b_inputs[t] for t in tenor_labels],
        }
        st.line_chart(chart_rows)

        selected_tenor = st.selectbox("Headline tenor", options=tenor_labels, index=1, key="headline_tenor_11")
        benchmark_rate_a = curve_a_inputs[selected_tenor]
        benchmark_rate_b = curve_b_inputs[selected_tenor]
        benchmark_curve_spread = curve_spread_bp(benchmark_rate_a, benchmark_rate_b)
        term_spreads = spread_term_structure_bp(curve_a_inputs, curve_b_inputs)

        st.metric(f"{curve_a_name} - {curve_b_name} spread at {selected_tenor} (bp)", f"{benchmark_curve_spread:.2f}")

        st.subheader("2) Secured/unsecured and repo wedge")
        b1, b2, b3 = st.columns(3)
        secured_rate = b1.number_input("Secured reference (%)", value=4.62, step=0.01, key="secured_11")
        unsecured_rate = b2.number_input("Unsecured reference (%)", value=4.86, step=0.01, key="unsecured_11")
        repo_rate = b3.number_input("Repo funding rate (%)", value=4.54, step=0.01, key="repo_11")
        reference_rate = st.number_input("Chosen valuation benchmark (%)", value=benchmark_rate_a, step=0.01, key="reference_11")

        su_basis = secured_unsecured_basis_bp(secured_rate, unsecured_rate)
        repo_wedge = repo_reference_basis_bp(repo_rate, reference_rate)

        st.metric("Secured-unsecured basis (bp)", f"{su_basis:.2f}")
        st.metric("Repo-reference wedge (bp)", f"{repo_wedge:.2f}")

        st.subheader("3) Transition overlay (subsection)")
        legacy_fixing = st.number_input("Legacy tenor fixing (%)", value=5.02, step=0.01, key="legacy_11")
        compounded_rfr = st.number_input("Compounded RFR (%)", value=4.71, step=0.01, key="rfr_11")
        contract_adjustment = st.number_input("Contract fallback adjustment (bp)", value=26.0, step=1.0, key="adj_11")

        transition_overlay = fallback_spread_bp(legacy_fixing, compounded_rfr)
        all_in_coupon = all_in_coupon_pct(compounded_rfr, contract_adjustment)

        decomposition = benchmark_spread_decomposition_bp(
            secured_unsecured_bp=su_basis,
            repo_reference_bp=repo_wedge,
            transition_overlay_bp=transition_overlay,
        )

        st.dataframe(
            [{"component": k, "bp": v} for k, v in decomposition.items()],
            use_container_width=True,
        )
        st.metric("All-in reset coupon (%)", f"{all_in_coupon:.3f}")
        st.caption("Benchmark choice changes valuation because discounting, floating coupons, and funding conversion all move with the chosen anchor curve.")

        conventions = st.multiselect(
            "Active conventions",
            options=[
                "Compounded-in-arrears coupons",
                "Lookback without observation shift",
                "Two-day payment delay",
                "ACT/360 day-count",
                "ISDA fallback median adjustment",
            ],
            default=["Compounded-in-arrears coupons", "ISDA fallback median adjustment"],
            key="conventions_11",
        )

        return ReferenceRateState(
            benchmark_curve_a=curve_a_name,
            benchmark_curve_b=curve_b_name,
            benchmark_rate_a_pct=benchmark_rate_a,
            benchmark_rate_b_pct=benchmark_rate_b,
            benchmark_curve_spread_bp=benchmark_curve_spread,
            spread_term_structure_bp=term_spreads,
            secured_rate_pct=secured_rate,
            unsecured_rate_pct=unsecured_rate,
            secured_unsecured_basis_bp=su_basis,
            repo_rate_pct=repo_rate,
            reference_rate_pct=reference_rate,
            repo_reference_basis_bp=repo_wedge,
            benchmark_spread_decomposition_bp=decomposition,
            legacy_fixing_pct=legacy_fixing,
            compounded_rfr_pct=compounded_rfr,
            fallback_spread_bp=transition_overlay,
            contract_adjustment_bp=contract_adjustment,
            all_in_coupon_pct=all_in_coupon,
            conventions_notes=conventions,
        )

    def case_studies(self) -> list[dict[str, str]]:
        return [
            {
                "name": "False richness from benchmark switch",
                "setup": "Desk switched from unsecured term benchmark to secured RFR discounting without re-basing historical screens.",
                "takeaway": "Apparent cheapness can disappear after benchmark decomposition; trade sizing should use harmonized anchors.",
            },
            {
                "name": "Repo shock with stable benchmark curve",
                "setup": "Reference curve barely moves but repo tightens into quarter-end balance-sheet stress.",
                "takeaway": "Wider repo wedge can impair carry despite stable benchmark spreads.",
            },
        ]

    def failure_modes(self) -> list[dict[str, str]]:
        return [
            {"mode": "Treating secured/unsecured spread as pure credit", "mitigation": "Separate structural money-market premium from issuer-specific credit assumptions."},
            {"mode": "Using repo from one collateral regime with benchmark from another", "mitigation": "Align collateral currency, day count, and fixing windows before comparing wedges."},
            {"mode": "Overweighting fallback mechanics", "mitigation": "Model fallback as a subsection after core benchmark decomposition is complete."},
        ]

    def assessment(self) -> list[dict[str, str]]:
        return [
            {
                "prompt": "Why can valuation move when cash rates barely change?",
                "expected": "Because benchmark selection and repo wedge can shift discounting and funding assumptions even with stable outright levels.",
            },
            {
                "prompt": "Where does fallback analysis belong in this chapter?",
                "expected": "As a contractual overlay after secured/unsecured and repo decomposition, not as the main driver.",
            },
        ]

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            signals=[
                "benchmark_curve_spread_bp",
                "spread_term_structure_bp",
                "secured_unsecured_basis_bp",
                "repo_reference_basis_bp",
                "benchmark_spread_decomposition_bp",
                "fallback_spread_bp",
                "all_in_coupon_pct",
            ],
            usage="Feeds Chapter 12 with benchmark decomposition inputs, repo wedge diagnostics, and fallback-adjusted coupon assumptions.",
            schema_name="ReferenceRateState",
        )
