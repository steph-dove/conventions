"""Integration tests for report generation."""
from __future__ import annotations

from pathlib import Path

import pytest

from conventions.report import (
    generate_markdown_report,
    generate_review_markdown,
    write_markdown_report,
    write_review_report,
)
from conventions.schemas import ConventionRule, ConventionsOutput, EvidenceSnippet, RepoMetadata


@pytest.fixture
def multi_rule_output() -> ConventionsOutput:
    """Create output with multiple rules of varying scores."""
    rules = [
        ConventionRule(
            id="python.conventions.typing_coverage",
            category="typing",
            title="Type Annotation Coverage",
            description="Coverage of type annotations in functions",
            confidence=0.95,
            language="python",
            evidence=[
                EvidenceSnippet(
                    file_path="src/main.py",
                    line_start=1,
                    line_end=10,
                    excerpt="def typed_func(x: int) -> int:\n    return x * 2",
                )
            ],
            stats={"any_annotation_coverage": 0.85},
        ),
        ConventionRule(
            id="python.conventions.testing_framework",
            category="testing",
            title="Testing Framework",
            description="Primary testing framework used",
            confidence=0.90,
            language="python",
            evidence=[
                EvidenceSnippet(
                    file_path="tests/test_main.py",
                    line_start=1,
                    line_end=5,
                    excerpt="import pytest\n\ndef test_func():\n    assert True",
                )
            ],
            stats={"primary_framework": "pytest", "test_file_count": 10},
        ),
        ConventionRule(
            id="python.conventions.docstrings",
            category="documentation",
            title="Docstring Coverage",
            description="Coverage of docstrings in functions",
            confidence=0.80,
            language="python",
            evidence=[],
            stats={"function_doc_ratio": 0.3},
        ),
    ]

    return ConventionsOutput(
        version="1.0.0",
        metadata=RepoMetadata(
            path="/test/project",
            detected_languages=["python"],
            total_files_scanned=50,
        ),
        rules=rules,
        warnings=[],
    )


class TestMarkdownReport:
    """Tests for markdown report generation."""

    def test_generate_markdown_report(self, sample_output: ConventionsOutput):
        """Test markdown report generation."""
        report = generate_markdown_report(sample_output)

        assert "# Code Conventions Report" in report
        assert "## Summary" in report
        assert "/test/repo" in report
        assert "python" in report
        assert "testing_framework" in report

    def test_markdown_report_includes_rules_table(self, multi_rule_output: ConventionsOutput):
        """Test markdown report includes rules table."""
        report = generate_markdown_report(multi_rule_output)

        assert "## Detected Conventions" in report
        assert "| ID | Title | Confidence | Evidence |" in report
        assert "typing_coverage" in report
        assert "testing_framework" in report

    def test_markdown_report_includes_details(self, multi_rule_output: ConventionsOutput):
        """Test markdown report includes detailed rule sections."""
        report = generate_markdown_report(multi_rule_output)

        assert "## Convention Details" in report
        assert "### Type Annotation Coverage" in report
        assert "**Statistics:**" in report

    def test_markdown_report_includes_evidence(self, multi_rule_output: ConventionsOutput):
        """Test markdown report includes evidence snippets."""
        report = generate_markdown_report(multi_rule_output)

        assert "**Evidence:**" in report
        assert "```" in report  # Code block
        assert "src/main.py" in report

    def test_write_markdown_report(self, tmp_path: Path, sample_output: ConventionsOutput):
        """Test writing markdown report to file."""
        report_path = write_markdown_report(sample_output, tmp_path)

        assert report_path.exists()
        assert report_path.name == "conventions.md"
        content = report_path.read_text()
        assert "# Code Conventions Report" in content


class TestReviewReport:
    """Tests for review report generation."""

    def test_generate_review_report(self, sample_output: ConventionsOutput):
        """Test review report generation."""
        report = generate_review_markdown(sample_output)

        assert "# Conventions Review Report" in report
        assert "## Score Legend" in report
        assert "## Summary" in report
        assert "Average Score" in report

    def test_review_report_includes_scores_table(self, multi_rule_output: ConventionsOutput):
        """Test review report includes scores overview table."""
        report = generate_review_markdown(multi_rule_output)

        assert "## Scores Overview" in report
        assert "| Convention | Score | Rating |" in report

    def test_review_report_groups_by_score(self, multi_rule_output: ConventionsOutput):
        """Test review report groups rules by score."""
        report = generate_review_markdown(multi_rule_output)

        assert "## Detailed Reviews" in report
        # Should have score group headers
        score_headers = ["### Excellent (5/5)", "### Good (4/5)", "### Average (3/5)"]
        # At least one score group should be present
        assert any(header in report for header in score_headers)

    def test_review_report_includes_suggestions(self, multi_rule_output: ConventionsOutput):
        """Test review report includes improvement suggestions."""
        report = generate_review_markdown(multi_rule_output)

        # Rules with non-perfect scores should have suggestions
        assert "**Suggestion:**" in report or "**Assessment:**" in report

    def test_review_report_includes_priorities(self, multi_rule_output: ConventionsOutput):
        """Test review report includes improvement priorities."""
        report = generate_review_markdown(multi_rule_output)

        assert "## Improvement Priorities" in report

    def test_write_review_report(self, tmp_path: Path, sample_output: ConventionsOutput):
        """Test writing review report to file."""
        report_path = write_review_report(sample_output, tmp_path)

        assert report_path.exists()
        assert report_path.name == "conventions-review.md"
        content = report_path.read_text()
        assert "# Conventions Review Report" in content


class TestEmptyOutput:
    """Tests for handling empty output."""

    def test_markdown_report_with_no_rules(self):
        """Test markdown report with no rules."""
        output = ConventionsOutput(
            metadata=RepoMetadata(
                path="/empty/project",
                detected_languages=[],
                total_files_scanned=0,
            ),
            rules=[],
            warnings=[],
        )

        report = generate_markdown_report(output)
        assert "# Code Conventions Report" in report
        assert "Conventions detected:** 0" in report

    def test_review_report_with_no_rules(self):
        """Test review report with no rules."""
        output = ConventionsOutput(
            metadata=RepoMetadata(
                path="/empty/project",
                detected_languages=[],
                total_files_scanned=0,
            ),
            rules=[],
            warnings=[],
        )

        report = generate_review_markdown(output)
        assert "# Conventions Review Report" in report
        assert "No conventions detected to review" in report


class TestReportWithWarnings:
    """Tests for reports with warnings."""

    def test_markdown_report_includes_warnings(self, sample_output: ConventionsOutput):
        """Test markdown report includes warnings section."""
        from conventions.schemas import DetectorWarning

        output = ConventionsOutput(
            metadata=sample_output.metadata,
            rules=sample_output.rules,
            warnings=[
                DetectorWarning(detector="test_detector", message="Test warning"),
            ],
        )

        report = generate_markdown_report(output)
        assert "## Warnings" in report
        assert "test_detector" in report
        assert "Test warning" in report
