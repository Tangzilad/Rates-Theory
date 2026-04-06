from __future__ import annotations

import streamlit as st

from core.types import (
    DependencyEdgeState,
    DependencyMapState,
    DependencyNodeState,
    ShockNarrativeState,
)

from .base import ChapterBase


class Chapter10(ChapterBase):
    chapter_id = "10"

    def chapter_meta(self) -> dict[str, str]:
        return {
            "chapter": self.chapter_id,
            "title": "Chapter 10: Funding basis dependency map",
            "objective": "Map how bond, repo, benchmark-rate, and credit legs propagate through asset-swap and basis pricing decisions.",
        }

    def prerequisites(self) -> list[str]:
        return [
            "Cash bond valuation conventions",
            "Repo financing and balance-sheet frictions",
            "Cross-currency and intra-currency basis swap intuition",
            "Single-name/sovereign CDS spread interpretation",
        ]

    def concept_map(self) -> dict[str, list[str]]:
        return {
            "nodes": [
                "Bond",
                "Repo",
                "Reference rate",
                "Asset swap",
                "CDS",
                "Intra-currency basis swap",
                "Cross-currency basis swap",
            ],
            "edges": [
                "Bond->Asset swap",
                "Repo->Asset swap",
                "Reference rate->Intra-currency basis swap",
                "Reference rate->Cross-currency basis swap",
                "Asset swap->CDS",
                "Intra-currency basis swap->Cross-currency basis swap",
                "Cross-currency basis swap->Asset swap",
                "CDS->Bond",
            ],
        }

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {"name": "Asset-swap spread", "equation": "ASW_bp ≈ bond_zspread_bp - repo_specialness_bp + collateral/funding_adjustments_bp"},
            {"name": "CDS-bond basis", "equation": "CDS_Basis_bp = CDS_spread_bp - ASW_bp"},
            {"name": "Cross-currency all-in basis", "equation": "CCY_all_in_bp ≈ CCBS_quote_bp + intra_currency_basis_bp + FX_hedge_roll_bp"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Anchor the cash bond and repo legs to establish financing-adjusted bond carry.",
            "Translate benchmark conventions into intra-currency and cross-currency basis wedges.",
            "Reconcile funding-adjusted asset-swap valuation against CDS for residual credit basis.",
            "Push residual basis outputs into trade selection, hedge sizing, and stress testing.",
        ]

    @staticmethod
    def _dependency_nodes() -> list[DependencyNodeState]:
        return [
            DependencyNodeState(
                node_id="bond",
                label="Bond",
                required_inputs=["Clean price", "Coupon schedule", "Issuer curve / z-spread"],
                pricing_dependencies=["Repo", "Asset swap", "CDS"],
                downstream_outputs=["Funding-adjusted carry", "Cash-vs-derivative richness"],
            ),
            DependencyNodeState(
                node_id="repo",
                label="Repo",
                required_inputs=["GC rate", "Specialness", "Haircut / margin terms"],
                pricing_dependencies=["Bond"],
                downstream_outputs=["Financing drag", "Bond carry adjustment", "ASW fair-value shift"],
            ),
            DependencyNodeState(
                node_id="reference_rate",
                label="Reference rate",
                required_inputs=["OIS curve", "Term benchmark fixings", "Fallback conventions"],
                pricing_dependencies=["Intra-currency basis swap", "Cross-currency basis swap"],
                downstream_outputs=["Floating-leg discounting anchor", "Tenor-conversion adjustments"],
            ),
            DependencyNodeState(
                node_id="asset_swap",
                label="Asset swap",
                required_inputs=["Bond spread", "Swap curve", "Repo-adjusted carry"],
                pricing_dependencies=["Bond", "Repo", "Reference rate", "Cross-currency basis swap"],
                downstream_outputs=["ASW spread", "CDS-bond basis input", "Trade RV signal"],
            ),
            DependencyNodeState(
                node_id="cds",
                label="CDS",
                required_inputs=["CDS spread curve", "Recovery assumption", "Hazard term structure"],
                pricing_dependencies=["Bond", "Asset swap"],
                downstream_outputs=["CDS-bond basis", "Default-hedge cost", "Credit dislocation flag"],
            ),
            DependencyNodeState(
                node_id="intra_ccy_basis",
                label="Intra-currency basis swap",
                required_inputs=["Tenor pair quotes", "Collateral currency", "Reset lag conventions"],
                pricing_dependencies=["Reference rate"],
                downstream_outputs=["Tenor conversion wedge", "Swap-leg normalization"],
            ),
            DependencyNodeState(
                node_id="cross_ccy_basis",
                label="Cross-currency basis swap",
                required_inputs=["CCBS quotes", "FX forward points", "Collateral currency"],
                pricing_dependencies=["Reference rate", "Intra-currency basis swap", "Asset swap"],
                downstream_outputs=["Hedged foreign-asset carry", "Funding transfer price", "Relative-value gate"],
            ),
        ]

    @staticmethod
    def _dependency_edges() -> list[DependencyEdgeState]:
        return [
            DependencyEdgeState(source="bond", target="asset_swap", relation="cash leg into swap package"),
            DependencyEdgeState(source="repo", target="asset_swap", relation="financing cost adjustment"),
            DependencyEdgeState(source="reference_rate", target="intra_ccy_basis", relation="tenor benchmark anchor"),
            DependencyEdgeState(source="reference_rate", target="cross_ccy_basis", relation="discounting/forecasting base"),
            DependencyEdgeState(source="intra_ccy_basis", target="cross_ccy_basis", relation="tenor-to-overnight conversion"),
            DependencyEdgeState(source="cross_ccy_basis", target="asset_swap", relation="FX-hedged funding overlay"),
            DependencyEdgeState(source="asset_swap", target="cds", relation="cash-credit reconciliation"),
            DependencyEdgeState(source="cds", target="bond", relation="implied default premium feedback"),
        ]

    @staticmethod
    def _shock_narratives() -> list[ShockNarrativeState]:
        return [
            ShockNarrativeState(
                shock="Repo widening",
                transmission_path=[
                    "Repo specialness cheapens or GC rises versus policy rate",
                    "Bond financing drag increases",
                    "Asset-swap fair spread widens to compensate",
                ],
                required_reprice_nodes=["Repo", "Bond", "Asset swap", "CDS"],
                downstream_impact=["Lower carry", "Potential ASW cheapening signal", "Higher hedge notional for neutral carry"],
            ),
            ShockNarrativeState(
                shock="Cross-currency basis widening",
                transmission_path=[
                    "CCBS quote moves more negative for funding currency",
                    "FX-hedged foreign asset funding deteriorates",
                    "ASW and cross-market RV screens re-rank opportunities",
                ],
                required_reprice_nodes=["Cross-currency basis swap", "Reference rate", "Asset swap"],
                downstream_impact=["Reduced foreign bond attractiveness", "Shift toward domestic funding books", "Higher transfer-pricing add-on"],
            ),
            ShockNarrativeState(
                shock="Sovereign CDS widening",
                transmission_path=[
                    "Sovereign hazard premium reprices wider",
                    "CDS-bond basis shifts as cash lags or overreacts",
                    "Repo haircuts and balance-sheet usage can tighten simultaneously",
                ],
                required_reprice_nodes=["CDS", "Bond", "Repo", "Asset swap"],
                downstream_impact=["Credit hedge cost rises", "Potential basis dislocation signal", "Stress-loss contribution increases"],
            ),
        ]

    def interactive_lab(self) -> DependencyMapState:
        nodes = self._dependency_nodes()
        edges = self._dependency_edges()
        shocks = self._shock_narratives()
        node_by_label = {node.label: node for node in nodes}

        st.markdown("#### Funding basis dependency graph")
        st.caption("Click a node and section to inspect required inputs, pricing dependencies, and downstream outputs.")

        graph_rows = [f"- **{edge.source}** → **{edge.target}** ({edge.relation})" for edge in edges]
        with st.expander("View directed graph edges", expanded=True):
            for row in graph_rows:
                st.markdown(row)

        selected_label = st.radio("Select node", list(node_by_label.keys()), horizontal=True, key="node_10")
        selected_section = st.radio(
            "Select section",
            ["Required inputs", "Pricing dependencies", "Downstream outputs"],
            horizontal=True,
            key="section_10",
        )
        selected_node = node_by_label[selected_label]

        section_map = {
            "Required inputs": selected_node.required_inputs,
            "Pricing dependencies": selected_node.pricing_dependencies,
            "Downstream outputs": selected_node.downstream_outputs,
        }
        selected_items = section_map[selected_section]
        st.markdown(f"##### {selected_label} — {selected_section}")
        for item in selected_items:
            st.markdown(f"- {item}")

        with st.expander("Shock narratives", expanded=True):
            for narrative in shocks:
                st.markdown(f"**{narrative.shock}**")
                st.markdown("- Transmission path:")
                for step in narrative.transmission_path:
                    st.markdown(f"  - {step}")
                st.markdown(f"- Reprice nodes: {', '.join(narrative.required_reprice_nodes)}")
                st.markdown("- Downstream impact:")
                for impact in narrative.downstream_impact:
                    st.markdown(f"  - {impact}")

        return DependencyMapState(
            map_name="Funding basis dependency map",
            focal_node=selected_node.label,
            section_focus=selected_section,
            nodes=nodes,
            edges=edges,
            shock_narratives=shocks,
            signals=[
                "funding_basis_bp",
                "asset_swap_spread_bp",
                "cds_bond_basis_bp",
                "cross_currency_basis_bp",
            ],
            usage="Feeds Chapter 11+ with dependency-aware assumptions for benchmark transitions, ASW decomposition, and stress pathways.",
            schema_name="DependencyMapState",
        )

    def case_studies(self) -> list[dict[str, str]]:
        return [
            {
                "name": "Repo squeeze into quarter-end",
                "setup": "Special collateral pushes repo through GC while CDS stays range-bound.",
                "takeaway": "ASW can widen mechanically even without a true credit regime change.",
            },
            {
                "name": "Dollar funding stress",
                "setup": "Cross-currency basis widens as offshore USD demand spikes.",
                "takeaway": "FX-hedged foreign bond carry degrades; domestic substitutes screen richer but safer.",
            },
        ]

    def failure_modes(self) -> list[dict[str, str]]:
        return [
            {
                "mode": "Treating repo as static",
                "mitigation": "Reprice funding legs with scenario-specific repo and haircut assumptions.",
            },
            {
                "mode": "Ignoring CDS-bond basis regime shifts",
                "mitigation": "Cross-check cash and synthetic credit before attributing moves to pure rates basis.",
            },
        ]

    def assessment(self) -> list[dict[str, str]]:
        return [
            {
                "prompt": "If cross-currency basis widens while repo is unchanged, which node should reprice first?",
                "expected": "Cross-currency basis swap, then asset-swap economics for FX-hedged positions.",
            }
        ]

    def exports_to_next_chapter(self) -> DependencyMapState:
        nodes = self._dependency_nodes()
        return DependencyMapState(
            map_name="Funding basis dependency map",
            focal_node="Asset swap",
            section_focus="Pricing dependencies",
            nodes=nodes,
            edges=self._dependency_edges(),
            shock_narratives=self._shock_narratives(),
            signals=[
                "funding_basis_bp",
                "asset_swap_spread_bp",
                "cds_bond_basis_bp",
                "cross_currency_basis_bp",
            ],
            usage="Feeds benchmark-transition and asset-swap decomposition chapters with explicit dependency graph context.",
            schema_name="DependencyMapState",
        )
