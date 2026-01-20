"""Python convention detectors package."""

from .api_schema import PythonAPISchemaConventionsDetector
from .architecture import PythonLayeringConventionsDetector
from .async_concurrency import PythonAsyncConventionsDetector
from .background_tasks import PythonBackgroundTaskDetector
from .caching import PythonCachingDetector
from .cli_patterns import PythonCLIPatternDetector
from .db import PythonDBConventionsDetector
from .dependency_management import PythonDependencyManagementDetector
from .di_patterns import PythonDIConventionsDetector
from .documentation import PythonDocstringNamingConventionsDetector
from .errors import PythonErrorConventionsDetector
from .graphql import PythonGraphQLDetector
from .index import PythonIndex, make_evidence
from .logging import PythonLoggingConventionsDetector
from .observability import PythonObservabilityConventionsDetector
from .resilience import PythonRetriesTimeoutsConventionsDetector
from .security import PythonSecurityConventionsDetector
from .testing import PythonTestingConventionsDetector
from .tooling import PythonToolingDetector

# Import all detector classes to ensure they register
from .typing import PythonTypingConventionsDetector

__all__ = [
    "PythonIndex",
    "make_evidence",
    "PythonTypingConventionsDetector",
    "PythonDocstringNamingConventionsDetector",
    "PythonTestingConventionsDetector",
    "PythonLoggingConventionsDetector",
    "PythonErrorConventionsDetector",
    "PythonSecurityConventionsDetector",
    "PythonAsyncConventionsDetector",
    "PythonLayeringConventionsDetector",
    "PythonAPISchemaConventionsDetector",
    "PythonDIConventionsDetector",
    "PythonDBConventionsDetector",
    "PythonObservabilityConventionsDetector",
    "PythonRetriesTimeoutsConventionsDetector",
    "PythonToolingDetector",
    "PythonDependencyManagementDetector",
    "PythonCLIPatternDetector",
    "PythonBackgroundTaskDetector",
    "PythonCachingDetector",
    "PythonGraphQLDetector",
]
