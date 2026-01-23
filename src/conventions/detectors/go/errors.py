"""Go error handling conventions detector."""

from __future__ import annotations

import re

from ..base import DetectorContext, DetectorResult
from .base import GoDetector
from .index import GoIndex, make_evidence
from ..registry import DetectorRegistry


@DetectorRegistry.register
class GoErrorHandlingDetector(GoDetector):
    """Detect Go error handling conventions."""

    name = "go_errors"
    description = "Detects Go error handling patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Go error handling conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect custom error types
        self._detect_custom_error_types(ctx, index, result)

        # Detect sentinel errors
        self._detect_sentinel_errors(ctx, index, result)

        # Detect error wrapping patterns
        self._detect_error_wrapping(ctx, index, result)

        return result

    def _detect_custom_error_types(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect custom error types implementing error interface."""
        # Look for: func (e *SomeError) Error() string
        pattern = r"func\s+\([^)]+\)\s+Error\(\)\s+string"
        matches = index.search_pattern(pattern, limit=50, exclude_tests=True)

        if len(matches) < 2:
            return

        title = "Custom error types"
        description = (
            f"Defines custom error types implementing error interface. "
            f"Found {len(matches)} custom error types."
        )
        confidence = min(0.9, 0.6 + len(matches) * 0.05)

        evidence = []
        for rel_path, line, _ in matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.error_types",
            category="error_handling",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "custom_error_count": len(matches),
            },
        ))

    def _detect_sentinel_errors(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect sentinel error pattern (var ErrX = errors.New)."""
        # var ErrSomething = errors.New("...")
        # var ErrSomething = fmt.Errorf("...")
        pattern = r"var\s+Err\w+\s*=\s*(?:errors\.New|fmt\.Errorf)\("
        matches = index.search_pattern(pattern, limit=50, exclude_tests=True)

        if len(matches) < 2:
            return

        title = "Sentinel errors"
        description = (
            f"Uses sentinel error pattern (var ErrX = errors.New). "
            f"Found {len(matches)} sentinel errors."
        )
        confidence = min(0.95, 0.7 + len(matches) * 0.03)

        evidence = []
        for rel_path, line, _ in matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=2)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.sentinel_errors",
            category="error_handling",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "sentinel_count": len(matches),
            },
        ))

    def _detect_error_wrapping(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect error wrapping patterns (errors.Is, errors.As, fmt.Errorf %w)."""
        # errors.Is and errors.As (Go 1.13+)
        is_as_pattern = r"errors\.(?:Is|As)\("
        is_as_count = index.count_pattern(is_as_pattern, exclude_tests=True)

        # fmt.Errorf with %w
        wrap_pattern = r'fmt\.Errorf\([^)]*%w'
        wrap_count = index.count_pattern(wrap_pattern, exclude_tests=True)

        total = is_as_count + wrap_count
        if total < 3:
            return

        matches = index.search_pattern(is_as_pattern, limit=10)
        matches.extend(index.search_pattern(wrap_pattern, limit=10))

        title = "Error wrapping (Go 1.13+)"
        description = (
            f"Uses Go 1.13+ error wrapping. "
            f"errors.Is/As: {is_as_count}, fmt.Errorf %%w: {wrap_count}."
        )
        confidence = min(0.95, 0.7 + total * 0.02)

        evidence = []
        for rel_path, line, _ in matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.error_wrapping",
            category="error_handling",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "is_as_count": is_as_count,
                "wrap_count": wrap_count,
            },
        ))
