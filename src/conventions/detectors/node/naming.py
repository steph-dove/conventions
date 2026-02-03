"""Node.js file naming conventions detector."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import NodeDetector


@DetectorRegistry.register
class NodeNamingDetector(NodeDetector):
    """Detect Node.js file naming conventions."""

    name = "node_naming"
    description = "Detects file naming conventions (kebab-case, camelCase, etc.)"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect file naming conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        self._detect_file_naming_convention(ctx, index, result)

        return result

    def _detect_file_naming_convention(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect file naming convention (kebab-case, camelCase, PascalCase, snake_case)."""
        naming_patterns: Counter[str] = Counter()
        examples: dict[str, list[str]] = {
            "kebab-case": [],
            "camelCase": [],
            "PascalCase": [],
            "snake_case": [],
            "other": [],
        }

        # Patterns for each naming convention
        # kebab-case: lowercase words separated by hyphens (e.g., user-service.ts)
        kebab_pattern = re.compile(r'^[a-z][a-z0-9]*(?:-[a-z0-9]+)+$')
        # camelCase: starts lowercase, has uppercase letters (e.g., userService.ts)
        camel_pattern = re.compile(r'^[a-z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*$')
        # PascalCase: starts uppercase (e.g., UserService.ts)
        pascal_pattern = re.compile(r'^[A-Z][a-zA-Z0-9]+$')
        # snake_case: lowercase with underscores (e.g., user_service.ts)
        snake_pattern = re.compile(r'^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$')
        # Simple lowercase (e.g., users.ts)
        simple_pattern = re.compile(r'^[a-z][a-z0-9]*$')

        for rel_path in index.files:
            # Get just the filename without extension
            path = Path(rel_path)
            name = path.stem

            # Skip index files and config files
            if name in ("index", "config", "main", "app", "server"):
                continue

            # Skip files with dots in name (like user.test.ts, user.spec.ts)
            if "." in name:
                base_name = name.split(".")[0]
            else:
                base_name = name

            # Classify the naming convention
            if kebab_pattern.match(base_name):
                naming_patterns["kebab-case"] += 1
                if len(examples["kebab-case"]) < 5:
                    examples["kebab-case"].append(path.name)
            elif camel_pattern.match(base_name):
                naming_patterns["camelCase"] += 1
                if len(examples["camelCase"]) < 5:
                    examples["camelCase"].append(path.name)
            elif pascal_pattern.match(base_name):
                naming_patterns["PascalCase"] += 1
                if len(examples["PascalCase"]) < 5:
                    examples["PascalCase"].append(path.name)
            elif snake_pattern.match(base_name):
                naming_patterns["snake_case"] += 1
                if len(examples["snake_case"]) < 5:
                    examples["snake_case"].append(path.name)
            elif simple_pattern.match(base_name):
                # Simple names could be any convention, count separately
                naming_patterns["simple"] += 1
            else:
                naming_patterns["other"] += 1

        # Remove simple names from the decision - they're ambiguous
        countable = {k: v for k, v in naming_patterns.items() if k not in ("simple", "other")}

        if not countable:
            return

        total = sum(countable.values())
        if total < 5:
            return

        primary, primary_count = max(countable.items(), key=lambda x: x[1])
        primary_ratio = primary_count / total if total else 0

        if primary_ratio >= 0.7:
            title = f"File naming: {primary}"
            description = (
                f"Files follow {primary} naming convention. "
                f"Examples: {', '.join(examples.get(primary, [])[:3])}."
            )
            confidence = min(0.9, 0.6 + primary_ratio * 0.3)
        elif primary_ratio >= 0.4:
            secondary = sorted(
                [(k, v) for k, v in countable.items() if k != primary],
                key=lambda x: -x[1]
            )
            if secondary:
                second_name, second_count = secondary[0]
                title = f"Mixed naming: {primary} + {second_name}"
                description = (
                    f"Files use mixed naming conventions. "
                    f"{primary}: {primary_count}, {second_name}: {second_count}."
                )
                confidence = 0.75
            else:
                title = f"Primary naming: {primary}"
                description = f"Files primarily use {primary} naming. Count: {primary_count}."
                confidence = 0.7
        else:
            title = "Inconsistent file naming"
            breakdown = ", ".join(f"{k}: {v}" for k, v in sorted(countable.items(), key=lambda x: -x[1])[:3])
            description = f"No dominant file naming convention. {breakdown}."
            confidence = 0.65

        result.rules.append(self.make_rule(
            rule_id="node.conventions.file_naming",
            category="structure",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=[],
            stats={
                "naming_pattern_counts": dict(naming_patterns),
                "primary_pattern": primary,
                "primary_ratio": round(primary_ratio, 3),
                "examples": {k: v for k, v in examples.items() if v},
            },
        ))
