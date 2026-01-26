"""Python serialization conventions detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


@DetectorRegistry.register
class PythonSerializationDetector(PythonDetector):
    """Detect Python serialization library conventions."""

    name = "python_serialization"
    description = "Detects JSON library and serialization patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect serialization patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        self._detect_json_library(ctx, index, result)

        return result

    def _detect_json_library(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect JSON library usage."""
        json_libs: Counter[str] = Counter()
        json_examples: dict[str, list[tuple[str, int]]] = {}

        for rel_path, imp in index.get_all_imports():
            # Skip test files
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            # orjson (fastest)
            if imp.module == "orjson" or "orjson" in imp.names:
                json_libs["orjson"] += 1
                if "orjson" not in json_examples:
                    json_examples["orjson"] = []
                json_examples["orjson"].append((rel_path, imp.line))

            # ujson (fast)
            if imp.module == "ujson" or "ujson" in imp.names:
                json_libs["ujson"] += 1
                if "ujson" not in json_examples:
                    json_examples["ujson"] = []
                json_examples["ujson"].append((rel_path, imp.line))

            # simplejson
            if imp.module == "simplejson" or "simplejson" in imp.names:
                json_libs["simplejson"] += 1
                if "simplejson" not in json_examples:
                    json_examples["simplejson"] = []
                json_examples["simplejson"].append((rel_path, imp.line))

            # stdlib json
            if imp.module == "json":
                json_libs["json"] += 1
                if "json" not in json_examples:
                    json_examples["json"] = []
                json_examples["json"].append((rel_path, imp.line))

            # rapidjson
            if "rapidjson" in imp.module:
                json_libs["rapidjson"] += 1
                if "rapidjson" not in json_examples:
                    json_examples["rapidjson"] = []
                json_examples["rapidjson"].append((rel_path, imp.line))

        # Check for usage patterns
        for rel_path, call in index.get_all_calls():
            if "orjson.dumps" in call.name or "orjson.loads" in call.name:
                json_libs["orjson"] += 1
            elif "ujson.dumps" in call.name or "ujson.loads" in call.name:
                json_libs["ujson"] += 1
            elif "json.dumps" in call.name or "json.loads" in call.name:
                json_libs["json"] += 1

        if not json_libs:
            return

        primary, primary_count = json_libs.most_common(1)[0]
        total = sum(json_libs.values())

        lib_names = {
            "orjson": "orjson",
            "ujson": "ujson",
            "simplejson": "simplejson",
            "json": "stdlib json",
            "rapidjson": "python-rapidjson",
        }

        # Performance tiers
        if primary == "orjson":
            title = "JSON library: orjson (fastest)"
            description = f"Uses orjson for JSON serialization ({primary_count} usages). ~10x faster than stdlib."
        elif primary == "ujson":
            title = "JSON library: ujson (fast)"
            description = f"Uses ujson for JSON serialization ({primary_count} usages). ~3x faster than stdlib."
        elif primary == "json":
            # Check if other faster libs are also used
            if "orjson" in json_libs or "ujson" in json_libs:
                title = "JSON library: mixed"
                other = "orjson" if "orjson" in json_libs else "ujson"
                description = f"Uses both stdlib json and {other}. Consider standardizing on {other}."
            else:
                title = "JSON library: stdlib json"
                description = f"Uses standard library json ({primary_count} usages)."
        else:
            title = f"JSON library: {lib_names.get(primary, primary)}"
            description = f"Uses {lib_names.get(primary, primary)} for JSON serialization."

        confidence = min(0.9, 0.6 + total * 0.02)

        # Build evidence
        evidence = []
        for rel_path, line in json_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.json_library",
            category="serialization",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "json_library_counts": dict(json_libs),
                "primary_library": primary,
                "total_usages": total,
            },
        ))
