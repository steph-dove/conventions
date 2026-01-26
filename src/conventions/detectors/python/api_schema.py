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

        # Detect API versioning (only for web APIs)
        self._detect_api_versioning(ctx, index, result)

        # Detect OpenAPI documentation
        self._detect_openapi_docs(ctx, index, result)

        # Detect data class style
        self._detect_data_class_style(ctx, index, result)

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

    def _detect_api_versioning(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect API versioning patterns (only for web APIs)."""
        import re

        # First check if this is a web API project
        api_frameworks = ["fastapi", "flask", "django", "starlette"]
        api_import_count = 0
        for framework in api_frameworks:
            api_import_count += index.count_imports_matching(framework)

        if api_import_count < 2:
            return  # Not a web API project

        versioning_patterns: Counter[str] = Counter()
        versioning_examples: list[tuple[str, int, str]] = []

        # URL versioning patterns
        url_version_pattern = re.compile(r'''['"](/v\d+/|/api/v\d+)''', re.IGNORECASE)
        header_version_pattern = re.compile(r'''(api[-_]version|x[-_]api[-_]version|accept[-_]version)''', re.IGNORECASE)

        for rel_path, file_idx in index.files.items():
            if file_idx.role in ("test", "docs"):
                continue

            for i, line in enumerate(file_idx.lines, 1):
                # URL versioning (/v1/, /api/v2/)
                if url_version_pattern.search(line):
                    versioning_patterns["url_versioning"] += 1
                    if len(versioning_examples) < 10:
                        versioning_examples.append((rel_path, i, "url"))

                # Header versioning
                if header_version_pattern.search(line.lower()):
                    versioning_patterns["header_versioning"] += 1
                    if len(versioning_examples) < 10:
                        versioning_examples.append((rel_path, i, "header"))

        # Check for APIRouter with prefix containing version
        for rel_path, call in index.get_all_calls():
            if "APIRouter" in call.name or "Blueprint" in call.name:
                if "prefix" in call.kwargs:
                    versioning_patterns["router_prefix"] = versioning_patterns.get("router_prefix", 0) + 1

        if not versioning_patterns:
            return  # No versioning detected - that's okay for simple APIs

        total = sum(versioning_patterns.values())

        if "url_versioning" in versioning_patterns:
            title = "URL-based API versioning"
            description = (
                f"Uses URL path versioning (e.g., /v1/, /api/v2/). "
                f"Found {versioning_patterns['url_versioning']} versioned routes."
            )
            primary = "url_versioning"
        elif "header_versioning" in versioning_patterns:
            title = "Header-based API versioning"
            description = (
                f"Uses HTTP headers for API versioning. "
                f"Found {versioning_patterns['header_versioning']} header version references."
            )
            primary = "header_versioning"
        else:
            title = "API versioning pattern detected"
            description = f"API versioning detected. Found {total} version indicators."
            primary = list(versioning_patterns.keys())[0]

        confidence = min(0.85, 0.5 + total * 0.03)

        # Build evidence
        evidence = []
        for rel_path, line, _ in versioning_examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.api_versioning",
            category="api",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "versioning_patterns": dict(versioning_patterns),
                "primary_pattern": primary,
            },
        ))

    def _detect_openapi_docs(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect OpenAPI/Swagger documentation (only for web APIs)."""
        # First check if this is a web API project
        api_frameworks = ["fastapi", "flask", "django", "starlette"]
        api_import_count = 0
        has_fastapi = False
        for framework in api_frameworks:
            count = index.count_imports_matching(framework)
            api_import_count += count
            if framework == "fastapi" and count > 0:
                has_fastapi = True

        if api_import_count < 2:
            return  # Not a web API project

        openapi_indicators: Counter[str] = Counter()
        openapi_examples: dict[str, list[tuple[str, int]]] = {}

        # FastAPI has built-in OpenAPI - check if it's customized
        if has_fastapi:
            openapi_indicators["fastapi_builtin"] = 1

        for rel_path, imp in index.get_all_imports():
            # flasgger (Flask OpenAPI)
            if "flasgger" in imp.module:
                openapi_indicators["flasgger"] += 1
                if "flasgger" not in openapi_examples:
                    openapi_examples["flasgger"] = []
                openapi_examples["flasgger"].append((rel_path, imp.line))

            # flask-openapi3
            if "flask_openapi3" in imp.module:
                openapi_indicators["flask_openapi3"] += 1
                if "flask_openapi3" not in openapi_examples:
                    openapi_examples["flask_openapi3"] = []
                openapi_examples["flask_openapi3"].append((rel_path, imp.line))

            # apispec
            if "apispec" in imp.module:
                openapi_indicators["apispec"] += 1
                if "apispec" not in openapi_examples:
                    openapi_examples["apispec"] = []
                openapi_examples["apispec"].append((rel_path, imp.line))

            # drf-spectacular (Django REST Framework)
            if "drf_spectacular" in imp.module:
                openapi_indicators["drf_spectacular"] += 1
                if "drf_spectacular" not in openapi_examples:
                    openapi_examples["drf_spectacular"] = []
                openapi_examples["drf_spectacular"].append((rel_path, imp.line))

            # spectree
            if "spectree" in imp.module:
                openapi_indicators["spectree"] += 1
                if "spectree" not in openapi_examples:
                    openapi_examples["spectree"] = []
                openapi_examples["spectree"].append((rel_path, imp.line))

        # Check for OpenAPI customization in FastAPI
        for rel_path, call in index.get_all_calls():
            if call.name == "FastAPI":
                openapi_args = ["openapi_url", "docs_url", "redoc_url", "openapi_tags"]
                if any(arg in call.kwargs for arg in openapi_args):
                    openapi_indicators["fastapi_customized"] = openapi_indicators.get("fastapi_customized", 0) + 1
                    if "fastapi_customized" not in openapi_examples:
                        openapi_examples["fastapi_customized"] = []
                    openapi_examples["fastapi_customized"].append((rel_path, call.line))

        if not openapi_indicators:
            return  # No OpenAPI detected

        # Determine primary
        if "fastapi_customized" in openapi_indicators:
            primary = "fastapi_customized"
            title = "OpenAPI with FastAPI (customized)"
            description = "Uses FastAPI's built-in OpenAPI with custom configuration."
        elif "fastapi_builtin" in openapi_indicators and len(openapi_indicators) == 1:
            primary = "fastapi_builtin"
            title = "OpenAPI with FastAPI (default)"
            description = "Uses FastAPI's built-in OpenAPI documentation at /docs and /redoc."
        elif "drf_spectacular" in openapi_indicators:
            primary = "drf_spectacular"
            title = "OpenAPI with drf-spectacular"
            description = "Uses drf-spectacular for Django REST Framework OpenAPI documentation."
        elif "flasgger" in openapi_indicators:
            primary = "flasgger"
            title = "OpenAPI with Flasgger"
            description = "Uses Flasgger for Flask OpenAPI/Swagger documentation."
        else:
            primary = list(openapi_indicators.keys())[0]
            title = "OpenAPI documentation"
            description = "Uses OpenAPI/Swagger documentation."

        confidence = 0.85 if primary != "fastapi_builtin" else 0.7

        # Build evidence
        evidence = []
        for rel_path, line in openapi_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.openapi_docs",
            category="api",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "openapi_indicators": dict(openapi_indicators),
                "primary_tool": primary,
            },
        ))

    def _detect_data_class_style(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect data class style (dataclass, attrs, Pydantic, msgspec)."""
        style_counts: Counter[str] = Counter()
        style_examples: dict[str, list[tuple[str, int]]] = {}
        has_validation = False

        for rel_path, dec in index.get_all_decorators():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            # Standard dataclass
            if dec.name == "dataclass" or dec.name.endswith(".dataclass"):
                style_counts["dataclass"] += 1
                if "dataclass" not in style_examples:
                    style_examples["dataclass"] = []
                if len(style_examples["dataclass"]) < 5:
                    style_examples["dataclass"].append((rel_path, dec.line))

            # attrs
            if dec.name in ("attr.s", "attrs", "define", "attr.define", "attrs.define"):
                style_counts["attrs"] += 1
                if "attrs" not in style_examples:
                    style_examples["attrs"] = []
                if len(style_examples["attrs"]) < 5:
                    style_examples["attrs"].append((rel_path, dec.line))

        # Check for Pydantic BaseModel inheritance
        for rel_path, cls in index.get_all_classes():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            if "BaseModel" in cls.bases:
                style_counts["pydantic"] += 1
                has_validation = True
                if "pydantic" not in style_examples:
                    style_examples["pydantic"] = []
                if len(style_examples["pydantic"]) < 5:
                    style_examples["pydantic"].append((rel_path, cls.line))

        # Check for msgspec imports
        for rel_path, imp in index.get_all_imports():
            file_idx = index.files.get(rel_path)
            if file_idx and file_idx.role in ("test", "docs"):
                continue

            if "msgspec" in imp.module:
                if "Struct" in imp.names:
                    style_counts["msgspec"] += 1
                    if "msgspec" not in style_examples:
                        style_examples["msgspec"] = []
                    if len(style_examples["msgspec"]) < 5:
                        style_examples["msgspec"].append((rel_path, imp.line))

        if not style_counts:
            return

        # Determine primary style
        primary, primary_count = style_counts.most_common(1)[0]
        total = sum(style_counts.values())

        # Build title and description
        style_names = {
            "pydantic": "Pydantic BaseModel",
            "dataclass": "dataclasses",
            "attrs": "attrs",
            "msgspec": "msgspec Struct",
        }

        # Check if there's appropriate usage per context
        has_pydantic = "pydantic" in style_counts
        has_dataclass = "dataclass" in style_counts
        has_api = index.count_imports_matching("fastapi") > 0 or index.count_imports_matching("flask") > 0

        if has_pydantic and has_dataclass and has_api:
            title = "Data class style: Pydantic for API + dataclasses for internal"
            description = (
                f"Uses Pydantic for API schemas ({style_counts['pydantic']}) and "
                f"dataclasses for internal DTOs ({style_counts['dataclass']}). Good separation."
            )
            confidence = 0.9
        elif len(style_counts) == 1:
            title = f"Data class style: {style_names.get(primary, primary)}"
            description = (
                f"Consistently uses {style_names.get(primary, primary)} for data structures. "
                f"Found {primary_count} usages."
            )
            confidence = min(0.9, 0.6 + primary_count * 0.03)
        else:
            other_styles = [style_names.get(s, s) for s in style_counts if s != primary]
            title = f"Data class style: primarily {style_names.get(primary, primary)}"
            description = (
                f"Primarily uses {style_names.get(primary, primary)} ({primary_count}/{total}). "
                f"Also uses: {', '.join(other_styles)}."
            )
            confidence = min(0.85, 0.5 + (primary_count / total) * 0.35)

        # Build evidence
        evidence = []
        for rel_path, line in style_examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=5)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.data_class_style",
            category="api",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "primary_style": primary,
                "style_counts": dict(style_counts),
                "has_validation": has_validation,
            },
        ))
