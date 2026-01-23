"""Node.js convention detectors package."""

from .index import NodeIndex, make_evidence
from .base import NodeDetector

# Import all detector classes to ensure they register
from .conventions import NodeConventionsDetector
from .typescript import NodeTypeScriptDetector
from .documentation import NodeDocumentationDetector
from .testing import NodeTestingDetector
from .logging import NodeLoggingDetector
from .errors import NodeErrorHandlingDetector
from .security import NodeSecurityDetector
from .async_patterns import NodeAsyncPatternsDetector
from .architecture import NodeArchitectureDetector
from .api import NodeAPIDetector
from .patterns import NodePatternsDetector
from .package_manager import NodePackageManagerDetector
from .monorepo import NodeMonorepoDetector
from .build_tools import NodeBuildToolsDetector
from .linting import NodeLintingDetector
from .formatting import NodeFormattingDetector
from .frontend import NodeFrontendDetector
from .state_management import NodeStateManagementDetector

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
