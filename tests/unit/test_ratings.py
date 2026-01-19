"""Tests for rating rules and scoring."""
from __future__ import annotations

import pytest

from conventions.ratings import (
    DEFAULT_RATING_RULE,
    RATING_RULES,
    SCORE_LABELS,
    get_rating_rule,
    get_score_label,
    rate_convention,
)
from conventions.schemas import ConventionRule, EvidenceSnippet


def make_rule(rule_id: str, **stats) -> ConventionRule:
    """Helper to create a rule with given stats."""
    return ConventionRule(
        id=rule_id,
        category="test",
        title="Test Rule",
        description="Test description",
        confidence=0.9,
        language="python",
        evidence=[],
        stats=stats,
    )


class TestRatingRules:
    """Tests for rating rule registry."""

    def test_get_known_rule(self):
        """Test getting a known rating rule."""
        rule = get_rating_rule("python.conventions.typing_coverage")
        assert rule is not None
        assert rule != DEFAULT_RATING_RULE

    def test_get_unknown_rule(self):
        """Test getting an unknown rule returns default."""
        rule = get_rating_rule("unknown.rule.id")
        assert rule == DEFAULT_RATING_RULE

    def test_all_rules_have_required_functions(self):
        """Test that all rating rules have required functions."""
        for rule_id, rule in RATING_RULES.items():
            assert callable(rule.score_func), f"{rule_id} missing score_func"
            assert callable(rule.reason_func), f"{rule_id} missing reason_func"
            assert callable(rule.suggestion_func), f"{rule_id} missing suggestion_func"


class TestTypingCoverageRating:
    """Tests for Python typing coverage rating."""

    @pytest.mark.parametrize("coverage,expected_score", [
        (0.95, 5),  # Excellent
        (0.90, 5),
        (0.85, 4),  # Good
        (0.70, 4),
        (0.65, 3),  # Average
        (0.50, 3),
        (0.35, 2),  # Below Average
        (0.30, 2),
        (0.25, 1),  # Poor
        (0.0, 1),
    ])
    def test_typing_coverage_scores(self, coverage: float, expected_score: int):
        """Test typing coverage score boundaries."""
        rule = make_rule(
            "python.conventions.typing_coverage",
            any_annotation_coverage=coverage
        )
        score, reason, suggestion = rate_convention(rule)
        assert score == expected_score, f"Coverage {coverage} expected score {expected_score}, got {score}"

    def test_typing_coverage_reason(self):
        """Test typing coverage reason includes percentage."""
        rule = make_rule(
            "python.conventions.typing_coverage",
            any_annotation_coverage=0.75
        )
        score, reason, suggestion = rate_convention(rule)
        assert "75%" in reason

    def test_typing_coverage_suggestion(self):
        """Test typing coverage provides suggestion for low scores."""
        rule = make_rule(
            "python.conventions.typing_coverage",
            any_annotation_coverage=0.2
        )
        score, reason, suggestion = rate_convention(rule)
        assert score <= 2
        assert suggestion is not None
        assert "type" in suggestion.lower()

    def test_typing_coverage_no_suggestion_for_excellent(self):
        """Test no suggestion when typing coverage is excellent."""
        rule = make_rule(
            "python.conventions.typing_coverage",
            any_annotation_coverage=0.95
        )
        score, reason, suggestion = rate_convention(rule)
        assert score == 5
        assert suggestion is None


class TestTestingFrameworkRating:
    """Tests for testing framework rating."""

    def test_pytest_with_many_tests(self):
        """Test pytest with many test files scores excellent."""
        rule = make_rule(
            "python.conventions.testing_framework",
            primary_framework="pytest",
            test_file_count=10
        )
        score, reason, suggestion = rate_convention(rule)
        assert score == 5

    def test_pytest_with_few_tests(self):
        """Test pytest with few test files scores good."""
        rule = make_rule(
            "python.conventions.testing_framework",
            primary_framework="pytest",
            test_file_count=2
        )
        score, reason, suggestion = rate_convention(rule)
        assert score == 4

    def test_unittest_framework(self):
        """Test unittest framework scores lower."""
        rule = make_rule(
            "python.conventions.testing_framework",
            primary_framework="unittest",
            test_file_count=10
        )
        score, reason, suggestion = rate_convention(rule)
        assert score == 3
        assert "pytest" in suggestion.lower()

    def test_no_tests(self):
        """Test no tests scores poor."""
        rule = make_rule(
            "python.conventions.testing_framework",
            primary_framework="unknown",
            test_file_count=0
        )
        score, reason, suggestion = rate_convention(rule)
        assert score == 1


