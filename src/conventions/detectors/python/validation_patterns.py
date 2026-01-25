"""Python validation patterns detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


@DetectorRegistry.register
class PythonValidationPatternsDetector(PythonDetector):
    """Detect Python validation patterns."""

    name = "python_validation_patterns"
    description = "Detects validation approaches (Pydantic, manual, decorator-based)"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect validation patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        self._detect_validation_style(ctx, index, result)

        return result

    def _detect_validation_style(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect the dominant validation style."""
        validation_counts: Counter[str] = Counter()
        validation_examples: dict[str, list[tuple[str, int]]] = {}

        # Check for Pydantic validation
        for rel_path, imp in index.get_all_imports():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            # Pydantic
            if "pydantic" in imp.module.lower():
                if any(v in imp.names for v in ["BaseModel", "validator", "field_validator", "model_validator"]):
                    validation_counts["pydantic"] += 1
                    if "pydantic" not in validation_examples:
                        validation_examples["pydantic"] = []
                    if len(validation_examples["pydantic"]) < 5:
                        validation_examples["pydantic"].append((rel_path, imp.line))

            # Marshmallow
            if "marshmallow" in imp.module.lower():
                validation_counts["marshmallow"] += 1
                if "marshmallow" not in validation_examples:
                    validation_examples["marshmallow"] = []
                if len(validation_examples["marshmallow"]) < 5:
                    validation_examples["marshmallow"].append((rel_path, imp.line))

            # Cerberus
            if "cerberus" in imp.module.lower():
                validation_counts["cerberus"] += 1
                if "cerberus" not in validation_examples:
                    validation_examples["cerberus"] = []
                if len(validation_examples["cerberus"]) < 5:
                    validation_examples["cerberus"].append((rel_path, imp.line))

            # Voluptuous
            if "voluptuous" in imp.module.lower():
                validation_counts["voluptuous"] += 1

            # attrs with validators
            if imp.module == "attrs" or imp.module == "attr":
                if "validator" in imp.names or "validators" in imp.names:
                    validation_counts["attrs"] += 1

        # Check for validation decorators
        for rel_path, dec in index.get_all_decorators():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            dec_lower = dec.name.lower()
            if "validator" in dec_lower or "validate" in dec_lower:
                if "pydantic" not in dec_lower:  # Avoid double-counting pydantic
                    validation_counts["decorator"] += 1
                    if "decorator" not in validation_examples:
                        validation_examples["decorator"] = []
                    if len(validation_examples["decorator"]) < 5:
                        validation_examples["decorator"].append((rel_path, dec.line))

        # Check for manual validation (assert, raise ValueError)
        for rel_path, call in index.get_all_calls():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            if call.name in ("ValueError", "TypeError", "ValidationError"):
                validation_counts["manual"] += 1
                if "manual" not in validation_examples:
                    validation_examples["manual"] = []
                if len(validation_examples["manual"]) < 5:
                    validation_examples["manual"].append((rel_path, call.line))

        if not validation_counts:
            return

        total = sum(validation_counts.values())
        if total < 3:
            return

        # Determine dominant style
        dominant_style, dominant_count = validation_counts.most_common(1)[0]
        dominant_ratio = dominant_count / total if total else 0

        style_names = {
            "pydantic": "Pydantic validation",
            "marshmallow": "Marshmallow schemas",
            "cerberus": "Cerberus validation",
            "voluptuous": "Voluptuous validation",
            "attrs": "attrs validators",
            "decorator": "Decorator-based validation",
            "manual": "Manual validation (ValueError/TypeError)",
        }

        if dominant_ratio >= 0.6:
            title = style_names.get(dominant_style, f"{dominant_style} validation")
            description = (
                f"Uses {style_names.get(dominant_style, dominant_style)} for input validation. "
                f"{dominant_count}/{total} ({dominant_ratio:.0%}) validation patterns use this approach."
            )
            confidence = min(0.9, 0.6 + dominant_ratio * 0.3)
        else:
            title = "Mixed validation approaches"
            used_styles = [style_names.get(s, s) for s, c in validation_counts.most_common(3) if c > 0]
            description = (
                f"Uses multiple validation approaches: {', '.join(used_styles)}."
            )
            confidence = 0.7

        # Build evidence
        evidence = []
        for rel_path, line in validation_examples.get(dominant_style, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.validation_style",
            category="validation",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "validation_counts": dict(validation_counts),
                "dominant_style": dominant_style,
                "dominant_ratio": round(dominant_ratio, 3),
            },
        ))
