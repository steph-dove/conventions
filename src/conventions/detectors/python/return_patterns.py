"""Python return value and null handling patterns detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


@DetectorRegistry.register
class PythonReturnPatternsDetector(PythonDetector):
    """Detect Python return value and null handling patterns."""

    name = "python_return_patterns"
    description = "Detects return value patterns, Optional usage, and null handling"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect return and null handling patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        self._detect_optional_usage(ctx, index, result)
        self._detect_return_none_pattern(ctx, index, result)
        self._detect_result_type_pattern(ctx, index, result)

        return result

    def _detect_optional_usage(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect Optional type usage patterns."""
        optional_count = 0
        union_none_count = 0
        pipe_none_count = 0
        optional_examples: list[tuple[str, int]] = []

        # Check imports for Optional usage
        for rel_path, imp in index.get_all_imports():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            if imp.module == "typing" and "Optional" in imp.names:
                optional_count += 1
                if len(optional_examples) < 5:
                    optional_examples.append((rel_path, imp.line))

        # Check function return annotations for patterns
        functions_with_optional_return = 0
        functions_with_union_none = 0

        for rel_path, func in index.get_all_functions():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            # We can't easily inspect the actual annotation from FunctionInfo
            # But we can track functions that have return annotations
            if func.has_return_annotation:
                # This is a proxy - we'd need AST access for full analysis
                pass

        total = optional_count + union_none_count + pipe_none_count
        if total < 2:
            return

        title = "Optional type annotations"
        description = f"Uses Optional type hint for nullable values. Found {optional_count} imports of Optional."

        # Build evidence
        evidence = []
        for rel_path, line in optional_examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.optional_usage",
            category="typing",
            title=title,
            description=description,
            confidence=min(0.8, 0.5 + optional_count * 0.05),
            language="python",
            evidence=evidence,
            stats={
                "optional_imports": optional_count,
            },
        ))

    def _detect_return_none_pattern(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect patterns of returning None vs raising exceptions."""
        none_returns = 0
        total_returns = 0
        none_return_examples: list[tuple[str, int]] = []

        for rel_path, ret in index.get_all_returns():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            total_returns += 1
            if ret.returns_none:
                none_returns += 1
                if len(none_return_examples) < 5:
                    none_return_examples.append((rel_path, ret.line))

        if total_returns < 10:
            return  # Not enough evidence

        none_ratio = none_returns / total_returns if total_returns else 0

        if none_ratio >= 0.3:
            title = "Frequent None returns"
            description = (
                f"Functions frequently return None. "
                f"{none_returns}/{total_returns} ({none_ratio:.0%}) return statements are None/bare returns."
            )
            confidence = min(0.8, 0.5 + none_ratio * 0.3)

            # Build evidence
            evidence = []
            for rel_path, line in none_return_examples[:ctx.max_evidence_snippets]:
                ev = make_evidence(index, rel_path, line, radius=3)
                if ev:
                    evidence.append(ev)

            result.rules.append(self.make_rule(
                rule_id="python.conventions.none_returns",
                category="error_handling",
                title=title,
                description=description,
                confidence=confidence,
                language="python",
                evidence=evidence,
                stats={
                    "none_returns": none_returns,
                    "total_returns": total_returns,
                    "none_ratio": round(none_ratio, 3),
                },
            ))

    def _detect_result_type_pattern(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect Result/Either type pattern usage."""
        result_imports = 0
        result_examples: list[tuple[str, int]] = []

        # Check for Result/Either type imports
        result_libraries = {
            "returns": ["Result", "Success", "Failure", "Maybe", "Some", "Nothing"],
            "result": ["Ok", "Err", "Result"],
            "option": ["Some", "Nothing", "Option"],
            "either": ["Left", "Right", "Either"],
        }

        for rel_path, imp in index.get_all_imports():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            for lib, types in result_libraries.items():
                if lib in imp.module.lower():
                    if any(t in imp.names for t in types):
                        result_imports += 1
                        if len(result_examples) < 5:
                            result_examples.append((rel_path, imp.line))
                        break

        if result_imports < 2:
            return

        title = "Result/Either type pattern"
        description = (
            f"Uses Result/Either types for error handling. "
            f"Found {result_imports} imports of Result-type libraries."
        )

        # Build evidence
        evidence = []
        for rel_path, line in result_examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.result_types",
            category="error_handling",
            title=title,
            description=description,
            confidence=min(0.9, 0.6 + result_imports * 0.1),
            language="python",
            evidence=evidence,
            stats={
                "result_imports": result_imports,
            },
        ))
