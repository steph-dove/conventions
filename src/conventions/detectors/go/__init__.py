"""Go convention detectors package."""

from .api import GoAPIDetector
from .architecture import GoArchitectureDetector
from .base import GoDetector
from .cli import GoCLIDetector
from .codegen import GoCodegenDetector
from .concurrency import GoConcurrencyDetector

# Import all detector classes to ensure they register
from .conventions import GoConventionsDetector
from .di import GoDIDetector
from .documentation import GoDocumentationDetector
from .errors import GoErrorHandlingDetector
from .grpc import GoGRPCDetector
from .index import GoIndex, make_evidence
from .logging import GoLoggingDetector
from .migrations import GoMigrationsDetector
from .modules import GoModulesDetector
from .patterns import GoPatternsDetector
from .security import GoSecurityDetector
from .testing import GoTestingDetector

__all__ = [
    "GoIndex",
    "make_evidence",
    "GoDetector",
    "GoConventionsDetector",
    "GoDocumentationDetector",
    "GoTestingDetector",
    "GoLoggingDetector",
    "GoErrorHandlingDetector",
    "GoSecurityDetector",
    "GoConcurrencyDetector",
    "GoArchitectureDetector",
    "GoAPIDetector",
    "GoPatternsDetector",
    "GoModulesDetector",
    "GoCLIDetector",
    "GoMigrationsDetector",
    "GoDIDetector",
    "GoGRPCDetector",
    "GoCodegenDetector",
]
