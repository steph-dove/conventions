"""Node.js security conventions detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import NodeDetector
from .index import NodeIndex, make_evidence


@DetectorRegistry.register
class NodeSecurityDetector(NodeDetector):
    """Detect Node.js security conventions."""

    name = "node_security"
    description = "Detects Node.js security patterns and practices"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Node.js security conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect SQL patterns
        self._detect_sql_patterns(ctx, index, result)

        # Detect environment/config management
        self._detect_env_config(ctx, index, result)

        # Detect input validation
        self._detect_input_validation(ctx, index, result)

        # Detect security middleware (helmet)
        self._detect_security_middleware(ctx, index, result)

        return result

    def _detect_sql_patterns(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect SQL query patterns."""
        # Raw query patterns (potential SQL injection)
        raw_pattern = r'query\s*\(\s*[`\'"](?:SELECT|INSERT|UPDATE|DELETE)'
        raw_count = index.count_pattern(raw_pattern, exclude_tests=True)

        # Parameterized queries: query('...', [params]) or query`...`
        param_pattern = r'query\s*\(\s*[`\'"][^`\'"]*\?\s*[^`\'"]*[`\'"],\s*\['
        param_count = index.count_pattern(param_pattern, exclude_tests=True)

        # ORM usage (Prisma, Sequelize, TypeORM)
        orm_imports = (
            index.find_imports_matching("@prisma", limit=5) +
            index.find_imports_matching("sequelize", limit=5) +
            index.find_imports_matching("typeorm", limit=5)
        )
        orm_count = len(orm_imports)

        total = raw_count + param_count + orm_count
        if total < 2:
            return

        if orm_count > 0:
            title = "ORM for database access"
            description = f"Uses ORM for database queries. Found {orm_count} ORM imports."
            confidence = 0.9
        elif param_count > raw_count:
            title = "Parameterized SQL queries"
            description = (
                f"Uses parameterized queries. "
                f"Parameterized: {param_count}, Raw: {raw_count}."
            )
            confidence = 0.85
        else:
            title = "SQL injection risk"
            description = (
                f"Uses string interpolation in SQL queries. "
                f"Raw: {raw_count}, Parameterized: {param_count}."
            )
            confidence = 0.8

        result.rules.append(self.make_rule(
            rule_id="node.conventions.sql_injection",
            category="security",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=[],
            stats={
                "raw_query_count": raw_count,
                "parameterized_count": param_count,
                "orm_usage": orm_count > 0,
            },
        ))

    def _detect_env_config(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect environment configuration management."""
        config_libs = {
            "dotenv": "dotenv",
            "config": "config",
            "convict": "convict",
            "envalid": "envalid",
        }

        lib_counts: Counter[str] = Counter()
        examples: dict[str, list[tuple[str, int]]] = {}

        for name, pkg in config_libs.items():
            imports = index.find_imports_matching(pkg, limit=10)
            if imports:
                lib_counts[name] = len(imports)
                examples[name] = [(r, ln) for r, _, ln in imports[:5]]

        # Also check for process.env usage
        process_env_count = index.count_pattern(r'process\.env\.', exclude_tests=True)

        if not lib_counts and process_env_count < 5:
            return

        if lib_counts:
            primary, primary_count = lib_counts.most_common(1)[0]
            lib_names = {
                "dotenv": "dotenv",
                "config": "node-config",
                "convict": "convict",
                "envalid": "envalid",
            }
            title = f"Config with {lib_names.get(primary, primary)}"
            description = (
                f"Uses {lib_names.get(primary, primary)} for configuration. "
                f"process.env: {process_env_count} usages."
            )
            confidence = 0.85
        else:
            title = "Direct process.env usage"
            description = f"Reads configuration from process.env. Found {process_env_count} usages."
            confidence = 0.7

        evidence = []
        if lib_counts:
            primary = max(lib_counts, key=lib_counts.get)  # type: ignore
            for rel_path, line in examples.get(primary, [])[:ctx.max_evidence_snippets]:
                ev = make_evidence(index, rel_path, line, radius=3)
                if ev:
                    evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.env_config",
            category="security",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "config_library": list(lib_counts.keys())[0] if lib_counts else None,
                "process_env_count": process_env_count,
            },
        ))

    def _detect_input_validation(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect input validation library usage."""
        validation_libs = {
            "joi": "joi",
            "zod": "zod",
            "yup": "yup",
            "class-validator": "class-validator",
            "express-validator": "express-validator",
        }

        lib_counts: Counter[str] = Counter()
        examples: dict[str, list[tuple[str, int]]] = {}

        for name, pkg in validation_libs.items():
            imports = index.find_imports_matching(pkg, limit=20)
            if imports:
                lib_counts[name] = len(imports)
                examples[name] = [(r, ln) for r, _, ln in imports[:5]]

        if not lib_counts:
            return

        primary, primary_count = lib_counts.most_common(1)[0]

        lib_names = {
            "joi": "Joi",
            "zod": "Zod",
            "yup": "Yup",
            "class-validator": "class-validator",
            "express-validator": "express-validator",
        }

        title = f"Input validation with {lib_names.get(primary, primary)}"
        description = (
            f"Uses {lib_names.get(primary, primary)} for input validation. "
            f"Found in {primary_count} files."
        )
        confidence = min(0.9, 0.7 + primary_count * 0.03)

        evidence = []
        for rel_path, line in examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.input_validation",
            category="security",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "validation_library": primary,
                "library_counts": dict(lib_counts),
            },
        ))

    def _detect_security_middleware(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect security middleware usage (helmet, cors, etc.)."""
        security_libs = {
            "helmet": "helmet",
            "cors": "cors",
            "csurf": "csurf",
            "express-rate-limit": "express-rate-limit",
            "hpp": "hpp",
        }

        lib_counts: Counter[str] = Counter()
        examples: dict[str, list[tuple[str, int]]] = {}

        for name, pkg in security_libs.items():
            imports = index.find_imports_matching(pkg, limit=10)
            if imports:
                lib_counts[name] = len(imports)
                examples[name] = [(r, ln) for r, _, ln in imports[:3]]

        if not lib_counts:
            return

        libs_used = list(lib_counts.keys())

        title = "Security middleware"
        description = f"Uses security middleware: {', '.join(libs_used)}."
        confidence = min(0.9, 0.7 + len(libs_used) * 0.05)

        evidence = []
        for lib in libs_used[:2]:
            for rel_path, line in examples.get(lib, [])[:2]:
                ev = make_evidence(index, rel_path, line, radius=3)
                if ev:
                    evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.helmet_security",
            category="security",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "security_libraries": libs_used,
                "library_counts": dict(lib_counts),
            },
        ))
