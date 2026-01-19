"""Generic (language-agnostic) convention detectors package."""

from .repo_layout import GenericRepoLayoutDetector
from .ci_cd import CICDDetector
from .git_conventions import GitConventionsDetector
from .dependency_updates import DependencyUpdatesDetector
from .api_docs import APIDocumentationDetector
from .containerization import ContainerizationDetector
from .editor_config import EditorConfigDetector

__all__ = [
    "GenericRepoLayoutDetector",
    "CICDDetector",
    "GitConventionsDetector",
    "DependencyUpdatesDetector",
    "APIDocumentationDetector",
    "ContainerizationDetector",
    "EditorConfigDetector",
]
