"""Rates Theory — unified study interface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
from core.diagnostics import validate_boundary
from core.types import FactorState, MeanReversionState, RelativeValueState, RiskMetricState
from src.chapter_summary_schema import (
    ChapterSummarySchemaError,
    document_to_chapter_map,
    parse_chapters_map,
)
from src.chapters.registry import (
    build_chapter_registry,
    get_chapter,
    validate_chapter_dependencies,
)
from src.ui.components import render_bulleted_lines, render_json_payload, render_struct_cards
from src.ui.derivation_panel import render_derivation_body
from src.ui.equation_cards import render_equation_cards_body
from src.ui.quiz_panel import render_quiz_body

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Rates Theory Lab",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Curriculum structure ───────────────────────────────────────────────────────

CURRICULUM_GROUPS: List[Tuple[str, List[str]]] = [
    ("Foundations", ["1", "2", "3"]),
    ("Factor Models", ["4", "5", "6"]),
    ("Risk & Screening", ["7", "8", "9"]),
    ("Funding & Basis", ["10", "11", "12"]),
    ("Credit & Cross-Currency", ["13", "14", "15"]),
    ("Integrated Strategies", ["16", "17", "18"]),
]

CHAPTER_BOUNDARY_RULES: Dict[str, Dict[str, type]] = {
    "2": {"1": RelativeValueState},
    "3": {"2": MeanReversionState},
    "5": {"3": FactorState},
    "8": {"5": RiskMetricState},
    "9": {"2": MeanReversionState, "3": FactorState, "5": RiskMetricState},
}

# Accumulated lab exports shared across chapters within one session.
upstream_exports: Dict[str, Any] = {}


# ── Data loading ───────────────────────────────────────────────────────────────

def load_primary_chapters() -> Tuple[Dict[str, dict], Optional[str]]:
    json_path = Path(__file__).resolve().parent.parent / "data" / "chapters.json"
    try:
        with json_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        return parse_chapters_map(payload), None
    except FileNotFoundError:
        return {}, f"Required chapter content file not found at {json_path}."
    except (json.JSONDecodeError, OSError) as exc:
        return {}, f"Could not parse chapter content JSON ({exc})."
    except ChapterSummarySchemaError as exc:
        return {}, str(exc)


def load_parser_helper_metadata() -> Tuple[Dict[str, dict], Optional[str]]:
    json_path = Path(__file__).resolve().parent.parent / "data" / "chapter_summaries.json"
    if not json_path.exists():
        return {}, None
    try:
        with json_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        if not isinstance(payload, dict) or "schema_version" not in payload:
            raise ChapterSummarySchemaError(
                "Optional parser helper metadata must use schema v1.0 with 'schema_version'."
            )
        return document_to_chapter_map(payload), None
    except (json.JSONDecodeError, OSError) as exc:
        return {}, f"Could not parse optional parser helper metadata ({exc})."
    except ChapterSummarySchemaError as exc:
        return {}, str(exc)


def merge_parser_helper_metadata(
    primary: Dict[str, dict], parser_helper: Dict[str, dict]
) -> Dict[str, dict]:
    merged: Dict[str, dict] = {}
    for key, chapter in primary.items():
        merged_chapter = dict(chapter)
        helper = parser_helper.get(key)
        if helper:
            merged_chapter["helper_metadata"] = {
                "parser_summary": helper.get("summary", ""),
                "parser_quotes": helper.get("quotes", []),
            }
        merged[key] = merged_chapter
    return merged


def chapter_key_sorter(k: str) -> Tuple[int, str]:
    if k.isdigit():
        return int(k), ""
    return 10_000, k


# ── Contract field resolver ────────────────────────────────────────────────────

def _resolve(
    chapter: Any,
    chapter_data: Dict[str, Any],
    method_name: str,
    fallback_fields: List[str],
    default: Any,
) -> Any:
    """Prefer chapter-module methods; fall back to JSON data fields."""
    if hasattr(chapter, method_name):
        try:
            candidate = getattr(chapter, method_name)
            value = candidate() if callable(candidate) else candidate
            if value not in (None, "", [], {}):
                return value
        except Exception:
            pass
    for field in fallback_fields:
        candidate = chapter_data.get(field)
        if candidate not in (None, "", [], {}):
            return candidate
    return default


# ── Sidebar ────────────────────────────────────────────────────────────────────

def render_sidebar(
    chapter_data_map: Dict[str, dict],
    chapter_keys: List[str],
) -> Tuple[str, bool]:
    """Render the grouped curriculum sidebar. Returns (selected_key, study_mode)."""

    with st.sidebar:
        st.markdown("## Rates Theory Lab")
        st.caption("Fixed income fundamentals to integrated strategies")
        st.divider()

        study_mode: bool = st.toggle(
            "Study Mode",
            value=st.session_state.get("study_mode", True),
            help="Study Mode hides raw state, parser metadata, and advanced derivation detail.",
        )
        st.session_state["study_mode"] = study_mode

        if study_mode:
            st.caption("Study Mode — clean narrative view")
        else:
            st.caption("Advanced Mode — full diagnostics exposed")

        st.divider()
        st.caption("CURRICULUM")

        # Find which group contains the current chapter.
        current_key = st.session_state.get("selected_chapter", chapter_keys[0] if chapter_keys else "1")

        for group_name, group_keys in CURRICULUM_GROUPS:
            available = [k for k in group_keys if k in chapter_data_map]
            if not available:
                continue
            group_is_active = current_key in available
            with st.expander(group_name, expanded=group_is_active):
                for k in available:
                    raw_title = chapter_data_map[k].get("title", f"Chapter {k}")
                    short = raw_title.split(": ", 1)[-1] if ": " in raw_title else raw_title
                    is_current = k == current_key
                    btn_label = f"**Ch.{k}** — {short}" if is_current else f"Ch.{k} — {short}"
                    if st.button(
                        btn_label,
                        key=f"nav_{k}",
                        use_container_width=True,
                        type="primary" if is_current else "secondary",
                    ):
                        st.session_state["selected_chapter"] = k
                        st.rerun()

        st.divider()
        completed = st.session_state.get("chapter_exports", {})
        n_done = len(completed)
        n_total = len(chapter_keys)
        st.caption(f"Progress: {n_done}/{n_total} labs run")
        if n_done:
            st.progress(n_done / n_total)

    return current_key, study_mode


# ── Chapter header ─────────────────────────────────────────────────────────────

def render_chapter_header(
    selected_key: str,
    chapter_keys: List[str],
    chapter_data: Dict[str, Any],
    chapter_meta: Dict[str, Any],
    chapter: Any,
    study_mode: bool,
) -> None:
    idx = chapter_keys.index(selected_key) if selected_key in chapter_keys else 0
    prev_key = chapter_keys[idx - 1] if idx > 0 else None
    next_key = chapter_keys[idx + 1] if idx < len(chapter_keys) - 1 else None

    nav_left, title_col, nav_right = st.columns([1, 6, 1])
    with nav_left:
        if prev_key:
            if st.button("← Prev", use_container_width=True):
                st.session_state["selected_chapter"] = prev_key
                st.rerun()
    with title_col:
        st.header(chapter_meta.get("title", chapter_data.get("title", "Chapter")))
    with nav_right:
        if next_key:
            if st.button("Next →", use_container_width=True):
                st.session_state["selected_chapter"] = next_key
                st.rerun()

    # Objective
    objective = chapter_meta.get("objective", chapter_data.get("learning_objective", ""))
    if objective:
        st.markdown(f"**Objective:** {objective}")

    # Prerequisites + exports inline badges
    prereqs = _resolve(chapter, chapter_data, "prerequisites", ["prerequisites"], [])
    exports = _resolve(
        chapter, chapter_data, "exports_to_next_chapter", ["exports_to_next_chapter"], {}
    )

    badge_left, badge_right = st.columns(2)
    with badge_left:
        if prereqs:
            prereq_text = " · ".join(f"`{p}`" for p in prereqs)
            st.caption(f"**Prerequisites:** {prereq_text}")
    with badge_right:
        if isinstance(exports, list) and exports:
            export_text = "  ".join(f"`{e}`" for e in exports)
            st.caption(f"**Exports:** {export_text}")
        elif isinstance(exports, dict) and exports.get("signals"):
            export_text = "  ".join(f"`{e}`" for e in exports["signals"])
            st.caption(f"**Exports:** {export_text}")

    st.divider()


# ── Tab renderers ──────────────────────────────────────────────────────────────

def render_learn_tab(
    chapter: Any,
    chapter_data: Dict[str, Any],
    study_mode: bool,
) -> None:
    summary = chapter_data.get("summary", chapter.chapter_meta().get("objective", ""))
    if summary:
        st.markdown(summary)

    core_claim = _resolve(
        chapter, chapter_data, "core_claim", ["core_claim", "learning_objective"], ""
    )
    if core_claim:
        st.info(f"**Core claim:** {core_claim}")

    quotes = chapter_data.get("quotes", [])
    if quotes:
        st.markdown("")
        for q in quotes:
            st.markdown(f"> *{q}*")

    st.markdown("---")
    st.subheader("Market Objects")
    market_objects = _resolve(chapter, chapter_data, "market_objects", ["market_objects"], [])
    if market_objects:
        cols = st.columns(min(4, len(market_objects)))
        for i, obj in enumerate(market_objects):
            cols[i % len(cols)].markdown(f"**{obj}**")
    else:
        st.caption("No market objects defined.")

    st.markdown("---")
    st.subheader("Common Confusions")
    failure_modes = _resolve(
        chapter, chapter_data, "failure_modes_model_risk", ["failure_modes"], []
    )
    limit = 2 if study_mode else len(failure_modes)
    shown = failure_modes[:limit] if isinstance(failure_modes, list) else []
    if shown:
        for fm in shown:
            if isinstance(fm, dict):
                st.warning(f"**{fm.get('mode', '')}** — {fm.get('mitigation', '')}")
    else:
        st.caption("No common confusions listed.")

    if not study_mode:
        helper = chapter_data.get("helper_metadata", {})
        if helper:
            with st.expander("Parser-derived metadata", expanded=False):
                if helper.get("parser_summary"):
                    st.write(helper["parser_summary"])
                for q in helper.get("parser_quotes", []):
                    st.markdown(f"- {q}")


def render_derive_tab(
    chapter: Any,
    chapter_data: Dict[str, Any],
    study_mode: bool,
) -> None:
    st.subheader("Key Equations")
    equations = _resolve(
        chapter, chapter_data, "technical_equations", ["equations", "technical_equations"], []
    )
    render_equation_cards_body(equations)

    st.markdown("---")
    st.subheader("Derivation Steps")
    derivation = _resolve(
        chapter, chapter_data, "derivation", ["derivation_steps", "step_by_step_derivation"], []
    )
    render_derivation_body(derivation)

    if not study_mode:
        exports = _resolve(
            chapter, chapter_data, "exports_to_next_chapter", ["exports_to_next_chapter"], {}
        )
        with st.expander("Output construction — exported signals", expanded=False):
            render_json_payload(exports)

        concept_map = chapter.concept_map() if hasattr(chapter, "concept_map") else {}
        if concept_map:
            with st.expander("Concept map (nodes / edges)", expanded=False):
                render_json_payload(concept_map)


def render_lab_tab(
    selected_key: str,
    chapter: Any,
    chapter_data: Dict[str, Any],
    study_mode: bool,
) -> None:
    errors = validate_boundary(
        selected_key,
        CHAPTER_BOUNDARY_RULES.get(selected_key, {}),
        upstream_exports,
    )
    if errors:
        st.error("Upstream export validation failed — run prerequisite chapter labs first.")
        for err in errors:
            st.markdown(f"- {err}")
        return

    try:
        lab_payload = chapter.interactive_lab()
    except Exception as exc:
        st.error(f"Lab could not be rendered: {exc}")
        return

    upstream_exports[selected_key] = lab_payload
    if "chapter_exports" not in st.session_state:
        st.session_state["chapter_exports"] = {}
    st.session_state["chapter_exports"][selected_key] = lab_payload

    if not study_mode:
        with st.expander("Inspect lab state (raw output)", expanded=False):
            render_json_payload(lab_payload)


def render_trade_use_tab(
    selected_key: str,
    chapter: Any,
    chapter_data: Dict[str, Any],
    chapter_keys: List[str],
    chapter_data_map: Dict[str, dict],
) -> None:
    st.subheader("Output Interpretation")
    trade_interp = _resolve(
        chapter, chapter_data, "trade_interpretation", ["trade_interpretation"], []
    )
    if isinstance(trade_interp, list) and trade_interp:
        for item in trade_interp:
            st.markdown(f"- {item}")
    else:
        st.caption("No trade interpretation defined.")

    st.markdown("---")
    st.subheader("Desk Relevance")
    case_studies: list = []
    if hasattr(chapter, "case_studies"):
        try:
            case_studies = chapter.case_studies() or []
        except Exception:
            pass
    if case_studies:
        for cs in case_studies:
            if not isinstance(cs, dict):
                continue
            with st.container(border=True):
                st.markdown(f"**{cs.get('name', 'Case Study')}**")
                if cs.get("setup"):
                    st.caption(cs["setup"])
                if cs.get("takeaway"):
                    st.success(cs["takeaway"])
    else:
        st.caption("No case studies available.")

    st.markdown("---")
    st.subheader("Feeds Into Next Chapter")
    exports = _resolve(
        chapter, chapter_data, "exports_to_next_chapter", ["exports_to_next_chapter"], {}
    )
    if isinstance(exports, list) and exports:
        st.markdown("  ".join(f"`{e}`" for e in exports))
    elif isinstance(exports, dict):
        signals = exports.get("signals", [])
        if signals:
            st.markdown("  ".join(f"`{e}`" for e in signals))
        if exports.get("usage"):
            st.caption(exports["usage"])
    else:
        st.caption("No exports defined.")

    idx = chapter_keys.index(selected_key) if selected_key in chapter_keys else 0
    next_key = chapter_keys[idx + 1] if idx < len(chapter_keys) - 1 else None
    if next_key and next_key in chapter_data_map:
        next_title = chapter_data_map[next_key].get("title", f"Chapter {next_key}")
        st.caption(f"**Next chapter:** {next_title}")


def render_risks_tab(
    chapter: Any,
    chapter_data: Dict[str, Any],
    study_mode: bool,
) -> None:
    st.subheader("Failure Modes & Model Risk")
    failure_modes = _resolve(
        chapter, chapter_data, "failure_modes_model_risk", ["failure_modes"], []
    )
    if isinstance(failure_modes, list) and failure_modes:
        render_struct_cards(failure_modes, primary_key="mode", secondary_key="mitigation",
                            empty_message="No failure modes listed.")
    elif isinstance(failure_modes, dict):
        render_json_payload(failure_modes)
    else:
        st.caption("No failure modes listed.")

    st.markdown("---")
    st.subheader("Assumptions & Prerequisites")
    prereqs: list = []
    if hasattr(chapter, "prerequisites"):
        try:
            prereqs = chapter.prerequisites() or []
        except Exception:
            pass
    if not prereqs:
        prereqs = chapter_data.get("prerequisites", [])
    render_bulleted_lines(prereqs, empty_message="No prerequisites listed.")

    if not study_mode:
        helper = chapter_data.get("helper_metadata", {})
        if helper:
            with st.expander("Parser metadata / caveats", expanded=False):
                render_json_payload(helper)


def render_checkpoint_tab(
    selected_key: str,
    chapter: Any,
    chapter_data: Dict[str, Any],
) -> None:
    # Recap strip
    core_claim = _resolve(
        chapter, chapter_data, "core_claim", ["core_claim", "learning_objective"], ""
    )
    if core_claim:
        st.markdown(f"**Core claim:** {core_claim}")

    market_objects = _resolve(chapter, chapter_data, "market_objects", ["market_objects"], [])
    if market_objects:
        st.markdown("**Key concepts:** " + " · ".join(f"`{c}`" for c in market_objects))

    st.markdown("---")
    st.subheader("Quiz")
    assessment = _resolve(
        chapter, chapter_data, "checkpoint", ["checkpoint_assessment"], []
    )
    render_quiz_body(assessment, key_prefix=selected_key)

    # Show recap of answered questions
    answered = [
        f"quiz_reveal_{selected_key}_{i}"
        for i in range(1, len(assessment) + 1)
        if st.session_state.get(f"quiz_reveal_{selected_key}_{i}")
    ]
    if answered:
        st.caption(f"{len(answered)}/{len(assessment)} question(s) revealed")


# ── Dependency validation banner ───────────────────────────────────────────────

def check_dependencies(selected_key: str, registry: dict, validation_result: Any) -> bool:
    """Show dependency errors. Returns False if a hard blocker prevents loading."""
    blocking = validation_result.blocking_issues_for(selected_key)
    errors = [i for i in blocking if i.severity == "error"]
    warnings = [i for i in blocking if i.severity == "warning"]

    if warnings:
        with st.expander(f"{len(warnings)} dependency warning(s)", expanded=False):
            for w in warnings:
                st.markdown(f"- Ch.{w.chapter}: {w.message}")

    if errors:
        st.error("Chapter dependency errors — resolve before loading:")
        for e in errors:
            st.markdown(f"- **Ch.{e.chapter}:** {e.message}")
        return False
    return True


# ── Main ───────────────────────────────────────────────────────────────────────

# Load data
chapter_data_map, chapter_summary_error = load_primary_chapters()
if chapter_summary_error:
    st.error(chapter_summary_error)
    st.stop()

parser_metadata_map, parser_metadata_error = load_parser_helper_metadata()
if parser_metadata_error:
    st.warning(parser_metadata_error)
chapter_data_map = merge_parser_helper_metadata(chapter_data_map, parser_metadata_map)

chapter_keys = sorted(chapter_data_map.keys(), key=chapter_key_sorter)

# Initialise session state
if "selected_chapter" not in st.session_state:
    st.session_state["selected_chapter"] = chapter_keys[0] if chapter_keys else "1"

# Sidebar — returns the active key and mode flag
selected_key, study_mode = render_sidebar(chapter_data_map, chapter_keys)
chapter_data = chapter_data_map.get(selected_key, {})

# Registry & chapter object
registry = build_chapter_registry()
validation_result = validate_chapter_dependencies(registry)
chapter = get_chapter(selected_key, registry, validation_result=validation_result)
chapter_meta = chapter.chapter_meta()

# ── Header ─────────────────────────────────────────────────────────────────────

render_chapter_header(
    selected_key, chapter_keys, chapter_data, chapter_meta, chapter, study_mode
)

# ── Dependency check ────────────────────────────────────────────────────────────

if not check_dependencies(selected_key, registry, validation_result):
    st.stop()

# ── Tabs ────────────────────────────────────────────────────────────────────────

tab_learn, tab_derive, tab_lab, tab_trade, tab_risks, tab_checkpoint = st.tabs(
    ["Learn", "Derive", "Lab", "Trade Use", "Risks", "Checkpoint"]
)

with tab_learn:
    render_learn_tab(chapter, chapter_data, study_mode)

with tab_derive:
    render_derive_tab(chapter, chapter_data, study_mode)

with tab_lab:
    render_lab_tab(selected_key, chapter, chapter_data, study_mode)

with tab_trade:
    render_trade_use_tab(selected_key, chapter, chapter_data, chapter_keys, chapter_data_map)

with tab_risks:
    render_risks_tab(chapter, chapter_data, study_mode)

with tab_checkpoint:
    render_checkpoint_tab(selected_key, chapter, chapter_data)
