from __future__ import annotations

import csv
import io

import numpy as np
import streamlit as st

from core.types import ChapterExportState, GlobalRVBondSignalState, GlobalRVDisagreementState, GlobalRVScreenState
from src.models.asset_swaps import asset_swap_spread_bp, coupon_mismatch_bp
from src.models.fitted_curves import fit_parametric_curve, rank_residual_series, sofr_asw_residuals_bp

from .base import SimpleChapter


class Chapter17(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(
            chapter_id="17",
            title="Chapter 17: Global bond RV",
            objective="Rank global bond relative-value opportunities across fitted-curve and SOFR-ASW lenses with disagreement diagnostics and attribution-ready signals.",
        )

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Curve residual", "equation": "curve_residual_i^{bp}=100*(y_i^{obs}-y_i^{fit})"},
            {
                "name": "SOFR-ASW residual",
                "equation": "sofr_asw_residual_i=ASW_i-(SOFR_OIS_i+funding_basis_i+credit_diff_i+benchmark_choice_i)",
            },
            {
                "name": "Disagreement",
                "equation": "rank_gap_i=|rank_i^{curve}-rank_i^{sofr_asw}|",
            },
            {
                "name": "Stress envelope",
                "equation": "total_stress_pnl=-(spread_shock_bp*portfolio_cs01+rate_shock_bp*residual_dv01)-liquidity_haircut",
            },
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Ingest a global bond universe from synthetic defaults or uploaded CSV fields.",
            "Fit a parametric curve and rank fitted-curve residual richness/cheapness.",
            "Build SOFR-ASW residuals with funding/basis, credit, and benchmark-choice adjustments.",
            "Compare rankings, flag disagreement outliers, and summarize attribution buckets.",
            "Export portfolio-selection-ready signals plus stress envelope fields for Chapter 18.",
        ]

    @staticmethod
    def _synthetic_universe(n_bonds: int) -> list[dict[str, float | str]]:
        regions = ["US", "UK", "EZ", "JP", "AU"]
        maturities = np.linspace(1.0, 25.0, n_bonds)
        rows: list[dict[str, float | str]] = []
        for i, maturity in enumerate(maturities):
            region = regions[i % len(regions)]
            base_curve = 2.7 + 0.7 * np.exp(-maturity / 3.5) + 0.35 * np.sin(maturity / 8.0)
            curve_noise = 0.08 * np.sin(i * 1.7)
            repo = 4.55 + 0.08 * np.cos(i / 3.0)
            benchmark = 4.35 + 0.05 * np.sin(i / 4.0)
            rows.append(
                {
                    "bond_id": f"{region}-B{i+1:02d}",
                    "region": region,
                    "maturity_years": float(maturity),
                    "observed_yield_pct": float(base_curve + curve_noise),
                    "z_spread_bp": float(70.0 + 18.0 * np.sin(i / 2.0)),
                    "coupon_pct": float(3.0 + 0.45 * np.cos(i / 2.2)),
                    "benchmark_rate_pct": float(benchmark),
                    "repo_funding_rate_pct": float(repo),
                    "sofr_ois_spread_bp": float(38.0 + 6.0 * np.cos(i / 2.5)),
                    "credit_difference_bp": float(4.0 * np.sin(i / 1.9)),
                    "benchmark_choice_bp": float(2.0 * np.cos(i / 2.7)),
                }
            )
        return rows

    @staticmethod
    def _parse_upload(csv_bytes: bytes) -> list[dict[str, float | str]]:
        required_fields = {
            "bond_id",
            "region",
            "maturity_years",
            "observed_yield_pct",
            "z_spread_bp",
            "coupon_pct",
            "benchmark_rate_pct",
            "repo_funding_rate_pct",
            "sofr_ois_spread_bp",
            "credit_difference_bp",
            "benchmark_choice_bp",
        }
        text = csv_bytes.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        missing = sorted(required_fields - set(reader.fieldnames or []))
        if missing:
            raise ValueError(f"Upload missing required columns: {missing}")

        rows: list[dict[str, float | str]] = []
        for raw in reader:
            rows.append(
                {
                    "bond_id": str(raw["bond_id"]),
                    "region": str(raw["region"]),
                    "maturity_years": float(raw["maturity_years"]),
                    "observed_yield_pct": float(raw["observed_yield_pct"]),
                    "z_spread_bp": float(raw["z_spread_bp"]),
                    "coupon_pct": float(raw["coupon_pct"]),
                    "benchmark_rate_pct": float(raw["benchmark_rate_pct"]),
                    "repo_funding_rate_pct": float(raw["repo_funding_rate_pct"]),
                    "sofr_ois_spread_bp": float(raw["sofr_ois_spread_bp"]),
                    "credit_difference_bp": float(raw["credit_difference_bp"]),
                    "benchmark_choice_bp": float(raw["benchmark_choice_bp"]),
                }
            )
        if len(rows) < 4:
            raise ValueError("Upload must contain at least 4 bonds for curve fitting")
        return rows

    def interactive_lab(self) -> GlobalRVScreenState:
        st.subheader("Global bond universe")
        universe_source = st.radio("Universe input", options=["Synthetic", "Upload CSV"], horizontal=True, key="ch17_universe_src")
        fit_method = st.selectbox("Curve fit", options=["svensson", "nelson_siegel"], index=0, key="ch17_fit_method")
        disagreement_threshold = st.slider("Disagreement rank-gap threshold", min_value=1, max_value=8, value=3, step=1, key="ch17_rank_gap")

        if universe_source == "Synthetic":
            n_bonds = st.slider("Synthetic bond count", min_value=6, max_value=20, value=10, step=1, key="ch17_n")
            universe = self._synthetic_universe(n_bonds)
        else:
            upload = st.file_uploader("Upload global bond universe CSV", type=["csv"], key="ch17_csv")
            if upload is None:
                st.info("Upload a CSV to run Chapter 17 screening. Using synthetic placeholder until upload is provided.")
                universe = self._synthetic_universe(8)
            else:
                try:
                    universe = self._parse_upload(upload.getvalue())
                except ValueError as exc:
                    st.error(str(exc))
                    universe = self._synthetic_universe(8)

        maturities = np.asarray([float(row["maturity_years"]) for row in universe], dtype=float)
        yields = np.asarray([float(row["observed_yield_pct"]) for row in universe], dtype=float)
        labels = [str(row["bond_id"]) for row in universe]

        fit = fit_parametric_curve(maturities, yields, method=fit_method)
        curve_residual_bp = fit.residuals_pct * 100.0
        curve_ranked = rank_residual_series(labels, curve_residual_bp)

        coupon_mismatch = np.asarray(
            [
                coupon_mismatch_bp(
                    bond_coupon_pct=float(row["coupon_pct"]),
                    benchmark_rate_pct=float(row["benchmark_rate_pct"]),
                )
                for row in universe
            ],
            dtype=float,
        )
        asw_spread = np.asarray(
            [
                asset_swap_spread_bp(
                    z_spread_bp=float(row["z_spread_bp"]),
                    coupon_mismatch_bp_value=float(coupon_mismatch[i]),
                )
                for i, row in enumerate(universe)
            ],
            dtype=float,
        )
        funding_basis = np.asarray(
            [
                (float(row["repo_funding_rate_pct"]) - float(row["benchmark_rate_pct"])) * 100.0
                for row in universe
            ],
            dtype=float,
        )
        credit_difference = np.asarray([float(row["credit_difference_bp"]) for row in universe], dtype=float)
        benchmark_choice = np.asarray([float(row["benchmark_choice_bp"]) for row in universe], dtype=float)
        sofr_ois_spread = np.asarray([float(row["sofr_ois_spread_bp"]) for row in universe], dtype=float)

        sofr_asw_residual = sofr_asw_residuals_bp(
            asset_swap_spread_bp=asw_spread,
            sofr_ois_spread_bp=sofr_ois_spread,
            funding_basis_bp=funding_basis,
            credit_difference_bp=credit_difference,
            benchmark_choice_bp=benchmark_choice,
        )
        sofr_ranked = rank_residual_series(labels, sofr_asw_residual)

        curve_rank_map = {label: curve_ranked.rank_descending[i] for i, label in enumerate(curve_ranked.labels)}
        sofr_rank_map = {label: sofr_ranked.rank_descending[i] for i, label in enumerate(sofr_ranked.labels)}
        curve_z_map = {label: curve_ranked.zscores[i] for i, label in enumerate(curve_ranked.labels)}
        sofr_z_map = {label: sofr_ranked.zscores[i] for i, label in enumerate(sofr_ranked.labels)}
        curve_resid_map = {label: curve_ranked.residual_bp[i] for i, label in enumerate(curve_ranked.labels)}
        sofr_resid_map = {label: sofr_ranked.residual_bp[i] for i, label in enumerate(sofr_ranked.labels)}

        bond_signals: list[GlobalRVBondSignalState] = []
        disagreement_rows: list[dict[str, float | str | bool]] = []
        rank_gaps: list[int] = []
        for i, row in enumerate(universe):
            label = str(row["bond_id"])
            curve_rank = int(curve_rank_map[label])
            sofr_rank = int(sofr_rank_map[label])
            rank_gap = abs(curve_rank - sofr_rank)
            rank_gaps.append(rank_gap)
            disagreement = rank_gap >= disagreement_threshold
            composite_signal = 0.5 * float(curve_z_map[label]) + 0.5 * float(sofr_z_map[label])
            preferred_direction = "Long bond RV (cheap)" if composite_signal > 0.0 else "Short bond RV (rich)"

            disagreement_rows.append(
                {
                    "Bond": label,
                    "Region": str(row["region"]),
                    "Curve rank": curve_rank,
                    "SOFR-ASW rank": sofr_rank,
                    "Rank gap": rank_gap,
                    "Disagreement": disagreement,
                }
            )
            bond_signals.append(
                GlobalRVBondSignalState(
                    bond_id=label,
                    region=str(row["region"]),
                    maturity_years=float(row["maturity_years"]),
                    observed_yield_pct=float(row["observed_yield_pct"]),
                    curve_residual_bp=float(curve_resid_map[label]),
                    curve_residual_zscore=float(curve_z_map[label]),
                    curve_rank=curve_rank,
                    sofr_asw_residual_bp=float(sofr_resid_map[label]),
                    sofr_asw_residual_zscore=float(sofr_z_map[label]),
                    sofr_asw_rank=sofr_rank,
                    rank_gap=rank_gap,
                    disagreement_flag=disagreement,
                    curve_mismatch_bp=float(curve_resid_map[label]),
                    funding_basis_bp=float(funding_basis[i]),
                    credit_difference_bp=float(credit_difference[i]),
                    benchmark_choice_bp=float(benchmark_choice[i]),
                    composite_signal_score=float(composite_signal),
                    preferred_trade_direction=preferred_direction,
                )
            )

        st.subheader("Disagreement table")
        st.dataframe(disagreement_rows, use_container_width=True)

        st.subheader("Residual ranking views")
        c1, c2 = st.columns(2)
        curve_order = [label for _, label in sorted((curve_rank_map[l], l) for l in labels)]
        sofr_order = [label for _, label in sorted((sofr_rank_map[l], l) for l in labels)]
        c1.markdown("**Fitted-curve ranking (cheap → rich)**")
        c1.write(curve_order)
        c2.markdown("**SOFR-ASW ranking (cheap → rich)**")
        c2.write(sofr_order)

        disagreement_ids = [signal.bond_id for signal in bond_signals if signal.disagreement_flag]
        disagreement_state = GlobalRVDisagreementState(
            disagreement_count=len(disagreement_ids),
            disagreement_share=float(len(disagreement_ids) / max(len(bond_signals), 1)),
            mean_rank_gap=float(np.mean(rank_gaps)) if rank_gaps else 0.0,
            max_rank_gap=int(max(rank_gaps)) if rank_gaps else 0,
            top_disagreement_bonds=sorted(disagreement_ids)[:5],
        )

        attribution_buckets = {
            "curve_mismatch": float(np.mean(np.abs(curve_residual_bp))),
            "funding_basis": float(np.mean(np.abs(funding_basis))),
            "credit_differences": float(np.mean(np.abs(credit_difference))),
            "benchmark_choice": float(np.mean(np.abs(benchmark_choice))),
        }

        ranked_by_composite = sorted(bond_signals, key=lambda x: x.composite_signal_score, reverse=True)
        long_candidates = [x.bond_id for x in ranked_by_composite[:3]]
        short_candidates = [x.bond_id for x in ranked_by_composite[-3:]]
        composite_strength = float(np.mean([abs(x.composite_signal_score) for x in ranked_by_composite[:4]])) if ranked_by_composite else 0.0

        st.subheader("Portfolio stress envelope")
        spread_shock_bp = st.number_input("Global spread shock (bp)", value=65.0, step=5.0, key="ch17_spread")
        rate_shock_bp = st.number_input("Rates shock (bp)", value=35.0, step=5.0, key="ch17_rate")
        portfolio_cs01 = st.number_input("Portfolio CS01 ($/bp)", value=90_000.0, step=2_000.0, key="ch17_cs01")
        residual_dv01 = st.number_input("Residual DV01 from ch16 ($/bp)", value=22_000.0, step=1_000.0, key="ch17_dv01")
        liquidity_haircut = st.number_input("Liquidity haircut ($)", value=300_000.0, step=10_000.0, key="ch17_liq")

        rv_spread_pnl = -((float(spread_shock_bp) * float(portfolio_cs01)) + (float(rate_shock_bp) * float(residual_dv01)))
        total_stress_pnl = rv_spread_pnl - float(liquidity_haircut)
        st.metric("Core RV stress P&L ($)", f"{rv_spread_pnl:,.0f}")
        st.metric("Total stress P&L ($)", f"{total_stress_pnl:,.0f}")

        return GlobalRVScreenState(
            universe_source=universe_source.lower(),
            fit_method=fit_method,
            fitted_curve_parameters={k: float(v) for k, v in fit.params.items()},
            bond_signals=bond_signals,
            curve_ranking=curve_order,
            sofr_asw_ranking=sofr_order,
            disagreement_diagnostics=disagreement_state,
            attribution_buckets_bp=attribution_buckets,
            portfolio_selection_signals={
                "long_candidates": long_candidates,
                "short_candidates": short_candidates,
                "composite_strength": composite_strength,
                "selection_style": "dual-residual-consensus",
            },
            residual_rmse_bp=float(fit.rmse_bp),
            rv_spread_pnl=float(rv_spread_pnl),
            total_stress_pnl=float(total_stress_pnl),
        )

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            signals=[
                "curve_ranking",
                "sofr_asw_ranking",
                "disagreement_diagnostics",
                "attribution_buckets_bp",
                "portfolio_selection_signals",
                "rv_spread_pnl",
                "total_stress_pnl",
            ],
            usage="Exports dual-ranking diagnostics and attribution buckets for portfolio selection while preserving Chapter 18 stress handoff.",
            schema_name="GlobalRVScreenState",
        )
