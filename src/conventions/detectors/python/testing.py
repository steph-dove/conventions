"""Python testing conventions detector."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from ..base import DetectorContext, DetectorResult, PythonDetector
from .index import make_evidence
from ..registry import DetectorRegistry


@DetectorRegistry.register
class PythonTestingConventionsDetector(PythonDetector):
    """Detect Python testing conventions and patterns."""

    name = "python_testing_conventions"
    description = "Detects testing framework, fixtures, and mocking patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect testing framework, fixtures, and mocking patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Only analyze test files
        test_files = index.get_files_by_role("test")
        if not test_files:
            return result

        # Detect testing framework
        self._detect_testing_framework(ctx, index, test_files, result)

        # Detect fixture patterns
        self._detect_fixtures(ctx, index, test_files, result)

        # Detect mocking patterns
        self._detect_mocking(ctx, index, test_files, result)

        return result

    def _detect_testing_framework(
        self,
        ctx: DetectorContext,
        index,
        test_files: list,
        result: DetectorResult,
    ) -> None:
        """Detect which testing framework is used."""
        frameworks: Counter[str] = Counter()
        framework_examples: dict[str, list[tuple[str, int]]] = {}

        for file_idx in test_files:
            rel_path = file_idx.relative_path

            # Check imports
            for imp in file_idx.imports:
                if "pytest" in imp.module or "pytest" in imp.names:
                    frameworks["pytest"] += 1
                    if "pytest" not in framework_examples:
                        framework_examples["pytest"] = []
                    framework_examples["pytest"].append((rel_path, imp.line))

                if imp.module == "unittest" or "unittest" in imp.names:
                    frameworks["unittest"] += 1
                    if "unittest" not in framework_examples:
                        framework_examples["unittest"] = []
                    framework_examples["unittest"].append((rel_path, imp.line))

                if "hypothesis" in imp.module:
                    frameworks["hypothesis"] += 1
                    if "hypothesis" not in framework_examples:
                        framework_examples["hypothesis"] = []
                    framework_examples["hypothesis"].append((rel_path, imp.line))

            # Check for class-based tests (unittest style)
            for cls in file_idx.classes:
                if "TestCase" in cls.bases or cls.name.startswith("Test"):
                    frameworks["unittest_style"] += 1

            # Check for pytest decorators
            for dec in file_idx.decorators:
                if "pytest" in dec.name:
                    frameworks["pytest"] += 1

        if not frameworks:
            return

        # Determine primary framework
        primary, primary_count = frameworks.most_common(1)[0]
        total = sum(frameworks.values())

        # Map to friendly names
        framework_names = {
            "pytest": "pytest",
            "unittest": "unittest",
            "unittest_style": "unittest (class-based)",
            "hypothesis": "Hypothesis (property-based)",
        }

        if "pytest" in frameworks and frameworks["pytest"] > frameworks.get("unittest", 0):
            title = "pytest-based testing"
            description = (
                f"Uses pytest as primary testing framework. "
                f"Found {frameworks['pytest']} pytest usages."
            )
            confidence = min(0.95, 0.7 + frameworks["pytest"] * 0.02)
            primary = "pytest"
        elif "unittest" in frameworks or "unittest_style" in frameworks:
            unittest_total = frameworks.get("unittest", 0) + frameworks.get("unittest_style", 0)
            title = "unittest-based testing"
            description = (
                f"Uses unittest as primary testing framework. "
                f"Found {unittest_total} unittest usages."
            )
            confidence = min(0.9, 0.6 + unittest_total * 0.02)
            primary = "unittest"
        else:
            title = f"Uses {framework_names.get(primary, primary)}"
            description = f"Primary testing framework: {framework_names.get(primary, primary)}."
            confidence = 0.7

        # Build evidence
        evidence = []
        for rel_path, line in framework_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.testing_framework",
            category="testing",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "framework_counts": dict(frameworks),
                "primary_framework": primary,
                "test_file_count": len(test_files),
            },
        ))

    def _detect_fixtures(
        self,
        ctx: DetectorContext,
        index,
        test_files: list,
        result: DetectorResult,
    ) -> None:
        """Detect pytest fixture patterns."""
        fixture_count = 0
        fixture_examples: list[tuple[str, int, str]] = []
        fixture_scopes: Counter[str] = Counter()
        conftest_count = 0

        for file_idx in test_files:
            rel_path = file_idx.relative_path

            # Check if conftest.py
            if "conftest" in rel_path:
                conftest_count += 1

            # Check for @pytest.fixture decorators
            for dec in file_idx.decorators:
                if "fixture" in dec.name:
                    fixture_count += 1
                    if len(fixture_examples) < 10:
                        fixture_examples.append((rel_path, dec.line, dec.name))

                    # Check for scope argument
                    for arg in dec.call_args:
                        if arg == "scope":
                            # We can't easily get the value, but mark it as scoped
                            fixture_scopes["custom_scope"] += 1

        # Also check for async fixtures
        async_fixture_count = 0
        for dec_name in [ex[2] for ex in fixture_examples]:
            if "async" in dec_name.lower():
                async_fixture_count += 1

        if fixture_count < 2:
            return

        # Determine pattern
        if conftest_count > 0 and fixture_count > 5:
            title = "Centralized pytest fixtures in conftest.py"
            description = (
                f"Uses pytest fixtures with {conftest_count} conftest.py file(s). "
                f"Found {fixture_count} fixture definitions."
            )
            confidence = min(0.9, 0.6 + fixture_count * 0.02)
        else:
            title = "pytest fixture usage"
            description = f"Uses pytest fixtures. Found {fixture_count} fixture definitions."
            confidence = min(0.85, 0.5 + fixture_count * 0.03)

        # Build evidence
        evidence = []
        for rel_path, line, name in fixture_examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.testing_fixtures",
            category="testing",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "fixture_count": fixture_count,
                "conftest_count": conftest_count,
                "async_fixture_count": async_fixture_count,
            },
        ))

    def _detect_mocking(
        self,
        ctx: DetectorContext,
        index,
        test_files: list,
        result: DetectorResult,
    ) -> None:
        """Detect mocking library patterns."""
        mock_libs: Counter[str] = Counter()
        mock_examples: dict[str, list[tuple[str, int]]] = {}

        for file_idx in test_files:
            rel_path = file_idx.relative_path

            for imp in file_idx.imports:
                # unittest.mock
                if "unittest.mock" in imp.module or imp.module == "mock":
                    mock_libs["unittest_mock"] += 1
                    if "unittest_mock" not in mock_examples:
                        mock_examples["unittest_mock"] = []
                    mock_examples["unittest_mock"].append((rel_path, imp.line))

                # pytest-mock
                if "pytest_mock" in imp.module or "mocker" in imp.names:
                    mock_libs["pytest_mock"] += 1
                    if "pytest_mock" not in mock_examples:
                        mock_examples["pytest_mock"] = []
                    mock_examples["pytest_mock"].append((rel_path, imp.line))

                # responses (HTTP mocking)
                if imp.module == "responses" or "responses" in imp.names:
                    mock_libs["responses"] += 1
                    if "responses" not in mock_examples:
                        mock_examples["responses"] = []
                    mock_examples["responses"].append((rel_path, imp.line))

                # respx (async HTTP mocking)
                if imp.module == "respx" or "respx" in imp.names:
                    mock_libs["respx"] += 1
                    if "respx" not in mock_examples:
                        mock_examples["respx"] = []
                    mock_examples["respx"].append((rel_path, imp.line))

                # httpretty
                if "httpretty" in imp.module:
                    mock_libs["httpretty"] += 1
                    if "httpretty" not in mock_examples:
                        mock_examples["httpretty"] = []
                    mock_examples["httpretty"].append((rel_path, imp.line))

                # freezegun (time mocking)
                if "freezegun" in imp.module:
                    mock_libs["freezegun"] += 1
                    if "freezegun" not in mock_examples:
                        mock_examples["freezegun"] = []
                    mock_examples["freezegun"].append((rel_path, imp.line))

                # factory_boy
                if "factory" in imp.module:
                    mock_libs["factory_boy"] += 1
                    if "factory_boy" not in mock_examples:
                        mock_examples["factory_boy"] = []
                    mock_examples["factory_boy"].append((rel_path, imp.line))

        if not mock_libs:
            return

        # Determine pattern
        total = sum(mock_libs.values())
        primary, primary_count = mock_libs.most_common(1)[0]

        # Map to friendly names
        lib_names = {
            "unittest_mock": "unittest.mock",
            "pytest_mock": "pytest-mock",
            "responses": "responses (HTTP)",
            "respx": "respx (async HTTP)",
            "httpretty": "httpretty",
            "freezegun": "freezegun",
            "factory_boy": "factory_boy",
        }

        lib_list = [lib_names.get(lib, lib) for lib in mock_libs.keys()]

        if len(mock_libs) == 1:
            title = f"Uses {lib_names.get(primary, primary)} for mocking"
            description = f"Exclusively uses {lib_names.get(primary, primary)}. Found {primary_count} usages."
            confidence = min(0.9, 0.6 + primary_count * 0.03)
        else:
            title = f"Multiple mocking libraries ({len(mock_libs)})"
            description = f"Uses: {', '.join(lib_list)}. Total: {total} usages."
            confidence = min(0.85, 0.5 + total * 0.02)

        # Build evidence
        evidence = []
        for rel_path, line in mock_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.testing_mocking",
            category="testing",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "mock_library_counts": dict(mock_libs),
                "primary_mock_library": primary,
            },
        ))
