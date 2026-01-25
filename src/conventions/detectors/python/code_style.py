"""Python code style conventions detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


@DetectorRegistry.register
class PythonCodeStyleDetector(PythonDetector):
    """Detect Python code style conventions."""

    name = "python_code_style"
    description = "Detects string formatting, path handling, and import patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect code style conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        self._detect_string_formatting(ctx, index, result)
        self._detect_path_handling(ctx, index, result)
        self._detect_import_style(ctx, index, result)

        return result

    def _detect_string_formatting(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect string formatting conventions."""
        format_counts: Counter[str] = Counter()
        format_examples: dict[str, list[tuple[str, int]]] = {}

        for rel_path, fmt in index.get_all_string_formats():
            # Skip test files for convention detection
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            format_counts[fmt.format_type] += 1
            if fmt.format_type not in format_examples:
                format_examples[fmt.format_type] = []
            if len(format_examples[fmt.format_type]) < 5:
                format_examples[fmt.format_type].append((rel_path, fmt.line))

        total = sum(format_counts.values())
        if total < 5:
            return  # Not enough evidence

        # Determine dominant style
        fstring_count = format_counts.get("fstring", 0)
        format_method_count = format_counts.get("format_method", 0)
        percent_count = format_counts.get("percent", 0)

        fstring_ratio = fstring_count / total if total else 0
        format_ratio = format_method_count / total if total else 0
        percent_ratio = percent_count / total if total else 0

        if fstring_ratio >= 0.7:
            title = "Modern f-string formatting"
            description = (
                f"Uses f-strings consistently for string formatting. "
                f"{fstring_count}/{total} ({fstring_ratio:.0%}) use f-strings."
            )
            style = "fstring"
            confidence = min(0.95, 0.6 + fstring_ratio * 0.35)
        elif format_ratio >= 0.5:
            title = ".format() method formatting"
            description = (
                f"Uses .format() method for string formatting. "
                f"{format_method_count}/{total} ({format_ratio:.0%}) use .format()."
            )
            style = "format_method"
            confidence = min(0.85, 0.5 + format_ratio * 0.35)
        elif percent_ratio >= 0.3:
            title = "Legacy % string formatting"
            description = (
                f"Uses % operator for string formatting (legacy style). "
                f"{percent_count}/{total} ({percent_ratio:.0%}) use % formatting."
            )
            style = "percent"
            confidence = min(0.8, 0.5 + percent_ratio * 0.3)
        else:
            title = "Mixed string formatting styles"
            description = (
                f"Uses multiple string formatting styles: "
                f"f-strings ({fstring_count}), .format() ({format_method_count}), "
                f"% ({percent_count})."
            )
            style = "mixed"
            confidence = 0.7

        # Build evidence
        evidence = []
        primary_style = max(format_counts, key=lambda k: format_counts[k]) if format_counts else "fstring"
        for rel_path, line in format_examples.get(primary_style, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.string_formatting",
            category="code_style",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "total_formats": total,
                "fstring_count": fstring_count,
                "format_method_count": format_method_count,
                "percent_count": percent_count,
                "fstring_ratio": round(fstring_ratio, 3),
                "dominant_style": style,
            },
        ))

    def _detect_path_handling(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect path handling conventions (pathlib vs os.path)."""
        pathlib_count = 0
        ospath_count = 0
        pathlib_examples: list[tuple[str, int]] = []
        ospath_examples: list[tuple[str, int]] = []

        for rel_path, imp in index.get_all_imports():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            if imp.module == "pathlib" or "Path" in imp.names:
                pathlib_count += 1
                if len(pathlib_examples) < 5:
                    pathlib_examples.append((rel_path, imp.line))
            elif imp.module == "os.path" or (imp.module == "os" and "path" in imp.names):
                ospath_count += 1
                if len(ospath_examples) < 5:
                    ospath_examples.append((rel_path, imp.line))

        # Also check for os.path calls
        for rel_path, call in index.get_all_calls():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            if call.name.startswith("os.path."):
                ospath_count += 1
                if len(ospath_examples) < 5:
                    ospath_examples.append((rel_path, call.line))
            elif call.name.startswith("Path"):
                pathlib_count += 1
                if len(pathlib_examples) < 5:
                    pathlib_examples.append((rel_path, call.line))

        total = pathlib_count + ospath_count
        if total < 3:
            return  # Not enough evidence

        pathlib_ratio = pathlib_count / total if total else 0

        if pathlib_ratio >= 0.8:
            title = "Modern pathlib for path handling"
            description = (
                f"Uses pathlib consistently for file paths. "
                f"{pathlib_count}/{total} ({pathlib_ratio:.0%}) use pathlib."
            )
            style = "pathlib"
            confidence = min(0.95, 0.6 + pathlib_ratio * 0.35)
            examples = pathlib_examples
        elif pathlib_ratio <= 0.2:
            title = "Legacy os.path for path handling"
            description = (
                f"Uses os.path for file paths (consider migrating to pathlib). "
                f"{ospath_count}/{total} use os.path."
            )
            style = "os.path"
            confidence = min(0.85, 0.5 + (1 - pathlib_ratio) * 0.35)
            examples = ospath_examples
        else:
            title = "Mixed path handling (pathlib and os.path)"
            description = (
                f"Uses both pathlib ({pathlib_count}) and os.path ({ospath_count}). "
                f"Consider standardizing on pathlib."
            )
            style = "mixed"
            confidence = 0.7
            examples = pathlib_examples if pathlib_count >= ospath_count else ospath_examples

        # Build evidence
        evidence = []
        for rel_path, line in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.path_handling",
            category="code_style",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "pathlib_count": pathlib_count,
                "ospath_count": ospath_count,
                "pathlib_ratio": round(pathlib_ratio, 3),
                "style": style,
            },
        ))

    def _detect_import_style(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect import style conventions (absolute vs relative)."""
        absolute_count = 0
        relative_count = 0
        relative_examples: list[tuple[str, int]] = []
        absolute_examples: list[tuple[str, int]] = []

        for rel_path, imp in index.get_all_imports():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            # Skip stdlib and third-party imports - focus on internal imports
            # Heuristic: relative imports are always internal
            if imp.is_relative:
                relative_count += 1
                if len(relative_examples) < 5:
                    relative_examples.append((rel_path, imp.line))
            else:
                # For absolute imports, we count them but can't easily distinguish
                # internal from external without more context
                absolute_count += 1
                if len(absolute_examples) < 5:
                    absolute_examples.append((rel_path, imp.line))

        # Only report if there are relative imports (indicates internal structure)
        if relative_count < 3:
            return

        total = absolute_count + relative_count
        relative_ratio = relative_count / total if total else 0

        if relative_ratio >= 0.5:
            title = "Relative imports for internal modules"
            description = (
                f"Uses relative imports for internal module references. "
                f"{relative_count} relative imports found."
            )
            style = "relative"
            confidence = min(0.85, 0.5 + relative_ratio * 0.35)
        else:
            title = "Absolute imports preferred"
            description = (
                f"Prefers absolute imports. "
                f"{relative_count} relative vs {absolute_count} absolute imports."
            )
            style = "absolute"
            confidence = 0.7

        # Build evidence
        evidence = []
        examples = relative_examples if relative_count > 0 else absolute_examples
        for rel_path, line in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.import_style",
            category="code_style",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "relative_count": relative_count,
                "absolute_count": absolute_count,
                "relative_ratio": round(relative_ratio, 3),
                "style": style,
            },
        ))
