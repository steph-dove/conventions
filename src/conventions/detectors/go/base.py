"""Go detector base class."""

from __future__ import annotations

from ..base import BaseDetector, DetectorContext
from .index import GoIndex


class GoDetector(BaseDetector):
    """Base class for Go detectors."""

    languages: set[str] = {"go"}

    def get_index(self, ctx: DetectorContext) -> GoIndex:
        """Get or create Go index."""
        if not hasattr(ctx, "_go_index") or ctx._go_index is None:
            ctx._go_index = GoIndex(ctx.repo_root, max_files=ctx.max_files)
            ctx._go_index.build()
        return ctx._go_index
