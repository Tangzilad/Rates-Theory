from __future__ import annotations

from dataclasses import is_dataclass
from typing import Any, Callable, Iterable, List, Dict

import streamlit as st


def normalize_payload(payload: Any) -> Any:
    """Normalize dataclass-like payloads for consistent Streamlit display."""
    if is_dataclass(payload):
        return payload.model_dump() if hasattr(payload, "model_dump") else payload
    return payload


def render_json_payload(payload: Any) -> None:
    """Render payload using json when structure exists, otherwise fallback to text."""
    normalized = normalize_payload(payload)
    if isinstance(normalized, (dict, list)):
        st.json(normalized)
    else:
        st.write(normalized)


def render_bulleted_lines(lines: Iterable[str], empty_message: str = "No content available.") -> None:
    values = list(lines)
    if values:
        for line in values:
            st.markdown(f"- {line}")
    else:
        st.caption(empty_message)


def render_struct_cards(
    items: List[Dict[str, str]],
    primary_key: str,
    secondary_key: str | None = None,
    empty_message: str = "No items available.",
) -> None:
    """Render a list of dicts as bordered cards with a bolded primary field and optional secondary."""
    if not items:
        st.caption(empty_message)
        return
    for item in items:
        if not isinstance(item, dict):
            continue
        with st.container(border=True):
            primary = item.get(primary_key, "")
            if primary:
                st.markdown(f"**{primary}**")
            if secondary_key:
                secondary = item.get(secondary_key, "")
                if secondary:
                    st.markdown(secondary)


def section_expander(
    label: str,
    *,
    expanded: bool = False,
    icon: str | None = None,
    body: Callable[[], None],
) -> None:
    """Standardized expander used by all chapter presentation panels."""
    with st.expander(label, expanded=expanded, icon=icon):
        body()
