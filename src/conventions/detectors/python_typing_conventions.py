"""Python typing conventions detector."""

from __future__ import annotations

from .base import DetectorResult, PythonDetector
from .python_index import make_evidence
from .registry import DetectorRegistry


@DetectorRegistry.register
class PythonTypingConventionsDetector(PythonDetector):
    """Detect Python typing conventions and coverage."""

    name = "python_typing_conventions"
    description = "Detects typing annotation patterns and coverage"

    def detect(self, ctx) -> DetectorResult:
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Count functions and their annotations
        total_functions = 0
        annotated_functions = 0
        fully_annotated_functions = 0
        typed_examples = []
        untyped_examples = []

        for rel_path, func in index.get_all_functions():
            # Skip test files for typing coverage
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role == "test":
                continue

            # Skip private/dunder methods for the aggregate count
            if func.name.startswith("_") and not func.name.startswith("__"):
                continue

            total_functions += 1

            if func.has_any_annotation:
                annotated_functions += 1

                # Check if fully annotated
                all_args_annotated = func.annotated_args == func.total_args
                if all_args_annotated and func.has_return_annotation:
                    fully_annotated_functions += 1

                # Collect typed example
                if len(typed_examples) < 3:
                    typed_examples.append((rel_path, func.line, func.name))
            else:
                # Collect untyped example
                if len(untyped_examples) < 3:
                    untyped_examples.append((rel_path, func.line, func.name))

        if total_functions == 0:
            return result

        # Calculate coverage
        any_annotation_coverage = annotated_functions / total_functions
        full_annotation_coverage = fully_annotated_functions / total_functions

        # Determine title and description based on coverage
        if any_annotation_coverage >= 0.80:
            title = "High type annotation coverage"
            description = (
                f"Type annotations are commonly used in this codebase. "
                f"{annotated_functions}/{total_functions} functions ({any_annotation_coverage:.0%}) "
                f"have at least one type annotation."
            )
        elif any_annotation_coverage >= 0.40:
            title = "Mixed type annotation coverage"
            description = (
                f"Type annotations are partially adopted. "
                f"{annotated_functions}/{total_functions} functions ({any_annotation_coverage:.0%}) "
                f"have at least one type annotation."
            )
        else:
            title = "Low type annotation coverage"
            description = (
                f"Type annotations are not widely used. "
                f"Only {annotated_functions}/{total_functions} functions ({any_annotation_coverage:.0%}) "
                f"have type annotations."
            )

        # Calculate confidence based on sample size
        confidence = min(0.95, 0.5 + (total_functions / 200) * 0.45)
        confidence = max(0.3, confidence)

        # Build evidence
        evidence = []
        for rel_path, line, name in typed_examples[:2]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        for rel_path, line, name in untyped_examples[:2]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.typing_coverage",
            category="typing",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence[:ctx.max_evidence_snippets],
            stats={
                "total_functions": total_functions,
                "annotated_functions": annotated_functions,
                "fully_annotated_functions": fully_annotated_functions,
                "any_annotation_coverage": round(any_annotation_coverage, 3),
                "full_annotation_coverage": round(full_annotation_coverage, 3),
            },
        ))

        return result
