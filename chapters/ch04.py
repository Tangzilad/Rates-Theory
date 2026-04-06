from __future__ import annotations

from typing import Any, Dict, List

from .base import ChapterBase


class Chapter04(ChapterBase):
    chapter_id = "4"

    def chapter_meta(self) -> Dict[str, Any]:
        return {"chapter": self.chapter_id, "title": "Chapter 4: Contract placeholder", "objective": "Reserved chapter slot with minimal contract."}

    def prerequisites(self) -> List[str]:
        return ["Review chapters 1-3 outputs."]

    def concept_map(self) -> Dict[str, List[str]]:
        return {"nodes": ["placeholder"], "edges": []}

    def equation_set(self) -> List[Dict[str, str]]:
        return [{"name": "Placeholder", "equation": "N/A"}]

    def derivation_steps(self) -> List[str]:
        return ["No derivation defined for this placeholder chapter."]

    def interactive_lab(self) -> Dict[str, str]:
        return {"status": "placeholder", "chapter": self.chapter_id}

    def case_studies(self) -> List[Dict[str, str]]:
        return [{"name": "Placeholder", "setup": "N/A", "takeaway": "Chapter slot reserved."}]

    def failure_modes(self) -> List[Dict[str, str]]:
        return [{"mode": "No implementation", "mitigation": "Replace placeholder with concrete chapter."}]

    def assessment(self) -> List[Dict[str, str]]:
        return [{"prompt": "What is the purpose of this chapter?", "expected": "It is a placeholder contract."}]

    def exports_to_next_chapter(self) -> Dict[str, Any]:
        return {"signals": [], "status": "placeholder"}
