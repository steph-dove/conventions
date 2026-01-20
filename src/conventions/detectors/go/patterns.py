"""Go design patterns detector."""

from __future__ import annotations

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import GoDetector
from .index import GoIndex, make_evidence


@DetectorRegistry.register
class GoPatternsDetector(GoDetector):
    """Detect Go design patterns."""

    name = "go_patterns"
    description = "Detects Go design patterns and idioms"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Go design patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect functional options pattern
        self._detect_options_pattern(ctx, index, result)

        # Detect builder pattern
        self._detect_builder_pattern(ctx, index, result)

        # Detect repository pattern
        self._detect_repository_pattern(ctx, index, result)

        return result

    def _detect_options_pattern(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect functional options pattern."""
        # type Option func(*Config) or type XxxOption func(*Xxx)
        option_type_pattern = r'type\s+\w*Option\s+func\s*\(\s*\*\w+'
        option_types = index.search_pattern(option_type_pattern, limit=30, exclude_tests=True)

        # WithXxx functions returning Option
        with_func_pattern = r'func\s+With\w+\s*\([^)]*\)\s+\w*Option'
        with_funcs = index.search_pattern(with_func_pattern, limit=50, exclude_tests=True)

        if len(option_types) < 1 or len(with_funcs) < 2:
            return

        title = "Functional options pattern"
        description = (
            f"Uses Go functional options pattern for configuration. "
            f"Found {len(option_types)} Option types, {len(with_funcs)} With* functions."
        )
        confidence = min(0.95, 0.7 + len(with_funcs) * 0.03)

        evidence = []
        for rel_path, line, _ in option_types[:2]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)
        for rel_path, line, _ in with_funcs[:ctx.max_evidence_snippets - len(evidence)]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.options_pattern",
            category="patterns",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "option_type_count": len(option_types),
                "with_func_count": len(with_funcs),
            },
        ))

    def _detect_builder_pattern(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect builder pattern."""
        # Methods returning *Builder or *Self for chaining
        # func (b *XxxBuilder) WithYyy(...) *XxxBuilder
        builder_method_pattern = r'func\s+\(\s*\w+\s+\*\w*Builder\s*\)\s+\w+\s*\([^)]*\)\s+\*\w*Builder'
        builder_methods = index.search_pattern(builder_method_pattern, limit=50, exclude_tests=True)

        # NewXxxBuilder functions
        new_builder_pattern = r'func\s+New\w*Builder\s*\('
        new_builders = index.search_pattern(new_builder_pattern, limit=20, exclude_tests=True)

        # Build() method
        build_method_pattern = r'func\s+\(\s*\w+\s+\*\w*Builder\s*\)\s+Build\s*\('
        build_methods = index.search_pattern(build_method_pattern, limit=20, exclude_tests=True)

        if len(builder_methods) < 2:
            return

        title = "Builder pattern"
        description = (
            f"Uses builder pattern for object construction. "
            f"Found {len(new_builders)} builders, {len(builder_methods)} chain methods."
        )
        confidence = min(0.9, 0.6 + len(builder_methods) * 0.04)

        evidence = []
        for rel_path, line, _ in new_builders[:2]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)
        for rel_path, line, _ in builder_methods[:ctx.max_evidence_snippets - len(evidence)]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.builder_pattern",
            category="patterns",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "new_builder_count": len(new_builders),
                "builder_method_count": len(builder_methods),
                "build_method_count": len(build_methods),
            },
        ))

    def _detect_repository_pattern(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect repository pattern."""
        # Repository interfaces
        repo_interface_pattern = r'type\s+\w*Repository\s+interface\s*\{'
        repo_interfaces = index.search_pattern(repo_interface_pattern, limit=30, exclude_tests=True)

        # Repository structs
        repo_struct_pattern = r'type\s+\w*Repository\s+struct\s*\{'
        repo_structs = index.search_pattern(repo_struct_pattern, limit=30, exclude_tests=True)

        # Common repo methods: Create, Get, Update, Delete, List, Find
        crud_pattern = r'func\s+\([^)]+Repository[^)]*\)\s+(?:Create|Get|Update|Delete|List|Find|Save)\w*\s*\('
        crud_methods = index.search_pattern(crud_pattern, limit=50, exclude_tests=True)

        total = len(repo_interfaces) + len(repo_structs)
        if total < 2:
            return

        title = "Repository pattern"
        description = (
            f"Uses repository pattern for data access. "
            f"Found {len(repo_interfaces)} interfaces, {len(repo_structs)} implementations."
        )
        confidence = min(0.9, 0.6 + total * 0.05)

        evidence = []
        for rel_path, line, _ in repo_interfaces[:3]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)
        for rel_path, line, _ in repo_structs[:ctx.max_evidence_snippets - len(evidence)]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.repository_pattern",
            category="patterns",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "repo_interface_count": len(repo_interfaces),
                "repo_struct_count": len(repo_structs),
                "crud_method_count": len(crud_methods),
            },
        ))
