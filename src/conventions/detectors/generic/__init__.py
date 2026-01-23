"""Generic (language-agnostic) convention detectors package."""

from .api_docs import APIDocumentationDetector
from .ci_cd import CICDDetector
from .containerization import ContainerizationDetector
from .dependency_updates import DependencyUpdatesDetector
from .editor_config import EditorConfigDetector
from .git_conventions import GitConventionsDetector
from .repo_layout import GenericRepoLayoutDetector

__all__ = [
    "GenericRepoLayoutDetector",
    "CICDDetector",
    "GitConventionsDetector",
    "DependencyUpdatesDetector",
    "APIDocumentationDetector",
    "ContainerizationDetector",
    "EditorConfigDetector",
]
