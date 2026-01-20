"""Convention detectors package."""

from .base import BaseDetector, DetectorContext, DetectorResult, PythonDetector
from .go.base import GoDetector
from .node.base import NodeDetector
from .registry import DetectorRegistry

__all__ = [
    "BaseDetector",
    "DetectorContext",
    "DetectorResult",
    "PythonDetector",
    "GoDetector",
    "NodeDetector",
    "DetectorRegistry",
]
