"""Base class for Rust convention detectors."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..base import BaseDetector, DetectorContext

if TYPE_CHECKING:
    from .index import RustIndex


class RustDetector(BaseDetector):
    """Base class for Rust-specific detectors."""

    language = "rust"

    def get_index(self, ctx: DetectorContext) -> "RustIndex":
        """Get or create the Rust index from context."""
        from .index import RustIndex

        cache_key = "rust_index"
        if cache_key not in ctx.cache:
            index = RustIndex(ctx.repo_root)
            index.build()
            ctx.cache[cache_key] = index
        return ctx.cache[cache_key]
