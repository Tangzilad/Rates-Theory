"""Convenience adapters for fitted-curve residual workflows."""

from __future__ import annotations

import numpy as np

from .yield_curve import fit_nelson_siegel_svensson, rich_cheap_indicators


def fit_curve_and_residuals(maturities: np.ndarray, observed_yields: np.ndarray) -> dict[str, np.ndarray | float]:
    """Fit an NSS curve and return fitted values plus residual diagnostics."""
    params = fit_nelson_siegel_svensson(maturities, observed_yields)
    diagnostics = rich_cheap_indicators(maturities, observed_yields, params)
    return {
        "tau1": params.tau1,
        "tau2": params.tau2,
        "fitted": diagnostics["fitted"],
        "residual": diagnostics["residual"],
        "zscore": diagnostics["zscore"],
    }
