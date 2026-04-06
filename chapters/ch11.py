from __future__ import annotations

from .swap_basis import SwapBasisChapter


class Chapter11(SwapBasisChapter):
    def __init__(self) -> None:
        super().__init__(chapter_id="11", title="Chapter 11: Swap spread and basis block", objective="Evaluate funding, tenor, and collateral basis relationships.")