class TestLoggingRating:
    """Tests for logging library rating."""

    @pytest.mark.parametrize("library,expected_min_score", [
        ("structlog", 4),
        ("loguru", 4),
        ("stdlib_logging", 2),
    ])
    def test_logging_library_scores(self, library: str, expected_min_score: int):
        """Test logging library scores by library type."""
        rule = make_rule(
            "python.conventions.logging_library",
            primary_library=library,
            primary_ratio=0.9
        )
        score, reason, suggestion = rate_convention(rule)
        assert score >= expected_min_score


class TestGenericRating:
    """Tests for generic/fallback rating."""

    @pytest.mark.parametrize("confidence,expected_score", [
        (0.95, 4),
        (0.75, 3),
        (0.55, 2),
        (0.25, 1),
    ])
    def test_generic_rating_by_confidence(self, confidence: float, expected_score: int):
        """Test generic rating uses confidence as proxy."""
        rule = make_rule("unknown.rule.id")
        rule.confidence = confidence
        score, reason, suggestion = rate_convention(rule)
        assert score == expected_score


class TestScoreLabels:
    """Tests for score label functions."""

    @pytest.mark.parametrize("score,label", [
        (1, "Poor"),
        (2, "Below Average"),
        (3, "Average"),
        (4, "Good"),
        (5, "Excellent"),
    ])
    def test_score_labels(self, score: int, label: str):
        """Test score labels are correct."""
        assert get_score_label(score) == label

    def test_unknown_score_label(self):
        """Test unknown score returns Unknown."""
        assert get_score_label(0) == "Unknown"
        assert get_score_label(6) == "Unknown"


class TestRateConvention:
    """Tests for the rate_convention function."""

    def test_returns_tuple(self, sample_rule: ConventionRule):
        """Test rate_convention returns correct tuple structure."""
        result = rate_convention(sample_rule)
        assert isinstance(result, tuple)
        assert len(result) == 3
        score, reason, suggestion = result
        assert isinstance(score, int)
        assert isinstance(reason, str)
        assert suggestion is None or isinstance(suggestion, str)

    def test_score_in_range(self, sample_rule: ConventionRule):
        """Test score is always in 1-5 range."""
        score, _, _ = rate_convention(sample_rule)
        assert 1 <= score <= 5

    def test_reason_not_empty(self, sample_rule: ConventionRule):
        """Test reason is never empty."""
        _, reason, _ = rate_convention(sample_rule)
        assert len(reason) > 0


class TestGoRules:
    """Tests for Go-specific rating rules."""

    def test_go_doc_comments(self):
        """Test Go doc comments rating."""
        rule = make_rule(
            "go.conventions.doc_comments",
            doc_ratio=0.85
        )
        score, reason, suggestion = rate_convention(rule)
        assert score >= 4

    def test_go_table_driven_tests(self):
        """Test Go table-driven tests rating."""
        rule = make_rule(
            "go.conventions.table_driven_tests",
            table_test_count=10
        )
        score, reason, suggestion = rate_convention(rule)
        assert score >= 4


class TestNodeRules:
    """Tests for Node.js-specific rating rules."""

    def test_node_strict_mode(self):
        """Test TypeScript strict mode rating."""
        rule = make_rule(
            "node.conventions.strict_mode",
            has_strict=True
        )
        score, reason, suggestion = rate_convention(rule)
        assert score == 5

    def test_node_type_coverage(self):
        """Test Node type coverage rating."""
        rule = make_rule(
            "node.conventions.type_coverage",
            any_ratio=0.02
        )
        score, reason, suggestion = rate_convention(rule)
        assert score == 5


class TestRustRules:
    """Tests for Rust-specific rating rules."""

    def test_rust_cargo_edition(self):
        """Test Rust cargo edition rating."""
        rule = make_rule(
            "rust.conventions.cargo",
            edition="2021",
            has_gomod=True
        )
        score, reason, suggestion = rate_convention(rule)
        assert score == 5

    def test_rust_error_handling(self):
        """Test Rust error handling rating."""
        rule = make_rule(
            "rust.conventions.error_handling",
            patterns=["thiserror", "anyhow"]
        )
        score, reason, suggestion = rate_convention(rule)
        assert score == 5
