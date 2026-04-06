from __future__ import annotations

import streamlit as st

from core.types import ChapterExportState
from src.models.cds import compute_cds_state

from .base import SimpleChapter


class Chapter13(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(
            chapter_id="13",
            title="Chapter 13: CDS premium/protection legs and pure-credit extraction",
            objective="Decompose observed CDS into premium-leg and protection-leg intuition, then strip technical contamination to infer a recovery-sensitive pure-credit signal.",
        )

    def key_takeaway(self) -> str:
        return "Observed CDS is not equal to pure default risk; clean interpretation requires stripping liquidity/technical contamination and conditioning on recovery."

    def learn_focus(self) -> list[str]:
        return [
            "Premium leg is a running payment stream that can embed non-default premia.",
            "Protection leg value scales with expected loss (1-recovery), so recovery assumptions are first-order.",
            "Delivery-option style frictions can move quoted spreads without a real default regime shift.",
        ]

    def derive_focus(self) -> list[str]:
        return [
            "Observed spread = purified default spread + liquidity + technical contamination.",
            "Purified spread maps to hazard under flat-hazard pedagogy via spread/(1-recovery).",
            "Recovery sensitivity is nonlinear and grows as recovery approaches 1.",
        ]

    def trade_use_focus(self) -> list[str]:
        return [
            "Use purified spread for cross-instrument comparison (cash bonds, ASW, CDS).",
            "Track recovery sensitivity to avoid false conviction in high-recovery assumptions.",
            "Treat technical contamination as execution risk, not fundamental credit information.",
        ]

    def concept_map(self) -> dict[str, list[str]]:
        return {
            "nodes": [
                "Observed CDS spread",
                "Premium leg",
                "Protection leg",
                "Recovery assumption",
                "Liquidity contamination",
                "Technical contamination",
                "Purified credit spread",
                "Hazard proxy",
            ],
            "edges": [
                "Observed CDS spread->Premium leg",
                "Observed CDS spread->Protection leg",
                "Premium leg->Purified credit spread",
                "Liquidity contamination->Purified credit spread",
                "Technical contamination->Purified credit spread",
                "Protection leg->Hazard proxy",
                "Recovery assumption->Hazard proxy",
                "Purified credit spread->Hazard proxy",
            ],
        }

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {
                "name": "Purified credit spread",
                "equation": "purified_credit_spread_bp = observed_spread_bp - liquidity_component_bp - technical_component_bp",
            },
            {
                "name": "Flat-hazard proxy",
                "equation": "hazard_proxy = purified_credit_spread_bp / (10000*(1-recovery_rate))",
            },
            {
                "name": "Recovery sensitivity",
                "equation": "d_hazard_d_recovery = purified_credit_spread_bp / (10000*(1-recovery_rate)^2)",
            },
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Premium leg: buyer pays periodic coupons until maturity/default, so observed coupon includes default and non-default premia.",
            "Protection leg: seller compensates loss-given-default, tying fair premium to hazard × (1-recovery).",
            "Subtract liquidity and technical contamination from quoted CDS to recover purified default compensation.",
            "Map purified spread to hazard with a flat-hazard approximation conditional on recovery.",
            "Stress recovery assumptions and compare raw vs purified interpretation before trade decisions.",
        ]

    def interactive_lab(self) -> dict[str, dict[str, float]]:
        st.markdown("#### 1) Leg intuition")
        c1, c2 = st.columns(2)
        with c1:
            st.info("**Premium leg**: running coupons can widen on liquidity/positioning stress even with stable expected default.")
        with c2:
            st.info("**Protection leg**: expected payout scales with LGD = (1-recovery), so recovery is not a cosmetic assumption.")

        st.markdown("#### 2) Extraction lab")
        observed_spread = st.number_input("Observed CDS spread (bp)", value=118.0, step=1.0, key="obs_13")
        liquidity_component = st.number_input("Liquidity contamination (bp)", value=21.0, step=1.0, key="liq_13")
        technical_component = st.number_input("Technical contamination (bp)", value=9.0, step=1.0, key="tech_13")
        recovery = st.slider("Recovery rate", min_value=0.05, max_value=0.85, value=0.40, step=0.01, key="rec_13")

        state = compute_cds_state(
            observed_spread_bp=observed_spread,
            liquidity_component_bp=liquidity_component,
            technical_component_bp=technical_component,
            recovery_rate=recovery,
        )

        st.metric("Purified spread (bp)", f"{state.purified_spread_bp:.2f}")
        st.metric("Hazard proxy", f"{state.hazard_proxy:.4%}")
        st.metric("d(hazard)/d(recovery)", f"{state.d_hazard_d_recovery:.6f}")

        st.markdown("#### 3) Recovery-sensitivity panel")
        chart_rows = {
            "recovery_rate": [pt.recovery_rate for pt in state.recovery_sensitivity_scenarios],
            "hazard_proxy": [pt.hazard_proxy for pt in state.recovery_sensitivity_scenarios],
            "d_hazard_d_recovery": [pt.d_hazard_d_recovery for pt in state.recovery_sensitivity_scenarios],
        }
        st.dataframe(chart_rows, use_container_width=True)

        show_compare = st.toggle("Compare observed vs purified credit interpretation", value=True, key="cmp_13")
        if show_compare:
            raw_hazard = observed_spread / (10_000.0 * max(1e-6, 1.0 - recovery))
            l, r = st.columns(2)
            l.warning(f"Raw implied hazard from observed spread: **{raw_hazard:.4%}**")
            r.success(f"Purified hazard proxy: **{state.hazard_proxy:.4%}**")

        st.caption("Delivery-option style intuition: cheapest-to-deliver dynamics and contract technicals can distort observed spreads away from default fundamentals.")

        return {
            "inputs": {
                "observed_spread_bp": observed_spread,
                "liquidity_component_bp": liquidity_component,
                "technical_component_bp": technical_component,
                "recovery_rate": recovery,
            },
            "outputs": {
                "purified_credit_spread_bp": state.purified_spread_bp,
                "hazard_proxy": state.hazard_proxy,
                "recovery_sensitivity": state.d_hazard_d_recovery,
            },
        }

    def failure_modes(self) -> list[dict[str, str]]:
        return [
            {"mode": "Treating observed CDS as pure default premium", "mitigation": "Subtract liquidity and technical components before default inference."},
            {"mode": "Using a single recovery assumption as truth", "mitigation": "Run recovery-sensitivity panel and size conviction to robustness."},
            {"mode": "Ignoring delivery-option style contamination", "mitigation": "Cross-check with deliverables, index basis, and market microstructure context."},
        ]

    def assessment(self) -> list[dict[str, str]]:
        return [
            {
                "prompt": "Why can observed CDS widen while purified credit stays stable?",
                "expected": "Liquidity/technical contamination in premium leg can move the quote without a fundamental hazard shift.",
            }
        ]

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            schema_name="PureCreditState",
            signals=[
                "observed_spread_bp",
                "purified_credit_spread_bp",
                "hazard_proxy",
                "recovery_sensitivity",
            ],
            usage="Feeds Chapter 14 with purified credit context so basis interpretation is not polluted by raw CDS technicals.",
        )
