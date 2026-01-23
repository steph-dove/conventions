"""Convention detectors package."""

from .base import BaseDetector, DetectorContext, DetectorResult, PythonDetector
from .registry import DetectorRegistry
from .go.base import GoDetector
from .node.base import NodeDetector

__all__ = [
    "BaseDetector",
    "DetectorContext",
    "DetectorResult",
    "PythonDetector",
    "GoDetector",
    "NodeDetector",
    "DetectorRegistry",
]
