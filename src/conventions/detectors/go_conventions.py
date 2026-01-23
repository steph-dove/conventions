"""Go conventions detector (lighter, regex-based)."""

from __future__ import annotations

import re
from collections import Counter

from .base import BaseDetector, DetectorContext, DetectorResult
from .go_index import GoIndex, make_evidence
from .registry import DetectorRegistry


class GoDetector(BaseDetector):
    """Base class for Go detectors."""

    languages: set[str] = {"go"}

    def get_index(self, ctx: DetectorContext) -> GoIndex:
        """Get or create Go index."""
        if not hasattr(ctx, "_go_index") or ctx._go_index is None:
            ctx._go_index = GoIndex(ctx.repo_root, max_files=ctx.max_files)
            ctx._go_index.build()
        return ctx._go_index


@DetectorRegistry.register
class GoConventionsDetector(GoDetector):
    """Detect Go conventions."""

    name = "go_conventions"
    description = "Detects Go framework, error handling, and patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect web framework
        self._detect_framework(ctx, index, result)

        # Detect error handling patterns
        self._detect_error_handling(ctx, index, result)

        # Detect testing patterns
        self._detect_testing(ctx, index, result)

        # Detect interface usage
        self._detect_interfaces(ctx, index, result)

        return result

    def _detect_framework(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect web framework usage."""
        frameworks: Counter[str] = Counter()
        framework_examples: dict[str, list[tuple[str, int]]] = {}

        framework_patterns = {
            "gin": ["github.com/gin-gonic/gin"],
            "echo": ["github.com/labstack/echo"],
            "fiber": ["github.com/gofiber/fiber"],
            "chi": ["github.com/go-chi/chi"],
            "gorilla": ["github.com/gorilla/mux"],
            "net_http": ["net/http"],
            "fasthttp": ["github.com/valyala/fasthttp"],
        }

        for framework, patterns in framework_patterns.items():
            for pattern in patterns:
                imports = index.find_imports_matching(pattern, limit=10)
                if imports:
                    frameworks[framework] += len(imports)
                    if framework not in framework_examples:
                        framework_examples[framework] = []
                    for rel_path, pkg, line in imports[:5]:
                        framework_examples[framework].append((rel_path, line))

        if not frameworks:
            return

        # Filter out net/http if another framework is present
        if len(frameworks) > 1 and "net_http" in frameworks:
            del frameworks["net_http"]

        primary, primary_count = frameworks.most_common(1)[0]
        total = sum(frameworks.values())

        framework_names = {
            "gin": "Gin",
            "echo": "Echo",
            "fiber": "Fiber",
            "chi": "Chi",
            "gorilla": "Gorilla Mux",
            "net_http": "net/http (stdlib)",
            "fasthttp": "FastHTTP",
        }

        if len(frameworks) == 1:
            title = f"Uses {framework_names.get(primary, primary)}"
            description = (
                f"Web application built with {framework_names.get(primary, primary)}. "
                f"Found {primary_count} imports."
            )
            confidence = min(0.95, 0.7 + primary_count * 0.03)
        else:
            other = [framework_names.get(f, f) for f in frameworks if f != primary]
            title = f"Primary framework: {framework_names.get(primary, primary)}"
            description = (
                f"Uses {framework_names.get(primary, primary)} ({primary_count}/{total}). "
                f"Also: {', '.join(other)}."
            )
            confidence = min(0.85, 0.5 + (primary_count / total) * 0.35)

        # Build evidence
        evidence = []
        for rel_path, line in framework_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.framework",
            category="api",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "framework_counts": dict(frameworks),
                "primary_framework": primary,
            },
        ))

    def _detect_error_handling(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect error handling patterns."""
        error_patterns: Counter[str] = Counter()
        pattern_examples: dict[str, list[tuple[str, int]]] = {}

        # Check for error wrapping libraries
        errors_pkg = index.find_imports_matching("github.com/pkg/errors", limit=20)
        if errors_pkg:
            error_patterns["pkg_errors"] = len(errors_pkg)
            pattern_examples["pkg_errors"] = [(p, l) for p, _, l in errors_pkg[:5]]

        # Check for stdlib errors
        stdlib_errors = index.find_imports_matching("errors", limit=20)
        # Filter to exact match
        stdlib_errors = [(p, pkg, l) for p, pkg, l in stdlib_errors if pkg == "errors"]
        if stdlib_errors:
            error_patterns["stdlib_errors"] = len(stdlib_errors)
            pattern_examples["stdlib_errors"] = [(p, l) for p, _, l in stdlib_errors[:5]]

        # Check for fmt.Errorf usage (heuristic)
        errorf_count = 0
        for file_idx in index.files.values():
            content = "\n".join(file_idx.lines)
            errorf_count += len(re.findall(r"fmt\.Errorf", content))

        if errorf_count > 0:
            error_patterns["fmt_errorf"] = errorf_count

        if not error_patterns:
            return

        primary, primary_count = error_patterns.most_common(1)[0]

        pattern_names = {
            "pkg_errors": "pkg/errors wrapping",
            "stdlib_errors": "stdlib errors package",
            "fmt_errorf": "fmt.Errorf formatting",
        }

        if "pkg_errors" in error_patterns:
            title = "Error wrapping with pkg/errors"
            description = (
                f"Uses github.com/pkg/errors for error wrapping. "
                f"Found {error_patterns['pkg_errors']} imports."
            )
            primary = "pkg_errors"
        elif errorf_count > 5:
            title = "Error wrapping with fmt.Errorf"
            description = (
                f"Uses fmt.Errorf with %%w for error wrapping. "
                f"Found {errorf_count} fmt.Errorf usages."
            )
            primary = "fmt_errorf"
        else:
            title = f"Error handling: {pattern_names.get(primary, primary)}"
            description = f"Uses {pattern_names.get(primary, primary)}."

        confidence = min(0.85, 0.5 + primary_count * 0.03)

        # Build evidence
        evidence = []
        for rel_path, line in pattern_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.error_handling",
            category="error_handling",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats=dict(error_patterns),
        ))

    def _detect_testing(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect testing patterns."""
        test_libs: Counter[str] = Counter()
        test_examples: dict[str, list[tuple[str, int]]] = {}

        test_patterns = {
            "testify": ["github.com/stretchr/testify"],
            "gomock": ["github.com/golang/mock"],
            "mockery": ["github.com/vektra/mockery"],
            "ginkgo": ["github.com/onsi/ginkgo"],
            "goconvey": ["github.com/smartystreets/goconvey"],
        }

        for lib, patterns in test_patterns.items():
            for pattern in patterns:
                imports = index.find_imports_matching(pattern, limit=10)
                if imports:
                    test_libs[lib] += len(imports)
                    if lib not in test_examples:
                        test_examples[lib] = []
                    for rel_path, pkg, line in imports[:5]:
                        test_examples[lib].append((rel_path, line))

        # Count test files
        test_file_count = sum(
            1 for f in index.files.values()
            if f.relative_path.endswith("_test.go")
        )

        if not test_libs and test_file_count < 3:
            return

        if test_libs:
            primary, primary_count = test_libs.most_common(1)[0]

            lib_names = {
                "testify": "testify",
                "gomock": "gomock",
                "mockery": "mockery",
                "ginkgo": "Ginkgo (BDD)",
                "goconvey": "GoConvey",
            }

            title = f"Testing with {lib_names.get(primary, primary)}"
            description = (
                f"Uses {lib_names.get(primary, primary)} for testing. "
                f"Found {primary_count} imports across {test_file_count} test files."
            )
            confidence = min(0.9, 0.6 + primary_count * 0.03)
        else:
            title = "Standard library testing"
            description = (
                f"Uses Go's standard testing package. "
                f"Found {test_file_count} test files."
            )
            primary = "stdlib"
            confidence = min(0.85, 0.5 + test_file_count * 0.02)

        # Build evidence
        evidence = []
        for rel_path, line in test_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.testing",
            category="testing",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "test_library_counts": dict(test_libs),
                "test_file_count": test_file_count,
            },
        ))

    def _detect_interfaces(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect interface usage patterns."""
        total_interfaces = 0
        interface_examples: list[tuple[str, str, int]] = []

        for file_idx in index.files.values():
            if file_idx.role == "test":
                continue

            for name, line in file_idx.interfaces:
                total_interfaces += 1
                if len(interface_examples) < 10:
                    interface_examples.append((file_idx.relative_path, name, line))

        if total_interfaces < 3:
            return

        # Check for interface naming patterns
        er_suffix_count = sum(
            1 for _, name, _ in interface_examples
            if name.endswith("er") or name.endswith("or")
        )

        naming_ratio = er_suffix_count / len(interface_examples) if interface_examples else 0

        if naming_ratio >= 0.5:
            title = "Idiomatic interface naming (*er/*or suffix)"
            description = (
                f"Interfaces follow Go naming conventions (Reader, Writer, etc.). "
                f"Found {total_interfaces} interfaces, {er_suffix_count} with *er/*or suffix."
            )
        else:
            title = "Interface-based design"
            description = f"Uses interfaces for abstraction. Found {total_interfaces} interfaces."

        confidence = min(0.85, 0.5 + total_interfaces * 0.03)

        # Build evidence
        evidence = []
        for rel_path, name, line in interface_examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.interfaces",
            category="design",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "total_interfaces": total_interfaces,
                "er_suffix_count": er_suffix_count,
                "naming_ratio": round(naming_ratio, 3),
            },
        ))
