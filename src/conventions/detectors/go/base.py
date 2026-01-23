"""Go detector base class."""

from __future__ import annotations

from ..base import BaseDetector, DetectorContext
from .index import GoIndex


class GoDetector(BaseDetector):
    """Base class for Go detectors."""

    languages: set[str] = {"go"}

    def get_index(self, ctx: DetectorContext) -> GoIndex:
        """Get or create Go index."""
        if "go_index" not in ctx.cache or ctx.cache["go_index"] is None:
            index = GoIndex(ctx.repo_root, max_files=ctx.max_files)
            index.build()
            ctx.cache["go_index"] = index
        result: GoIndex = ctx.cache["go_index"]
        return result
