"""Python docstring and naming conventions detector."""

from __future__ import annotations

import re
from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


@DetectorRegistry.register
class PythonDocstringNamingConventionsDetector(PythonDetector):
    """Detect Python docstring and naming conventions."""

    name = "python_docstring_naming_conventions"
    description = "Detects docstring style and naming patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect docstring style and naming patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect docstring prevalence and style
        self._detect_docstrings(ctx, index, result)

        # Detect docstring style
        self._detect_docstring_style(ctx, index, result)

        # Detect naming conventions
        self._detect_naming(ctx, index, result)

        return result

    def _detect_docstrings(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect docstring prevalence."""
        total_public_functions = 0
        documented_functions = 0
        documented_examples: list[tuple[str, int, str]] = []
        undocumented_examples: list[tuple[str, int, str]] = []

        total_classes = 0
        documented_classes = 0

        for rel_path, file_idx in index.files.items():
            if file_idx.role in ("test", "docs"):
                continue

            for func in file_idx.functions:
                # Skip private functions
                if func.name.startswith("_") and not func.name.startswith("__"):
                    continue

                total_public_functions += 1

                if func.has_docstring:
                    documented_functions += 1
                    if len(documented_examples) < 5:
                        documented_examples.append((rel_path, func.line, func.name))
                else:
                    if len(undocumented_examples) < 5:
                        undocumented_examples.append((rel_path, func.line, func.name))

            for cls in file_idx.classes:
                if cls.name.startswith("_"):
                    continue

                total_classes += 1
                if cls.has_docstring:
                    documented_classes += 1

        if total_public_functions < 5:
            return

        func_doc_ratio = documented_functions / total_public_functions if total_public_functions else 0
        class_doc_ratio = documented_classes / total_classes if total_classes else 0

        if func_doc_ratio >= 0.7:
            title = "High docstring coverage"
            description = (
                f"Most public functions have docstrings. "
                f"Functions: {documented_functions}/{total_public_functions} ({func_doc_ratio:.0%}). "
                f"Classes: {documented_classes}/{total_classes}."
            )
            confidence = min(0.9, 0.6 + func_doc_ratio * 0.3)
        elif func_doc_ratio >= 0.3:
            title = "Partial docstring coverage"
            description = (
                f"Some functions have docstrings. "
                f"Functions: {documented_functions}/{total_public_functions} ({func_doc_ratio:.0%})."
            )
            confidence = 0.7
        else:
            title = "Low docstring coverage"
            description = (
                f"Few functions have docstrings. "
                f"Only {documented_functions}/{total_public_functions} ({func_doc_ratio:.0%})."
            )
            confidence = 0.6

        # Build evidence
        evidence = []
        for rel_path, line, name in documented_examples[:2]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)
        for rel_path, line, name in undocumented_examples[:2]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.docstrings",
            category="documentation",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence[:ctx.max_evidence_snippets],
            stats={
                "total_public_functions": total_public_functions,
                "documented_functions": documented_functions,
                "function_doc_ratio": round(func_doc_ratio, 3),
                "total_classes": total_classes,
                "documented_classes": documented_classes,
                "class_doc_ratio": round(class_doc_ratio, 3),
            },
        ))

    def _detect_docstring_style(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect docstring style (Google, NumPy, Sphinx)."""
        styles: Counter[str] = Counter()
        style_examples: dict[str, list[tuple[str, int]]] = {}

        # Patterns for different docstring styles
        google_pattern = re.compile(r"\n\s+(Args|Returns|Raises|Yields|Examples):\s*\n", re.IGNORECASE)
        numpy_pattern = re.compile(r"\n\s+(Parameters|Returns|Raises)\s*\n\s*-+", re.IGNORECASE)
        sphinx_pattern = re.compile(r":param\s+\w+:|:returns:|:rtype:|:raises:", re.IGNORECASE)

        for rel_path, file_idx in index.files.items():
            if file_idx.role in ("test", "docs"):
                continue

            for func in file_idx.functions:
                if not func.docstring:
                    continue

                docstring = func.docstring

                if google_pattern.search(docstring):
                    styles["google"] += 1
                    if "google" not in style_examples:
                        style_examples["google"] = []
                    style_examples["google"].append((rel_path, func.line))

                elif numpy_pattern.search(docstring):
                    styles["numpy"] += 1
                    if "numpy" not in style_examples:
                        style_examples["numpy"] = []
                    style_examples["numpy"].append((rel_path, func.line))

                elif sphinx_pattern.search(docstring):
                    styles["sphinx"] += 1
                    if "sphinx" not in style_examples:
                        style_examples["sphinx"] = []
                    style_examples["sphinx"].append((rel_path, func.line))

        if not styles:
            return

        primary, primary_count = styles.most_common(1)[0]
        total = sum(styles.values())
        primary_ratio = primary_count / total if total else 0

        style_names = {
            "google": "Google style",
            "numpy": "NumPy style",
            "sphinx": "Sphinx/reST style",
        }

        if primary_ratio >= 0.8:
            title = f"{style_names.get(primary, primary)} docstrings"
            description = (
                f"Docstrings follow {style_names.get(primary, primary)}. "
                f"{primary_count}/{total} docstrings use this style."
            )
            confidence = min(0.9, 0.6 + primary_ratio * 0.3)
        else:
            style_list = [style_names.get(s, s) for s in styles.keys()]
            title = "Mixed docstring styles"
            description = f"Docstrings use mixed styles: {', '.join(style_list)}."
            confidence = 0.6

        # Build evidence
        evidence = []
        for rel_path, line in style_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=8)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.docstring_style",
            category="documentation",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "style_counts": dict(styles),
                "primary_style": primary,
                "primary_ratio": round(primary_ratio, 3),
            },
        ))

    def _detect_naming(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect naming convention patterns."""
        # Look for constants (UPPER_CASE) at module level
        constant_count = 0

        # Check for snake_case vs camelCase in function names
        snake_case_funcs = 0
        camel_case_funcs = 0

        re.compile(r"^[a-z][a-z0-9_]*$")
        camel_case_pattern = re.compile(r"^[a-z][a-zA-Z0-9]*$")  # camelCase
        has_underscore = re.compile(r"_")

        for rel_path, file_idx in index.files.items():
            if file_idx.role in ("test", "docs"):
                continue

            # Look for module-level constants (heuristic: UPPER_CASE names)
            # This is approximate since we don't track assignments
            content = "\n".join(file_idx.lines)

            # Simple heuristic: look for lines like "SOME_CONST = ..."
            const_matches = re.findall(r"^([A-Z][A-Z0-9_]+)\s*=", content, re.MULTILINE)
            constant_count += len(const_matches)

            for func in file_idx.functions:
                name = func.name
                if name.startswith("_"):
                    continue

                if has_underscore.search(name):
                    snake_case_funcs += 1
                elif camel_case_pattern.match(name) and name != name.lower():
                    camel_case_funcs += 1
                else:
                    snake_case_funcs += 1  # Single word is considered snake_case

        total_funcs = snake_case_funcs + camel_case_funcs
        if total_funcs < 5:
            return

        snake_ratio = snake_case_funcs / total_funcs if total_funcs else 0

        if snake_ratio >= 0.95:
            title = "PEP 8 snake_case naming"
            description = (
                f"Function names follow PEP 8 snake_case convention. "
                f"{snake_case_funcs}/{total_funcs} functions use snake_case."
            )
            confidence = min(0.95, 0.7 + snake_ratio * 0.25)
        elif snake_ratio >= 0.7:
            title = "Mostly snake_case naming"
            description = (
                f"Most function names use snake_case. "
                f"snake_case: {snake_case_funcs}, camelCase: {camel_case_funcs}."
            )
            confidence = 0.8
        else:
            title = "Mixed naming conventions"
            description = (
                f"Function names use mixed conventions. "
                f"snake_case: {snake_case_funcs}, camelCase: {camel_case_funcs}."
            )
            confidence = 0.6

        if constant_count > 0:
            description += f" Found {constant_count} module-level constants."

        result.rules.append(self.make_rule(
            rule_id="python.conventions.naming",
            category="style",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=[],  # Naming is aggregate, hard to show single example
            stats={
                "snake_case_functions": snake_case_funcs,
                "camel_case_functions": camel_case_funcs,
                "snake_case_ratio": round(snake_ratio, 3),
                "module_constants": constant_count,
            },
        ))
