from __future__ import annotations

from typing import Dict, List

import streamlit as st

from .components import section_expander


def _render_equation(expression: str) -> None:
    """Render an equation, using LaTeX when the expression contains LaTeX syntax."""
    latex_indicators = {"\\", "{", "}"}
    if any(c in expression for c in latex_indicators):
        st.latex(expression)
    else:
        st.code(expression, language=None)


def render_equation_cards_body(equations: List[Dict[str, str]]) -> None:
    """Render equation cards directly (no expander wrapper)."""
    if not equations:
        st.caption("No equations available.")
        return
    for item in equations:
        name = item.get("name", "Equation")
        expression = item.get("equation", "")
        with st.container(border=True):
            st.markdown(f"**{name}**")
            _render_equation(expression)


def render_equation_cards(equations: List[Dict[str, str]]) -> None:
    """Render chapter equation set inside a collapsible expander (legacy entry point)."""
    section_expander(
        "3) Technical equations",
        expanded=True,
        icon="🧮",
        body=lambda: render_equation_cards_body(equations),
    )
