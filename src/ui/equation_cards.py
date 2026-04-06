from __future__ import annotations

from typing import Dict, List

import streamlit as st

from .components import section_expander


def render_equation_cards(equations: List[Dict[str, str]]) -> None:
    """Render chapter equation set using consistent card-like containers."""

    def _body() -> None:
        if not equations:
            st.caption("No equations available.")
            return

        for item in equations:
            name = item.get("name", "Equation")
            expression = item.get("equation", "")
            with st.container(border=True):
                st.markdown(f"**{name}**")
                st.code(expression)

    section_expander("Equations", expanded=True, icon="🧮", body=_body)
