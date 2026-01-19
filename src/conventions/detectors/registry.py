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
    from . import generic_repo_layout  # noqa: F401

    # Python detectors
    from . import python_typing_conventions  # noqa: F401
    from . import python_error_conventions  # noqa: F401
    from . import python_db_conventions  # noqa: F401
    from . import python_logging_conventions  # noqa: F401
    from . import python_layering_conventions  # noqa: F401
    from . import python_di_conventions  # noqa: F401
    from . import python_testing_conventions  # noqa: F401
    from . import python_api_schema_conventions  # noqa: F401
    from . import python_retries_timeouts_conventions  # noqa: F401
    from . import python_observability_conventions  # noqa: F401
    from . import python_async_conventions  # noqa: F401
    from . import python_docstring_naming_conventions  # noqa: F401
    from . import python_security_conventions  # noqa: F401

    # Node.js detectors (lighter)
    from . import node_conventions  # noqa: F401

    # Go detectors (lighter)
    from . import go_conventions  # noqa: F401
