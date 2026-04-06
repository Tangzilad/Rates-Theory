from __future__ import annotations

from .swap_basis import SwapBasisChapter


class Chapter13(SwapBasisChapter):
    def __init__(self) -> None:
        super().__init__(chapter_id="13", title="Chapter 13: Swap spread and basis block", objective="Evaluate funding, tenor, and collateral basis relationships.")
