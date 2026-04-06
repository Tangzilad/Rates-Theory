"""Deprecated compatibility shim for `pca_module`.

Canonical implementation lives in `src.models.pca_module`.
"""

from __future__ import annotations

from warnings import warn

warn(
    "Importing `pca_module` from repository root is deprecated; use `src.models.pca_module` instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.models.pca_module import *  # noqa: F401,F403
