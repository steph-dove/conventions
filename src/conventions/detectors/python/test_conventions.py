"""Python test-specific conventions detector.

This detector focuses on conventions within test files, such as:
- Testing framework (pytest vs unittest)
- Fixture usage patterns
- Assertion styles (using AST-based counting)
- Mocking patterns
- Parametrized tests
"""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import FileIndex, make_evidence


@DetectorRegistry.register
class PythonTestConventionsDetector(PythonDetector):
    """Detect Python test-specific conventions."""

    name = "python_test_conventions"
    description = "Detects test-specific conventions like fixtures, assertions, and mocking"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect test-specific conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Get actual test files (test_*.py, *_test.py) - not support files
        test_files = index.get_test_files(include_support=False)
        # Get all files in test directories (for conftest counting)
        all_test_dir_files = index.get_files_by_role("test")
        # Get conftest files
        conftest_files = index.get_conftest_files(include_docs=False)

        if len(test_files) < 3:
            return result  # Not enough test files

        self._detect_testing_framework(ctx, index, test_files, result)
        self._detect_fixture_patterns(ctx, index, test_files, conftest_files, result)
        self._detect_assertion_style(ctx, index, test_files, result)
        self._detect_mocking_patterns(ctx, index, all_test_dir_files, result)
        self._detect_parametrized_tests(ctx, index, test_files, result)

        return result

    def _detect_testing_framework(
        self,
        ctx: DetectorContext,
        index,
        test_files: list[FileIndex],
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
                    if len(framework_examples["pytest"]) < 5:
                        framework_examples["pytest"].append((rel_path, imp.line))

                if imp.module == "unittest" or "unittest" in imp.names:
                    frameworks["unittest"] += 1
                    if "unittest" not in framework_examples:
                        framework_examples["unittest"] = []
                    if len(framework_examples["unittest"]) < 5:
                        framework_examples["unittest"].append((rel_path, imp.line))

                if "hypothesis" in imp.module:
                    frameworks["hypothesis"] += 1
                    if "hypothesis" not in framework_examples:
                        framework_examples["hypothesis"] = []
                    if len(framework_examples["hypothesis"]) < 5:
                        framework_examples["hypothesis"].append((rel_path, imp.line))

            # Check for pytest decorators
            for dec in file_idx.decorators:
                if "pytest" in dec.name:
                    frameworks["pytest"] += 1

        if not frameworks:
            return

        # Determine primary framework
        primary, primary_count = frameworks.most_common(1)[0]

        if "pytest" in frameworks and frameworks["pytest"] > frameworks.get("unittest", 0):
            title = "pytest-based testing"
            description = (
                f"Uses pytest as primary testing framework. "
                f"Found {frameworks['pytest']} pytest usages across {len(test_files)} test files."
            )
            confidence = min(0.95, 0.7 + frameworks["pytest"] * 0.02)
            primary = "pytest"
        elif "unittest" in frameworks:
            title = "unittest-based testing"
            description = (
                f"Uses unittest as primary testing framework. "
                f"Found {frameworks['unittest']} unittest usages."
            )
            confidence = min(0.9, 0.6 + frameworks["unittest"] * 0.02)
            primary = "unittest"
        else:
            framework_names = {
                "pytest": "pytest",
                "unittest": "unittest",
                "hypothesis": "Hypothesis (property-based)",
            }
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

    def _detect_fixture_patterns(
        self,
        ctx: DetectorContext,
        index,
        test_files: list[FileIndex],
        conftest_files: list[FileIndex],
        result: DetectorResult,
    ) -> None:
        """Detect fixture usage patterns."""
        fixture_counts: Counter[str] = Counter()
        fixture_examples: dict[str, list[tuple[str, int]]] = {}

        # Check test files and conftest files for fixtures
        all_files = list(test_files) + [f for f in conftest_files if f not in test_files]

        for file_idx in all_files:
            rel_path = file_idx.relative_path

            # Check for pytest fixture decorator
            for dec in file_idx.decorators:
                if "fixture" in dec.name.lower():
                    fixture_counts["pytest_fixture"] += 1
                    if "pytest_fixture" not in fixture_examples:
                        fixture_examples["pytest_fixture"] = []
                    if len(fixture_examples["pytest_fixture"]) < 5:
                        fixture_examples["pytest_fixture"].append((rel_path, dec.line))

            # Check for class-based setup/teardown
            for func in file_idx.functions:
                if func.name in ("setUp", "tearDown", "setUpClass", "tearDownClass"):
                    fixture_counts["unittest_setup"] += 1
                    if "unittest_setup" not in fixture_examples:
                        fixture_examples["unittest_setup"] = []
                    if len(fixture_examples["unittest_setup"]) < 5:
                        fixture_examples["unittest_setup"].append((rel_path, func.line))

                if func.name in ("setup_method", "teardown_method", "setup_function", "teardown_function"):
                    fixture_counts["pytest_setup"] += 1
                    if "pytest_setup" not in fixture_examples:
                        fixture_examples["pytest_setup"] = []
                    if len(fixture_examples["pytest_setup"]) < 5:
                        fixture_examples["pytest_setup"].append((rel_path, func.line))

        conftest_count = len(conftest_files)

        total = sum(fixture_counts.values())
        if total < 2 and conftest_count == 0:
            return

        # Determine dominant pattern
        if fixture_counts["pytest_fixture"] > fixture_counts.get("unittest_setup", 0):
            title = "pytest fixtures for test setup"
            description = f"Uses pytest @fixture decorator for test setup. Found {fixture_counts['pytest_fixture']} fixtures."
            if conftest_count:
                description += f" Uses {conftest_count} conftest.py file(s) for shared fixtures."
            pattern = "pytest_fixture"
            confidence = min(0.9, 0.5 + fixture_counts["pytest_fixture"] * 0.05)
        elif fixture_counts.get("unittest_setup", 0) > 0:
            title = "unittest setUp/tearDown pattern"
            description = f"Uses unittest-style setUp/tearDown methods. Found {fixture_counts['unittest_setup']} usages."
            pattern = "unittest_setup"
            confidence = 0.8
        else:
            title = "pytest setup functions"
            description = f"Uses pytest setup_method/setup_function. Found {fixture_counts.get('pytest_setup', 0)} usages."
            pattern = "pytest_setup"
            confidence = 0.75

        # Build evidence
        evidence = []
        for rel_path, line in fixture_examples.get(pattern, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.test_conventions.fixtures",
            category="testing",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "fixture_counts": dict(fixture_counts),
                "conftest_files": conftest_count,
                "pattern": pattern,
            },
        ))

    def _detect_assertion_style(
        self,
        ctx: DetectorContext,
        index,
        test_files: list[FileIndex],
        result: DetectorResult,
    ) -> None:
        """Detect assertion style using AST-based counting."""
        assertion_counts: Counter[str] = Counter()
        assertion_examples: dict[str, list[tuple[str, int]]] = {}

        for file_idx in test_files:
            rel_path = file_idx.relative_path

            # Use AST-based assertion counting
            assert_count = len(file_idx.asserts)
            if assert_count > 0:
                assertion_counts["plain_assert"] += assert_count
                # Add first assert as example if we don't have enough
                if "plain_assert" not in assertion_examples:
                    assertion_examples["plain_assert"] = []
                if len(assertion_examples["plain_assert"]) < 5 and file_idx.asserts:
                    assertion_examples["plain_assert"].append((rel_path, file_idx.asserts[0].line))

            # Check for pytest.raises, pytest.warns
            for call in file_idx.calls:
                if "pytest.raises" in call.name or call.name == "raises":
                    assertion_counts["pytest_raises"] += 1
                    if "pytest_raises" not in assertion_examples:
                        assertion_examples["pytest_raises"] = []
                    if len(assertion_examples["pytest_raises"]) < 5:
                        assertion_examples["pytest_raises"].append((rel_path, call.line))

                if "pytest.warns" in call.name:
                    assertion_counts["pytest_warns"] += 1

                # unittest-style assertions
                if call.name.startswith("self.assert") or call.name.startswith("self.fail"):
                    assertion_counts["unittest_assert"] += 1
                    if "unittest_assert" not in assertion_examples:
                        assertion_examples["unittest_assert"] = []
                    if len(assertion_examples["unittest_assert"]) < 5:
                        assertion_examples["unittest_assert"].append((rel_path, call.line))

        total = sum(assertion_counts.values())
        if total < 5:
            return

        plain_ratio = assertion_counts.get("plain_assert", 0) / total if total else 0
        unittest_ratio = assertion_counts.get("unittest_assert", 0) / total if total else 0

        if plain_ratio >= 0.7:
            title = "Plain assert statements"
            description = (
                f"Uses plain Python assert statements for test assertions. "
                f"{assertion_counts.get('plain_assert', 0)} assert statements."
            )
            if assertion_counts.get("pytest_raises", 0) > 0:
                description += f" Uses pytest.raises for exception testing ({assertion_counts['pytest_raises']} usages)."
            style = "plain_assert"
            confidence = min(0.9, 0.5 + plain_ratio * 0.4)
        elif unittest_ratio >= 0.5:
            title = "unittest-style assertions"
            description = (
                f"Uses unittest-style self.assert* methods. "
                f"{assertion_counts.get('unittest_assert', 0)} assertion calls."
            )
            style = "unittest_assert"
            confidence = min(0.85, 0.5 + unittest_ratio * 0.35)
        else:
            title = "Mixed assertion styles"
            description = (
                f"Uses mixed assertion styles: "
                f"plain assert ({assertion_counts.get('plain_assert', 0)}), "
                f"self.assert* ({assertion_counts.get('unittest_assert', 0)})."
            )
            style = "mixed"
            confidence = 0.7

        # Build evidence
        evidence = []
        primary_examples = assertion_examples.get("pytest_raises", []) or assertion_examples.get("unittest_assert", []) or assertion_examples.get("plain_assert", [])
        for rel_path, line in primary_examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.test_conventions.assertions",
            category="testing",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "assertion_counts": dict(assertion_counts),
                "style": style,
            },
        ))

    def _detect_mocking_patterns(
        self,
        ctx: DetectorContext,
        index,
        test_files: list[FileIndex],
        result: DetectorResult,
    ) -> None:
        """Detect mocking patterns (mock, monkeypatch, responses, etc.)."""
        mock_counts: Counter[str] = Counter()
        mock_examples: dict[str, list[tuple[str, int]]] = {}

        for file_idx in test_files:
            rel_path = file_idx.relative_path

            # Check imports for mocking libraries
            for imp in file_idx.imports:
                if "unittest.mock" in imp.module or imp.module == "mock":
                    mock_counts["unittest_mock"] += 1
                    if "unittest_mock" not in mock_examples:
                        mock_examples["unittest_mock"] = []
                    if len(mock_examples["unittest_mock"]) < 5:
                        mock_examples["unittest_mock"].append((rel_path, imp.line))

                if "pytest" in imp.module and "monkeypatch" in str(imp.names).lower():
                    mock_counts["monkeypatch"] += 1

                if imp.module == "responses" or "responses" in imp.names:
                    mock_counts["responses"] += 1
                    if "responses" not in mock_examples:
                        mock_examples["responses"] = []
                    if len(mock_examples["responses"]) < 5:
                        mock_examples["responses"].append((rel_path, imp.line))

                if imp.module == "httpretty":
                    mock_counts["httpretty"] += 1

                if "respx" in imp.module:
                    mock_counts["respx"] += 1
                    if "respx" not in mock_examples:
                        mock_examples["respx"] = []
                    if len(mock_examples["respx"]) < 5:
                        mock_examples["respx"].append((rel_path, imp.line))

                if "pytest_httpx" in imp.module:
                    mock_counts["pytest_httpx"] += 1

                if "freezegun" in imp.module:
                    mock_counts["freezegun"] += 1

            # Check for @patch decorator
            for dec in file_idx.decorators:
                if "patch" in dec.name.lower():
                    mock_counts["patch_decorator"] += 1
                    if "patch_decorator" not in mock_examples:
                        mock_examples["patch_decorator"] = []
                    if len(mock_examples["patch_decorator"]) < 5:
                        mock_examples["patch_decorator"].append((rel_path, dec.line))

            # Check for monkeypatch as function parameter (fixture)
            content = "\n".join(file_idx.lines)
            if "monkeypatch" in content:
                # Only count once per file to avoid overcounting
                if not mock_counts.get("monkeypatch"):
                    mock_counts["monkeypatch"] = 0
                mock_counts["monkeypatch"] += 1
                if "monkeypatch" not in mock_examples:
                    mock_examples["monkeypatch"] = []
                if len(mock_examples["monkeypatch"]) < 5:
                    # Find first function using monkeypatch
                    for func in file_idx.functions:
                        if func.name.startswith("test"):
                            mock_examples["monkeypatch"].append((rel_path, func.line))
                            break

        total = sum(mock_counts.values())
        if total < 2:
            return

        # Determine dominant pattern
        primary, primary_count = Counter(mock_counts).most_common(1)[0]

        pattern_names = {
            "unittest_mock": "unittest.mock / Mock",
            "patch_decorator": "@patch decorator",
            "monkeypatch": "pytest monkeypatch fixture",
            "responses": "responses library (HTTP mocking)",
            "httpretty": "HTTPretty (HTTP mocking)",
            "respx": "respx (async HTTP mocking)",
            "pytest_httpx": "pytest-httpx",
            "freezegun": "freezegun (time mocking)",
        }

        title = f"Mocking with {pattern_names.get(primary, primary)}"
        description = f"Uses {pattern_names.get(primary, primary)} for test mocking. Found {primary_count} usages."

        # List other mocking tools
        others = [pattern_names.get(p, p) for p, c in mock_counts.most_common(3)[1:] if c > 0]
        if others:
            description += f" Also uses: {', '.join(others)}."

        confidence = min(0.9, 0.5 + primary_count * 0.05)

        # Build evidence
        evidence = []
        for rel_path, line in mock_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.test_conventions.mocking",
            category="testing",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "mock_counts": dict(mock_counts),
                "primary_pattern": primary,
            },
        ))

    def _detect_parametrized_tests(
        self,
        ctx: DetectorContext,
        index,
        test_files: list[FileIndex],
        result: DetectorResult,
    ) -> None:
        """Detect parametrized test patterns."""
        parametrize_count = 0
        parametrize_examples: list[tuple[str, int]] = []

        for file_idx in test_files:
            rel_path = file_idx.relative_path

            for dec in file_idx.decorators:
                if "parametrize" in dec.name.lower() or "parameterize" in dec.name.lower():
                    parametrize_count += 1
                    if len(parametrize_examples) < 5:
                        parametrize_examples.append((rel_path, dec.line))

        if parametrize_count < 3:
            return

        title = "Parametrized tests"
        description = (
            f"Uses @pytest.mark.parametrize for data-driven tests. "
            f"Found {parametrize_count} parametrized test functions."
        )
        confidence = min(0.9, 0.5 + parametrize_count * 0.05)

        # Build evidence
        evidence = []
        for rel_path, line in parametrize_examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.test_conventions.parametrized",
            category="testing",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "parametrize_count": parametrize_count,
            },
        ))
