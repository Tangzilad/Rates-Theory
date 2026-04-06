import json
from pathlib import Path
from typing import Dict, Optional, Tuple

import streamlit as st
from src.chapter_summary_schema import (
    ChapterSummarySchemaError,
    document_to_chapter_map,
    legacy_map_to_document,
)

from chapters import build_chapter_registry, get_chapter, validate_chapter_dependencies


st.set_page_config(page_title="Rates Theory Lab", layout="wide")


def load_chapter_summaries() -> Tuple[Dict[str, dict], bool, Optional[str]]:
    """Load chapter summaries and return (data, loaded_flag, error_message)."""
    json_path = Path(__file__).resolve().parent.parent / "data" / "chapter_summaries.json"
    if json_path.exists():
        try:
            with json_path.open("r", encoding="utf-8") as f:
                payload = json.load(f)

            if isinstance(payload, dict) and "schema_version" in payload:
                return document_to_chapter_map(payload), True, None

            if isinstance(payload, dict):
                legacy_document = legacy_map_to_document(payload)
                return document_to_chapter_map(legacy_document), True, (
                    "Loaded legacy chapter summary JSON and normalized it to schema v1.0."
                )

            raise ChapterSummarySchemaError(
                "Malformed chapter summaries file: expected a schema object."
            )
        except (json.JSONDecodeError, OSError) as exc:
            error_message = f"Could not parse chapter summaries JSON ({exc})."
        except ChapterSummarySchemaError as exc:
            error_message = str(exc)
        return _fallback_chapter_summaries(), False, error_message

    return _fallback_chapter_summaries(), False, "Chapter summary JSON file was not found."


def _fallback_chapter_summaries() -> Dict[str, dict]:
    fallback = {
        str(i): {
            "title": f"Chapter {i}",
            "summary": "Summary file missing; using built-in fallback content.",
            "quotes": ["Add data/chapter_summaries.json to see curated chapter excerpts."],
        }
        for i in range(1, 25)
    }
    fallback["final"] = {
        "title": "Final Chapters",
        "summary": "Integrated review of models, diagnostics, and implementation caveats.",
        "quotes": ["Model outputs are only as good as assumptions and data quality."],
    }
    return fallback


def chapter_key_sorter(k: str) -> Tuple[int, str]:
    if k.isdigit():
        return int(k), ""
    return 10_000, k


def render_chapter_header(chapter_data: dict, chapter_meta: dict) -> None:
    st.header(chapter_meta.get("title", chapter_data.get("title", "Chapter")))
    st.write(chapter_data.get("summary", chapter_meta.get("objective", "No summary available.")))
    quotes = chapter_data.get("quotes", [])
    with st.expander("Key quotes"):
        if quotes:
            for q in quotes:
                st.markdown(f"- {q}")
        else:
            st.write("No quotes available.")


def render_contract_section(title: str, payload) -> None:
    st.subheader(title)
    if isinstance(payload, (dict, list)):
        st.json(payload)
    else:
        st.write(payload)


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

    tab_labels = [
        "Prerequisites",
        "Concept Map",
        "Equations",
        "Derivation",
        "Interactive Lab",
        "Case Studies",
        "Failure Modes",
        "Assessment",
        "Exports",
    ]
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        render_contract_section("Prerequisites", chapter.prerequisites())
    with tabs[1]:
        render_contract_section("Concept Map", chapter.concept_map())
    with tabs[2]:
        render_contract_section("Equation Set", chapter.equation_set())
    with tabs[3]:
        render_contract_section("Derivation Steps", chapter.derivation_steps())
    with tabs[4]:
        st.subheader("Interactive Lab")
        lab_payload = chapter.interactive_lab()
        st.caption("Structured lab payload")
        st.json(lab_payload)
    with tabs[5]:
        render_contract_section("Case Studies", chapter.case_studies())
    with tabs[6]:
        render_contract_section("Failure Modes", chapter.failure_modes())
    with tabs[7]:
        render_contract_section("Assessment", chapter.assessment())
    with tabs[8]:
        render_contract_section("Exports to Next Chapter", chapter.exports_to_next_chapter())


st.title("Rates Theory Interactive Companion")
chapter_data_map, loaded, chapter_summary_error = load_chapter_summaries()
if chapter_summary_error:
    st.warning(
        f"{chapter_summary_error} "
        "Showing fallback chapter summaries where needed."
    )

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
