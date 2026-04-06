from __future__ import annotations

from .swap_basis import SwapBasisChapter


class Chapter15(SwapBasisChapter):
    def __init__(self) -> None:
        super().__init__(chapter_id="15", title="Chapter 15: Swap spread and basis block", objective="Evaluate funding, tenor, and collateral basis relationships.")
