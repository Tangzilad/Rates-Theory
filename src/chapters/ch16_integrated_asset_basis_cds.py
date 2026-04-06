from __future__ import annotations

import streamlit as st

from core.types import ChapterExportState, IntegratedRVState
from src.models.integrated_rv import integrated_rv_state

from .base import SimpleChapter


class Chapter16(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(
            chapter_id="16",
            title="Chapter 16: Integrated asset-basis and CDS",
            objective="Jointly map bond, asset-swap, basis, and CDS signals into a common frame and inspect shock propagation before final hedge sizing.",
        )

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {
                "name": "Common-space normalization",
                "equation": "normalized_signal_i_bp=transformed_signal_i_bp-sofr_anchor_bp",
            },
            {
                "name": "Agreement ratio",
                "equation": "agreement_ratio=(count of signals with same sign as mean signal)/(total signals)",
            },
            {
                "name": "Shock propagation",
                "equation": "shocked_signal_j=baseline_signal_j+shock_bp*beta(shocked_input,j)",
            },
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Start from bond local-space RV and transform into asset-swap, basis, and CDS pure-credit spaces.",
            "Normalize all transformed signals to a USD SOFR-relative pedagogical frame for apples-to-apples comparison.",
            "Diagnose agreement/divergence across normalized signals before translating into chapter 17 risk inputs.",
            "Shock one dependency node and propagate the impact through Chapter 10 directed graph semantics.",
        ]

    @staticmethod
    def _render_dependency_trace_panel() -> None:
        st.markdown("#### Dependency trace panel (Chapter 10 semantics)")
        st.caption("Directed links reuse the Chapter 10 dependency-map logic: source node shocks flow forward to downstream pricing spaces.")

        edges = [
            "Bond → Asset swap (cash leg into swap package)",
            "Repo/Funding anchor → Asset swap (financing adjustment)",
            "Reference rate → Intra-currency basis (tenor anchor)",
            "Intra-currency basis → Cross-currency basis (tenor conversion)",
            "Cross-currency basis → Asset swap (FX-hedged funding overlay)",
            "Asset swap ↔ CDS pure credit (cash-credit reconciliation feedback)",
        ]
        with st.expander("View dependency edges", expanded=True):
            for edge in edges:
                st.markdown(f"- {edge}")

    def interactive_lab(self) -> IntegratedRVState:
        col1, col2 = st.columns(2)
        with col1:
            bond_local = st.number_input("Bond local-space signal (bp)", value=24.0, step=1.0, key="bond_local_16")
            asset_swap_signal = st.number_input("Asset-swap transformed signal (bp)", value=18.0, step=1.0, key="asw_signal_16")
            intra_basis_signal = st.number_input("Intra-currency basis transformed signal (bp)", value=12.0, step=1.0, key="basis_intra_16")
        with col2:
            cross_basis_signal = st.number_input("Cross-currency basis transformed signal (bp)", value=15.0, step=1.0, key="basis_cross_16")
            cds_pure_credit_signal = st.number_input("CDS pure-credit signal (bp)", value=20.0, step=1.0, key="cds_credit_16")
            sofr_anchor = st.number_input("SOFR anchor for common-space normalization (bp)", value=8.0, step=0.5, key="sofr_anchor_16")

        self._render_dependency_trace_panel()

        st.markdown("#### Shock one input, propagate to others")
        shocked_input = st.selectbox(
            "Shock source node",
            options=["bond", "asset_swap", "basis_intra", "basis_cross", "cds_pure_credit"],
            index=0,
            key="shock_src_16",
        )
        shock_bp = st.slider("Shock size (bp)", min_value=-75.0, max_value=75.0, value=10.0, step=1.0, key="shock_bp_16")
        divergence_threshold = st.slider(
            "Divergence alert threshold (bp)", min_value=2.0, max_value=50.0, value=12.5, step=0.5, key="div_thresh_16"
        )

        state = integrated_rv_state(
            bond_local_space_signal_bp=bond_local,
            asset_swap_transformed_signal_bp=asset_swap_signal,
            intra_basis_transformed_signal_bp=intra_basis_signal,
            cross_currency_basis_transformed_signal_bp=cross_basis_signal,
            cds_pure_credit_signal_bp=cds_pure_credit_signal,
            sofr_anchor_bp=sofr_anchor,
            shocked_input=shocked_input,
            shock_bp=shock_bp,
            divergence_threshold_bp=divergence_threshold,
        )

        diag = state.agreement_divergence_diagnostics
        st.metric("Agreement ratio", f"{diag.agreement_ratio:.2%}")
        st.metric("Max deviation from mean (bp)", f"{diag.max_deviation_bp:.2f}")
        st.metric("Divergence flag", "ON" if diag.divergence_flag else "OFF")

        return state

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            schema_name="IntegratedRVState",
            signals=[
                "common_space_normalization.normalized_signals_bp",
                "agreement_divergence_diagnostics",
                "shock_propagation_results",
            ],
            usage="Passes normalized multi-leg signals and propagated-shock diagnostics into chapter 17 global RV stress ranking.",
        )
