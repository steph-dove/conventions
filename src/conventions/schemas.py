"""Pydantic schemas for conventions detection output."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Language(str, Enum):
    """Supported programming languages."""
    PYTHON = "python"
    GO = "go"
    NODE = "node"


class EvidenceSnippet(BaseModel):
    """A code snippet providing evidence for a convention."""

    file_path: str = Field(..., description="Relative path to the file")
    line_start: int = Field(..., description="Starting line number (1-indexed)")
    line_end: int = Field(..., description="Ending line number (1-indexed)")
    excerpt: str = Field(..., description="Code excerpt with context (~5 lines before/after)")

    class Config:
        extra = "forbid"


class ConventionRule(BaseModel):
    """A detected convention rule with evidence."""

    id: str = Field(..., description="Unique rule identifier (e.g., 'python.conventions.typing_coverage')")
    category: str = Field(..., description="Category of the convention (e.g., 'typing', 'error_handling')")
    title: str = Field(..., description="Human-readable title")
    description: str = Field(..., description="Detailed description of the observed convention")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    language: Optional[str] = Field(None, description="Language this rule applies to (python/go/node/None)")
    evidence: list[EvidenceSnippet] = Field(default_factory=list, description="Evidence snippets from source code")
    stats: dict[str, Any] = Field(default_factory=dict, description="Statistics supporting this rule")
    docs_url: Optional[str] = Field(None, description="URL to relevant documentation for this convention/tool")

    class Config:
        extra = "forbid"


class DetectorWarning(BaseModel):
    """A warning from a detector that didn't fully succeed."""

    detector: str = Field(..., description="Name of the detector that produced the warning")
    message: str = Field(..., description="Warning message")

    class Config:
        extra = "forbid"


class RepoMetadata(BaseModel):
    """Metadata about the scanned repository."""

    path: str = Field(..., description="Absolute path to the repository")
    detected_languages: list[str] = Field(default_factory=list, description="Detected programming languages")
    total_files_scanned: int = Field(0, description="Number of files scanned")

    class Config:
        extra = "forbid"


class ConventionsOutput(BaseModel):
    """Root output schema for conventions detection."""

    version: str = Field("1.0.0", description="Schema version")
    metadata: RepoMetadata = Field(..., description="Repository metadata")
    rules: list[ConventionRule] = Field(default_factory=list, description="Detected convention rules")
    warnings: list[DetectorWarning] = Field(default_factory=list, description="Warnings from detectors")

    class Config:
        extra = "forbid"
