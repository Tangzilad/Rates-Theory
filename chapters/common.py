from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import streamlit as st

from core.equations import shock_adjusted_price
from core.types import ChapterExportState, RiskMetricState

from .base import ChapterBase


@dataclass
class SimpleChapter(ChapterBase):
    chapter_id: str
    title: str
    objective: str

    def chapter_meta(self) -> Dict[str, Any]:
        return {"chapter": self.chapter_id, "title": self.title, "objective": self.objective}

    def prerequisites(self) -> List[str]:
        return ["Prior chapter outputs", "Rates market conventions"]

    def concept_map(self) -> Dict[str, List[str]]:
        return {"nodes": ["Inputs", "Model", "Diagnostics", "Decision"], "edges": ["Inputs->Model", "Model->Diagnostics", "Diagnostics->Decision"]}

    def equation_set(self) -> List[Dict[str, str]]:
        return [{"name": "Placeholder", "equation": "Section intentionally minimal in wave-1."}]

    def derivation_steps(self) -> List[str]:
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

    def case_studies(self) -> List[Dict[str, str]]:
        return [{"name": "Baseline workflow", "setup": "Run model under neutral assumptions", "takeaway": "Establish reproducible benchmark output."}]

    def failure_modes(self) -> List[Dict[str, str]]:
        return [{"mode": "Parameter drift", "mitigation": "Recalibrate and compare to control limits."}]

    def assessment(self) -> List[Dict[str, str]]:
        return [{"prompt": "Which input dominates scenario value?", "expected": "Sensitivity times bp shock."}]

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            signals=["scenario_value"],
            usage="Forwarded into downstream diagnostics.",
            schema_name="RiskMetricState",
        )
