from __future__ import annotations

import streamlit as st

from core.types import ChapterExportState
from src.models.ccbs import basis_shock_sensitivity, implied_cross_currency_basis, synthetic_domestic_hedged_yield

from .base import SimpleChapter


class Chapter15(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(
            chapter_id="15",
            title="Chapter 15: Cross-currency basis swaps and CIP wedges",
            objective="Use CIP intuition to explain cross-currency basis, then evaluate synthetic domestic exposure from foreign asset + FX hedge + basis swap.",
        )

    def key_takeaway(self) -> str:
        return "Cross-currency basis is the price of balance-sheet and funding imbalance in FX-hedged allocation, not just an FX math residual."

    def learn_focus(self) -> list[str]:
        return [
            "Under CIP, hedged foreign funding should match domestic funding; persistent gaps appear as basis.",
            "Cross-currency basis captures scarcity/constraints in collateral and balance sheet across currencies.",
            "Synthetic domestic yield from foreign asset + hedge is often the practical trader lens.",
        ]

    def derive_focus(self) -> list[str]:
        return [
            "Compute implied basis from domestic leg, foreign leg, and FX-forward-implied funding.",
            "Decompose hedge cost into FX forward carry plus optional stress add-ons.",
            "Map basis into synthetic domestic hedged yield and stress-test with basis shocks.",
        ]

    def trade_use_focus(self) -> list[str]:
        return [
            "Go where synthetic hedged yield exceeds domestic alternative after hedge costs.",
            "Treat basis widening risk as core P&L driver, not a tail detail.",
            "Use sensitivity panel to set stop-loss and sizing against basis shock scenarios.",
        ]

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Implied CCBS", "equation": "basis_bp=(domestic_float-(foreign_float+fx_forward_implied))*100-adjustments_bp"},
            {"name": "Synthetic domestic hedged yield", "equation": "synthetic_yield_pct=foreign_leg_yield_pct+fx_hedge_cost_pct+basis_bp/100"},
            {"name": "Expected package P&L", "equation": "expected_total_pnl=notional*(basis_carry_bp+convergence_bp)*horizon/10000-hedging_costs"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Set domestic and foreign floating legs plus FX-forward implied funding leg (CIP reference).",
            "Infer cross-currency basis as deviation from CIP-consistent parity after adjustments.",
            "Compute synthetic domestic hedged yield using foreign asset carry, FX hedge cost, and basis.",
            "Add convergence and implementation costs to estimate expected package economics.",
            "Stress basis shocks to understand downside if funding imbalance worsens.",
        ]

    def interactive_lab(self) -> dict[str, dict[str, float]]:
        st.markdown("#### 1) Domestic vs foreign legs and CIP intuition")
        d1, d2, d3 = st.columns(3)
        domestic_leg = d1.number_input("Domestic floating leg (%)", value=5.00, step=0.01, key="dom_leg_15")
        foreign_leg = d2.number_input("Foreign floating leg (%)", value=3.65, step=0.01, key="for_leg_15")
        fx_forward_implied = d3.number_input("FX-forward implied funding (%)", value=1.10, step=0.01, key="fx_implied_15")

        st.markdown("#### 2) Hedge cost and synthetic domestic exposure")
        foreign_asset_yield = st.number_input("Foreign asset yield (%)", value=4.25, step=0.01, key="for_asset_15")
        fx_hedge_cost = st.number_input("FX hedge cost (%)", value=0.30, step=0.01, key="fx_hedge_15")
        credit_adj = st.number_input("Credit adjustment (bp)", value=2.0, step=0.5, key="credit_adj_15")
        repo_adj = st.number_input("Repo adjustment (bp)", value=1.0, step=0.5, key="repo_adj_15")
        ref_adj = st.number_input("Reference-rate adjustment (bp)", value=2.0, step=0.5, key="ref_adj_15")

        basis_bp = implied_cross_currency_basis(
            domestic_float_rate_pct=domestic_leg,
            foreign_float_rate_pct=foreign_leg,
            fx_forward_implied_rate_pct=fx_forward_implied,
            quote_convention="domestic_minus_hedged_foreign",
            credit_adjustment_bp=credit_adj,
            repo_adjustment_bp=repo_adj,
            reference_rate_adjustment_bp=ref_adj,
        )
        synthetic_yield = synthetic_domestic_hedged_yield(
            foreign_leg_yield_pct=foreign_asset_yield,
            fx_hedge_cost_pct=fx_hedge_cost,
            basis_bp=basis_bp,
        )

        st.metric("Cross-currency basis (bp)", f"{basis_bp:.2f}")
        st.metric("Synthetic domestic hedged yield (%)", f"{synthetic_yield:.3f}")

        st.markdown("#### 3) Carry and execution interpretation")
        notional = st.number_input("Notional ($)", value=40_000_000.0, step=1_000_000.0, key="notional_15")
        convergence_bp = st.number_input("Expected convergence (bp)", value=16.0, step=1.0, key="conv_15")
        horizon_years = st.slider("Holding horizon (years)", min_value=0.1, max_value=2.0, value=0.75, step=0.05, key="h_15")
        hedging_costs = st.number_input("Execution costs ($)", value=95_000.0, step=5_000.0, key="hedge_cost_15")

        carry_pnl = notional * (basis_bp / 10_000.0) * horizon_years
        convergence_pnl = notional * (convergence_bp / 10_000.0) * horizon_years
        expected_total_pnl = carry_pnl + convergence_pnl - hedging_costs
        hedge_cost_bp_equiv = (hedging_costs / max(notional * horizon_years, 1e-6)) * 10_000.0

        st.metric("Carry P&L ($)", f"{carry_pnl:,.0f}")
        st.metric("Convergence P&L ($)", f"{convergence_pnl:,.0f}")
        st.metric("Hedge cost equivalent (bp)", f"{hedge_cost_bp_equiv:.2f}")
        st.metric("Expected total P&L ($)", f"{expected_total_pnl:,.0f}")

        sensitivity = basis_shock_sensitivity(
            base_basis_bp=basis_bp,
            foreign_leg_yield_pct=foreign_asset_yield,
            fx_hedge_cost_pct=fx_hedge_cost,
            shocks_bp=[-20.0, -10.0, 0.0, 10.0, 20.0],
        )
        st.dataframe(
            [
                {
                    "basis_shock_bp": p.basis_shock_bp,
                    "shocked_basis_bp": p.shocked_basis_bp,
                    "shocked_synthetic_domestic_yield_pct": p.shocked_synthetic_domestic_yield_pct,
                }
                for p in sensitivity
            ],
            use_container_width=True,
        )

        return {
            "inputs": {
                "domestic_leg_pct": domestic_leg,
                "foreign_leg_pct": foreign_leg,
                "fx_forward_implied_pct": fx_forward_implied,
                "foreign_asset_yield_pct": foreign_asset_yield,
                "fx_hedge_cost_pct": fx_hedge_cost,
            },
            "outputs": {
                "cross_currency_basis_bp": basis_bp,
                "synthetic_domestic_hedged_yield_pct": synthetic_yield,
                "carry_pnl": carry_pnl,
                "convergence_pnl": convergence_pnl,
                "expected_total_pnl": expected_total_pnl,
            },
        }

    def failure_modes(self) -> list[dict[str, str]]:
        return [
            {"mode": "Assuming CIP holds exactly at tradable levels", "mitigation": "Model execution/constraint wedges explicitly and stress basis persistence."},
            {"mode": "Ignoring hedge-cost drag", "mitigation": "Convert dollar hedge costs into bp-equivalent and net against basis carry."},
            {"mode": "Using one basis point estimate for all tenors", "mitigation": "Check tenor-specific basis and hedge-reset mismatches."},
        ]

    def assessment(self) -> list[dict[str, str]]:
        return [
            {
                "prompt": "Why can a foreign asset with higher unhedged yield underperform on a hedged basis?",
                "expected": "FX hedge costs plus adverse cross-currency basis can more than offset foreign yield pickup.",
            }
        ]

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            schema_name="CCBSState",
            signals=["carry_pnl", "convergence_pnl", "expected_total_pnl", "cross_currency_basis_bp", "synthetic_domestic_hedged_yield_pct"],
            usage="Supplies Chapter 16 with hedged cross-currency carry, convergence, and synthetic-yield diagnostics.",
        )
