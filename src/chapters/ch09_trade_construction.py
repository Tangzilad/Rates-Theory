from __future__ import annotations

from typing import Any

import streamlit as st

from core.types import ChapterExportState, GovBondTradeBlueprint

from .base import ChapterBase


class Chapter09(ChapterBase):
    chapter_id = "9"

    _WIZARD_STEPS = [
        "1) Universe selection",
        "2) Curve-fit integration",
        "3) Rich/cheap identification",
        "4) PCA neutralization",
        "5) Mean-reversion validation",
        "6) Hedge comparison",
        "7) Trade blueprint",
    ]

    def chapter_meta(self) -> dict[str, str]:
        return {
            "chapter": self.chapter_id,
            "title": "Chapter 9: Trade construction",
            "objective": "Build a governed rates RV trade from screening, factor controls, and hedge selection.",
        }

    def prerequisites(self) -> list[str]:
        return [
            "Chapter 8 screen residuals and curve-fit diagnostics",
            "Chapter 3 factor-neutral hedge candidates",
            "Chapter 5 duration/DV01 and fair-value diagnostics",
            "Chapter 2 OU mean-reversion state",
        ]

    def concept_map(self) -> dict[str, list[str]]:
        return {
            "nodes": [
                "Universe",
                "Curve residual",
                "Rich/Cheap decomposition",
                "PCA neutrality",
                "Mean reversion",
                "Hedge alternatives",
                "Blueprint",
            ],
            "edges": [
                "Universe->Curve residual",
                "Curve residual->Rich/Cheap decomposition",
                "Rich/Cheap decomposition->PCA neutrality",
                "PCA neutrality->Mean reversion",
                "Mean reversion->Hedge alternatives",
                "Hedge alternatives->Blueprint",
            ],
        }

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Residual z-score", "equation": r"z=(\epsilon_t-\mu_\epsilon)/\sigma_\epsilon"},
            {"name": "Expected reversion", "equation": r"E[\Delta\epsilon_h]=\mu_\epsilon-\epsilon_t"},
            {"name": "Hedge efficiency", "equation": r"Score=|NetDV01|+\lambda|PCA_{resid}|"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Select bond universe and candidate security.",
            "Bring in Chapter 8 curve-fit residual and convert to standardized richness signal.",
            "Decompose residual into curve, carry/roll, and liquidity components for explainability.",
            "Optionally apply Chapter 3 PCA-neutral hedge weights and assess residual factor exposure.",
            "Validate convergence profile against Chapter 2/5 mean-reversion and risk metrics.",
            "Compare hedge choices (neighbor bond, futures, swap proxy) with cost/risk trade-offs.",
            "Export executable trade blueprint with rationale and controls.",
        ]

    @staticmethod
    def _as_mapping(payload: Any) -> dict[str, Any]:
        if payload is None:
            return {}
        if hasattr(payload, "model_dump"):
            dumped = payload.model_dump()
            return dumped if isinstance(dumped, dict) else {}
        return payload if isinstance(payload, dict) else {}

    def interactive_lab(self) -> GovBondTradeBlueprint:
        upstream: dict[str, Any] = st.session_state.get("chapter_exports", {})
        ch8 = self._as_mapping(upstream.get("8"))
        ch3 = self._as_mapping(upstream.get("3"))
        ch5 = self._as_mapping(upstream.get("5"))
        ch2 = self._as_mapping(upstream.get("2"))

        st.caption("Wizard flow: complete each step and publish a typed trade blueprint.")
        active_step = st.select_slider("Construction step", options=self._WIZARD_STEPS, value=self._WIZARD_STEPS[0])

        universe = st.selectbox("Government-bond universe", ["UST", "Bund", "Gilt"], index=0)
        candidates = {
            "UST": ["UST 2Y", "UST 5Y", "UST 10Y", "UST 30Y"],
            "Bund": ["DE 2Y", "DE 5Y", "DE 10Y", "DE 30Y"],
            "Gilt": ["UKT 2Y", "UKT 5Y", "UKT 10Y", "UKT 30Y"],
        }
        candidate_bond = st.selectbox("Candidate bond", candidates[universe], index=2)

        st.markdown("### Chapter 8 curve-fit integration")
        default_curve_residual = float(ch8.get("curve_fit_residual_bp", ch8.get("approximation_error", 0.0)))
        curve_fit_residual_bp = st.number_input("Curve-fit residual (bp)", value=default_curve_residual, step=0.25)
        curve_fit_zscore = st.number_input("Curve-fit residual z-score", value=float(ch8.get("residual_zscore", 1.8)), step=0.1)

        st.markdown("### Why rich/cheap decomposition")
        carry_roll_bp = st.number_input("Carry/roll adjustment (bp)", value=0.6, step=0.1)
        liquidity_bp = st.number_input("Liquidity premium adjustment (bp)", value=0.4, step=0.1)
        risk_fair_price = float(ch5.get("fair_price_under_shock", ch5.get("fair_price", 100.0)))
        market_price = st.number_input("Observed market price", value=risk_fair_price + 0.55, step=0.01)
        richness_bp = curve_fit_residual_bp + carry_roll_bp + liquidity_bp
        valuation_gap = market_price - risk_fair_price
        rich_cheap_signal = "rich" if richness_bp > 0 else "cheap"

        panel_left, panel_right = st.columns(2)
        panel_left.metric("Residual-driven richness (bp)", f"{richness_bp:.2f}")
        panel_left.metric("Price gap vs fair value", f"{valuation_gap:.3f}")
        panel_right.metric("Curve residual", f"{curve_fit_residual_bp:.2f} bp")
        panel_right.metric("Carry + liquidity", f"{carry_roll_bp + liquidity_bp:.2f} bp")

        with st.expander("Why is this bond rich/cheap?", expanded=True):
            st.markdown(
                "\n".join(
                    [
                        f"- **Curve fit dislocation:** {curve_fit_residual_bp:.2f} bp from Chapter 8 residual diagnostics.",
                        f"- **Carry/roll contribution:** {carry_roll_bp:.2f} bp projected over holding window.",
                        f"- **Liquidity premium:** {liquidity_bp:.2f} bp execution penalty/benefit.",
                        f"- **Net signal:** {richness_bp:.2f} bp ({rich_cheap_signal.upper()}).",
                    ]
                )
            )

        st.markdown("### Optional PCA neutralization (Chapter 3)")
        apply_pca_neutralization = st.toggle("Apply PCA-neutral hedge overlay", value=True)
        pca_weights = ch3.get("candidate_neutral_hedge_weights", {}) if isinstance(ch3.get("candidate_neutral_hedge_weights", {}), dict) else {}
        pca_residual_factor = st.number_input("Post-neutralization residual factor exposure", value=0.15 if apply_pca_neutralization else 0.85, step=0.05)

        st.markdown("### Mean-reversion validation (Chapter 5/2)")
        ou_z = float(ch2.get("current_z_score", curve_fit_zscore))
        ou_half_life = float(ch2.get("half_life", 45.0) or 45.0)
        first_passage = float(ch2.get("first_passage_probability", 0.58))
        modified_duration = float(ch5.get("modified_duration", ch5.get("duration", 7.5)))
        dv01 = float(ch5.get("dv01", 0.082))

        horizon_days = st.slider("Planned holding horizon (days)", 5, 180, 45, 5)
        mean_reversion_valid = (abs(ou_z) >= 1.0) and (first_passage >= 0.45) and (ou_half_life <= horizon_days)
        st.write(
            f"Validation checks: |z|={abs(ou_z):.2f}, hit-prob={first_passage:.2%}, half-life={ou_half_life:.1f}d, horizon={horizon_days}d."
        )
        st.success("Mean-reversion checks passed.") if mean_reversion_valid else st.warning("Mean-reversion checks are weak; downgrade conviction.")

        st.markdown("### Hedge choice comparison")
        neighbor_bond_cost = st.number_input("Neighbor bond hedge cost (bp)", value=0.4, step=0.05)
        futures_cost = st.number_input("Futures hedge cost (bp)", value=0.2, step=0.05)
        swap_proxy_cost = st.number_input("Swap-proxy hedge cost (bp)", value=0.35, step=0.05)
        neighbor_net_dv01 = st.number_input("Neighbor hedge net DV01", value=0.01, step=0.01)
        futures_net_dv01 = st.number_input("Futures hedge net DV01", value=0.04, step=0.01)
        swap_net_dv01 = st.number_input("Swap hedge net DV01", value=0.03, step=0.01)

        hedge_table = {
            "neighbor_bond": {"cost_bp": neighbor_bond_cost, "net_dv01": neighbor_net_dv01},
            "futures": {"cost_bp": futures_cost, "net_dv01": futures_net_dv01},
            "swap_proxy": {"cost_bp": swap_proxy_cost, "net_dv01": swap_net_dv01},
        }
        preferred_hedge = min(hedge_table.items(), key=lambda kv: abs(kv[1]["net_dv01"]) + kv[1]["cost_bp"])[0]
        st.dataframe(hedge_table, use_container_width=True)
        st.info(f"Preferred hedge by cost-adjusted DV01 score: **{preferred_hedge}**")

        if active_step != self._WIZARD_STEPS[-1]:
            st.caption("Use the step slider to move through the wizard; blueprint updates continuously.")

        direction = "short_candidate_bond" if rich_cheap_signal == "rich" else "long_candidate_bond"
        conviction = "high" if mean_reversion_valid and abs(curve_fit_zscore) >= 1.5 else "medium"

        blueprint = GovBondTradeBlueprint(
            universe=universe,
            candidate_bond=candidate_bond,
            rich_cheap_signal=rich_cheap_signal,
            richness_bp=richness_bp,
            curve_fit_residual_bp=curve_fit_residual_bp,
            curve_fit_zscore=curve_fit_zscore,
            decomposition={
                "curve_fit_residual_bp": curve_fit_residual_bp,
                "carry_roll_bp": carry_roll_bp,
                "liquidity_bp": liquidity_bp,
                "total_richness_bp": richness_bp,
            },
            pca_neutralization_applied=apply_pca_neutralization,
            pca_residual_factor_exposure=pca_residual_factor,
            pca_candidate_weights={k: float(v) for k, v in pca_weights.items()},
            mean_reversion_validated=mean_reversion_valid,
            mean_reversion_metrics={
                "current_z_score": ou_z,
                "half_life_days": ou_half_life,
                "first_passage_probability": first_passage,
                "horizon_days": float(horizon_days),
            },
            risk_metrics={"modified_duration": modified_duration, "dv01": dv01, "fair_price": risk_fair_price, "market_price": market_price},
            hedge_comparison=hedge_table,
            preferred_hedge=preferred_hedge,
            trade_direction=direction,
            conviction=conviction,
            rationale=(
                f"{candidate_bond} screens {rich_cheap_signal} by {richness_bp:.2f} bp; "
                f"mean-reversion validation={mean_reversion_valid}; hedge={preferred_hedge}."
            ),
        )

        st.subheader("Trade blueprint output")
        st.json(blueprint.model_dump())
        return blueprint

    def case_studies(self) -> list[dict[str, str]]:
        return [
            {
                "name": "10Y rich-to-curve RV",
                "setup": "Bond looks rich on curve residual and carry decomposition.",
                "takeaway": "Require factor-neutral and mean-reversion checks before shorting cash bond.",
            }
        ]

    def failure_modes(self) -> list[dict[str, str]]:
        return [
            {
                "mode": "Apparent richness is a structural liquidity regime shift",
                "mitigation": "Force decomposition review and reduce conviction if mean-reversion validation fails.",
            }
        ]

    def assessment(self) -> list[dict[str, str]]:
        return [
            {
                "prompt": "Why can a rich residual still be a no-trade?",
                "expected": "If mean-reversion metrics or hedge efficiency are weak, expected convergence is not robust.",
            }
        ]

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            signals=[
                "universe",
                "candidate_bond",
                "rich_cheap_signal",
                "richness_bp",
                "curve_fit_residual_bp",
                "curve_fit_zscore",
                "decomposition",
                "pca_neutralization_applied",
                "mean_reversion_validated",
                "hedge_comparison",
                "preferred_hedge",
                "trade_direction",
                "conviction",
            ],
            usage="Blueprinted trade payload for implementation, funding checks, and execution sequencing.",
            schema_name="GovBondTradeBlueprint",
        )
