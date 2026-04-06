from __future__ import annotations

from typing import Dict, List

import streamlit as st

from .components import section_expander


def render_quiz_body(assessment: List[Dict[str, str]], key_prefix: str = "") -> None:
    """Render quiz questions with per-question reveal (no expander wrapper)."""
    if not assessment:
        st.caption("No assessment prompts available.")
        return

    for idx, item in enumerate(assessment, start=1):
        prompt = item.get("prompt", "Prompt unavailable")
        expected = item.get("expected", "Expected direction unavailable")
        reveal_key = f"quiz_reveal_{key_prefix}_{idx}"

        with st.container(border=True):
            st.markdown(f"**Q{idx}. {prompt}**")
            if st.button("Show answer", key=f"btn_{reveal_key}"):
                st.session_state[reveal_key] = True
            if st.session_state.get(reveal_key):
                st.success(f"**Expected direction:** {expected}")


def render_quiz_panel(assessment: List[Dict[str, str]]) -> None:
    """Render assessment inside a collapsible expander (legacy entry point)."""
    section_expander(
        "8) Checkpoint",
        expanded=False,
        icon="✅",
        body=lambda: render_quiz_body(assessment),
    )
