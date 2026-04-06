"""Deprecated compatibility shim for `swap_spreads`.

Canonical implementation lives in `src.models.swap_spreads`.
"""

from __future__ import annotations

from warnings import warn

warn(
    "Importing `swap_spreads` from repository root is deprecated; use `src.models.swap_spreads` instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.models.swap_spreads import *  # noqa: F401,F403
