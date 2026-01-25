"""Python constants and enums patterns detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


@DetectorRegistry.register
class PythonConstantsEnumsDetector(PythonDetector):
    """Detect Python constants and enum patterns."""

    name = "python_constants_enums"
    description = "Detects constant definitions, enums, and magic value handling"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect constants and enum patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        self._detect_constant_style(ctx, index, result)
        self._detect_enum_usage(ctx, index, result)

        return result

    def _detect_constant_style(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect constant definition style (ALL_CAPS vs other)."""
        all_caps_count = 0
        lowercase_count = 0
        all_caps_examples: list[tuple[str, int, str]] = []
        lowercase_examples: list[tuple[str, int, str]] = []

        for rel_path, const in index.get_all_constants():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            # Skip dunder names and private names
            if const.name.startswith("_"):
                continue

            # Skip common non-constant patterns
            if const.name in ("app", "router", "logger", "log", "db", "engine", "session"):
                continue

            # Skip TypeVar definitions (single uppercase letters or names ending in _T)
            # TypeVars are typically T, K, V, F, or names like ItemT, KeyT
            if len(const.name) == 1 and const.name.isupper():
                continue
            if const.name.endswith("_T") or const.name.endswith("T") and len(const.name) <= 3:
                continue

            # Only count string/int/float constants (likely intentional constants)
            if const.value_type not in ("str", "int", "float"):
                continue

            if const.is_all_caps:
                all_caps_count += 1
                if len(all_caps_examples) < 5:
                    all_caps_examples.append((rel_path, const.line, const.name))
            else:
                # Check if it looks like a constant (simple value assignment)
                lowercase_count += 1
                if len(lowercase_examples) < 5:
                    lowercase_examples.append((rel_path, const.line, const.name))

        total = all_caps_count + lowercase_count
        if total < 5:
            return  # Not enough evidence

        all_caps_ratio = all_caps_count / total if total else 0

        if all_caps_ratio >= 0.7:
            title = "ALL_CAPS constant naming"
            description = (
                f"Uses ALL_CAPS naming for constants consistently. "
                f"{all_caps_count}/{total} ({all_caps_ratio:.0%}) follow this pattern."
            )
            style = "all_caps"
            confidence = min(0.9, 0.6 + all_caps_ratio * 0.3)
            examples = all_caps_examples
        elif all_caps_ratio <= 0.3:
            title = "lowercase constant naming"
            description = (
                f"Uses lowercase naming for module-level values. "
                f"{lowercase_count}/{total} use lowercase."
            )
            style = "lowercase"
            confidence = 0.7
            examples = lowercase_examples
        else:
            title = "Mixed constant naming styles"
            description = (
                f"Uses mixed naming for constants: "
                f"{all_caps_count} ALL_CAPS, {lowercase_count} lowercase."
            )
            style = "mixed"
            confidence = 0.6
            examples = all_caps_examples if all_caps_count >= lowercase_count else lowercase_examples

        # Build evidence
        evidence = []
        for rel_path, line, name in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=2)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.constant_naming",
            category="naming",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "all_caps_count": all_caps_count,
                "lowercase_count": lowercase_count,
                "all_caps_ratio": round(all_caps_ratio, 3),
                "style": style,
            },
        ))

    def _detect_enum_usage(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect enum usage patterns."""
        enum_classes: list[tuple[str, int, str, str]] = []  # (path, line, name, type)
        string_constant_groups: Counter[str] = Counter()

        for rel_path, cls in index.get_all_classes():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            # Check for enum base classes
            for base in cls.bases:
                if "Enum" in base:
                    enum_type = "Enum"
                    if "Int" in base:
                        enum_type = "IntEnum"
                    elif "Str" in base:
                        enum_type = "StrEnum"
                    elif "Flag" in base:
                        enum_type = "Flag"
                    enum_classes.append((rel_path, cls.line, cls.name, enum_type))
                    break

        # Count string constants that could be enums (prefixed similarly)
        for rel_path, const in index.get_all_constants():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            if const.value_type == "str" and const.is_all_caps and "_" in const.name:
                # Extract prefix (e.g., STATUS_ACTIVE -> STATUS)
                prefix = const.name.rsplit("_", 1)[0]
                if len(prefix) >= 3:
                    string_constant_groups[prefix] += 1

        if not enum_classes and not string_constant_groups:
            return

        # Detect enum-like constant groups
        potential_enums = [
            (prefix, count) for prefix, count in string_constant_groups.items()
            if count >= 3
        ]

        if enum_classes:
            enum_types: Counter[str] = Counter(e[3] for e in enum_classes)
            most_common_type = enum_types.most_common(1)[0][0] if enum_types else "Enum"

            title = f"Enum usage: {most_common_type}"
            description = (
                f"Uses Python enums for categorical values. "
                f"Found {len(enum_classes)} enum class(es)."
            )
            if len(enum_types) > 1:
                type_summary = ", ".join(f"{t} ({c})" for t, c in enum_types.most_common())
                description += f" Types: {type_summary}."

            # Build evidence
            evidence = []
            for rel_path, line, name, _ in enum_classes[:ctx.max_evidence_snippets]:
                ev = make_evidence(index, rel_path, line, radius=5)
                if ev:
                    evidence.append(ev)

            result.rules.append(self.make_rule(
                rule_id="python.conventions.enum_usage",
                category="code_style",
                title=title,
                description=description,
                confidence=min(0.9, 0.6 + len(enum_classes) * 0.05),
                language="python",
                evidence=evidence,
                stats={
                    "enum_count": len(enum_classes),
                    "enum_types": dict(enum_types),
                    "enum_names": [e[2] for e in enum_classes[:10]],
                },
            ))

        if potential_enums and not enum_classes:
            # Has constant groups but no enums - suggest using enums
            top_group, top_count = potential_enums[0]

            title = "String constants instead of enums"
            description = (
                f"Uses string constants for categorical values (e.g., {top_group}_* with {top_count} values). "
                f"Consider using Python Enum or StrEnum for type safety."
            )

            result.rules.append(self.make_rule(
                rule_id="python.conventions.string_constants",
                category="code_style",
                title=title,
                description=description,
                confidence=0.7,
                language="python",
                evidence=[],
                stats={
                    "potential_enum_groups": [p[0] for p in potential_enums[:5]],
                    "largest_group_count": top_count,
                },
            ))
