"""Node.js design patterns detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import NodeDetector
from .index import NodeIndex, make_evidence


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

        # Detect store pattern (MongoDB/data stores)
        self._detect_store_pattern(ctx, index, result)

        # Detect constructor injection (manual DI)
        self._detect_constructor_injection(ctx, index, result)

        # Detect context object pattern
        self._detect_context_pattern(ctx, index, result)

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
                examples[name] = [(r, ln) for r, _, ln in imports[:5]]

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

    def _detect_store_pattern(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect store pattern (data stores, MongoDB stores, etc.)."""
        # Class or interface named *Store
        store_class_pattern = r'(?:class|interface)\s+\w*Store\b'
        store_matches = index.search_pattern(store_class_pattern, limit=30, exclude_tests=True)

        # implements IStore pattern
        implements_pattern = r'implements\s+I?Store\b'
        implements_count = index.count_pattern(implements_pattern, exclude_tests=True)

        # Check for stores/ or data-store/ directories
        from pathlib import Path
        store_dirs = set()
        for rel_path in index.files:
            parts = Path(rel_path).parts
            for part in parts:
                if part.lower() in ("stores", "store", "data-store", "data-stores"):
                    store_dirs.add(part)

        total = len(store_matches) + implements_count
        if total < 2 and not store_dirs:
            return

        title = "Store pattern"
        parts = []
        if store_matches:
            parts.append(f"{len(store_matches)} Store classes")
        if implements_count:
            parts.append(f"{implements_count} IStore implementations")
        if store_dirs:
            parts.append(f"directories: {', '.join(store_dirs)}")

        description = f"Uses store pattern for data access. {', '.join(parts)}."
        confidence = min(0.9, 0.6 + total * 0.05)

        evidence = []
        for rel_path, line, _ in store_matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.store_pattern",
            category="patterns",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "store_class_count": len(store_matches),
                "implements_istore_count": implements_count,
                "store_directories": list(store_dirs),
            },
        ))

    def _detect_constructor_injection(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect manual constructor injection (without DI framework)."""
        # Constructor with private/readonly parameters (TypeScript)
        ts_constructor_pattern = r'constructor\s*\([^)]*(?:private|readonly)\s+\w+\s*:'
        ts_matches = index.search_pattern(ts_constructor_pattern, limit=50, exclude_tests=True)

        # Also check for constructor assigning this.* from parameters
        assign_pattern = r'constructor\s*\([^)]*\)\s*\{[^}]*this\.\w+\s*=\s*\w+'
        assign_count = index.count_pattern(assign_pattern, exclude_tests=True)

        # Check if they're also using a DI library (if so, skip manual DI detection)
        di_imports = (
            index.find_imports_matching("tsyringe", limit=5) +
            index.find_imports_matching("inversify", limit=5) +
            index.find_imports_matching("typedi", limit=5) +
            index.find_imports_matching("awilix", limit=5) +
            index.find_imports_matching("@nestjs/common", limit=5)
        )
        if di_imports:
            # Already has DI library, skip manual DI
            return

        total = len(ts_matches) + (assign_count // 2)
        if total < 3:
            return

        title = "Constructor injection"
        description = (
            f"Services receive dependencies via constructor injection. "
            f"Found {len(ts_matches)} classes with injected dependencies."
        )
        confidence = min(0.85, 0.6 + len(ts_matches) * 0.03)

        evidence = []
        for rel_path, line, _ in ts_matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.constructor_injection",
            category="patterns",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "ts_constructor_injection_count": len(ts_matches),
                "assignment_pattern_count": assign_count,
            },
        ))

    def _detect_context_pattern(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect context object pattern (IContext, AppContext passed through layers)."""
        # Interface or type named *Context
        context_interface_pattern = r'(?:interface|type)\s+(?:I?(?:App)?Context|I?\w+Context)\s*[={<]'
        context_matches = index.search_pattern(context_interface_pattern, limit=20, exclude_tests=True)

        # Check for context parameter in functions
        context_param_pattern = r'(?:ctx|context)\s*:\s*(?:I?(?:App)?Context|I?\w+Context)\b'
        param_count = index.count_pattern(context_param_pattern, exclude_tests=True)

        # Check for context carrying services/stores
        context_services_pattern = r'(?:context|ctx)\.(?:services|stores|models|utilities)\.'
        services_count = index.count_pattern(context_services_pattern, exclude_tests=True)

        if not context_matches and param_count < 5:
            return

        title = "Context object pattern"
        parts = []
        if context_matches:
            parts.append(f"{len(context_matches)} Context interfaces")
        if param_count:
            parts.append(f"{param_count} context parameters")
        if services_count:
            parts.append("carries services/stores through stack")

        description = f"Uses context object to pass dependencies through layers. {', '.join(parts)}."
        confidence = min(0.9, 0.6 + len(context_matches) * 0.1 + param_count * 0.02)

        evidence = []
        for rel_path, line, _ in context_matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.context_pattern",
            category="patterns",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "context_interface_count": len(context_matches),
                "context_param_count": param_count,
                "context_services_usage": services_count,
            },
        ))
