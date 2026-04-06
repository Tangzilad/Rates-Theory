from __future__ import annotations

from typing import Dict, List

import streamlit as st

from .components import section_expander


def render_quiz_panel(assessment: List[Dict[str, str]]) -> None:
    """Render chapter assessment content in a consistent Q/A panel."""

    def _body() -> None:
        if not assessment:
            st.caption("No assessment prompts available.")
            return

        for idx, item in enumerate(assessment, start=1):
            prompt = item.get("prompt", "Prompt unavailable")
            expected = item.get("expected", "Expected direction unavailable")
            with st.container(border=True):
                st.markdown(f"**Q{idx}. {prompt}**")
                st.markdown(f"_Expected direction:_ {expected}")

    section_expander("Assessment", expanded=False, icon="✅", body=_body)
