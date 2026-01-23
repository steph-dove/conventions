"""Node.js detector base class."""

from __future__ import annotations

from ..base import BaseDetector, DetectorContext
from .index import NodeIndex


class NodeDetector(BaseDetector):
    """Base class for Node.js detectors."""

    languages: set[str] = {"node"}

    def get_index(self, ctx: DetectorContext) -> NodeIndex:
        """Get or create Node.js index."""
        # Cache on context
        if not hasattr(ctx, "_node_index") or ctx._node_index is None:
            ctx._node_index = NodeIndex(ctx.repo_root, max_files=ctx.max_files)
            ctx._node_index.build()
        return ctx._node_index
