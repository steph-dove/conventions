"""Generic (language-agnostic) convention detectors package."""

from .api_docs import APIDocumentationDetector
from .ci_cd import CICDDetector
from .code_ownership import CodeOwnershipDetector
from .config_patterns import ConfigPatternsDetector
from .containerization import ContainerizationDetector
from .dependency_updates import DependencyUpdatesDetector
from .editor_config import EditorConfigDetector
from .environment_setup import EnvironmentSetupDetector
from .generated_code import GeneratedCodeDetector
from .git_conventions import GitConventionsDetector
from .repo_layout import GenericRepoLayoutDetector
from .task_runners import TaskRunnerDetector

__all__ = [
    "GenericRepoLayoutDetector",
    "CICDDetector",
    "CodeOwnershipDetector",
    "ConfigPatternsDetector",
    "GitConventionsDetector",
    "DependencyUpdatesDetector",
    "APIDocumentationDetector",
    "ContainerizationDetector",
    "EditorConfigDetector",
    "EnvironmentSetupDetector",
    "GeneratedCodeDetector",
    "TaskRunnerDetector",
]
