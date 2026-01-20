"""Node.js documentation conventions detector."""

from __future__ import annotations

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import NodeDetector
from .index import NodeIndex, make_evidence


@DetectorRegistry.register
class NodeDocumentationDetector(NodeDetector):
    """Detect Node.js documentation conventions."""

    name = "node_documentation"
    description = "Detects JSDoc usage and documentation patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Node.js documentation conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect JSDoc usage
        self._detect_jsdoc(ctx, index, result)

        return result

    def _detect_jsdoc(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect JSDoc comment coverage."""
        # JSDoc block comments: /** ... */
        jsdoc_pattern = r'/\*\*[\s\S]*?\*/'
        jsdoc_matches = index.search_pattern(jsdoc_pattern, limit=200, exclude_tests=True)
        jsdoc_count = len(jsdoc_matches)

        # Count functions (rough estimate)
        total_functions = sum(
            f.function_count for f in index.get_non_test_files()
        )

        if total_functions < 5:
            return

        jsdoc_ratio = jsdoc_count / total_functions if total_functions else 0

        # Check for @param, @returns, @type tags
        param_count = index.count_pattern(r'@param\s+', exclude_tests=True)
        returns_count = index.count_pattern(r'@returns?\s+', exclude_tests=True)
        type_count = index.count_pattern(r'@type\s+', exclude_tests=True)

        has_rich_jsdoc = param_count > 5 or returns_count > 5

        if jsdoc_ratio >= 0.5 and has_rich_jsdoc:
            title = "Comprehensive JSDoc"
            description = (
                f"Good JSDoc coverage with typed annotations. "
                f"JSDoc blocks: {jsdoc_count}, @param: {param_count}, @returns: {returns_count}."
            )
            confidence = 0.9
        elif jsdoc_ratio >= 0.3:
            title = "Partial JSDoc coverage"
            description = (
                f"Some JSDoc documentation present. "
                f"JSDoc blocks: {jsdoc_count}, functions: ~{total_functions}."
            )
            confidence = 0.75
        elif jsdoc_count >= 5:
            title = "Limited JSDoc"
            description = (
                f"Limited JSDoc documentation. "
                f"Only {jsdoc_count} JSDoc blocks for ~{total_functions} functions."
            )
            confidence = 0.7
        else:
            return

        evidence = []
        for rel_path, line, _ in jsdoc_matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.jsdoc",
            category="documentation",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "jsdoc_count": jsdoc_count,
                "param_tags": param_count,
                "returns_tags": returns_count,
                "type_tags": type_count,
                "function_count": total_functions,
                "jsdoc_ratio": round(jsdoc_ratio, 3),
            },
        ))
