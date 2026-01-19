"""Convention detectors package."""

from .base import BaseDetector, DetectorContext, DetectorResult, PythonDetector
from .registry import DetectorRegistry

__all__ = [
    "BaseDetector",
    "DetectorContext",
    "DetectorResult",
    "PythonDetector",
    "DetectorRegistry",
]
