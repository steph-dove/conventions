"""Rust convention detectors package."""

from .index import RustIndex, make_evidence
from .base import RustDetector

# Import all detector classes to ensure they register
from .cargo import RustCargoDetector
from .testing import RustTestingDetector
from .errors import RustErrorHandlingDetector
from .async_runtime import RustAsyncDetector
from .web import RustWebDetector
from .cli import RustCLIDetector
from .serialization import RustSerializationDetector
from .documentation import RustDocumentationDetector
from .unsafe_code import RustUnsafeDetector
from .macros import RustMacrosDetector
from .logging import RustLoggingDetector
from .database import RustDatabaseDetector

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
