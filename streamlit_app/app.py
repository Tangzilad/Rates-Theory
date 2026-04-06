import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import streamlit as st
from core.diagnostics import validate_boundary
from core.types import (
    ExecutableTradeState,
    FactorState,
    MeanReversionState,
    RiskMetricState,
)
from src.chapter_summary_schema import (
    ChapterSummarySchemaError,
    document_to_chapter_map,
    parse_chapters_map,
)

from src.chapters.registry import build_chapter_registry, get_chapter, validate_chapter_dependencies


st.set_page_config(page_title="Rates Theory Lab", layout="wide")


def load_primary_chapters() -> Tuple[Dict[str, dict], Optional[str]]:
    """Load curated chapter content from data/chapters.json."""
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
    """Load optional parser-derived helper metadata from data/chapter_summaries.json."""
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


def render_chapter_header(chapter_data: dict, chapter_meta: dict) -> None:
    st.header(chapter_meta.get("title", chapter_data.get("title", "Chapter")))
    st.write(chapter_data.get("summary", chapter_meta.get("objective", "No summary available.")))
    learning_objective = chapter_data.get("learning_objective")
    if learning_objective:
        st.caption(f"Learning objective: {learning_objective}")
    quotes = chapter_data.get("quotes", [])
    with st.expander("Key quotes"):
        if quotes:
            for q in quotes:
                st.markdown(f"- {q}")
        else:
            st.write("No quotes available.")
    helper = chapter_data.get("helper_metadata", {})
    if helper:
        with st.expander("Parser-derived helper metadata (optional)"):
            parser_summary = helper.get("parser_summary")
            parser_quotes = helper.get("parser_quotes", [])
            if parser_summary:
                st.write(parser_summary)
            if parser_quotes:
                st.markdown("**Candidate quotes**")
                for q in parser_quotes:
                    st.markdown(f"- {q}")


CHAPTER_BOUNDARY_RULES: dict[str, dict[str, type]] = {
    "2": {"1": ExecutableTradeState},
    "3": {"2": MeanReversionState},
    "5": {"3": FactorState},
    "8": {"5": RiskMetricState},
}


def render_chapter_contract(selected_key: str) -> None:
    registry = build_chapter_registry()
    validation_result = validate_chapter_dependencies(registry)
    blocking_issues = validation_result.blocking_issues_for(selected_key)
    if blocking_issues:
        st.error("Chapter dependency validation failed. Resolve the following before loading this chapter:")
        for issue in blocking_issues:
            prefix = "ERROR" if issue.severity == "error" else "WARNING"
            st.write(f"- [{prefix}] Chapter {issue.chapter}: {issue.message}")
        if any(issue.severity == "error" for issue in blocking_issues):
            st.stop()

    chapter = get_chapter(selected_key, registry, validation_result=validation_result)

    render_diagnostics_panel(
        prerequisites=chapter.prerequisites(),
        concept_map=chapter.concept_map(),
        case_studies=chapter.case_studies(),
        failure_modes=chapter.failure_modes(),
        exports=chapter.exports_to_next_chapter(),
    )
    render_equation_cards(chapter.equation_set())
    render_derivation_panel(chapter.derivation_steps())

    def _interactive_lab_body() -> None:
        errors = validate_boundary(selected_key, CHAPTER_BOUNDARY_RULES.get(selected_key, {}), upstream_exports)
        if errors:
            st.error("Upstream export validation failed:")
            for err in errors:
                st.markdown(f"- {err}")
            st.caption("Run prerequisite chapter labs to populate validated upstream exports.")
            return

        lab_payload = chapter.interactive_lab()
        upstream_exports[selected_key] = lab_payload
        st.caption("Structured lab payload")
        render_json_payload(lab_payload)

    section_expander("Interactive Lab", expanded=True, icon="🧪", body=_interactive_lab_body)
    render_quiz_panel(chapter.assessment())


st.title("Rates Theory Interactive Companion")
chapter_data_map, chapter_summary_error = load_primary_chapters()
if chapter_summary_error:
    st.error(chapter_summary_error)
    st.stop()

parser_metadata_map, parser_metadata_error = load_parser_helper_metadata()
if parser_metadata_error:
    st.warning(parser_metadata_error)
chapter_data_map = merge_parser_helper_metadata(chapter_data_map, parser_metadata_map)

chapter_keys = sorted(chapter_data_map.keys(), key=chapter_key_sorter)
selected_key = st.sidebar.selectbox("Select chapter", chapter_keys, index=0)
chapter_data = chapter_data_map[selected_key]
registry = build_chapter_registry()
validation_result = validate_chapter_dependencies(registry)
chapter_meta = get_chapter(selected_key, registry, validation_result=validation_result).chapter_meta()
render_chapter_header(chapter_data, chapter_meta)
render_chapter_contract(selected_key)

st.divider()
st.caption("Contract-driven UI shell active: chapter content is loaded through the shared chapter interface.")
