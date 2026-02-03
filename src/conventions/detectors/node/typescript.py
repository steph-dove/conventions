"""Node.js TypeScript conventions detector."""

from __future__ import annotations

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import NodeDetector
from .index import NodeIndex


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

        # Detect branded/nominal types
        self._detect_branded_types(ctx, index, result)

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

    def _detect_branded_types(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect branded/nominal types for type-safe IDs and values."""
        # Pattern for branded types: type XId = string & { __brand: 'x' }
        brand_pattern = r'type\s+\w+(?:Id|ID)\s*=\s*(?:string|number)\s*&\s*\{'
        brand_matches = index.search_pattern(brand_pattern, limit=20, exclude_tests=True)

        # Pattern for generic branded types: StringIdFor<'tableName'>
        generic_id_pattern = r'(?:StringIdFor|NumberIdFor|BrandedId|TypedId)<'
        generic_matches = index.search_pattern(generic_id_pattern, limit=30, exclude_tests=True)

        # Pattern for Opaque/Nominal type utilities
        opaque_pattern = r'(?:Opaque|Nominal|Brand|Tagged)<'
        opaque_count = index.count_pattern(opaque_pattern, exclude_tests=True)

        # Check for __brand or __type or __tag fields (common branding approaches)
        brand_field_pattern = r'__(?:brand|type|tag|nominal)\s*[?:]'
        brand_field_count = index.count_pattern(brand_field_pattern, exclude_tests=True)

        total = len(brand_matches) + len(generic_matches) + opaque_count + (brand_field_count // 2)
        if total < 2:
            return

        title = "Branded types for IDs"
        parts = []
        if brand_matches:
            parts.append(f"{len(brand_matches)} branded ID types")
        if generic_matches:
            parts.append(f"{len(generic_matches)} generic ID types")
        if opaque_count:
            parts.append(f"{opaque_count} opaque type usages")

        description = (
            f"Uses branded/nominal types for type-safe identifiers. "
            f"{', '.join(parts)}."
        )
        confidence = min(0.9, 0.7 + total * 0.05)

        evidence = []
        all_matches = brand_matches + generic_matches
        for rel_path, line, _ in all_matches[:ctx.max_evidence_snippets]:
            from .index import make_evidence
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.branded_types",
            category="language",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "branded_id_types": len(brand_matches),
                "generic_id_types": len(generic_matches),
                "opaque_type_usages": opaque_count,
                "brand_field_count": brand_field_count,
            },
        ))
