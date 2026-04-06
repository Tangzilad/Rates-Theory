"""Shared chapter contracts and reusable chapter scaffolding."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import streamlit as st

from core.equations import shock_adjusted_price
from core.types import ChapterExportState, RiskMetricState


class ChapterBase(ABC):
    """Abstract base class used by all chapter modules."""

    chapter_id: str

    @abstractmethod
    def chapter_meta(self) -> dict[str, Any]:
        """Return title and high-level context metadata."""

    @abstractmethod
    def prerequisites(self) -> list[str]:
        """Return prerequisite knowledge list for the chapter."""

    @abstractmethod
    def concept_map(self) -> dict[str, list[str]]:
        """Return concept nodes and directed links."""

    @abstractmethod
    def equation_set(self) -> list[dict[str, str]]:
        """Return key equations and descriptions."""

    @abstractmethod
    def derivation_steps(self) -> list[str]:
        """Return derivation sequence in compact bullet form."""

    @abstractmethod
    def interactive_lab(self) -> Any:
        """Render chapter lab widgets and return computed payload."""

    @abstractmethod
    def case_studies(self) -> list[dict[str, str]]:
        """Return case studies with setup and takeaway."""

    @abstractmethod
    def failure_modes(self) -> list[dict[str, str]]:
        """Return failure scenarios and mitigations."""

    @abstractmethod
    def assessment(self) -> list[dict[str, str]]:
        """Return assessment prompts and expected direction."""

    @abstractmethod
    def exports_to_next_chapter(self) -> Any:
        """Return explicit outputs that feed later chapters."""

    # Canonical section-order API for Streamlit presentation.
    def core_claim(self) -> str:
        return self.chapter_meta().get("objective", "")

    def market_objects(self) -> list[str]:
        concept_map = self.concept_map()
        return concept_map.get("nodes", []) if isinstance(concept_map, dict) else []

    def technical_equations(self) -> list[dict[str, str]]:
        return self.equation_set()

    def derivation(self) -> list[str]:
        return self.derivation_steps()

    def trade_interpretation(self) -> list[str]:
        case_studies = self.case_studies()
        return [item.get("takeaway", "") for item in case_studies if isinstance(item, dict) and item.get("takeaway")]

    def failure_modes_model_risk(self) -> list[dict[str, str]]:
        return self.failure_modes()

    def checkpoint(self) -> list[dict[str, str]]:
        return self.assessment()

    def key_takeaway(self) -> str:
        return self.core_claim()

    def common_confusions(self) -> list[dict[str, str]]:
        return self.failure_modes_model_risk()

    def learn_focus(self) -> list[str]:
        return []

    def derive_focus(self) -> list[str]:
        return []

    def trade_use_focus(self) -> list[str]:
        return []


class PlaceholderChapter(ChapterBase):
    """Explicitly non-implemented chapter that surfaces missing contracts."""

    def __init__(self, chapter_id: str, diagnostics: list[str] | None = None) -> None:
        self.chapter_id = chapter_id
        self._diagnostics = diagnostics or [
            "Module is not implemented.",
            "No chapter contract is available for this key.",
        ]

    def chapter_meta(self) -> dict[str, Any]:
        return {
            "chapter": self.chapter_id,
            "title": f"Chapter {self.chapter_id}: Not implemented",
            "objective": "Module contract missing. Implement chapter module and register dependencies.",
        }

    def prerequisites(self) -> list[str]:
        return ["Not implemented: prerequisite contract unavailable."]

    def concept_map(self) -> dict[str, list[str]]:
        return {"status": ["not_implemented"], "diagnostics": self._diagnostics}

    def equation_set(self) -> list[dict[str, str]]:
        return [{"name": "Not implemented", "equation": "No equation contract available."}]

    def derivation_steps(self) -> list[str]:
        return ["Not implemented: derive chapter contract before use."]

    def interactive_lab(self) -> dict[str, Any]:
        return {"status": "not_implemented", "missing_contract": self._diagnostics}

    def case_studies(self) -> list[dict[str, str]]:
        return [{"name": "Not implemented", "setup": "N/A", "takeaway": "Missing chapter contract."}]

    def failure_modes(self) -> list[dict[str, str]]:
        return [{"mode": "Unimplemented chapter selected", "mitigation": "Add concrete chapter module and registry wiring."}]

    def assessment(self) -> list[dict[str, str]]:
        return [{"prompt": "What is missing?", "expected": "A concrete chapter implementation and dependency contract."}]

    def exports_to_next_chapter(self) -> dict[str, Any]:
        return {"status": "not_implemented", "signals": [], "missing_contract": self._diagnostics}


@dataclass
class SimpleChapter(ChapterBase):
    chapter_id: str
    title: str
    objective: str

    def chapter_meta(self) -> dict[str, Any]:
        return {"chapter": self.chapter_id, "title": self.title, "objective": self.objective}

    def prerequisites(self) -> list[str]:
        return ["Prior chapter outputs", "Rates market conventions"]

    def concept_map(self) -> dict[str, list[str]]:
        return {"nodes": ["Inputs", "Model", "Diagnostics", "Decision"], "edges": ["Inputs->Model", "Model->Diagnostics", "Diagnostics->Decision"]}

    def equation_set(self) -> list[dict[str, str]]:
        return [{"name": "Placeholder", "equation": "Section intentionally minimal in wave-1."}]

    def derivation_steps(self) -> list[str]:
        return ["Define inputs.", "Apply chapter model.", "Interpret outputs with risk controls."]

    def interactive_lab(self) -> RiskMetricState:
        shock_bp = st.slider("Scenario shock (bp)", -200, 200, 25, 5, key=f"shock_{self.chapter_id}")
        base = st.number_input("Base value", value=100.0, step=0.5, key=f"base_{self.chapter_id}")
        sensitivity = st.number_input("Sensitivity per bp", value=0.08, step=0.01, key=f"sens_{self.chapter_id}")
        scenario = shock_adjusted_price(base, shock_bp * sensitivity / 100.0)
        st.metric("Scenario output", f"{scenario:.3f}")
        return RiskMetricState(
            curve_slope_bp=0.0,
            duration=sensitivity,
            convexity=0.0,
            dy_bp=shock_bp,
            dp_pct=(scenario / base - 1.0) if base else 0.0,
            fair_price=scenario,
        )

    def case_studies(self) -> list[dict[str, str]]:
        return [{"name": "Baseline workflow", "setup": "Run model under neutral assumptions", "takeaway": "Establish reproducible benchmark output."}]

    def failure_modes(self) -> list[dict[str, str]]:
        return [{"mode": "Parameter drift", "mitigation": "Recalibrate and compare to control limits."}]

    def assessment(self) -> list[dict[str, str]]:
        return [{"prompt": "Which input dominates scenario value?", "expected": "Sensitivity times bp shock."}]

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            signals=["scenario_value"],
            usage="Forwarded into downstream diagnostics.",
            schema_name="RiskMetricState",
        )
