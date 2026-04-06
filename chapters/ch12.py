from __future__ import annotations

from .swap_basis import SwapBasisChapter


class Chapter12(SwapBasisChapter):
    def __init__(self) -> None:
        super().__init__(chapter_id="12", title="Chapter 12: Swap spread and basis block", objective="Evaluate funding, tenor, and collateral basis relationships.")
