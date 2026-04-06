from __future__ import annotations

import streamlit as st

from .base import SimpleChapter


def _spread_bp(lhs: float, rhs: float) -> float:
    return (lhs - rhs) * 100.0


class Chapter12(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(chapter_id="12", title="Chapter 12: Asset-swap decomposition", objective="Split bond carry into curve, credit, and package-adjusted asset-swap spread.")

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Asset-swap spread", "equation": "ass_bp=z_spread_bp-(bond_coupon-swap_rate)*100"},
            {"name": "Package carry", "equation": "carry_bp=ass_bp-repo_haircut_bp"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Measure bond z-spread and swap par coupon on matched maturity.",
            "Convert bond coupon mismatch into bp adjustment.",
            "Subtract financing drag to isolate executable package carry.",
        ]

    def interactive_lab(self) -> dict[str, dict[str, float]]:
        z_spread = st.number_input("Bond z-spread (bp)", value=92.0, step=1.0, key="z_12")
        bond_coupon = st.number_input("Bond coupon (%)", value=4.15, step=0.01, key="coupon_12")
        swap_rate = st.number_input("Par swap rate (%)", value=3.88, step=0.01, key="swap_12")
        repo_haircut_bp = st.number_input("Repo / funding drag (bp)", value=14.0, step=1.0, key="repo_12")

        coupon_mismatch_bp = _spread_bp(bond_coupon, swap_rate)
        asset_swap_spread_bp = z_spread - coupon_mismatch_bp
        package_carry_bp = asset_swap_spread_bp - repo_haircut_bp

        st.metric("Coupon mismatch (bp)", f"{coupon_mismatch_bp:.2f}")
        st.metric("Asset-swap spread (bp)", f"{asset_swap_spread_bp:.2f}")
        st.metric("Package carry after funding (bp)", f"{package_carry_bp:.2f}")

        return {"inputs": {"z_spread_bp": z_spread, "bond_coupon_pct": bond_coupon, "swap_rate_pct": swap_rate, "repo_drag_bp": repo_haircut_bp}, "outputs": {"coupon_mismatch_bp": coupon_mismatch_bp, "asset_swap_spread_bp": asset_swap_spread_bp, "package_carry_bp": package_carry_bp}}

    def exports_to_next_chapter(self) -> dict[str, object]:
        return {"schema_name": "AssetSwapState", "signals": ["asset_swap_spread_bp", "package_carry_bp", "coupon_mismatch_bp"], "usage": "Provides clean package spread inputs to pure-credit extraction."}
