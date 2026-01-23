"""Node.js logging conventions detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import NodeDetector
from .index import NodeIndex, make_evidence


@DetectorRegistry.register
class NodeLoggingDetector(NodeDetector):
    """Detect Node.js logging conventions."""

    name = "node_logging"
    description = "Detects Node.js logging library and patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Node.js logging conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect logging library
        self._detect_logging_library(ctx, index, result)

        # Detect console.log vs structured logging
        self._detect_logging_style(ctx, index, result)

        return result

    def _detect_logging_library(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect logging library usage."""
        libraries = {
            "winston": "winston",
            "pino": "pino",
            "bunyan": "bunyan",
            "log4js": "log4js",
            "morgan": "morgan",
        }

        lib_counts: Counter[str] = Counter()
        examples: dict[str, list[tuple[str, int]]] = {}

        for name, pkg in libraries.items():
            imports = index.find_imports_matching(pkg, limit=20)
            if imports:
                lib_counts[name] = len(imports)
                examples[name] = [(r, ln) for r, _, ln in imports[:5]]

        if not lib_counts:
            return

        primary, primary_count = lib_counts.most_common(1)[0]

        lib_names = {
            "winston": "Winston",
            "pino": "Pino",
            "bunyan": "Bunyan",
            "log4js": "log4js",
            "morgan": "Morgan (HTTP)",
        }

        if len(lib_counts) == 1:
            title = f"Logging with {lib_names.get(primary, primary)}"
            description = (
                f"Uses {lib_names.get(primary, primary)} for logging. "
                f"Found in {primary_count} files."
            )
        else:
            others = [lib_names.get(n, n) for n in lib_counts if n != primary]
            title = f"Primary logging: {lib_names.get(primary, primary)}"
            description = (
                f"Primarily uses {lib_names.get(primary, primary)}. "
                f"Also: {', '.join(others)}."
            )

        confidence = min(0.95, 0.7 + primary_count * 0.03)

        evidence = []
        for rel_path, line in examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.logging_library",
            category="observability",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "library_counts": dict(lib_counts),
                "primary_library": primary,
            },
        ))

    def _detect_logging_style(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect console.log vs structured logging."""
        # console.log/warn/error usage
        console_pattern = r'console\.(?:log|warn|error|info|debug)\s*\('
        console_count = index.count_pattern(console_pattern, exclude_tests=True)

        # Structured logging patterns (with objects)
        # logger.info({...}), logger.info('message', {...})
        structured_pattern = r'logger\.(?:info|warn|error|debug)\s*\(\s*\{'
        structured_count = index.count_pattern(structured_pattern, exclude_tests=True)

        # General logger usage
        logger_pattern = r'logger\.(?:info|warn|error|debug)\s*\('
        logger_count = index.count_pattern(logger_pattern, exclude_tests=True)

        total = console_count + logger_count
        if total < 5:
            return

        console_ratio = console_count / total if total else 0

        if console_ratio <= 0.1 and logger_count >= 5:
            title = "Structured logging"
            description = (
                f"Uses dedicated logger over console.log. "
                f"Logger: {logger_count}, console: {console_count}."
            )
            confidence = 0.9
        elif console_ratio <= 0.3:
            title = "Mixed logging"
            description = (
                f"Mix of logger and console.log. "
                f"Logger: {logger_count}, console: {console_count}."
            )
            confidence = 0.75
        else:
            title = "Console.log logging"
            description = (
                f"Relies on console.log for logging. "
                f"console: {console_count}, logger: {logger_count}."
            )
            confidence = 0.8

        result.rules.append(self.make_rule(
            rule_id="node.conventions.structured_logging",
            category="observability",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=[],
            stats={
                "console_count": console_count,
                "logger_count": logger_count,
                "structured_count": structured_count,
                "console_ratio": round(console_ratio, 3),
            },
        ))
