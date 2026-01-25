"""Python test organization patterns detector."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


@DetectorRegistry.register
class PythonTestOrganizationDetector(PythonDetector):
    """Detect Python test organization patterns."""

    name = "python_test_organization"
    description = "Detects test file structure, naming conventions, and organization"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect test organization patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        self._detect_test_structure(ctx, index, result)
        self._detect_test_naming(ctx, index, result)

        return result

    def _detect_test_structure(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect test directory structure."""
        # Use actual test files (test_*.py, *_test.py) for accurate counting
        test_files = index.get_test_files(include_support=False)

        if len(test_files) < 3:
            return  # Not enough test files

        # Analyze test file locations
        test_dirs: Counter[str] = Counter()
        has_unit = False
        has_integration = False
        has_e2e = False
        has_functional = False

        for test_file in test_files:
            rel_path = test_file.relative_path
            parts = Path(rel_path).parts

            # Track top-level test directory
            if parts:
                test_dirs[parts[0]] += 1

            # Check for subdirectory organization
            path_lower = rel_path.lower()
            if "/unit/" in path_lower or "\\unit\\" in path_lower:
                has_unit = True
            if "/integration/" in path_lower or "\\integration\\" in path_lower:
                has_integration = True
            if "/e2e/" in path_lower or "\\e2e\\" in path_lower or "/end_to_end/" in path_lower:
                has_e2e = True
            if "/functional/" in path_lower or "\\functional\\" in path_lower:
                has_functional = True

        # Determine structure pattern
        categories = []
        if has_unit:
            categories.append("unit")
        if has_integration:
            categories.append("integration")
        if has_e2e:
            categories.append("e2e")
        if has_functional:
            categories.append("functional")

        if len(categories) >= 2:
            title = "Layered test organization"
            description = (
                f"Tests organized by type: {', '.join(categories)}. "
                f"Total {len(test_files)} test files."
            )
            structure = "layered"
            confidence = 0.9
        elif len(test_dirs) == 1:
            top_dir = list(test_dirs.keys())[0]
            title = f"Single test directory: {top_dir}/"
            description = (
                f"All tests in '{top_dir}/' directory. "
                f"{len(test_files)} test files."
            )
            structure = "flat"
            confidence = 0.8
        else:
            title = "Distributed test files"
            description = (
                f"Test files spread across {len(test_dirs)} directories. "
                f"{len(test_files)} total test files."
            )
            structure = "distributed"
            confidence = 0.7

        result.rules.append(self.make_rule(
            rule_id="python.conventions.test_structure",
            category="testing",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=[],
            stats={
                "test_file_count": len(test_files),
                "test_directories": dict(test_dirs.most_common(5)),
                "has_unit": has_unit,
                "has_integration": has_integration,
                "has_e2e": has_e2e,
                "structure": structure,
                "categories": categories,
            },
        ))

    def _detect_test_naming(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect test naming conventions."""
        # Use actual test files (test_*.py, *_test.py) for accurate counting
        test_files = index.get_test_files(include_support=False)

        if len(test_files) < 3:
            return

        # Analyze test function names
        test_func_patterns: Counter[str] = Counter()
        test_func_examples: dict[str, list[tuple[str, int, str]]] = {}

        for test_file in test_files:
            for func in test_file.functions:
                if not func.name.startswith("test"):
                    continue

                pattern = self._classify_test_name(func.name)
                test_func_patterns[pattern] += 1

                if pattern not in test_func_examples:
                    test_func_examples[pattern] = []
                if len(test_func_examples[pattern]) < 3:
                    test_func_examples[pattern].append(
                        (test_file.relative_path, func.line, func.name)
                    )

        # Analyze test class usage
        test_classes = []
        for test_file in test_files:
            for cls in test_file.classes:
                if cls.name.startswith("Test"):
                    test_classes.append((test_file.relative_path, cls.line, cls.name))

        total_funcs = sum(test_func_patterns.values())
        if total_funcs < 5:
            return

        # Determine dominant naming pattern
        dominant_pattern, dominant_count = test_func_patterns.most_common(1)[0]
        dominant_ratio = dominant_count / total_funcs if total_funcs else 0

        pattern_descriptions = {
            "bdd_style": "BDD-style (test_should_*, test_when_*)",
            "action_result": "Action-result style (test_action_result)",
            "simple": "Simple style (test_feature)",
            "given_when_then": "Given-When-Then style",
        }

        if dominant_ratio >= 0.5:
            title = f"Test naming: {pattern_descriptions.get(dominant_pattern, dominant_pattern)}"
            description = (
                f"Uses {pattern_descriptions.get(dominant_pattern, dominant_pattern)} naming. "
                f"{dominant_count}/{total_funcs} ({dominant_ratio:.0%}) test functions."
            )
            confidence = min(0.85, 0.5 + dominant_ratio * 0.35)
        else:
            title = "Mixed test naming styles"
            patterns_used = [p for p, c in test_func_patterns.most_common(3) if c > 0]
            description = (
                "Uses multiple test naming styles: "
                + ", ".join(pattern_descriptions.get(p, p) for p in patterns_used)
                + "."
            )
            confidence = 0.7

        # Add class usage info
        if test_classes:
            description += f" Uses {len(test_classes)} test classes for grouping."

        # Build evidence
        evidence = []
        for rel_path, line, name in test_func_examples.get(dominant_pattern, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.test_naming",
            category="testing",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "total_test_functions": total_funcs,
                "pattern_counts": dict(test_func_patterns),
                "test_class_count": len(test_classes),
                "dominant_pattern": dominant_pattern,
            },
        ))

    def _classify_test_name(self, name: str) -> str:
        """Classify a test function name by its style."""
        # Remove 'test_' prefix
        name = name[5:] if name.startswith("test_") else name

        # BDD-style patterns
        if any(name.startswith(p) for p in ["should_", "when_", "given_", "it_"]):
            return "bdd_style"

        # Given-When-Then
        if "given" in name.lower() and ("when" in name.lower() or "then" in name.lower()):
            return "given_when_then"

        # Action-result pattern (contains both verb and expected outcome)
        parts = name.split("_")
        if len(parts) >= 2:
            # Check if it has common result words
            result_words = {"returns", "raises", "creates", "updates", "deletes", "fails", "succeeds", "error", "success"}
            if any(word in parts for word in result_words):
                return "action_result"

        return "simple"
