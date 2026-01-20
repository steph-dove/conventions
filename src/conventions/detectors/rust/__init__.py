"""Rust convention detectors package."""

from .async_runtime import RustAsyncDetector
from .base import RustDetector

# Import all detector classes to ensure they register
from .cargo import RustCargoDetector
from .cli import RustCLIDetector
from .database import RustDatabaseDetector
from .documentation import RustDocumentationDetector
from .errors import RustErrorHandlingDetector
from .index import RustIndex, make_evidence
from .logging import RustLoggingDetector
from .macros import RustMacrosDetector
from .serialization import RustSerializationDetector
from .testing import RustTestingDetector
from .unsafe_code import RustUnsafeDetector
from .web import RustWebDetector

__all__ = [
    "RustIndex",
    "make_evidence",
    "RustDetector",
    "RustCargoDetector",
    "RustTestingDetector",
    "RustErrorHandlingDetector",
    "RustAsyncDetector",
    "RustWebDetector",
    "RustCLIDetector",
    "RustSerializationDetector",
    "RustDocumentationDetector",
    "RustUnsafeDetector",
    "RustMacrosDetector",
    "RustLoggingDetector",
    "RustDatabaseDetector",
]
