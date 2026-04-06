from __future__ import annotations

import streamlit as st

from .base import SimpleChapter


class Chapter13(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(
            chapter_id="13",
            title="Chapter 13: Credit default swaps and pure-credit extraction",
            objective="Separate default-risk compensation from liquidity and technical contamination, then map to a recovery-sensitive hazard proxy.",
        )

    def concept_map(self) -> dict[str, list[str]]:
        return {
            "nodes": [
                "Observed CDS spread",
                "Liquidity component",
                "Technical component",
                "Purified credit spread",
                "Recovery assumption",
                "Hazard proxy",
                "Interpretation panel",
            ],
            "edges": [
                "Observed CDS spread->Purified credit spread",
                "Liquidity component->Purified credit spread",
                "Technical component->Purified credit spread",
                "Purified credit spread->Hazard proxy",
                "Recovery assumption->Hazard proxy",
                "Observed CDS spread->Interpretation panel",
                "Purified credit spread->Interpretation panel",
            ],
        }

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {
                "name": "Observed vs purified decomposition",
                "equation": "purified_credit_spread_bp = observed_spread_bp - liquidity_component_bp - technical_component_bp",
            },
            {
                "name": "Hazard proxy",
                "equation": "hazard_proxy = purified_credit_spread_bp / (10000*(1-recovery_rate))",
            },
            {
                "name": "Recovery sensitivity",
                "equation": "d(hazard_proxy)/d(recovery_rate) = purified_credit_spread_bp / (10000*(1-recovery_rate)^2)",
            },
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Premium leg intuition: the buyer pays a running coupon while no credit event occurs, so richer coupon obligations reflect both default and non-default premia.",
            "Protection leg intuition: the seller's expected payout scales with loss-given-default (1-recovery), linking spread interpretation directly to recovery assumptions.",
            "Observed-vs-purified spread decomposition: remove liquidity and technical premia from the quoted CDS level to approximate default-only compensation.",
            "Recovery-rate dependence exposition: for the same purified spread, higher assumed recovery implies lower LGD and therefore a higher hazard required to match compensation.",
            "Interpretation check: compare raw observed spread readings with purified readings before using a spread move as a default-risk signal.",
        ]

    def interactive_lab(self) -> dict[str, dict[str, float]]:
        st.markdown("#### CDS cash-flow intuition")
        with st.expander("Premium leg intuition block", expanded=False):
            st.write(
                "The premium leg is a stream of periodic payments made until maturity or default. "
                "Observed coupons therefore embed not only expected default losses but also compensation "
                "for trading frictions and positioning pressures."
            )

        with st.expander("Protection leg intuition block", expanded=False):
            st.write(
                "The protection leg approximates expected default payout: probability of default × loss-given-default. "
                "Because loss-given-default is (1 - recovery), any hazard inference from spread is conditional "
                "on recovery assumptions."
            )

        with st.expander("Recovery-rate dependence exposition", expanded=False):
            st.write(
                "Holding purified spread fixed, the hazard proxy is inversely proportional to (1 - recovery). "
                "As recovery rises, inferred hazard rises nonlinearly because the same premium must explain a smaller LGD."
            )

        with st.expander("Observed vs purified spread decomposition", expanded=False):
            st.write(
                "Observed CDS spread is not pure default compensation. A practical decomposition subtracts "
                "liquidity and technical components to isolate a cleaner default-risk proxy."
            )

        with st.expander("Sovereign CDS caveat panel", expanded=False):
            st.warning(
                "Sovereign contracts may be influenced by restructuring clauses, deliverable-bond eligibility, "
                "capital controls, and redenomination concerns. Purified interpretation is therefore less structural "
                "than in plain-vanilla corporate CDS."
            )

        with st.expander("Delivery-option / technical contamination panel", expanded=False):
            st.info(
                "Cheapest-to-deliver optionality, index-vs-single-name basis, collateral/funding frictions, and "
                "positioning squeezes can all distort observed spreads away from default fundamentals."
            )

        st.markdown("#### Interactive extraction lab")
        observed_spread = st.number_input("Observed spread (bp)", value=118.0, step=1.0, key="obs_13")
        liquidity_component = st.number_input("Liquidity component (bp)", value=21.0, step=1.0, key="liq_13")
        technical_component = st.number_input("Technical component (bp)", value=9.0, step=1.0, key="tech_13")
        recovery = st.slider("Recovery rate", min_value=0.05, max_value=0.85, value=0.40, step=0.01, key="rec_13")

        purified_credit_spread = observed_spread - liquidity_component - technical_component
        denominator = max(1e-6, 1.0 - recovery)
        hazard_proxy = purified_credit_spread / (10_000.0 * denominator)
        recovery_sensitivity = purified_credit_spread / (10_000.0 * (denominator**2))

        st.metric("Purified credit spread (bp)", f"{purified_credit_spread:.2f}")
        st.metric("Hazard proxy (annualized)", f"{hazard_proxy:.4%}")
        st.metric("Sensitivity of hazard to recovery", f"{recovery_sensitivity:.6f}")

        show_comparison = st.toggle("Compare raw observed vs purified interpretations", value=True, key="cmp_13")
        if show_comparison:
            left, right = st.columns(2)
            with left:
                st.caption("Raw observed interpretation")
                raw_hazard = observed_spread / (10_000.0 * denominator)
                st.write(f"Spread includes default + liquidity + technical effects: **{observed_spread:.2f} bp**")
                st.write(f"Naive hazard from raw spread: **{raw_hazard:.4%}**")
            with right:
                st.caption("Purified interpretation")
                st.write(f"Spread after non-default stripping: **{purified_credit_spread:.2f} bp**")
                st.write(f"Hazard proxy from purified spread: **{hazard_proxy:.4%}**")

        return {
            "inputs": {
                "observed_spread_bp": observed_spread,
                "liquidity_component_bp": liquidity_component,
                "technical_component_bp": technical_component,
                "recovery_rate": recovery,
            },
            "outputs": {
                "purified_credit_spread_bp": purified_credit_spread,
                "hazard_proxy": hazard_proxy,
                "recovery_sensitivity": recovery_sensitivity,
            },
        }

    def exports_to_next_chapter(self) -> dict[str, object]:
        return {
            "schema_name": "PureCreditState",
            "signals": [
                "observed_spread_bp",
                "purified_credit_spread_bp",
                "hazard_proxy",
                "recovery_sensitivity",
            ],
            "usage": "Feeds downstream trade design with raw-vs-purified credit signal diagnostics and recovery-aware hazard mapping.",
        }
