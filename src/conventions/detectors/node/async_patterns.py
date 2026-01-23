"""Node.js async patterns detector."""

from __future__ import annotations

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import NodeDetector
from .index import NodeIndex, make_evidence


@DetectorRegistry.register
class NodeAsyncPatternsDetector(NodeDetector):
    """Detect Node.js async patterns."""

    name = "node_async_patterns"
    description = "Detects Node.js async/await, promises, and callback patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Node.js async patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect async style (callbacks vs promises vs async/await)
        self._detect_async_style(ctx, index, result)

        # Detect Promise patterns
        self._detect_promise_patterns(ctx, index, result)

        return result

    def _detect_async_style(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect primary async style."""
        # async/await
        async_await_count = sum(f.async_function_count for f in index.get_non_test_files())

        # Promise constructor: new Promise(
        promise_constructor_pattern = r'new\s+Promise\s*\('
        index.count_pattern(promise_constructor_pattern, exclude_tests=True)

        # .then() chains
        then_chain_pattern = r'\.then\s*\('
        then_chain_count = index.count_pattern(then_chain_pattern, exclude_tests=True)

        # Callback patterns: function(err, result), (err, data) =>
        callback_pattern = r'(?:function\s*\(|=>)\s*(?:err|error)\s*,\s*\w+'
        callback_count = index.count_pattern(callback_pattern, exclude_tests=True)

        total = async_await_count + then_chain_count + callback_count
        if total < 5:
            return

        async_ratio = async_await_count / total if total else 0
        promise_ratio = then_chain_count / total if total else 0
        callback_ratio = callback_count / total if total else 0

        if async_ratio >= 0.6:
            title = "Modern async/await"
            description = (
                f"Primarily uses async/await for async operations. "
                f"async/await: {async_await_count}, .then(): {then_chain_count}, callbacks: {callback_count}."
            )
            confidence = min(0.95, 0.7 + async_ratio * 0.2)
        elif promise_ratio >= 0.4:
            title = "Promise-based async"
            description = (
                f"Uses Promise .then() chains. "
                f".then(): {then_chain_count}, async/await: {async_await_count}, callbacks: {callback_count}."
            )
            confidence = 0.8
        elif callback_ratio >= 0.4:
            title = "Callback-style async"
            description = (
                f"Uses callback pattern for async. "
                f"Callbacks: {callback_count}, async/await: {async_await_count}, .then(): {then_chain_count}."
            )
            confidence = 0.75
        else:
            title = "Mixed async patterns"
            description = (
                f"Uses multiple async patterns. "
                f"async/await: {async_await_count}, .then(): {then_chain_count}, callbacks: {callback_count}."
            )
            confidence = 0.7

        result.rules.append(self.make_rule(
            rule_id="node.conventions.async_style",
            category="async",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=[],
            stats={
                "async_await_count": async_await_count,
                "then_chain_count": then_chain_count,
                "callback_count": callback_count,
                "async_ratio": round(async_ratio, 3),
            },
        ))

    def _detect_promise_patterns(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect Promise utility patterns."""
        # Promise.all
        promise_all_pattern = r'Promise\.all\s*\('
        all_count = index.count_pattern(promise_all_pattern, exclude_tests=True)

        # Promise.allSettled
        all_settled_pattern = r'Promise\.allSettled\s*\('
        all_settled_count = index.count_pattern(all_settled_pattern, exclude_tests=True)

        # Promise.race
        race_pattern = r'Promise\.race\s*\('
        race_count = index.count_pattern(race_pattern, exclude_tests=True)

        # Promise.any
        any_pattern = r'Promise\.any\s*\('
        any_count = index.count_pattern(any_pattern, exclude_tests=True)

        total = all_count + all_settled_count + race_count + any_count
        if total < 3:
            return

        parts = []
        if all_count:
            parts.append(f"Promise.all: {all_count}")
        if all_settled_count:
            parts.append(f"Promise.allSettled: {all_settled_count}")
        if race_count:
            parts.append(f"Promise.race: {race_count}")
        if any_count:
            parts.append(f"Promise.any: {any_count}")

        title = "Promise combinators"
        description = f"Uses Promise utility methods. {', '.join(parts)}."
        confidence = min(0.9, 0.6 + total * 0.03)

        matches = index.search_pattern(promise_all_pattern, limit=10)

        evidence = []
        for rel_path, line, _ in matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.promise_patterns",
            category="async",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "promise_all_count": all_count,
                "promise_all_settled_count": all_settled_count,
                "promise_race_count": race_count,
                "promise_any_count": any_count,
            },
        ))
