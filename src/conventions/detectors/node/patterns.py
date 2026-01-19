"""Node.js design patterns detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult
from .base import NodeDetector
from .index import NodeIndex, make_evidence
from ..registry import DetectorRegistry


@DetectorRegistry.register
class NodePatternsDetector(NodeDetector):
    """Detect Node.js design patterns."""

    name = "node_patterns"
    description = "Detects Node.js design patterns and idioms"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Node.js design patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect dependency injection
        self._detect_dependency_injection(ctx, index, result)

        # Detect repository pattern
        self._detect_repository_pattern(ctx, index, result)

        # Detect singleton pattern
        self._detect_singleton_pattern(ctx, index, result)

        return result

    def _detect_dependency_injection(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect dependency injection libraries."""
        di_libs = {
            "tsyringe": "tsyringe",
            "inversify": "inversify",
            "typedi": "typedi",
            "nestjs": "@nestjs/common",
            "awilix": "awilix",
        }

        lib_counts: Counter[str] = Counter()
        examples: dict[str, list[tuple[str, int]]] = {}

        for name, pkg in di_libs.items():
            imports = index.find_imports_matching(pkg, limit=20)
            if imports:
                lib_counts[name] = len(imports)
                examples[name] = [(r, l) for r, _, l in imports[:5]]

        # Also check for @Injectable() decorator pattern
        injectable_pattern = r'@Injectable\s*\(\s*\)'
        injectable_count = index.count_pattern(injectable_pattern, exclude_tests=True)
        if injectable_count >= 3 and "nestjs" not in lib_counts:
            lib_counts["decorator_di"] = injectable_count

        if not lib_counts:
            return

        primary = max(lib_counts, key=lib_counts.get)  # type: ignore
        primary_count = lib_counts[primary]

        lib_names = {
            "tsyringe": "tsyringe",
            "inversify": "InversifyJS",
            "typedi": "TypeDI",
            "nestjs": "NestJS DI",
            "awilix": "Awilix",
            "decorator_di": "Decorator-based DI",
        }

        title = f"DI with {lib_names.get(primary, primary)}"
        description = (
            f"Uses {lib_names.get(primary, primary)} for dependency injection. "
            f"Found in {primary_count} files."
        )
        confidence = min(0.9, 0.7 + primary_count * 0.03)

        evidence = []
        for rel_path, line in examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.dependency_injection",
            category="patterns",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "di_library": primary,
                "library_counts": dict(lib_counts),
            },
        ))

    def _detect_repository_pattern(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect repository pattern."""
        # Class or interface named *Repository
        repo_class_pattern = r'(?:class|interface)\s+\w*Repository'
        repo_matches = index.search_pattern(repo_class_pattern, limit=30, exclude_tests=True)

        if len(repo_matches) < 2:
            return

        # Check for common repo methods
        crud_pattern = r'(?:findById|findOne|findAll|create|update|delete|save)\s*\('
        crud_count = index.count_pattern(crud_pattern, exclude_tests=True)

        title = "Repository pattern"
        description = (
            f"Uses repository pattern for data access. "
            f"Found {len(repo_matches)} repository classes/interfaces."
        )
        confidence = min(0.9, 0.6 + len(repo_matches) * 0.05)

        evidence = []
        for rel_path, line, _ in repo_matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.repository_pattern",
            category="patterns",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "repository_count": len(repo_matches),
                "crud_method_count": crud_count,
            },
        ))

    def _detect_singleton_pattern(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect singleton pattern (module exports instance)."""
        # Module-level instance export: module.exports = new Xxx()
        # or export default new Xxx()
        singleton_pattern = r'(?:module\.exports\s*=|export\s+default)\s*new\s+\w+'
        singleton_matches = index.search_pattern(singleton_pattern, limit=30, exclude_tests=True)

        # getInstance() pattern
        get_instance_pattern = r'static\s+getInstance\s*\(\s*\)'
        get_instance_count = index.count_pattern(get_instance_pattern, exclude_tests=True)

        total = len(singleton_matches) + get_instance_count
        if total < 3:
            return

        title = "Singleton pattern"
        description = (
            f"Uses singleton pattern for shared instances. "
            f"Module singletons: {len(singleton_matches)}, getInstance: {get_instance_count}."
        )
        confidence = min(0.85, 0.6 + total * 0.04)

        evidence = []
        for rel_path, line, _ in singleton_matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.singleton_pattern",
            category="patterns",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "module_singleton_count": len(singleton_matches),
                "get_instance_count": get_instance_count,
            },
        ))
