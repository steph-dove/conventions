"""Node.js error handling conventions detector."""

from __future__ import annotations

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import NodeDetector
from .index import NodeIndex, make_evidence


@DetectorRegistry.register
class NodeErrorHandlingDetector(NodeDetector):
    """Detect Node.js error handling conventions."""

    name = "node_errors"
    description = "Detects Node.js error handling patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Node.js error handling conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect custom error classes
        self._detect_custom_error_classes(ctx, index, result)

        # Detect async error handling
        self._detect_async_error_handling(ctx, index, result)

        # Detect error middleware
        self._detect_error_middleware(ctx, index, result)

        return result

    def _detect_custom_error_classes(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect custom Error classes."""
        # class XxxError extends Error
        error_class_pattern = r'class\s+\w*Error\s+extends\s+(?:Error|BaseError|\w*Error)'
        matches = index.search_pattern(error_class_pattern, limit=50, exclude_tests=True)

        if len(matches) < 2:
            return

        title = "Custom error classes"
        description = (
            f"Defines custom Error classes. "
            f"Found {len(matches)} custom error classes."
        )
        confidence = min(0.9, 0.6 + len(matches) * 0.05)

        evidence = []
        for rel_path, line, _ in matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.error_classes",
            category="error_handling",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "custom_error_count": len(matches),
            },
        ))

    def _detect_async_error_handling(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect async error handling patterns."""
        # try/catch in async functions
        try_catch_pattern = r'try\s*\{'
        try_catch_count = index.count_pattern(try_catch_pattern, exclude_tests=True)

        # .catch() on promises
        catch_chain_pattern = r'\.catch\s*\('
        catch_chain_count = index.count_pattern(catch_chain_pattern, exclude_tests=True)

        # Unhandled promise rejection handler
        unhandled_pattern = r'unhandledRejection'
        unhandled_count = index.count_pattern(unhandled_pattern, exclude_tests=True)

        # async function count
        async_count = sum(f.async_function_count for f in index.get_non_test_files())

        total_handling = try_catch_count + catch_chain_count
        if total_handling < 5 or async_count < 3:
            return

        handling_ratio = total_handling / async_count if async_count else 0

        if handling_ratio >= 0.5:
            title = "Comprehensive async error handling"
            description = (
                f"Good async error handling coverage. "
                f"try/catch: {try_catch_count}, .catch(): {catch_chain_count}, "
                f"async functions: {async_count}."
            )
            confidence = 0.85
        else:
            title = "Async error handling"
            description = (
                f"Uses try/catch and .catch() for async errors. "
                f"try/catch: {try_catch_count}, .catch(): {catch_chain_count}."
            )
            confidence = 0.75

        result.rules.append(self.make_rule(
            rule_id="node.conventions.async_error_handling",
            category="error_handling",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=[],
            stats={
                "try_catch_count": try_catch_count,
                "catch_chain_count": catch_chain_count,
                "async_function_count": async_count,
                "has_unhandled_rejection_handler": unhandled_count > 0,
            },
        ))

    def _detect_error_middleware(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect Express/Fastify error middleware."""
        # Express error middleware: (err, req, res, next)
        express_error_pattern = r'(?:function|=>)\s*\(\s*err\s*,\s*req\s*,\s*res\s*,\s*next\s*\)'
        express_matches = index.search_pattern(express_error_pattern, limit=20, exclude_tests=True)

        # app.use with error handler
        app_use_error_pattern = r'app\.use\s*\([^)]*error'
        index.count_pattern(app_use_error_pattern, exclude_tests=True)

        # Fastify error handler
        fastify_error_pattern = r'setErrorHandler\s*\('
        fastify_count = index.count_pattern(fastify_error_pattern, exclude_tests=True)

        total = len(express_matches) + fastify_count
        if total < 1:
            return

        if len(express_matches) > 0:
            title = "Express error middleware"
            description = (
                f"Uses Express-style error middleware (err, req, res, next). "
                f"Found {len(express_matches)} error handlers."
            )
        else:
            title = "Fastify error handler"
            description = f"Uses Fastify setErrorHandler. Found {fastify_count} handlers."

        confidence = min(0.9, 0.7 + total * 0.1)

        evidence = []
        for rel_path, line, _ in express_matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=4)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.error_middleware",
            category="error_handling",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "express_error_handlers": len(express_matches),
                "fastify_error_handlers": fastify_count,
            },
        ))
