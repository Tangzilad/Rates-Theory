from __future__ import annotations

import streamlit as st

from core.types import ChapterExportState
from src.models.icbs import icbs_chapter_payload

from .base import SimpleChapter


def _clamp_confidence(raw: float) -> float:
    return max(0.0, min(1.0, raw))


class Chapter14(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(
            chapter_id="14",
            title="Chapter 14: Intra-currency basis swaps (tenor basis)",
            objective="Price same-currency floating-vs-floating tenor basis using observed/fair term structures, then map carry and rolldown into executable trade interpretation.",
        )

    def key_takeaway(self) -> str:
        return "Observed tenor basis can look attractive, but execution quality depends on fair-value gap, term-structure shape, carry, and rolldown together."

    def learn_focus(self) -> list[str]:
        return [
            "Intra-currency basis is a same-currency tenor conversion wedge, not an outright rates view.",
            "Fair basis differs from observed basis when collateral, reset timing, and funding frictions diverge.",
            "Carry and rolldown can dominate short-horizon P&L even when spot basis looks rich/cheap.",
        ]

    def derive_focus(self) -> list[str]:
        return [
            "Compute observed basis from benchmark leg differential.",
            "Construct fair basis and net execution edge after implementation costs.",
            "Project carry and rolldown from current tenor and term-structure slope.",
        ]

    def trade_use_focus(self) -> list[str]:
        return [
            "Prefer tenors where observed-fair gap and carry align.",
            "Downsize if rolldown is adverse even with positive spot gap.",
            "Use execution confidence as a gate for cross-currency packaging in Chapter 15.",
        ]

    def concept_map(self) -> dict[str, list[str]]:
        return {
            "nodes": ["Observed basis", "Fair basis", "Term structure", "Carry", "Rolldown", "Execution decision"],
            "edges": [
                "Observed basis->Execution decision",
                "Fair basis->Execution decision",
                "Term structure->Rolldown",
                "Observed basis->Carry",
                "Carry->Execution decision",
                "Rolldown->Execution decision",
            ],
        }

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Observed tenor basis", "equation": "observed_basis_bp=(float_leg_a_pct-float_leg_b_pct)*100-reference_adjustment_bp"},
            {"name": "Net basis edge", "equation": "net_edge_bp=observed_basis_bp-fair_basis_bp-implementation_cost_bp"},
            {"name": "Carry estimate", "equation": "carry_estimate_bp=current_basis_bp*horizon_years+(expected_basis_bp-current_basis_bp)"},
            {"name": "Rolldown estimate", "equation": "rolldown_bp=basis(tenor-roll_horizon)-basis(tenor_now)"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Measure observed same-currency tenor basis from benchmark pair and reference adjustment.",
            "Estimate fair basis under harmonized collateral/reference assumptions.",
            "Build multi-tenor basis term structure to capture slope and curvature.",
            "Compute carry and rolldown from expected convergence and curve roll.",
            "Translate economics into execution confidence and trade/no-trade decision.",
        ]

    def interactive_lab(self) -> dict[str, dict[str, float | bool]]:
        st.markdown("#### 1) Inputs: observed and fair basis")
        benchmark_a_pct = st.number_input("Observed floating leg A (%)", value=5.10, step=0.01, key="bench_a_14")
        benchmark_b_pct = st.number_input("Observed floating leg B (%)", value=4.96, step=0.01, key="bench_b_14")
        fair_basis_bp = st.number_input("Model fair basis (bp)", value=8.5, step=0.5, key="fair_basis_14")
        implementation_cost_bp = st.number_input("Implementation cost (bp)", value=1.5, step=0.1, key="impl_14")
        entry_hurdle_bp = st.number_input("Entry hurdle (bp)", value=2.0, step=0.1, key="hurdle_14")
        reference_adjustment_bp = st.number_input("Reference adjustment (bp)", value=0.5, step=0.1, key="ref_adj_14")

        st.markdown("#### 2) Multi-tenor term-structure panel")
        maturities = [1.0, 2.0, 3.0, 5.0]
        curve_a = [5.05, 5.00, 4.95, 4.82]
        curve_b = [4.96, 4.91, 4.87, 4.77]

        current_maturity = st.selectbox("Current tenor (years)", options=maturities, index=2, key="cur_mat_14")
        roll_horizon = st.slider("Rolldown horizon (years)", min_value=0.25, max_value=2.0, value=1.0, step=0.25, key="roll_14")
        expected_basis_bp = st.number_input("Expected basis at horizon (bp)", value=10.0, step=0.5, key="expected_14")
        carry_horizon = st.slider("Carry horizon (years)", min_value=0.25, max_value=1.5, value=0.5, step=0.25, key="carry_h_14")

        state = icbs_chapter_payload(
            benchmark_a_name="Leg A",
            benchmark_b_name="Leg B",
            benchmark_a_pct=benchmark_a_pct,
            benchmark_b_pct=benchmark_b_pct,
            maturity_years=maturities,
            benchmark_a_curve_pct=curve_a,
            benchmark_b_curve_pct=curve_b,
            current_maturity_years=float(current_maturity),
            roll_horizon_years=roll_horizon,
            expected_basis_bp=expected_basis_bp,
            carry_horizon_years=carry_horizon,
            reference_rate_adjustment_bp=reference_adjustment_bp,
        )

        observed_basis_bp = state.current_basis_bp
        net_edge_bp = observed_basis_bp - fair_basis_bp - implementation_cost_bp
        execution_confidence = _clamp_confidence(net_edge_bp / max(entry_hurdle_bp, 1e-6))
        execute_flag = net_edge_bp > 0

        st.metric("Observed basis (bp)", f"{observed_basis_bp:.2f}")
        st.metric("Fair basis (bp)", f"{fair_basis_bp:.2f}")
        st.metric("Net edge (bp)", f"{net_edge_bp:.2f}")
        st.metric("Carry estimate (bp)", f"{state.carry_estimate_bp:.2f}")
        st.metric("Rolldown estimate (bp)", f"{state.rolldown_estimate_bp:.2f}")
        st.metric("Execution confidence", f"{execution_confidence:.2f}")
        st.metric("Execution interpretation", "Deploy" if execute_flag else "Wait")

        st.dataframe(
            [
                {
                    "maturity_years": p.maturity_years,
                    "benchmark_a_pct": p.benchmark_a_pct,
                    "benchmark_b_pct": p.benchmark_b_pct,
                    "basis_bp": p.basis_bp,
                }
                for p in state.term_structure
            ],
            use_container_width=True,
        )

        return {
            "inputs": {
                "observed_basis_bp": observed_basis_bp,
                "fair_basis_bp": fair_basis_bp,
                "implementation_cost_bp": implementation_cost_bp,
                "entry_hurdle_bp": entry_hurdle_bp,
                "expected_basis_bp": expected_basis_bp,
            },
            "outputs": {
                "net_edge_bp": net_edge_bp,
                "carry_estimate_bp": state.carry_estimate_bp,
                "rolldown_estimate_bp": state.rolldown_estimate_bp,
                "execution_confidence": execution_confidence,
                "execute_flag": execute_flag,
            },
        }

    def failure_modes(self) -> list[dict[str, str]]:
        return [
            {"mode": "Trading spot gap without term-structure context", "mitigation": "Check carry + rolldown and multi-tenor slope before sizing."},
            {"mode": "Treating implementation costs as negligible", "mitigation": "Explicitly subtract execution drag in net edge and hurdle test."},
            {"mode": "Assuming fair basis is static", "mitigation": "Re-estimate fair basis as reference and collateral assumptions change."},
        ]

    def assessment(self) -> list[dict[str, str]]:
        return [
            {
                "prompt": "If spot net edge is positive but rolldown is strongly negative, what should a trader do?",
                "expected": "Reduce size or avoid entry because horizon P&L may be dominated by adverse curve roll.",
            }
        ]

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            schema_name="ICBSState",
            signals=["net_edge_bp", "carry_estimate_bp", "rolldown_estimate_bp", "execution_confidence", "execute_flag"],
            usage="Feeds Chapter 15 with tenor-basis execution quality and carry/rolldown diagnostics.",
        )
