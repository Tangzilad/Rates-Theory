"""Chapter module registry."""

from __future__ import annotations

from typing import Dict

from .base import ChapterBase
from .ch01 import Chapter01
from .ch02 import Chapter02
from .ch03 import Chapter03
from .ch05 import Chapter05
from .ch08 import Chapter08
from .ch09 import Chapter09
from .ch11 import Chapter11
from .ch12 import Chapter12
from .ch13 import Chapter13
from .ch14 import Chapter14
from .ch15 import Chapter15
from .ch16 import Chapter16
from .ch17 import Chapter17
from .ch18 import Chapter18
from .common import SimpleChapter


class PlaceholderChapter(SimpleChapter):
    def __init__(self, chapter_id: str) -> None:
        super().__init__(
            chapter_id=chapter_id,
            title=f"Chapter {chapter_id}: Placeholder",
            objective="Structured placeholder for chapters outside wave-1 modules.",
        )


def build_chapter_registry() -> Dict[str, ChapterBase]:
    return {
        "1": Chapter01(),
        "2": Chapter02(),
        "3": Chapter03(),
        "5": Chapter05(),
        "8": Chapter08(),
        "9": Chapter09(),
        "11": Chapter11(),
        "12": Chapter12(),
        "13": Chapter13(),
        "14": Chapter14(),
        "15": Chapter15(),
        "16": Chapter16(),
        "17": Chapter17(),
        "18": Chapter18(),
    }


def get_chapter(chapter_key: str, registry: Dict[str, ChapterBase]) -> ChapterBase:
    return registry.get(chapter_key, PlaceholderChapter(chapter_key))
