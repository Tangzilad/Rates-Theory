"""Deprecated compatibility shim for `yield_curve`.

Canonical implementation lives in `src.models.yield_curve`.
"""

from __future__ import annotations

from warnings import warn

warn(
    "Importing `yield_curve` from repository root is deprecated; use `src.models.yield_curve` instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.models.yield_curve import *  # noqa: F401,F403
