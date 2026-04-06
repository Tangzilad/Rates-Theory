from __future__ import annotations

import streamlit as st

from src.models.asset_swaps import decompose_asset_swap

from .base import SimpleChapter


class Chapter12(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(chapter_id="12", title="Chapter 12: Asset-swap decomposition", objective="Split bond carry into curve, credit, and package-adjusted asset-swap spread.")

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Coupon mismatch", "equation": "coupon_mismatch_bp=(bond_coupon_pct-benchmark_rate_pct)*100"},
            {"name": "Asset-swap spread", "equation": "asw_bp=z_spread_bp-coupon_mismatch_bp"},
            {"name": "Package carry", "equation": "carry_bp=asw_bp-(repo_funding_rate_pct-benchmark_rate_pct)*100"},
            {"name": "Fair package level (simplified)", "equation": "fair_package_bp=asw_bp-package_upfront_pct*100"},
            {"name": "Funding sensitivity", "equation": "d(carry_bp)/d(funding_bp)=-1"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Select a reference benchmark (par swap or floating reference rate) to define coupon mismatch.",
            "Compute package anatomy explicitly: coupon mismatch, ASW spread, and funding-adjusted carry.",
            "Account for par vs non-par package upfront as a simplified fair-level adjustment.",
            "Stress funding by +1bp shocks using linear sensitivity (no full CSA-consistent repricing).",
        ]

    def interactive_lab(self) -> dict[str, dict[str, float]]:
        z_spread = st.number_input("Bond z-spread (bp)", value=92.0, step=1.0, key="z_12")
        bond_coupon = st.number_input("Bond coupon (%)", value=4.15, step=0.01, key="coupon_12")
        benchmark_type = st.radio("Benchmark mode", options=["Par swap", "Reference rate"], horizontal=True, key="bench_type_12")
        benchmark_rate = st.number_input(f"{benchmark_type} level (%)", value=3.88, step=0.01, key="bench_12")
        repo_funding_rate = st.number_input("Repo / funding rate (%)", value=4.02, step=0.01, key="repo_12")
        package_type = st.radio("Package structure", options=["Par package", "Non-par package"], horizontal=True, key="package_type_12")
        package_upfront = st.number_input("Upfront price (% of notional, + premium / - discount)", value=0.00, step=0.01, key="upfront_12")
        funding_shift = st.slider("Funding stress shift (bp)", min_value=-30, max_value=30, value=0, step=1, key="fund_shift_12")

        state = decompose_asset_swap(
            z_spread_bp=z_spread,
            bond_coupon_pct=bond_coupon,
            benchmark_rate_pct=benchmark_rate,
            repo_funding_rate_pct=repo_funding_rate,
            package_upfront_pct=package_upfront if package_type == "Non-par package" else 0.0,
            funding_shift_bp=float(funding_shift),
            reference_rate_name=benchmark_type,
            benchmark_type="par" if package_type == "Par package" else "non_par",
        )

        st.subheader("Package anatomy")
        col1, col2, col3 = st.columns(3)
        col1.metric("Coupon mismatch (bp)", f"{state.coupon_mismatch_bp:.2f}")
        col2.metric("Asset-swap spread (bp)", f"{state.asset_swap_spread_bp:.2f}")
        col3.metric("Package carry (bp)", f"{state.package_carry_bp:.2f}")
        st.metric("Fair package level (bp, simplified)", f"{state.fair_package_level_bp:.2f}")
        st.caption(f"Funding sensitivity: {state.funding_sensitivity_bp_per_1bp:.2f} bp carry per +1bp funding move.")

        with st.expander("Simplification disclaimer", expanded=True):
            for note in state.simplification_notes:
                st.write(f"- {note}")

        return {
            "inputs": {
                "z_spread_bp": z_spread,
                "bond_coupon_pct": bond_coupon,
                "benchmark_rate_pct": benchmark_rate,
                "reference_rate_name": benchmark_type,
                "package_upfront_pct": package_upfront if package_type == "Non-par package" else 0.0,
                "repo_funding_rate_pct": repo_funding_rate,
                "funding_shift_bp": float(funding_shift),
                "benchmark_type": "par" if package_type == "Par package" else "non_par",
            },
            "outputs": state.model_dump(),
        }

    def exports_to_next_chapter(self) -> dict[str, object]:
        return {"schema_name": "AssetSwapState", "signals": ["asset_swap_spread_bp", "package_carry_bp", "coupon_mismatch_bp", "fair_package_level_bp", "funding_sensitivity_bp_per_1bp"], "usage": "Provides explicit package anatomy with benchmark and funding assumptions for pure-credit extraction."}
