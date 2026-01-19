"""Node.js testing conventions detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult
from .base import NodeDetector
from .index import NodeIndex, make_evidence
from ..registry import DetectorRegistry


@DetectorRegistry.register
class NodeTestingDetector(NodeDetector):
    """Detect Node.js testing conventions."""

    name = "node_testing"
    description = "Detects Node.js testing patterns and frameworks"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Node.js testing conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        test_files = index.get_test_files()
        if not test_files:
            return result

        # Detect test patterns (describe/it)
        self._detect_test_patterns(ctx, index, result)

        # Detect mocking library
        self._detect_mocking(ctx, index, result)

        # Detect coverage configuration
        self._detect_coverage_config(ctx, index, result)

        return result

    def _detect_test_patterns(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect describe/it test patterns."""
        # describe blocks
        describe_pattern = r'\bdescribe\s*\(\s*[\'"`]'
        describe_matches = index.search_pattern(describe_pattern, limit=100)
        describe_count = len(describe_matches)

        # it/test blocks
        it_pattern = r'\b(?:it|test)\s*\(\s*[\'"`]'
        it_matches = index.search_pattern(it_pattern, limit=200)
        it_count = len(it_matches)

        # beforeEach/afterEach hooks
        hook_pattern = r'\b(?:beforeEach|afterEach|beforeAll|afterAll)\s*\('
        hook_count = index.count_pattern(hook_pattern)

        if it_count < 3:
            return

        if describe_count >= 3:
            title = "BDD-style tests (describe/it)"
            description = (
                f"Uses BDD-style testing with describe/it blocks. "
                f"describe: {describe_count}, it/test: {it_count}, hooks: {hook_count}."
            )
            confidence = min(0.95, 0.7 + describe_count * 0.02)
        else:
            title = "Test suite structure"
            description = (
                f"Test files with {it_count} test cases. "
                f"describe: {describe_count}, hooks: {hook_count}."
            )
            confidence = 0.8

        evidence = []
        for rel_path, line, _ in describe_matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=4)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.test_patterns",
            category="testing",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "describe_count": describe_count,
                "it_test_count": it_count,
                "hook_count": hook_count,
            },
        ))

    def _detect_mocking(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect mocking library usage."""
        mock_libs = {
            "jest_mock": ["jest.mock", "jest.fn", "jest.spyOn"],
            "sinon": ["sinon"],
            "nock": ["nock"],
            "msw": ["msw", "@mswjs"],
        }

        lib_counts: Counter[str] = Counter()
        examples: dict[str, list[tuple[str, int]]] = {}

        for lib, patterns in mock_libs.items():
            for pattern in patterns:
                imports = index.find_imports_matching(pattern, limit=10)
                if imports:
                    lib_counts[lib] += len(imports)
                    if lib not in examples:
                        examples[lib] = []
                    examples[lib].extend([(r, l) for r, _, l in imports[:5]])

        # Also check for inline usage
        jest_fn_count = index.count_pattern(r'jest\.(?:fn|mock|spyOn)\s*\(')
        if jest_fn_count >= 3:
            lib_counts["jest_mock"] += jest_fn_count // 3

        if not lib_counts:
            return

        primary = max(lib_counts, key=lib_counts.get)  # type: ignore
        primary_count = lib_counts[primary]

        lib_names = {
            "jest_mock": "Jest mocks",
            "sinon": "Sinon",
            "nock": "Nock (HTTP)",
            "msw": "MSW (Mock Service Worker)",
        }

        title = f"Mocking with {lib_names.get(primary, primary)}"
        description = (
            f"Uses {lib_names.get(primary, primary)} for test mocking. "
            f"Found {primary_count} usages."
        )
        confidence = min(0.9, 0.6 + primary_count * 0.05)

        evidence = []
        for rel_path, line in examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.mocking",
            category="testing",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "mock_library_counts": dict(lib_counts),
                "primary_library": primary,
            },
        ))

    def _detect_coverage_config(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect test coverage configuration."""
        from ...fs import read_file_safe

        # Check package.json for coverage config
        package_json = ctx.repo_root / "package.json"
        content = read_file_safe(package_json)

        has_coverage_script = False
        has_jest_coverage = False
        has_nyc = False
        has_c8 = False

        if content:
            has_coverage_script = '"coverage"' in content or '"test:coverage"' in content
            has_jest_coverage = '"collectCoverage"' in content or '--coverage' in content
            has_nyc = '"nyc"' in content
            has_c8 = '"c8"' in content

        # Check for coverage config files
        coverage_files = [
            ctx.repo_root / ".nycrc",
            ctx.repo_root / ".nycrc.json",
            ctx.repo_root / "jest.config.js",
            ctx.repo_root / "jest.config.ts",
        ]

        has_coverage_file = any(f.exists() for f in coverage_files)

        if not (has_coverage_script or has_jest_coverage or has_nyc or has_c8 or has_coverage_file):
            return

        tools = []
        if has_jest_coverage:
            tools.append("Jest")
        if has_nyc:
            tools.append("nyc/Istanbul")
        if has_c8:
            tools.append("c8")

        title = "Test coverage configured"
        if tools:
            description = f"Test coverage configured with {', '.join(tools)}."
        else:
            description = "Test coverage script configured in package.json."
        confidence = 0.85

        result.rules.append(self.make_rule(
            rule_id="node.conventions.coverage_config",
            category="testing",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=[],
            stats={
                "has_coverage_script": has_coverage_script,
                "coverage_tools": tools,
            },
        ))
