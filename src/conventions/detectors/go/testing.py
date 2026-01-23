"""Go testing conventions detector."""

from __future__ import annotations

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import GoDetector
from .index import GoIndex, make_evidence


@DetectorRegistry.register
class GoTestingDetector(GoDetector):
    """Detect Go testing conventions."""

    name = "go_testing"
    description = "Detects Go testing patterns and frameworks"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Go testing conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        test_files = index.get_test_files()
        if not test_files:
            return result

        # Detect table-driven tests
        self._detect_table_driven_tests(ctx, index, result)

        # Detect test helpers
        self._detect_test_helpers(ctx, index, result)

        # Detect subtests
        self._detect_subtests(ctx, index, result)

        # Detect testing framework
        self._detect_testing_framework(ctx, index, result)

        return result

    def _detect_table_driven_tests(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect table-driven test pattern."""
        # Look for patterns like: tests := []struct, testCases := []struct
        table_pattern = r"(?:tests|testCases|cases|tt)\s*:?=\s*\[\]struct\s*\{"
        matches = index.search_pattern(table_pattern, limit=50)

        if len(matches) < 2:
            return

        title = "Table-driven tests"
        description = (
            f"Uses Go's table-driven test pattern. "
            f"Found {len(matches)} table-driven test instances."
        )
        confidence = min(0.95, 0.7 + len(matches) * 0.03)

        evidence = []
        for rel_path, line, _ in matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.table_driven_tests",
            category="testing",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "table_test_count": len(matches),
            },
        ))

    def _detect_test_helpers(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect t.Helper() usage."""
        helper_pattern = r"t\.Helper\(\)"
        matches = index.search_pattern(helper_pattern, limit=50)

        if len(matches) < 2:
            return

        title = "Uses test helpers"
        description = (
            f"Uses t.Helper() for better test failure messages. "
            f"Found {len(matches)} helper functions."
        )
        confidence = min(0.9, 0.6 + len(matches) * 0.05)

        evidence = []
        for rel_path, line, _ in matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.test_helpers",
            category="testing",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "helper_count": len(matches),
            },
        ))

    def _detect_subtests(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect t.Run() subtest usage."""
        subtest_pattern = r"t\.Run\("
        matches = index.search_pattern(subtest_pattern, limit=100)

        if len(matches) < 3:
            return

        title = "Uses subtests"
        description = (
            f"Uses t.Run() for subtests. "
            f"Found {len(matches)} subtest invocations."
        )
        confidence = min(0.95, 0.7 + len(matches) * 0.02)

        evidence = []
        for rel_path, line, _ in matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.subtests",
            category="testing",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "subtest_count": len(matches),
            },
        ))

    def _detect_testing_framework(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect third-party testing framework usage."""
        frameworks = {
            "testify": "github.com/stretchr/testify",
            "gomega": "github.com/onsi/gomega",
            "ginkgo": "github.com/onsi/ginkgo",
            "gocheck": "gopkg.in/check",
            "goconvey": "github.com/smartystreets/goconvey",
        }

        framework_counts: dict[str, int] = {}
        examples: dict[str, list[tuple[str, int]]] = {}

        for name, pkg in frameworks.items():
            imports = index.find_imports_matching(pkg, limit=20)
            if imports:
                framework_counts[name] = len(imports)
                examples[name] = [(r, ln) for r, _, ln in imports[:5]]

        if not framework_counts:
            return

        primary = max(framework_counts, key=framework_counts.get)  # type: ignore
        primary_count = framework_counts[primary]

        framework_names = {
            "testify": "Testify",
            "gomega": "Gomega",
            "ginkgo": "Ginkgo",
            "gocheck": "gocheck",
            "goconvey": "GoConvey",
        }

        title = f"Testing with {framework_names.get(primary, primary)}"
        description = (
            f"Uses {framework_names.get(primary, primary)} testing framework. "
            f"Found {primary_count} imports."
        )
        confidence = min(0.95, 0.7 + primary_count * 0.03)

        evidence = []
        for rel_path, line in examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.testing_framework",
            category="testing",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "framework_counts": framework_counts,
                "primary_framework": primary,
            },
        ))
