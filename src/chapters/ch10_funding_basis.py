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
            "objective": "Build a dependency bridge across bond, repo, reference-rate, asset-swap, CDS, intra-currency basis, and cross-currency basis before deep-dives in Chapters 11–15.",
        }

    def key_takeaway(self) -> str:
        return "Relative-value signals are graph-dependent: each node (repo, benchmark, swap, CDS, basis) can contaminate the others if repricing paths are ignored."

    def learn_focus(self) -> list[str]:
        return [
            "This chapter is the map: later chapters zoom into each node but rely on this dependency order.",
            "Funding and benchmark assumptions propagate through asset-swap and CDS interpretations.",
            "Shock narratives clarify where to reprice first and where apparent opportunities can be mechanical.",
        ]

    def derive_focus(self) -> list[str]:
        return [
            "Encode market objects as graph nodes with required inputs and outputs.",
            "Draw directed edges to represent valuation transmission, not just conceptual similarity.",
            "Run shock paths to identify first-order repricing sequence.",
        ]

    def trade_use_focus(self) -> list[str]:
        return [
            "Use node-by-node diagnostics before entering RV trades.",
            "When a shock hits, reprice nodes in dependency order to avoid attribution errors.",
            "Use graph outputs as assumptions handoff to benchmark, CDS, and basis chapters.",
        ]

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
            {"name": "Intra-currency basis", "equation": "ICBS_bp ≈ tenor_leg_a_bp - tenor_leg_b_bp - benchmark_conversion_adjustments_bp"},
            {"name": "Cross-currency all-in basis", "equation": "CCY_all_in_bp ≈ CCBS_quote_bp + ICBS_bp + FX_hedge_roll_bp"},
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Anchor bond and repo legs to construct financing-adjusted cash carry.",
            "Translate benchmark conventions into intra-currency and cross-currency basis wedges.",
            "Reconcile asset-swap valuation against CDS to isolate residual credit/funding basis.",
            "Propagate shocks along graph edges and update downstream trade rankings.",
            "Export graph signals so Chapters 11–15 can zoom in with consistent assumptions.",
        ]

    @staticmethod
    def _dependency_nodes() -> list[DependencyNodeState]:
        return [
            DependencyNodeState(
                node_id="bond",
                label="Bond",
                required_inputs=["Clean price", "Coupon schedule", "Issuer curve / z-spread"],
                pricing_dependencies=["Repo", "Asset swap", "CDS"],
                downstream_outputs=["Funding-adjusted carry", "Cash-vs-derivative richness", "Input to Chapter 12 ASW decomposition"],
            ),
            DependencyNodeState(
                node_id="repo",
                label="Repo",
                required_inputs=["GC rate", "Specialness", "Haircut / margin terms"],
                pricing_dependencies=["Bond"],
                downstream_outputs=["Financing drag", "Bond carry adjustment", "Chapter 11 repo-reference wedge"],
            ),
            DependencyNodeState(
                node_id="reference_rate",
                label="Reference rate",
                required_inputs=["Secured curve", "Unsecured curve", "Fallback conventions"],
                pricing_dependencies=["Intra-currency basis swap", "Cross-currency basis swap"],
                downstream_outputs=["Benchmark decomposition", "Floating-leg forecast anchor for Chapter 11"],
            ),
            DependencyNodeState(
                node_id="asset_swap",
                label="Asset swap",
                required_inputs=["Bond spread", "Swap curve", "Repo-adjusted carry"],
                pricing_dependencies=["Bond", "Repo", "Reference rate", "Cross-currency basis swap"],
                downstream_outputs=["ASW spread", "CDS-bond basis input", "Chapter 12 package analytics"],
            ),
            DependencyNodeState(
                node_id="cds",
                label="CDS",
                required_inputs=["CDS spread curve", "Recovery assumption", "Hazard term structure"],
                pricing_dependencies=["Bond", "Asset swap"],
                downstream_outputs=["CDS-bond basis", "Default-hedge cost", "Chapter 13 pure-credit extraction"],
            ),
            DependencyNodeState(
                node_id="intra_ccy_basis",
                label="Intra-currency basis swap",
                required_inputs=["Tenor pair quotes", "Collateral currency", "Reset lag conventions"],
                pricing_dependencies=["Reference rate"],
                downstream_outputs=["Tenor conversion wedge", "Carry/rolldown input for Chapter 14"],
            ),
            DependencyNodeState(
                node_id="cross_ccy_basis",
                label="Cross-currency basis swap",
                required_inputs=["CCBS quotes", "FX forward points", "Collateral currency"],
                pricing_dependencies=["Reference rate", "Intra-currency basis swap", "Asset swap"],
                downstream_outputs=["Hedged foreign-asset carry", "Funding transfer price", "Chapter 15 synthetic yield diagnostics"],
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
                    "Asset-swap fair spread widens",
                    "CDS-bond basis interpretation may flip from credit story to funding story",
                ],
                required_reprice_nodes=["Repo", "Bond", "Asset swap", "CDS"],
                downstream_impact=["Lower carry", "Potential ASW cheapening signal", "Higher hedge notional for neutral carry"],
            ),
            ShockNarrativeState(
                shock="Reference benchmark transition shock",
                transmission_path=[
                    "Secured/unsecured curve gap shifts",
                    "Intra-currency tenor conversion reprices",
                    "Cross-currency basis and hedged carry rankings move",
                ],
                required_reprice_nodes=["Reference rate", "Intra-currency basis swap", "Cross-currency basis swap", "Asset swap"],
                downstream_impact=["Changed discounting anchor", "Different cross-market ranking", "Rebased ASW screening outputs"],
            ),
            ShockNarrativeState(
                shock="Sovereign CDS widening",
                transmission_path=[
                    "Hazard premium reprices",
                    "CDS-bond basis shifts as cash lags/overshoots",
                    "Repo haircuts and execution capacity tighten",
                ],
                required_reprice_nodes=["CDS", "Bond", "Repo", "Asset swap"],
                downstream_impact=["Higher hedge cost", "Potential basis dislocation signal", "Lower executable capacity"],
            ),
        ]

    def interactive_lab(self) -> DependencyMapState:
        nodes = self._dependency_nodes()
        edges = self._dependency_edges()
        shocks = self._shock_narratives()
        node_by_label = {node.label: node for node in nodes}

        st.markdown("#### Why this chapter matters")
        st.info("This chapter is the conceptual bridge from early-rate analytics into benchmark, CDS, and basis chapters. Use it to understand repricing order before calculating edge.")

        st.markdown("#### Funding basis dependency graph")
        with st.expander("View directed graph edges", expanded=True):
            for edge in edges:
                st.markdown(f"- **{edge.source}** → **{edge.target}** ({edge.relation})")

        selected_label = st.radio("Select node", list(node_by_label.keys()), horizontal=True, key="node_10")
        selected_section = st.radio("Inspect", ["Required inputs", "Pricing dependencies", "Downstream outputs"], horizontal=True, key="section_10")
        selected_node = node_by_label[selected_label]

        section_map = {
            "Required inputs": selected_node.required_inputs,
            "Pricing dependencies": selected_node.pricing_dependencies,
            "Downstream outputs": selected_node.downstream_outputs,
        }
        st.markdown(f"##### {selected_label} — {selected_section}")
        for item in section_map[selected_section]:
            st.markdown(f"- {item}")

        st.markdown("#### Shock propagation narratives")
        for narrative in shocks:
            with st.container(border=True):
                st.markdown(f"**{narrative.shock}**")
                st.markdown("Transmission path:")
                for step in narrative.transmission_path:
                    st.markdown(f"- {step}")
                st.caption(f"Reprice nodes: {', '.join(narrative.required_reprice_nodes)}")

        return DependencyMapState(
            map_name="Funding basis dependency map",
            focal_node=selected_node.label,
            section_focus=selected_section,
            nodes=nodes,
            edges=edges,
            shock_narratives=shocks,
            signals=["funding_basis_bp", "asset_swap_spread_bp", "cds_bond_basis_bp", "cross_currency_basis_bp"],
            usage="Feeds Chapters 11-15 with dependency-aware assumptions for benchmark selection, CDS purification, and basis package construction.",
            schema_name="DependencyMapState",
        )

    def case_studies(self) -> list[dict[str, str]]:
        return [
            {
                "name": "Quarter-end repo squeeze",
                "setup": "Special collateral pushes repo through GC while benchmark curves are stable.",
                "takeaway": "ASW widening can be mechanical funding transmission, not fresh credit deterioration.",
            },
            {
                "name": "USD funding stress with CCBS widening",
                "setup": "Cross-currency basis becomes more negative as offshore USD demand spikes.",
                "takeaway": "FX-hedged foreign carry degrades and Chapter 15 synthetic-yield rankings reorder quickly.",
            },
        ]

    def failure_modes(self) -> list[dict[str, str]]:
        return [
            {"mode": "Reading one node in isolation", "mitigation": "Trace dependency edges before assigning causality."},
            {"mode": "Repricing in arbitrary order", "mitigation": "Use shock narratives to follow first-order transmission sequence."},
            {"mode": "Ignoring chapter handoffs", "mitigation": "Use explicit downstream outputs to align assumptions with Chapters 11-15."},
        ]

    def assessment(self) -> list[dict[str, str]]:
        return [
            {
                "prompt": "If reference-rate conventions shift but repo is stable, which chapters are most immediately affected?",
                "expected": "Chapter 11 first, then Chapters 14-15 via benchmark and basis conversion assumptions.",
            }
        ]

    def exports_to_next_chapter(self) -> DependencyMapState:
        return DependencyMapState(
            map_name="Funding basis dependency map",
            focal_node="Asset swap",
            section_focus="Pricing dependencies",
            nodes=self._dependency_nodes(),
            edges=self._dependency_edges(),
            shock_narratives=self._shock_narratives(),
            signals=["funding_basis_bp", "asset_swap_spread_bp", "cds_bond_basis_bp", "cross_currency_basis_bp"],
            usage="Feeds benchmark-transition and asset-swap decomposition chapters with dependency-map context and shock pathways.",
            schema_name="DependencyMapState",
        )
