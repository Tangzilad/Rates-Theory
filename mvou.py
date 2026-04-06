"""Deprecated compatibility shim for `mvou`.

Canonical implementation lives in `src.models.mvou`.
"""

from __future__ import annotations

from warnings import warn

warn(
    "Importing `mvou` from repository root is deprecated; use `src.models.mvou` instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.models.mvou import *  # noqa: F401,F403
