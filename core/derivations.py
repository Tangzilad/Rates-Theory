from __future__ import annotations

import numpy as np


def ou_half_life_days(theta: float, trading_days: int = 252) -> float | None:
    if theta <= 0:
        return None
    return float(np.log(2) / theta * trading_days)


def confidence_from_distance(z_score: float, cap: float = 0.99) -> float:
    scaled = min(abs(z_score) / 3.0, cap)
    return float(scaled)
