"""Rust async runtime conventions detector."""

from __future__ import annotations

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import RustDetector
from .index import make_evidence


@DetectorRegistry.register
class RustAsyncDetector(RustDetector):
    """Detect Rust async runtime conventions."""

    name = "rust_async"
    description = "Detects async runtimes (Tokio, async-std, smol)"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect async runtime conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        runtimes: dict[str, dict] = {}
        examples: list[tuple[str, int]] = []

        # Check for Tokio
        tokio_uses = index.find_uses_matching("tokio", limit=50)
        if tokio_uses:
            runtimes["tokio"] = {
                "name": "Tokio",
                "count": len(tokio_uses),
            }
            examples.extend([(r, ln) for r, _, ln in tokio_uses[:3]])

            # Check for tokio::main
            tokio_main = index.search_pattern(r"#\[tokio::main\]", limit=10)
            if tokio_main:
                runtimes["tokio"]["has_main"] = True

            # Check for tokio::test
            tokio_test = index.search_pattern(r"#\[tokio::test\]", limit=20)
            if tokio_test:
                runtimes["tokio"]["test_count"] = len(tokio_test)

        # Check for async-std
        async_std_uses = index.find_uses_matching("async_std", limit=50)
        if async_std_uses:
            runtimes["async_std"] = {
                "name": "async-std",
                "count": len(async_std_uses),
            }
            examples.extend([(r, ln) for r, _, ln in async_std_uses[:3]])

        # Check for smol
        smol_uses = index.find_uses_matching("smol", limit=30)
        if smol_uses:
            runtimes["smol"] = {
                "name": "smol",
                "count": len(smol_uses),
            }

        # Check for futures crate
        futures_uses = index.find_uses_matching("futures", limit=30)
        if futures_uses:
            runtimes["futures"] = {
                "name": "futures",
                "count": len(futures_uses),
            }

        # Count async functions
        total_async = sum(f.async_count for f in index.files.values())

        # Check for common async patterns
        patterns = []

        # Check for async channels
        channel_uses = index.search_pattern(
            r"(?:mpsc|broadcast|watch|oneshot)::",
            limit=30,
            exclude_tests=True,
        )
        if channel_uses:
            patterns.append("async channels")

        # Check for spawn
        spawn_calls = index.search_pattern(
            r"(?:tokio::)?spawn\s*\(",
            limit=30,
            exclude_tests=True,
        )
        if spawn_calls:
            patterns.append("task spawning")

        # Check for select!
        select_macros = index.search_pattern(r"select!\s*\{", limit=20)
        if select_macros:
            patterns.append("select!")

        # Check for join!
        join_macros = index.search_pattern(r"join!\s*\(", limit=20)
        if join_macros:
            patterns.append("join!")

        if not runtimes and total_async == 0:
            return result

        # Determine primary runtime
        if "tokio" in runtimes:
            primary = "Tokio"
        elif "async_std" in runtimes:
            primary = "async-std"
        elif "smol" in runtimes:
            primary = "smol"
        elif total_async > 0:
            primary = "no runtime (library)"
        else:
            return result

        title = f"Async runtime: {primary}"
        description = f"Uses {primary}."

        if total_async > 0:
            description += f" {total_async} async function(s)."

        if patterns:
            description += f" Patterns: {', '.join(patterns[:3])}."

        confidence = 0.95

        evidence = []
        for rel_path, line in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="rust.conventions.async_runtime",
            category="async",
            title=title,
            description=description,
            confidence=confidence,
            language="rust",
            evidence=evidence,
            stats={
                "runtimes": list(runtimes.keys()),
                "primary_runtime": primary,
                "total_async_functions": total_async,
                "patterns": patterns,
                "runtime_details": runtimes,
            },
        ))

        return result
