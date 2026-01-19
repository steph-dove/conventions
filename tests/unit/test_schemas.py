"""Tests for Pydantic schemas."""
from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from conventions.schemas import (
    ConventionRule,
    ConventionsOutput,
    DetectorWarning,
    EvidenceSnippet,
    Language,
    RepoMetadata,
)


class TestLanguageEnum:
    """Tests for Language enum."""

    def test_language_values(self):
        """Test language enum values."""
        assert Language.PYTHON.value == "python"
        assert Language.GO.value == "go"
        assert Language.NODE.value == "node"


class TestEvidenceSnippet:
    """Tests for EvidenceSnippet model."""

    def test_valid_snippet(self):
        """Test creating a valid evidence snippet."""
        snippet = EvidenceSnippet(
            file_path="src/main.py",
            line_start=10,
            line_end=15,
            excerpt="def hello():\n    return 'world'"
        )
        assert snippet.file_path == "src/main.py"
        assert snippet.line_start == 10
        assert snippet.line_end == 15

    def test_snippet_requires_all_fields(self):
        """Test that all fields are required."""
        with pytest.raises(ValidationError):
            EvidenceSnippet(
                file_path="src/main.py",
                # Missing line_start, line_end, excerpt
            )

    def test_snippet_forbids_extra_fields(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValidationError):
            EvidenceSnippet(
                file_path="src/main.py",
                line_start=10,
                line_end=15,
                excerpt="code",
                extra_field="not allowed"
            )


class TestConventionRule:
    """Tests for ConventionRule model."""

    def test_valid_rule(self, sample_rule: ConventionRule):
        """Test creating a valid convention rule."""
        assert sample_rule.id == "python.conventions.testing_framework"
        assert sample_rule.category == "testing"
        assert sample_rule.confidence == 0.95
        assert len(sample_rule.evidence) == 1

    def test_rule_with_minimal_fields(self):
        """Test creating a rule with minimal required fields."""
        rule = ConventionRule(
            id="test.rule",
            category="test",
            title="Test Rule",
            description="A test rule",
            confidence=0.5,
        )
        assert rule.language is None
        assert rule.evidence == []
        assert rule.stats == {}

    def test_confidence_range_validation(self):
        """Test confidence must be between 0 and 1."""
        # Valid range
        rule = ConventionRule(
            id="test", category="test", title="T", description="D",
            confidence=0.5
        )
        assert rule.confidence == 0.5

        # Test boundaries
        rule_zero = ConventionRule(
            id="test", category="test", title="T", description="D",
            confidence=0.0
        )
        assert rule_zero.confidence == 0.0

        rule_one = ConventionRule(
            id="test", category="test", title="T", description="D",
            confidence=1.0
        )
        assert rule_one.confidence == 1.0

        # Invalid: greater than 1
        with pytest.raises(ValidationError):
            ConventionRule(
                id="test", category="test", title="T", description="D",
                confidence=1.5
            )

        # Invalid: less than 0
        with pytest.raises(ValidationError):
            ConventionRule(
                id="test", category="test", title="T", description="D",
                confidence=-0.1
            )

    def test_rule_serialization(self, sample_rule: ConventionRule):
        """Test rule can be serialized to JSON."""
        json_str = sample_rule.model_dump_json()
        data = json.loads(json_str)
        assert data["id"] == "python.conventions.testing_framework"
        assert data["confidence"] == 0.95


class TestDetectorWarning:
    """Tests for DetectorWarning model."""

    def test_valid_warning(self):
        """Test creating a valid warning."""
        warning = DetectorWarning(
            detector="test_detector",
            message="Something went wrong"
        )
        assert warning.detector == "test_detector"
        assert warning.message == "Something went wrong"

    def test_warning_requires_all_fields(self):
        """Test that all fields are required."""
        with pytest.raises(ValidationError):
            DetectorWarning(detector="test")


class TestRepoMetadata:
    """Tests for RepoMetadata model."""

    def test_valid_metadata(self):
        """Test creating valid metadata."""
        meta = RepoMetadata(
            path="/test/repo",
            detected_languages=["python", "go"],
            total_files_scanned=100
        )
        assert meta.path == "/test/repo"
        assert "python" in meta.detected_languages
        assert meta.total_files_scanned == 100

    def test_metadata_defaults(self):
        """Test metadata default values."""
        meta = RepoMetadata(path="/test")
        assert meta.detected_languages == []
        assert meta.total_files_scanned == 0


class TestConventionsOutput:
    """Tests for ConventionsOutput model."""

    def test_valid_output(self, sample_output: ConventionsOutput):
        """Test creating valid output."""
        assert sample_output.version == "1.0.0"
        assert len(sample_output.rules) == 1
        assert sample_output.warnings == []

    def test_output_with_warnings(self, sample_output: ConventionsOutput):
        """Test output with warnings."""
        output = ConventionsOutput(
            metadata=sample_output.metadata,
            rules=sample_output.rules,
            warnings=[
                DetectorWarning(
                    detector="test",
                    message="A warning"
                )
            ]
        )
        assert len(output.warnings) == 1

    def test_output_serialization(self, sample_output: ConventionsOutput):
        """Test full output serialization."""
        json_str = sample_output.model_dump_json(indent=2)
        data = json.loads(json_str)
        assert data["version"] == "1.0.0"
        assert len(data["rules"]) == 1
        assert data["metadata"]["path"] == "/test/repo"

    def test_output_deserialization(self, sample_output: ConventionsOutput):
        """Test output can be deserialized."""
        json_str = sample_output.model_dump_json()
        data = json.loads(json_str)
        restored = ConventionsOutput.model_validate(data)
        assert restored.version == sample_output.version
        assert len(restored.rules) == len(sample_output.rules)
        assert restored.rules[0].id == sample_output.rules[0].id

    def test_empty_output(self):
        """Test creating output with no rules."""
        output = ConventionsOutput(
            metadata=RepoMetadata(path="/empty"),
            rules=[],
            warnings=[]
        )
        assert len(output.rules) == 0

    def test_output_version_default(self):
        """Test output has default version."""
        output = ConventionsOutput(
            metadata=RepoMetadata(path="/test")
        )
        assert output.version == "1.0.0"
