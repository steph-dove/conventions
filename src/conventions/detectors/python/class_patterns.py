"""Python class definition patterns detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


@DetectorRegistry.register
class PythonClassPatternsDetector(PythonDetector):
    """Detect Python class definition patterns."""

    name = "python_class_patterns"
    description = "Detects class definition styles (dataclass, Pydantic, attrs, plain)"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect class definition patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        self._detect_class_style(ctx, index, result)

        return result

    def _detect_class_style(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect the dominant class definition style."""
        style_counts: Counter[str] = Counter()
        style_examples: dict[str, list[tuple[str, int, str]]] = {}

        for rel_path, cls in index.get_all_classes():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            style = self._classify_class(cls)
            if style:
                style_counts[style] += 1
                if style not in style_examples:
                    style_examples[style] = []
                if len(style_examples[style]) < 5:
                    style_examples[style].append((rel_path, cls.line, cls.name))

        total = sum(style_counts.values())
        if total < 3:
            return  # Not enough evidence

        # Get counts for each style
        dataclass_count = style_counts.get("dataclass", 0)
        pydantic_count = style_counts.get("pydantic", 0)
        attrs_count = style_counts.get("attrs", 0)
        namedtuple_count = style_counts.get("namedtuple", 0)
        plain_count = style_counts.get("plain", 0)

        # Determine dominant style (excluding plain classes)
        structured_counts = {
            "dataclass": dataclass_count,
            "pydantic": pydantic_count,
            "attrs": attrs_count,
            "namedtuple": namedtuple_count,
        }
        structured_total = sum(structured_counts.values())

        if structured_total == 0:
            # Only plain classes
            title = "Plain class definitions"
            description = f"Uses plain Python classes ({plain_count} classes)."
            style = "plain"
            confidence = 0.7
        else:
            dominant_style = max(structured_counts, key=structured_counts.get)
            dominant_count = structured_counts[dominant_style]
            dominant_ratio = dominant_count / structured_total if structured_total else 0

            style_names = {
                "dataclass": "dataclasses",
                "pydantic": "Pydantic models",
                "attrs": "attrs classes",
                "namedtuple": "NamedTuple",
            }

            if dominant_ratio >= 0.7:
                title = f"Data classes: {style_names[dominant_style]}"
                description = (
                    f"Uses {style_names[dominant_style]} for structured data. "
                    f"{dominant_count}/{structured_total} structured classes use this pattern."
                )
                style = dominant_style
                confidence = min(0.9, 0.6 + dominant_ratio * 0.3)
            else:
                # Multiple styles in use
                used_styles = [s for s, c in structured_counts.items() if c > 0]
                title = f"Mixed data class styles"
                description = (
                    f"Uses multiple data class styles: "
                    + ", ".join(f"{style_names[s]} ({structured_counts[s]})" for s in used_styles)
                    + "."
                )
                style = "mixed"
                confidence = 0.7

        # Build evidence
        evidence = []
        primary_examples = style_examples.get(
            style if style != "mixed" else max(structured_counts, key=structured_counts.get),
            []
        )
        for rel_path, line, name in primary_examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.class_style",
            category="code_style",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "dataclass_count": dataclass_count,
                "pydantic_count": pydantic_count,
                "attrs_count": attrs_count,
                "namedtuple_count": namedtuple_count,
                "plain_count": plain_count,
                "dominant_style": style,
            },
        ))

    def _classify_class(self, cls) -> str | None:
        """Classify a class by its definition style."""
        # Check decorators
        for dec in cls.decorators:
            if "dataclass" in dec:
                return "dataclass"
            if "attrs" in dec or "attr.s" in dec or "define" in dec:
                return "attrs"

        # Check base classes
        for base in cls.bases:
            if "BaseModel" in base or "pydantic" in base.lower():
                return "pydantic"
            if "NamedTuple" in base or "TypedDict" in base:
                return "namedtuple"
            if "Enum" in base or "IntEnum" in base or "StrEnum" in base:
                return None  # Don't count enums as class patterns

        # Skip exception classes and abstract base classes
        for base in cls.bases:
            if "Exception" in base or "Error" in base or "ABC" in base:
                return None

        # If it has bases that aren't common patterns, it's a plain class
        if cls.bases:
            # Has inheritance but not a known pattern
            return "plain"

        # No decorators, no special bases - plain class
        return "plain"
