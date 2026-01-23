"""Rust testing conventions detector."""

from __future__ import annotations

import re

from ..base import DetectorContext, DetectorResult
from .base import RustDetector
from .index import make_evidence
from ..registry import DetectorRegistry


@DetectorRegistry.register
class RustTestingDetector(RustDetector):
    """Detect Rust testing conventions."""

    name = "rust_testing"
    description = "Detects Rust testing patterns and test frameworks"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect testing conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        patterns: dict[str, dict] = {}
        examples: list[tuple[str, int]] = []

        # Count #[test] attributes
        test_attrs = index.search_pattern(r"#\[test\]", limit=100)
        if test_attrs:
            patterns["unit_tests"] = {
                "name": "Unit tests",
                "count": len(test_attrs),
            }
            examples.extend([(r, l) for r, l, _ in test_attrs[:3]])

        # Count #[cfg(test)] modules
        cfg_test = index.search_pattern(r"#\[cfg\(test\)\]", limit=50)
        if cfg_test:
            patterns["test_modules"] = {
                "name": "Test modules",
                "count": len(cfg_test),
            }

        # Check for integration tests directory
        tests_dir = ctx.repo_root / "tests"
        integration_test_count = 0
        if tests_dir.is_dir():
            integration_test_count = len(list(tests_dir.glob("**/*.rs")))
            if integration_test_count > 0:
                patterns["integration_tests"] = {
                    "name": "Integration tests",
                    "count": integration_test_count,
                }

        # Check for proptest
        proptest_uses = index.find_uses_matching("proptest", limit=20)
        if proptest_uses:
            patterns["proptest"] = {
                "name": "Property testing (proptest)",
                "count": len(proptest_uses),
            }
            examples.extend([(r, l) for r, _, l in proptest_uses[:2]])

        # Check for quickcheck
        quickcheck_uses = index.find_uses_matching("quickcheck", limit=20)
        if quickcheck_uses:
            patterns["quickcheck"] = {
                "name": "Property testing (quickcheck)",
                "count": len(quickcheck_uses),
            }

        # Check for test-case (parameterized tests)
        test_case_attrs = index.search_pattern(r"#\[test_case\(", limit=30)
        if test_case_attrs:
            patterns["test_case"] = {
                "name": "Parameterized tests",
                "count": len(test_case_attrs),
            }

        # Check for rstest
        rstest_attrs = index.search_pattern(r"#\[rstest\]", limit=30)
        if rstest_attrs:
            patterns["rstest"] = {
                "name": "rstest framework",
                "count": len(rstest_attrs),
            }

        # Check for criterion (benchmarks)
        criterion_uses = index.find_uses_matching("criterion", limit=20)
        if criterion_uses:
            patterns["criterion"] = {
                "name": "Criterion benchmarks",
                "count": len(criterion_uses),
            }

        # Check for mockall
        mockall_uses = index.find_uses_matching("mockall", limit=20)
        if mockall_uses:
            patterns["mockall"] = {
                "name": "Mockall mocking",
                "count": len(mockall_uses),
            }

        # Check for assert macros patterns
        assert_eq_count = index.count_pattern(r"assert_eq!\(")
        assert_ne_count = index.count_pattern(r"assert_ne!\(")
        assert_count = index.count_pattern(r"assert!\(")

        if not patterns:
            return result

        pattern_names = [p["name"] for p in patterns.values()]
        total_tests = patterns.get("unit_tests", {}).get("count", 0)
        total_tests += integration_test_count

        title = f"Testing: {total_tests} tests"
        description = f"Has {total_tests} test(s)."

        if "proptest" in patterns or "quickcheck" in patterns:
            description += " Uses property-based testing."

        if "criterion" in patterns:
            description += " Uses Criterion for benchmarks."

        if "mockall" in patterns:
            description += " Uses Mockall for mocking."

        confidence = min(0.95, 0.7 + total_tests * 0.01)

        evidence = []
        for rel_path, line in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="rust.conventions.testing",
            category="testing",
            title=title,
            description=description,
            confidence=confidence,
            language="rust",
            evidence=evidence,
            stats={
                "total_tests": total_tests,
                "patterns": list(patterns.keys()),
                "pattern_details": patterns,
                "assert_eq_count": assert_eq_count,
                "assert_count": assert_count,
            },
        ))

        return result
