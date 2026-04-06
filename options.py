"""Deprecated compatibility shim for `options`.

Canonical implementation lives in `src.models.options`.
"""

from __future__ import annotations

from warnings import warn

warn(
    "Importing `options` from repository root is deprecated; use `src.models.options` instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.models.options import *  # noqa: F401,F403
