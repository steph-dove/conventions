"""Node.js conventions detector (base conventions)."""

from __future__ import annotations

import re
from collections import Counter

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import NodeDetector
from .index import NodeIndex, make_evidence


@DetectorRegistry.register
class NodeConventionsDetector(NodeDetector):
    """Detect Node.js conventions."""

    name = "node_conventions"
    description = "Detects Node.js framework, TypeScript usage, and patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Node.js framework, TypeScript usage, and patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect TypeScript usage
        self._detect_typescript(ctx, index, result)

        # Detect framework
        self._detect_framework(ctx, index, result)

        # Detect testing framework
        self._detect_testing(ctx, index, result)

        # Detect module system
        self._detect_module_system(ctx, index, result)

        return result

    def _detect_typescript(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect TypeScript usage."""
        ts_files = sum(1 for f in index.files.values() if f.has_typescript)
        js_files = sum(1 for f in index.files.values() if not f.has_typescript)
        total = ts_files + js_files

        if total < 3:
            return

        ts_ratio = ts_files / total if total else 0

        if ts_ratio >= 0.9:
            title = "TypeScript codebase"
            description = (
                f"Codebase is written in TypeScript. "
                f"{ts_files}/{total} files are TypeScript."
            )
            confidence = 0.95
        elif ts_ratio >= 0.5:
            title = "Mixed TypeScript/JavaScript"
            description = (
                f"Codebase uses both TypeScript and JavaScript. "
                f"TypeScript: {ts_files}, JavaScript: {js_files}."
            )
            confidence = 0.8
        elif ts_ratio > 0:
            title = "JavaScript with some TypeScript"
            description = (
                f"Primarily JavaScript with some TypeScript files. "
                f"TypeScript: {ts_files}, JavaScript: {js_files}."
            )
            confidence = 0.75
        else:
            title = "JavaScript codebase"
            description = f"Codebase is written in JavaScript. {js_files} files."
            confidence = 0.9

        result.rules.append(self.make_rule(
            rule_id="node.conventions.typescript",
            category="language",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=[],
            stats={
                "typescript_files": ts_files,
                "javascript_files": js_files,
                "typescript_ratio": round(ts_ratio, 3),
            },
        ))

    def _detect_framework(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect web framework usage."""
        frameworks: Counter[str] = Counter()
        framework_examples: dict[str, list[tuple[str, int]]] = {}

        framework_patterns = {
            "express": ["express"],
            "fastify": ["fastify"],
            "koa": ["koa"],
            "nestjs": ["@nestjs/core", "@nestjs/common"],
            "hapi": ["@hapi/hapi", "hapi"],
            "next": ["next"],
            "nuxt": ["nuxt"],
            "remix": ["@remix-run"],
        }

        for framework, patterns in framework_patterns.items():
            for pattern in patterns:
                imports = index.find_imports_matching(pattern, limit=10)
                if imports:
                    frameworks[framework] += len(imports)
                    if framework not in framework_examples:
                        framework_examples[framework] = []
                    for rel_path, module, line in imports[:5]:
                        framework_examples[framework].append((rel_path, line))

        if not frameworks:
            return

        primary, primary_count = frameworks.most_common(1)[0]
        total = sum(frameworks.values())

        framework_names = {
            "express": "Express.js",
            "fastify": "Fastify",
            "koa": "Koa",
            "nestjs": "NestJS",
            "hapi": "Hapi",
            "next": "Next.js",
            "nuxt": "Nuxt.js",
            "remix": "Remix",
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
                f"Uses {framework_names.get(primary, primary)} "
                f"({primary_count}/{total} imports). Also: {', '.join(other)}."
            )
            confidence = min(0.85, 0.5 + (primary_count / total) * 0.35)

        # Build evidence
        evidence = []
        for rel_path, line in framework_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.framework",
            category="api",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "framework_counts": dict(frameworks),
                "primary_framework": primary,
            },
        ))

    def _detect_testing(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect testing framework usage."""
        test_libs: Counter[str] = Counter()
        test_examples: dict[str, list[tuple[str, int]]] = {}

        test_patterns = {
            "jest": ["jest", "@jest"],
            "mocha": ["mocha"],
            "vitest": ["vitest"],
            "ava": ["ava"],
            "tap": ["tap"],
            "jasmine": ["jasmine"],
        }

        for lib, patterns in test_patterns.items():
            for pattern in patterns:
                imports = index.find_imports_matching(pattern, limit=10)
                if imports:
                    test_libs[lib] += len(imports)
                    if lib not in test_examples:
                        test_examples[lib] = []
                    for rel_path, module, line in imports[:5]:
                        test_examples[lib].append((rel_path, line))

        if not test_libs:
            return

        primary, primary_count = test_libs.most_common(1)[0]

        lib_names = {
            "jest": "Jest",
            "mocha": "Mocha",
            "vitest": "Vitest",
            "ava": "AVA",
            "tap": "tap",
            "jasmine": "Jasmine",
        }

        title = f"Testing with {lib_names.get(primary, primary)}"
        description = (
            f"Uses {lib_names.get(primary, primary)} for testing. "
            f"Found {primary_count} test-related imports."
        )
        confidence = min(0.9, 0.6 + primary_count * 0.05)

        # Build evidence
        evidence = []
        for rel_path, line in test_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.testing_framework",
            category="testing",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "test_library_counts": dict(test_libs),
                "primary_library": primary,
            },
        ))

    def _detect_module_system(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect ES modules vs CommonJS usage."""
        esm_count = 0
        cjs_count = 0

        for file_idx in index.files.values():
            content = "\n".join(file_idx.lines)

            # Check for ES module syntax
            if re.search(r"^import\s+", content, re.MULTILINE):
                esm_count += 1
            elif re.search(r"^export\s+", content, re.MULTILINE):
                esm_count += 1

            # Check for CommonJS
            if re.search(r"require\s*\(", content):
                cjs_count += 1
            if re.search(r"module\.exports\s*=", content):
                cjs_count += 1

        total = esm_count + cjs_count
        if total < 5:
            return

        esm_ratio = esm_count / total if total else 0

        if esm_ratio >= 0.8:
            title = "ES Modules (ESM)"
            description = (
                f"Uses ES module syntax (import/export). "
                f"ESM: {esm_count}, CommonJS: {cjs_count}."
            )
            confidence = min(0.9, 0.6 + esm_ratio * 0.3)
        elif esm_ratio >= 0.3:
            title = "Mixed module systems"
            description = (
                f"Uses both ESM and CommonJS. "
                f"ESM: {esm_count}, CommonJS: {cjs_count}."
            )
            confidence = 0.7
        else:
            title = "CommonJS modules"
            description = (
                f"Uses CommonJS (require/module.exports). "
                f"CommonJS: {cjs_count}, ESM: {esm_count}."
            )
            confidence = min(0.9, 0.6 + (1 - esm_ratio) * 0.3)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.module_system",
            category="structure",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=[],
            stats={
                "esm_count": esm_count,
                "cjs_count": cjs_count,
                "esm_ratio": round(esm_ratio, 3),
            },
        ))
