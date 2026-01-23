"""Node.js TypeScript conventions detector."""

from __future__ import annotations

import re
from pathlib import Path

from ..base import DetectorContext, DetectorResult
from .base import NodeDetector
from .index import NodeIndex, make_evidence
from ..registry import DetectorRegistry


@DetectorRegistry.register
class NodeTypeScriptDetector(NodeDetector):
    """Detect Node.js TypeScript conventions."""

    name = "node_typescript"
    description = "Detects TypeScript usage patterns and strictness"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect TypeScript conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect TypeScript strict mode
        self._detect_strict_mode(ctx, index, result)

        # Detect type coverage (any usage)
        self._detect_type_coverage(ctx, index, result)

        return result

    def _detect_strict_mode(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect TypeScript strict mode from tsconfig."""
        # Look for tsconfig.json in the repo
        from ...fs import read_file_safe

        tsconfig_path = ctx.repo_root / "tsconfig.json"
        content = read_file_safe(tsconfig_path)

        if content is None:
            return

        # Check for strict mode settings
        has_strict = '"strict": true' in content or '"strict":true' in content
        has_strict_null = '"strictNullChecks": true' in content
        has_no_implicit_any = '"noImplicitAny": true' in content

        strict_settings = []
        if has_strict:
            strict_settings.append("strict")
        if has_strict_null:
            strict_settings.append("strictNullChecks")
        if has_no_implicit_any:
            strict_settings.append("noImplicitAny")

        if has_strict:
            title = "TypeScript strict mode"
            description = "TypeScript configured with strict mode enabled."
            confidence = 0.95
        elif strict_settings:
            title = "TypeScript partial strictness"
            description = f"TypeScript with partial strict settings: {', '.join(strict_settings)}."
            confidence = 0.8
        else:
            title = "TypeScript non-strict"
            description = "TypeScript configured without strict mode."
            confidence = 0.75

        result.rules.append(self.make_rule(
            rule_id="node.conventions.strict_mode",
            category="language",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=[],
            stats={
                "has_strict": has_strict,
                "has_strict_null_checks": has_strict_null,
                "has_no_implicit_any": has_no_implicit_any,
            },
        ))

    def _detect_type_coverage(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect type coverage by analyzing any usage and type assertions."""
        ts_files = index.get_typescript_files()
        if len(ts_files) < 3:
            return

        # Count 'any' type usage
        any_pattern = r':\s*any\b'
        any_count = index.count_pattern(any_pattern, exclude_tests=True)

        # Count type assertions (as Type, <Type>)
        assertion_pattern = r'\bas\s+\w+|<\w+>\s*\w+'
        assertion_count = index.count_pattern(assertion_pattern, exclude_tests=True)

        # Count explicit type annotations
        type_annotation_pattern = r':\s*(?:string|number|boolean|object|\w+\[\]|\w+<)'
        annotation_count = index.count_pattern(type_annotation_pattern, exclude_tests=True)

        total_type_hints = annotation_count + any_count
        if total_type_hints < 10:
            return

        any_ratio = any_count / total_type_hints if total_type_hints else 0

        if any_ratio <= 0.05:
            title = "Strong type coverage"
            description = (
                f"Minimal use of 'any' type. "
                f"any: {any_count}, typed: {annotation_count}."
            )
            confidence = 0.9
        elif any_ratio <= 0.2:
            title = "Good type coverage"
            description = (
                f"Limited use of 'any' type. "
                f"any: {any_count}, typed: {annotation_count}."
            )
            confidence = 0.8
        else:
            title = "Heavy 'any' usage"
            description = (
                f"Significant use of 'any' type reduces type safety. "
                f"any: {any_count}, typed: {annotation_count}."
            )
            confidence = 0.75

        result.rules.append(self.make_rule(
            rule_id="node.conventions.type_coverage",
            category="language",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=[],
            stats={
                "any_count": any_count,
                "assertion_count": assertion_count,
                "annotation_count": annotation_count,
                "any_ratio": round(any_ratio, 3),
            },
        ))
