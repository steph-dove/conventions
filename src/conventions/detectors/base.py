"""Base classes for convention detectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from ..schemas import ConventionRule, EvidenceSnippet


@dataclass
class DetectorContext:
    """Context passed to all detectors."""

    repo_root: Path
    selected_languages: set[str]
    max_files: int = 2000
    max_evidence_snippets: int = 5
    exclude_patterns: list[str] = field(default_factory=list)

    # Shared indexes can be cached here
    _python_index: Any = field(default=None, repr=False)

    # Generic cache for language indexes (Rust, Go, Node, etc.)
    cache: dict[str, Any] = field(default_factory=dict, repr=False)

    def get_python_index(self) -> Any:
        """Get or create Python index (lazy loading)."""
        if self._python_index is None:
            from .python.index import PythonIndex
            self._python_index = PythonIndex(
                self.repo_root,
                max_files=self.max_files,
                exclude_patterns=self.exclude_patterns,
            )
            self._python_index.build()
        return self._python_index


@dataclass
class DetectorResult:
    """Result from a detector run."""

    rules: list[ConventionRule] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class BaseDetector(ABC):
    """Abstract base class for convention detectors."""

    # Override in subclasses
    name: str = "base"
    description: str = "Base detector"
    languages: set[str] = set()  # Empty means language-agnostic

    def __init__(self):
        pass

    def should_run(self, ctx: DetectorContext) -> bool:
        """Check if this detector should run given the context."""
        if not self.languages:
            return True  # Language-agnostic detectors always run
        return bool(self.languages & ctx.selected_languages)

    @abstractmethod
    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """
        Run detection and return results.

        Must be implemented by subclasses.
        """
        pass

    def make_evidence(
        self,
        ctx: DetectorContext,
        file_path: Path,
        line: int,
        radius: int = 5,
    ) -> Optional[EvidenceSnippet]:
        """
        Create an evidence snippet from a file at a given line.

        Args:
            ctx: Detector context
            file_path: Path to the source file
            line: Target line number (1-indexed)
            radius: Number of lines before/after to include

        Returns:
            EvidenceSnippet or None if file cannot be read
        """
        from ..fs import get_relative_path, read_file_safe

        content = read_file_safe(file_path)
        if content is None:
            return None

        lines = content.splitlines()
        total_lines = len(lines)

        if line < 1 or line > total_lines:
            return None

        # Calculate line range (1-indexed)
        line_start = max(1, line - radius)
        line_end = min(total_lines, line + radius)

        # Extract excerpt (convert to 0-indexed for slicing)
        excerpt_lines = lines[line_start - 1 : line_end]
        excerpt = "\n".join(excerpt_lines)

        return EvidenceSnippet(
            file_path=get_relative_path(file_path, ctx.repo_root),
            line_start=line_start,
            line_end=line_end,
            excerpt=excerpt,
        )

    def make_rule(
        self,
        rule_id: str,
        category: str,
        title: str,
        description: str,
        confidence: float,
        language: Optional[str] = None,
        evidence: Optional[list[EvidenceSnippet]] = None,
        stats: Optional[dict[str, Any]] = None,
        docs_url: Optional[str] = None,
    ) -> ConventionRule:
        """Helper to create a ConventionRule with validated fields.

        Args:
            rule_id: Unique rule identifier
            category: Category of the convention
            title: Human-readable title
            description: Detailed description
            confidence: Confidence score (0.0-1.0)
            language: Language this rule applies to
            evidence: Evidence snippets from source code
            stats: Statistics supporting this rule
            docs_url: Explicit documentation URL (if None, auto-detected from stats)

        Returns:
            ConventionRule with documentation URL if available
        """
        final_stats = stats or {}

        # Auto-detect docs URL from stats if not explicitly provided
        if docs_url is None:
            from ..docs_registry import get_docs_url_for_rule
            docs_url = get_docs_url_for_rule(rule_id, final_stats)

        return ConventionRule(
            id=rule_id,
            category=category,
            title=title,
            description=description,
            confidence=min(1.0, max(0.0, confidence)),
            language=language,
            evidence=evidence or [],
            stats=final_stats,
            docs_url=docs_url,
        )


class PythonDetector(BaseDetector):
    """Base class for Python-specific detectors."""

    languages: set[str] = {"python"}

    def get_index(self, ctx: DetectorContext):
        """Get the Python index."""
        return ctx.get_python_index()
