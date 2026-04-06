from __future__ import annotations

from typing import List

import streamlit as st

from .components import section_expander


def render_derivation_panel(steps: List[str]) -> None:
    """Render derivation steps in a consistent ordered format."""

    def _body() -> None:
        if not steps:
            st.caption("No derivation steps available.")
            return

        for idx, step in enumerate(steps, start=1):
            st.markdown(f"{idx}. {step}")

    section_expander("Derivation", expanded=False, icon="🧠", body=_body)
