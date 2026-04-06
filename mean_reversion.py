"""Deprecated compatibility shim for `mean_reversion`.

Canonical implementation lives in `src.models.mean_reversion`.
"""

from __future__ import annotations

from warnings import warn

warn(
    "Importing `mean_reversion` from repository root is deprecated; use `src.models.mean_reversion` instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.models.mean_reversion import *  # noqa: F401,F403
