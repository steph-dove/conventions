"""Python documentation-specific conventions detector.

This detector focuses on conventions within documentation and example files, such as:
- Example code completeness (imports, runnable code)
- Documentation code style
- Tutorial structure patterns
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


@DetectorRegistry.register
class PythonDocsConventionsDetector(PythonDetector):
    """Detect Python documentation-specific conventions."""

    name = "python_docs_conventions"
    description = "Detects documentation-specific conventions like example style and completeness"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect documentation-specific conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Only analyze docs files
        docs_files = {
            path: file_idx
            for path, file_idx in index.files.items()
            if file_idx.role == "docs"
        }

        if len(docs_files) < 2:
            return result  # Not enough docs files

        self._detect_example_structure(ctx, index, docs_files, result)
        self._detect_example_completeness(ctx, index, docs_files, result)
        self._detect_docs_organization(ctx, index, docs_files, result)

        return result

    def _detect_example_structure(
        self,
        ctx: DetectorContext,
        index,
        docs_files: dict,
        result: DetectorResult,
    ) -> None:
        """Detect example file structure patterns."""
        # Analyze how examples are organized
        example_dirs: Counter[str] = Counter()
        has_readme = False
        has_main_pattern = 0
        has_standalone = 0
        examples_by_topic: Counter[str] = Counter()

        for rel_path, file_idx in docs_files.items():
            path = Path(rel_path)
            parts = path.parts

            # Track example directories
            if parts:
                example_dirs[parts[0]] += 1

            # Check for README in examples
            if "readme" in path.name.lower():
                has_readme = True

            # Check for main() pattern (standalone runnable examples)
            for func in file_idx.functions:
                if func.name == "main":
                    has_main_pattern += 1

            # Check if file has if __name__ == "__main__"
            content = "\n".join(file_idx.lines)
            if '__name__ == "__main__"' in content or "__name__ == '__main__'" in content:
                has_standalone += 1

            # Categorize by likely topic
            name_lower = path.stem.lower()
            for topic in ["auth", "database", "api", "crud", "async", "websocket", "graphql", "rest"]:
                if topic in name_lower:
                    examples_by_topic[topic] += 1
                    break

        total_files = len(docs_files)
        if total_files < 3:
            return

        standalone_ratio = has_standalone / total_files if total_files else 0

        if standalone_ratio >= 0.5:
            title = "Standalone runnable examples"
            description = (
                f"Documentation examples are standalone runnable scripts. "
                f"{has_standalone}/{total_files} ({standalone_ratio:.0%}) have if __name__ == '__main__'."
            )
            pattern = "standalone"
            confidence = min(0.9, 0.5 + standalone_ratio * 0.4)
        elif has_main_pattern >= 3:
            title = "Examples with main() entry point"
            description = (
                f"Examples use main() function as entry point. "
                f"Found {has_main_pattern} examples with main()."
            )
            pattern = "main_function"
            confidence = 0.8
        else:
            title = "Module-style examples"
            description = (
                f"Documentation contains {total_files} example files. "
                f"Examples are structured as importable modules."
            )
            pattern = "module"
            confidence = 0.7

        if has_readme:
            description += " Includes README for documentation."

        if examples_by_topic:
            topics = list(examples_by_topic.keys())[:3]
            description += f" Topics covered: {', '.join(topics)}."

        result.rules.append(self.make_rule(
            rule_id="python.docs_conventions.example_structure",
            category="documentation",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=[],
            stats={
                "total_example_files": total_files,
                "standalone_count": has_standalone,
                "main_function_count": has_main_pattern,
                "example_directories": dict(example_dirs.most_common(5)),
                "topics": dict(examples_by_topic),
                "pattern": pattern,
            },
        ))

    def _detect_example_completeness(
        self,
        ctx: DetectorContext,
        index,
        docs_files: dict,
        result: DetectorResult,
    ) -> None:
        """Detect if examples have complete imports and are self-contained."""
        complete_examples = 0
        incomplete_examples = 0
        complete_example_files: list[tuple[str, int]] = []
        incomplete_example_files: list[tuple[str, int]] = []

        for rel_path, file_idx in docs_files.items():
            # Check if file has imports
            has_imports = len(file_idx.imports) > 0

            # Check if file has function definitions or classes
            has_definitions = len(file_idx.functions) > 0 or len(file_idx.classes) > 0

            # Check for common missing imports (heuristics)
            content = "\n".join(file_idx.lines)
            missing_imports = []

            # Common patterns that suggest missing imports
            import_checks = [
                ("asyncio", "async def" in content or "await " in content),
                ("typing", "List[" in content or "Dict[" in content or "Optional[" in content),
                ("datetime", "datetime." in content or "timedelta" in content),
            ]

            for module, pattern_found in import_checks:
                if pattern_found:
                    has_import = any(module in str(imp.module) for imp in file_idx.imports)
                    if not has_import:
                        missing_imports.append(module)

            if has_imports and has_definitions and not missing_imports:
                complete_examples += 1
                if len(complete_example_files) < 5:
                    complete_example_files.append((rel_path, 1))
            elif has_definitions:  # Has code but may be incomplete
                incomplete_examples += 1
                if len(incomplete_example_files) < 5:
                    incomplete_example_files.append((rel_path, 1))

        total = complete_examples + incomplete_examples
        if total < 3:
            return

        complete_ratio = complete_examples / total if total else 0

        if complete_ratio >= 0.8:
            title = "Self-contained examples"
            description = (
                f"Documentation examples are self-contained with complete imports. "
                f"{complete_examples}/{total} ({complete_ratio:.0%}) examples are complete."
            )
            style = "complete"
            confidence = min(0.9, 0.5 + complete_ratio * 0.4)
        elif complete_ratio >= 0.5:
            title = "Mostly complete examples"
            description = (
                f"Most documentation examples have necessary imports. "
                f"{complete_examples}/{total} ({complete_ratio:.0%}) are complete."
            )
            style = "mostly_complete"
            confidence = 0.75
        else:
            title = "Snippet-style examples"
            description = (
                f"Documentation uses code snippets (may require context from docs). "
                f"Only {complete_examples}/{total} examples have all imports."
            )
            style = "snippets"
            confidence = 0.7

        result.rules.append(self.make_rule(
            rule_id="python.docs_conventions.example_completeness",
            category="documentation",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=[],
            stats={
                "complete_examples": complete_examples,
                "incomplete_examples": incomplete_examples,
                "complete_ratio": round(complete_ratio, 3),
                "style": style,
            },
        ))

    def _detect_docs_organization(
        self,
        ctx: DetectorContext,
        index,
        docs_files: dict,
        result: DetectorResult,
    ) -> None:
        """Detect documentation organization patterns."""
        # Analyze directory structure
        dir_structure: Counter[str] = Counter()
        file_prefixes: Counter[str] = Counter()

        for rel_path in docs_files:
            path = Path(rel_path)
            parts = path.parts

            # Track directory depth
            depth = len(parts) - 1  # Exclude filename
            dir_structure[f"depth_{depth}"] += 1

            # Track common prefixes/patterns
            name = path.stem.lower()
            for prefix in ["example", "tutorial", "guide", "demo", "sample", "quickstart"]:
                if name.startswith(prefix) or prefix in name:
                    file_prefixes[prefix] += 1
                    break

            # Check for numbered examples (01_intro, 02_basics, etc.)
            if name and name[0].isdigit():
                file_prefixes["numbered"] += 1

        total_files = len(docs_files)
        if total_files < 3:
            return

        # Determine organization style
        numbered_ratio = file_prefixes.get("numbered", 0) / total_files if total_files else 0
        tutorial_count = file_prefixes.get("tutorial", 0)

        if numbered_ratio >= 0.5:
            title = "Numbered/sequential examples"
            description = (
                f"Documentation examples are numbered for sequential learning. "
                f"{file_prefixes['numbered']}/{total_files} files are numbered."
            )
            style = "numbered"
            confidence = min(0.9, 0.5 + numbered_ratio * 0.4)
        elif tutorial_count >= 3:
            title = "Tutorial-style documentation"
            description = (
                f"Documentation organized as tutorials. "
                f"Found {tutorial_count} tutorial files."
            )
            style = "tutorials"
            confidence = 0.8
        elif dir_structure.get("depth_1", 0) > dir_structure.get("depth_0", 0):
            title = "Categorized documentation structure"
            description = (
                f"Documentation organized in subdirectories by category. "
                f"{total_files} example files across multiple directories."
            )
            style = "categorized"
            confidence = 0.75
        else:
            title = "Flat documentation structure"
            description = (
                f"Documentation examples in flat structure. "
                f"{total_files} example files."
            )
            style = "flat"
            confidence = 0.7

        if file_prefixes:
            common_types = [p for p, c in file_prefixes.most_common(3) if c > 1 and p != "numbered"]
            if common_types:
                description += f" Common types: {', '.join(common_types)}."

        result.rules.append(self.make_rule(
            rule_id="python.docs_conventions.organization",
            category="documentation",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=[],
            stats={
                "total_files": total_files,
                "file_prefixes": dict(file_prefixes),
                "dir_structure": dict(dir_structure),
                "style": style,
            },
        ))
