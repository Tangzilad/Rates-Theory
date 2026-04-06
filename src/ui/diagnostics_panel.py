from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from .components import render_json_payload, section_expander


def _render_struct_list(items: List[Dict[str, str]], empty_message: str) -> None:
    if not items:
        st.caption(empty_message)
        return

    for item in items:
        with st.container(border=True):
            for key, value in item.items():
                st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")


def render_diagnostics_panel(
    *,
    prerequisites: List[str],
    concept_map: Dict[str, List[str]],
    case_studies: List[Dict[str, str]],
    failure_modes: List[Dict[str, str]],
    exports: Any,
) -> None:
    """Render standardized diagnostics and context panels for chapter contracts."""

    section_expander(
        "Prerequisites",
        expanded=False,
        icon="📚",
        body=lambda: render_json_payload(prerequisites),
    )
    section_expander(
        "Concept Map",
        expanded=False,
        icon="🗺️",
        body=lambda: render_json_payload(concept_map),
    )
    section_expander(
        "Case Studies",
        expanded=False,
        icon="🧩",
        body=lambda: _render_struct_list(case_studies, "No case studies available."),
    )
    section_expander(
        "Failure Modes",
        expanded=False,
        icon="⚠️",
        body=lambda: _render_struct_list(failure_modes, "No failure modes available."),
    )
    section_expander(
        "Exports",
        expanded=False,
        icon="📦",
        body=lambda: render_json_payload(exports),
    )
