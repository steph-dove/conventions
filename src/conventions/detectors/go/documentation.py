"""Go documentation conventions detector."""

from __future__ import annotations

import re
from collections import Counter

from ..base import DetectorContext, DetectorResult
from .base import GoDetector
from .index import GoIndex, make_evidence
from ..registry import DetectorRegistry


@DetectorRegistry.register
class GoDocumentationDetector(GoDetector):
    """Detect Go documentation conventions."""

    name = "go_documentation"
    description = "Detects Go doc comment patterns and coverage"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Go documentation conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect doc comment coverage
        self._detect_doc_comments(ctx, index, result)

        # Detect example functions
        self._detect_examples(ctx, index, result)

        return result

    def _detect_doc_comments(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect doc comment coverage for exported functions."""
        documented = 0
        undocumented = 0
        examples: list[tuple[str, int]] = []

        for file_idx in index.get_non_test_files():
            content = "\n".join(file_idx.lines)
            lines = file_idx.lines

            for func_name, line_num in file_idx.functions:
                # Skip unexported functions (lowercase)
                if not func_name[0].isupper():
                    continue

                # Check if preceded by a doc comment
                # Look at lines before the function declaration
                if line_num > 1:
                    prev_lines = []
                    for i in range(line_num - 2, max(0, line_num - 5) - 1, -1):
                        line = lines[i].strip()
                        if line.startswith("//"):
                            prev_lines.insert(0, line)
                        elif line == "":
                            continue
                        else:
                            break

                    has_doc = any(
                        l.startswith(f"// {func_name}")
                        for l in prev_lines
                    )

                    if has_doc:
                        documented += 1
                        if len(examples) < 20:
                            examples.append((file_idx.relative_path, line_num))
                    else:
                        undocumented += 1
                else:
                    undocumented += 1

        total = documented + undocumented
        if total < 5:
            return

        doc_ratio = documented / total if total else 0

        if doc_ratio >= 0.8:
            title = "Well-documented exports"
            description = (
                f"Exported functions have Go-style doc comments. "
                f"{documented}/{total} ({doc_ratio:.0%}) documented."
            )
            confidence = min(0.95, 0.7 + doc_ratio * 0.2)
        elif doc_ratio >= 0.4:
            title = "Partial documentation"
            description = (
                f"Some exported functions have doc comments. "
                f"{documented}/{total} ({doc_ratio:.0%}) documented."
            )
            confidence = 0.75
        else:
            title = "Limited documentation"
            description = (
                f"Few exported functions have doc comments. "
                f"Only {documented}/{total} ({doc_ratio:.0%}) documented."
            )
            confidence = 0.7

        evidence = []
        for rel_path, line in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.doc_comments",
            category="documentation",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "documented_exports": documented,
                "undocumented_exports": undocumented,
                "doc_ratio": round(doc_ratio, 3),
            },
        ))

    def _detect_examples(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect Example functions in test files."""
        example_count = 0
        examples: list[tuple[str, int]] = []

        for file_idx in index.get_test_files():
            for func_name, line in file_idx.functions:
                if func_name.startswith("Example"):
                    example_count += 1
                    if len(examples) < 20:
                        examples.append((file_idx.relative_path, line))

        if example_count < 2:
            return

        title = "Uses Example tests"
        description = (
            f"Uses Go's Example function convention for documentation. "
            f"Found {example_count} Example functions."
        )
        confidence = min(0.9, 0.6 + example_count * 0.03)

        evidence = []
        for rel_path, line in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.example_tests",
            category="documentation",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "example_count": example_count,
            },
        ))
