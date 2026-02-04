"""Node.js testing conventions detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import NodeDetector
from .index import NodeIndex, make_evidence


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

        # Detect test file naming conventions
        self._detect_test_file_naming(ctx, index, result)

        # Detect coverage thresholds
        self._detect_coverage_thresholds(ctx, index, result)

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
                    examples[lib].extend([(r, ln) for r, _, ln in imports[:5]])

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

    def _detect_test_file_naming(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect test file naming conventions (*.unit.ts, *.int.ts, *.spec.ts, etc.)."""
        test_files = index.get_test_files()
        if len(test_files) < 3:
            return

        naming_patterns: Counter[str] = Counter()

        for f in test_files:
            rel_path = f.relative_path.lower()
            if ".unit." in rel_path:
                naming_patterns["unit"] += 1
            elif ".int." in rel_path or ".integration." in rel_path:
                naming_patterns["integration"] += 1
            elif ".e2e." in rel_path:
                naming_patterns["e2e"] += 1
            elif ".spec." in rel_path:
                naming_patterns["spec"] += 1
            elif ".test." in rel_path:
                naming_patterns["test"] += 1

        if not naming_patterns:
            return

        # Only report if there's a clear convention
        total = sum(naming_patterns.values())
        if total < 3:
            return

        primary, primary_count = naming_patterns.most_common(1)[0]

        naming_labels = {
            "unit": "*.unit.ts",
            "integration": "*.int.ts / *.integration.ts",
            "e2e": "*.e2e.ts",
            "spec": "*.spec.ts",
            "test": "*.test.ts",
        }

        # Check if multiple naming conventions are used (unit + integration is common)
        has_unit = naming_patterns.get("unit", 0) >= 2
        has_integration = naming_patterns.get("integration", 0) >= 2
        has_e2e = naming_patterns.get("e2e", 0) >= 2

        if has_unit and has_integration:
            title = "Unit/integration test separation"
            description = (
                f"Test files use naming convention to separate test types: "
                f"unit: {naming_patterns.get('unit', 0)}, "
                f"integration: {naming_patterns.get('integration', 0)}."
            )
            if has_e2e:
                description = description[:-1] + f", e2e: {naming_patterns.get('e2e', 0)}."
            confidence = 0.9
        else:
            title = f"Test naming: {naming_labels.get(primary, f'*.{primary}.ts')}"
            description = (
                f"Test files follow {naming_labels.get(primary, f'*.{primary}.ts')} naming convention. "
                f"Found {primary_count} files."
            )
            confidence = min(0.85, 0.6 + primary_count * 0.03)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.test_file_naming",
            category="testing",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=[],
            stats={
                "naming_pattern_counts": dict(naming_patterns),
                "primary_pattern": primary,
                "has_unit_integration_separation": has_unit and has_integration,
            },
        ))

    def _detect_coverage_thresholds(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect configured coverage thresholds."""
        import json
        import re

        from ...fs import read_file_safe

        thresholds: dict[str, float] = {}

        # Check package.json for Jest coverage config
        package_json = ctx.repo_root / "package.json"
        content = read_file_safe(package_json)
        if content:
            try:
                pkg_data = json.loads(content)
                jest_config = pkg_data.get("jest", {})
                coverage_threshold = jest_config.get("coverageThreshold", {})
                global_threshold = coverage_threshold.get("global", {})
                if global_threshold:
                    for key in ["lines", "branches", "functions", "statements"]:
                        if key in global_threshold:
                            thresholds[key] = global_threshold[key]
            except (json.JSONDecodeError, KeyError):
                pass

        # Check jest.config.js/ts
        for jest_config_name in ["jest.config.js", "jest.config.ts", "jest.config.mjs"]:
            jest_config_path = ctx.repo_root / jest_config_name
            jest_content = read_file_safe(jest_config_path)
            if jest_content:
                # Parse coverage thresholds from JS config
                for key in ["lines", "branches", "functions", "statements"]:
                    match = re.search(rf'{key}\s*:\s*(\d+)', jest_content)
                    if match:
                        thresholds[key] = float(match.group(1))

        # Check .nycrc / .nycrc.json for Istanbul/nyc config
        for nyc_config_name in [".nycrc", ".nycrc.json", "nyc.config.js"]:
            nyc_config_path = ctx.repo_root / nyc_config_name
            nyc_content = read_file_safe(nyc_config_path)
            if nyc_content:
                if nyc_config_name.endswith(".json") or nyc_config_name == ".nycrc":
                    try:
                        nyc_data = json.loads(nyc_content)
                        for key in ["lines", "branches", "functions", "statements"]:
                            if key in nyc_data:
                                thresholds[key] = nyc_data[key]
                    except json.JSONDecodeError:
                        pass
                else:
                    for key in ["lines", "branches", "functions", "statements"]:
                        match = re.search(rf'{key}\s*:\s*(\d+)', nyc_content)
                        if match:
                            thresholds[key] = float(match.group(1))

        if not thresholds:
            return

        # Determine strictness level
        line_threshold = thresholds.get("lines", 0)
        branch_threshold = thresholds.get("branches", 0)

        if line_threshold >= 90 and branch_threshold >= 90:
            title = "High coverage requirements"
            strictness = "strict"
        elif line_threshold >= 80 or branch_threshold >= 80:
            title = "Moderate coverage requirements"
            strictness = "moderate"
        else:
            title = "Coverage thresholds configured"
            strictness = "basic"

        threshold_strs = [f"{k}: {v}%" for k, v in sorted(thresholds.items())]
        description = f"Coverage thresholds: {', '.join(threshold_strs)}."

        confidence = 0.95

        result.rules.append(self.make_rule(
            rule_id="node.conventions.coverage_thresholds",
            category="testing",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=[],
            stats={
                "thresholds": thresholds,
                "strictness": strictness,
            },
        ))
