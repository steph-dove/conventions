"""Node.js convention detectors package."""

from .api import NodeAPIDetector
from .architecture import NodeArchitectureDetector
from .async_patterns import NodeAsyncPatternsDetector
from .base import NodeDetector
from .build_tools import NodeBuildToolsDetector

# Import all detector classes to ensure they register
from .conventions import NodeConventionsDetector
from .documentation import NodeDocumentationDetector
from .errors import NodeErrorHandlingDetector
from .formatting import NodeFormattingDetector
from .frontend import NodeFrontendDetector
from .index import NodeIndex, make_evidence
from .linting import NodeLintingDetector
from .logging import NodeLoggingDetector
from .monorepo import NodeMonorepoDetector
from .package_manager import NodePackageManagerDetector
from .patterns import NodePatternsDetector
from .security import NodeSecurityDetector
from .state_management import NodeStateManagementDetector
from .testing import NodeTestingDetector
from .typescript import NodeTypeScriptDetector

__all__ = [
    "NodeIndex",
    "make_evidence",
    "NodeDetector",
    "NodeConventionsDetector",
    "NodeTypeScriptDetector",
    "NodeDocumentationDetector",
    "NodeTestingDetector",
    "NodeLoggingDetector",
    "NodeErrorHandlingDetector",
    "NodeSecurityDetector",
    "NodeAsyncPatternsDetector",
    "NodeArchitectureDetector",
    "NodeAPIDetector",
    "NodePatternsDetector",
    "NodePackageManagerDetector",
    "NodeMonorepoDetector",
    "NodeBuildToolsDetector",
    "NodeLintingDetector",
    "NodeFormattingDetector",
    "NodeFrontendDetector",
    "NodeStateManagementDetector",
]
