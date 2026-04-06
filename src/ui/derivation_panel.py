from __future__ import annotations

from typing import List

import streamlit as st

from .components import section_expander


def render_derivation_body(steps: List[str]) -> None:
    """Render derivation steps directly (no expander wrapper)."""
    if not steps:
        st.caption("No derivation steps available.")
        return
    for idx, step in enumerate(steps, start=1):
        st.markdown(f"{idx}. {step}")


def render_derivation_panel(steps: List[str]) -> None:
    """Render derivation steps inside a collapsible expander (legacy entry point)."""
    section_expander(
        "4) Derivation",
        expanded=False,
        icon="🧠",
        body=lambda: render_derivation_body(steps),
    )
