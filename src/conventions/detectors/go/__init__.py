"""Go convention detectors package."""

from .index import GoIndex, make_evidence
from .base import GoDetector

# Import all detector classes to ensure they register
from .conventions import GoConventionsDetector
from .documentation import GoDocumentationDetector
from .testing import GoTestingDetector
from .logging import GoLoggingDetector
from .errors import GoErrorHandlingDetector
from .security import GoSecurityDetector
from .concurrency import GoConcurrencyDetector
from .architecture import GoArchitectureDetector
from .api import GoAPIDetector
from .patterns import GoPatternsDetector
from .modules import GoModulesDetector
from .cli import GoCLIDetector
from .migrations import GoMigrationsDetector
from .di import GoDIDetector
from .grpc import GoGRPCDetector
from .codegen import GoCodegenDetector

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
