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
        if "node_index" not in ctx.cache or ctx.cache["node_index"] is None:
            index = NodeIndex(ctx.repo_root, max_files=ctx.max_files)
            index.build()
            ctx.cache["node_index"] = index
        result: NodeIndex = ctx.cache["node_index"]
        return result
