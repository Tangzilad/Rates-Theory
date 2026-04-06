from __future__ import annotations

from core.types import ChapterExportState

from .base import SimpleChapter


class Chapter08(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(chapter_id="8", title="Chapter 8: Relative-value screens", objective="Combine model and market spread views into actionable flags.")

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            signals=[
                "curve_fit_residual_bp",
                "residual_zscore",
                "screen_rank",
                "screen_signal",
                "liquidity_score",
            ],
            usage="Primary screen outputs consumed by trade construction and hedge design.",
            schema_name="RelativeValueScreenState",
        )
