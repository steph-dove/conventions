"""Rust error handling conventions detector."""

from __future__ import annotations

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import RustDetector
from .index import make_evidence


@DetectorRegistry.register
class RustErrorHandlingDetector(RustDetector):
    """Detect Rust error handling conventions."""

    name = "rust_errors"
    description = "Detects error handling patterns (anyhow, thiserror, custom errors)"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect error handling conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        patterns: dict[str, dict] = {}
        examples: list[tuple[str, int]] = []

        # Check for anyhow
        anyhow_uses = index.find_uses_matching("anyhow", limit=30)
        if anyhow_uses:
            patterns["anyhow"] = {
                "name": "anyhow",
                "type": "application errors",
                "count": len(anyhow_uses),
            }
            examples.extend([(r, ln) for r, _, ln in anyhow_uses[:3]])

        # Check for thiserror
        thiserror_uses = index.find_uses_matching("thiserror", limit=30)
        if thiserror_uses:
            patterns["thiserror"] = {
                "name": "thiserror",
                "type": "library errors",
                "count": len(thiserror_uses),
            }
            examples.extend([(r, ln) for r, _, ln in thiserror_uses[:3]])

        # Check for eyre
        eyre_uses = index.find_uses_matching("eyre", limit=30)
        if eyre_uses:
            patterns["eyre"] = {
                "name": "eyre",
                "type": "error reporting",
                "count": len(eyre_uses),
            }

        # Check for miette
        miette_uses = index.find_uses_matching("miette", limit=30)
        if miette_uses:
            patterns["miette"] = {
                "name": "miette",
                "type": "diagnostic errors",
                "count": len(miette_uses),
            }

        # Check for color-eyre
        color_eyre_uses = index.find_uses_matching("color_eyre", limit=20)
        if color_eyre_uses:
            patterns["color_eyre"] = {
                "name": "color-eyre",
                "type": "colorful panics",
                "count": len(color_eyre_uses),
            }

        # Count ? operator usage
        question_mark_count = index.count_pattern(r"\?\s*[;}\)]", exclude_tests=True)

        # Count .unwrap() usage
        unwrap_count = index.count_pattern(r"\.unwrap\(\)", exclude_tests=True)

        # Count .expect() usage
        expect_count = index.count_pattern(r"\.expect\(", exclude_tests=True)

        # Custom error types (enum with Error in name)
        error_enums = index.search_pattern(
            r"(?:pub\s+)?enum\s+\w*Error\w*",
            limit=30,
            exclude_tests=True,
        )
        if error_enums:
            patterns["custom_errors"] = {
                "name": "Custom error types",
                "count": len(error_enums),
            }

        # Result alias patterns
        result_aliases = index.search_pattern(
            r"type\s+Result<[^>]*>\s*=",
            limit=20,
            exclude_tests=True,
        )
        if result_aliases:
            patterns["result_alias"] = {
                "name": "Result type aliases",
                "count": len(result_aliases),
            }

        if not patterns and question_mark_count == 0:
            return result

        [p["name"] for p in patterns.values()]

        # Determine primary error handling approach
        if "thiserror" in patterns and "anyhow" in patterns:
            primary = "thiserror + anyhow"
            style = "library with application errors"
        elif "thiserror" in patterns:
            primary = "thiserror"
            style = "structured library errors"
        elif "anyhow" in patterns:
            primary = "anyhow"
            style = "convenient application errors"
        elif "eyre" in patterns:
            primary = "eyre"
            style = "rich error reporting"
        elif "custom_errors" in patterns:
            primary = "custom errors"
            style = "manual error types"
        else:
            primary = "standard Result"
            style = "basic error handling"

        title = f"Error handling: {primary}"
        description = f"Uses {primary} for {style}."

        if unwrap_count > 0:
            ratio = unwrap_count / max(1, question_mark_count)
            if ratio > 0.5:
                description += f" Note: {unwrap_count} .unwrap() calls."

        confidence = 0.9

        evidence = []
        for rel_path, line in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="rust.conventions.error_handling",
            category="patterns",
            title=title,
            description=description,
            confidence=confidence,
            language="rust",
            evidence=evidence,
            stats={
                "patterns": list(patterns.keys()),
                "primary": primary,
                "question_mark_count": question_mark_count,
                "unwrap_count": unwrap_count,
                "expect_count": expect_count,
                "pattern_details": patterns,
            },
        ))

        return result
