"""Registry for convention detectors."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import BaseDetector


class DetectorRegistry:
    """Registry of all available detectors."""

    _detectors: list[type["BaseDetector"]] = []

    @classmethod
    def register(cls, detector_class: type["BaseDetector"]) -> type["BaseDetector"]:
        """Register a detector class. Can be used as a decorator."""
        if detector_class not in cls._detectors:
            cls._detectors.append(detector_class)
        return detector_class

    @classmethod
    def get_all(cls) -> list[type["BaseDetector"]]:
        """Get all registered detector classes."""
        return list(cls._detectors)

    @classmethod
    def clear(cls) -> None:
        """Clear all registered detectors (useful for testing)."""
        cls._detectors = []


def register_all_detectors() -> None:
    """
    Import all detector modules to trigger registration.

    This must be called before using the registry.
    """
    # Generic detectors (language-agnostic)
    # Python detectors
    # Go detectors
    # Node.js detectors
    # Rust detectors
    from . import (
        generic,  # noqa: F401
        go,  # noqa: F401
        node,  # noqa: F401
        python,  # noqa: F401
        rust,  # noqa: F401
    )
