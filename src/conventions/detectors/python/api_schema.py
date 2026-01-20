"""Python API and schema conventions detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


@DetectorRegistry.register
class PythonAPISchemaConventionsDetector(PythonDetector):
    """Detect Python API framework and schema library conventions."""

    name = "python_api_schema_conventions"
    description = "Detects API framework, schema library, and response patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect API framework, schema library, and response patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect API framework
        self._detect_api_framework(ctx, index, result)

        # Detect schema library
        self._detect_schema_library(ctx, index, result)

        # Detect response patterns
        self._detect_response_shape(ctx, index, result)

        return result

    def _detect_api_framework(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect which API framework is used."""
        frameworks: Counter[str] = Counter()
        framework_examples: dict[str, list[tuple[str, int]]] = {}

        for rel_path, imp in index.get_all_imports():
            # FastAPI
            if "fastapi" in imp.module or "FastAPI" in imp.names or "APIRouter" in imp.names:
                frameworks["fastapi"] += 1
                if "fastapi" not in framework_examples:
                    framework_examples["fastapi"] = []
                framework_examples["fastapi"].append((rel_path, imp.line))

            # Flask
            if imp.module == "flask" or "Flask" in imp.names:
                frameworks["flask"] += 1
                if "flask" not in framework_examples:
                    framework_examples["flask"] = []
                framework_examples["flask"].append((rel_path, imp.line))

            # Django / DRF
            if "django" in imp.module or "rest_framework" in imp.module:
                frameworks["django"] += 1
                if "django" not in framework_examples:
                    framework_examples["django"] = []
                framework_examples["django"].append((rel_path, imp.line))

            # Starlette
            if "starlette" in imp.module:
                frameworks["starlette"] += 1
                if "starlette" not in framework_examples:
                    framework_examples["starlette"] = []
                framework_examples["starlette"].append((rel_path, imp.line))

            # aiohttp
            if "aiohttp" in imp.module and "web" in imp.names:
                frameworks["aiohttp"] += 1
                if "aiohttp" not in framework_examples:
                    framework_examples["aiohttp"] = []
                framework_examples["aiohttp"].append((rel_path, imp.line))

            # Falcon
            if imp.module == "falcon" or "falcon" in imp.module:
                frameworks["falcon"] += 1
                if "falcon" not in framework_examples:
                    framework_examples["falcon"] = []
                framework_examples["falcon"].append((rel_path, imp.line))

            # Litestar (formerly Starlite)
            if "litestar" in imp.module or "starlite" in imp.module:
                frameworks["litestar"] += 1
                if "litestar" not in framework_examples:
                    framework_examples["litestar"] = []
                framework_examples["litestar"].append((rel_path, imp.line))

        # Also check for app instantiation
        for rel_path, call in index.get_all_calls():
            if call.name == "FastAPI":
                frameworks["fastapi"] += 2
            elif call.name == "Flask":
                frameworks["flask"] += 2
            elif call.name == "APIRouter":
                frameworks["fastapi"] += 1

        if not frameworks:
            return

        # Determine primary framework
        primary, primary_count = frameworks.most_common(1)[0]
        total = sum(frameworks.values())

        # Map to friendly names
        framework_names = {
            "fastapi": "FastAPI",
            "flask": "Flask",
            "django": "Django/DRF",
            "starlette": "Starlette",
            "aiohttp": "aiohttp",
            "falcon": "Falcon",
            "litestar": "Litestar",
        }

        if len(frameworks) == 1:
            title = f"Uses {framework_names.get(primary, primary)} framework"
            description = (
                f"Exclusively uses {framework_names.get(primary, primary)} for API endpoints. "
                f"Found {primary_count} usages."
            )
            confidence = min(0.95, 0.7 + primary_count * 0.02)
        else:
            other_frameworks = [
                framework_names.get(f, f)
                for f in frameworks if f != primary
            ]
            title = f"Primary API framework: {framework_names.get(primary, primary)}"
            description = (
                f"Uses {framework_names.get(primary, primary)} as primary framework "
                f"({primary_count}/{total} usages). Also uses: {', '.join(other_frameworks)}."
            )
            confidence = min(0.85, 0.5 + (primary_count / total) * 0.35)

        # Build evidence
        evidence = []
        for rel_path, line in framework_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.api_framework",
            category="api",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "framework_counts": dict(frameworks),
                "primary_framework": primary,
            },
        ))

    def _detect_schema_library(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect which schema/validation library is used."""
        libraries: Counter[str] = Counter()
        library_examples: dict[str, list[tuple[str, int]]] = {}

        for rel_path, imp in index.get_all_imports():
            # Pydantic
            if "pydantic" in imp.module or "BaseModel" in imp.names:
                libraries["pydantic"] += 1
                if "pydantic" not in library_examples:
                    library_examples["pydantic"] = []
                library_examples["pydantic"].append((rel_path, imp.line))

            # dataclasses
            if imp.module == "dataclasses" or "dataclass" in imp.names:
                libraries["dataclasses"] += 1
                if "dataclasses" not in library_examples:
                    library_examples["dataclasses"] = []
                library_examples["dataclasses"].append((rel_path, imp.line))

            # attrs
            if imp.module == "attr" or imp.module == "attrs":
                libraries["attrs"] += 1
                if "attrs" not in library_examples:
                    library_examples["attrs"] = []
                library_examples["attrs"].append((rel_path, imp.line))

            # marshmallow
            if "marshmallow" in imp.module:
                libraries["marshmallow"] += 1
                if "marshmallow" not in library_examples:
                    library_examples["marshmallow"] = []
                library_examples["marshmallow"].append((rel_path, imp.line))

            # msgspec
            if "msgspec" in imp.module:
                libraries["msgspec"] += 1
                if "msgspec" not in library_examples:
                    library_examples["msgspec"] = []
                library_examples["msgspec"].append((rel_path, imp.line))

        # Also check for BaseModel inheritance
        for rel_path, cls in index.get_all_classes():
            if "BaseModel" in cls.bases:
                libraries["pydantic"] += 1

        if not libraries:
            return

        # Determine primary library
        primary, primary_count = libraries.most_common(1)[0]
        total = sum(libraries.values())

        # Map to friendly names
        lib_names = {
            "pydantic": "Pydantic",
            "dataclasses": "dataclasses",
            "attrs": "attrs",
            "marshmallow": "Marshmallow",
            "msgspec": "msgspec",
        }

        if len(libraries) == 1:
            title = f"Uses {lib_names.get(primary, primary)} for schemas"
            description = (
                f"Exclusively uses {lib_names.get(primary, primary)} for data validation/serialization. "
                f"Found {primary_count} usages."
            )
            confidence = min(0.95, 0.7 + primary_count * 0.02)
        else:
            other_libs = [lib_names.get(lib, lib) for lib in libraries if lib != primary]
            title = f"Primary schema library: {lib_names.get(primary, primary)}"
            description = (
                f"Uses {lib_names.get(primary, primary)} as primary schema library "
                f"({primary_count}/{total} usages). Also uses: {', '.join(other_libs)}."
            )
            confidence = min(0.85, 0.5 + (primary_count / total) * 0.35)

        # Build evidence
        evidence = []
        for rel_path, line in library_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.schema_library",
            category="api",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "library_counts": dict(libraries),
                "primary_library": primary,
            },
        ))

    def _detect_response_shape(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect response envelope patterns."""
        # Look for common envelope patterns in return statements
        # This is heuristic - we look for dict keys like "data", "error", "message"

        envelope_indicators = 0
        envelope_examples: list[tuple[str, int]] = []

        # Check for response model classes with envelope patterns
        for rel_path, cls in index.get_all_classes():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role not in ("api", "schema"):
                continue

            # Check if class name suggests envelope
            name_lower = cls.name.lower()
            if any(x in name_lower for x in ["response", "result", "envelope", "wrapper"]):
                # Check if it has data/error fields by looking at the class body
                ev = make_evidence(index, rel_path, cls.line, radius=10)
                if ev:
                    excerpt_lower = ev.excerpt.lower()
                    if "data" in excerpt_lower or "error" in excerpt_lower:
                        envelope_indicators += 1
                        if len(envelope_examples) < 5:
                            envelope_examples.append((rel_path, cls.line))

        # Check for JSONResponse / dict returns with envelope keys
        for rel_path, call in index.get_all_calls():
            if call.name in ("JSONResponse", "jsonify"):
                # Check kwargs for envelope pattern
                if any(kw in call.kwargs for kw in ("data", "error", "message", "status")):
                    envelope_indicators += 1
                    if len(envelope_examples) < 5:
                        envelope_examples.append((rel_path, call.line))

        # If we have envelope patterns, emit rule
        if envelope_indicators >= 3:
            title = "Response envelope pattern"
            description = (
                f"Uses response envelope pattern (data/error/message keys). "
                f"Found {envelope_indicators} envelope indicators."
            )
            confidence = min(0.8, 0.5 + envelope_indicators * 0.05)

            # Build evidence
            evidence = []
            for rel_path, line in envelope_examples[:ctx.max_evidence_snippets]:
                ev = make_evidence(index, rel_path, line, radius=5)
                if ev:
                    evidence.append(ev)

            result.rules.append(self.make_rule(
                rule_id="python.conventions.response_shape",
                category="api",
                title=title,
                description=description,
                confidence=confidence,
                language="python",
                evidence=evidence,
                stats={
                    "envelope_indicators": envelope_indicators,
                },
            ))
