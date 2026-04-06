from __future__ import annotations

import numpy as np
import pandas as pd


def synthetic_tenor_matrix(n_obs: int = 350, seed: int = 42) -> pd.DataFrame:
    tenors = ["2Y", "5Y", "10Y", "30Y"]
    cov = np.array(
        [
            [1.0, 0.86, 0.70, 0.45],
            [0.86, 1.0, 0.82, 0.60],
            [0.70, 0.82, 1.0, 0.78],
            [0.45, 0.60, 0.78, 1.0],
        ]
    )
    sample = np.random.default_rng(seed).multivariate_normal(np.zeros(4), cov, size=n_obs)
    return pd.DataFrame(sample, columns=tenors)
