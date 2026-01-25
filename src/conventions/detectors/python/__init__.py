"""Python convention detectors package."""

from .api_response_patterns import PythonAPIResponsePatternsDetector
from .api_schema import PythonAPISchemaConventionsDetector
from .architecture import PythonLayeringConventionsDetector
from .async_concurrency import PythonAsyncConventionsDetector
from .background_tasks import PythonBackgroundTaskDetector
from .caching import PythonCachingDetector
from .class_patterns import PythonClassPatternsDetector
from .cli_patterns import PythonCLIPatternDetector
from .code_style import PythonCodeStyleDetector
from .constants_enums import PythonConstantsEnumsDetector
from .db import PythonDBConventionsDetector
from .decorator_patterns import PythonDecoratorPatternsDetector
from .dependency_management import PythonDependencyManagementDetector
from .di_patterns import PythonDIConventionsDetector
from .docs_conventions import PythonDocsConventionsDetector
from .documentation import PythonDocstringNamingConventionsDetector
from .errors import PythonErrorConventionsDetector
from .graphql import PythonGraphQLDetector
from .index import PythonIndex, make_evidence
from .logging import PythonLoggingConventionsDetector
from .observability import PythonObservabilityConventionsDetector
from .resilience import PythonRetriesTimeoutsConventionsDetector
from .resource_management import PythonResourceManagementDetector
from .return_patterns import PythonReturnPatternsDetector
from .security import PythonSecurityConventionsDetector
from .test_conventions import PythonTestConventionsDetector
from .test_organization import PythonTestOrganizationDetector
from .tooling import PythonToolingDetector
from .validation_patterns import PythonValidationPatternsDetector

# Import all detector classes to ensure they register
from .typing import PythonTypingConventionsDetector

__all__ = [
    "PythonIndex",
    "make_evidence",
    "PythonAPIResponsePatternsDetector",
    "PythonAPISchemaConventionsDetector",
    "PythonAsyncConventionsDetector",
    "PythonBackgroundTaskDetector",
    "PythonCachingDetector",
    "PythonClassPatternsDetector",
    "PythonCLIPatternDetector",
    "PythonCodeStyleDetector",
    "PythonConstantsEnumsDetector",
    "PythonDBConventionsDetector",
    "PythonDecoratorPatternsDetector",
    "PythonDependencyManagementDetector",
    "PythonDIConventionsDetector",
    "PythonDocsConventionsDetector",
    "PythonDocstringNamingConventionsDetector",
    "PythonErrorConventionsDetector",
    "PythonGraphQLDetector",
    "PythonLayeringConventionsDetector",
    "PythonLoggingConventionsDetector",
    "PythonObservabilityConventionsDetector",
    "PythonResourceManagementDetector",
    "PythonReturnPatternsDetector",
    "PythonRetriesTimeoutsConventionsDetector",
    "PythonSecurityConventionsDetector",
    "PythonTestConventionsDetector",
    "PythonTestOrganizationDetector",
    "PythonToolingDetector",
    "PythonTypingConventionsDetector",
    "PythonValidationPatternsDetector",
]
