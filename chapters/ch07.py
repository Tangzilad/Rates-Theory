from __future__ import annotations

from typing import Any, Dict

from .ch04 import Chapter04


class Chapter07(Chapter04):
    chapter_id = "7"

    def chapter_meta(self) -> Dict[str, Any]:
        return {"chapter": self.chapter_id, "title": "Chapter 7: Contract placeholder", "objective": "Reserved chapter slot with minimal contract."}
