"""Python convention detectors package."""

from .index import PythonIndex, make_evidence

# Import all detector classes to ensure they register
from .typing import PythonTypingConventionsDetector
from .documentation import PythonDocstringNamingConventionsDetector
from .testing import PythonTestingConventionsDetector
from .logging import PythonLoggingConventionsDetector
from .errors import PythonErrorConventionsDetector
from .security import PythonSecurityConventionsDetector
from .async_concurrency import PythonAsyncConventionsDetector
from .architecture import PythonLayeringConventionsDetector
from .api_schema import PythonAPISchemaConventionsDetector
from .di_patterns import PythonDIConventionsDetector
from .db import PythonDBConventionsDetector
from .observability import PythonObservabilityConventionsDetector
from .resilience import PythonRetriesTimeoutsConventionsDetector
from .tooling import PythonToolingDetector
from .dependency_management import PythonDependencyManagementDetector
from .cli_patterns import PythonCLIPatternDetector
from .background_tasks import PythonBackgroundTaskDetector
from .caching import PythonCachingDetector
from .graphql import PythonGraphQLDetector

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
