"""Python GraphQL patterns detector."""

from __future__ import annotations

from ..base import DetectorContext, DetectorResult, PythonDetector
from .index import PythonIndex, make_evidence
from ..registry import DetectorRegistry


@DetectorRegistry.register
class PythonGraphQLDetector(PythonDetector):
    """Detect Python GraphQL patterns."""

    name = "python_graphql"
    description = "Detects Python GraphQL libraries (Strawberry, Graphene, Ariadne)"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Python GraphQL patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        libraries: dict[str, dict] = {}
        examples: dict[str, list[tuple[str, int]]] = {}

        # Strawberry (modern, type-hint based)
        strawberry_imports = index.find_imports_matching("strawberry", limit=30)
        if strawberry_imports:
            libraries["strawberry"] = {
                "name": "Strawberry",
                "import_count": len(strawberry_imports),
                "style": "code-first (type hints)",
            }
            examples["strawberry"] = [(rel_path, imp.line) for rel_path, imp in strawberry_imports[:5]]

        # Graphene
        graphene_imports = index.find_imports_matching("graphene", limit=30)
        if graphene_imports:
            libraries["graphene"] = {
                "name": "Graphene",
                "import_count": len(graphene_imports),
                "style": "code-first (classes)",
            }
            examples["graphene"] = [(rel_path, imp.line) for rel_path, imp in graphene_imports[:5]]

        # Ariadne (schema-first)
        ariadne_imports = index.find_imports_matching("ariadne", limit=30)
        if ariadne_imports:
            libraries["ariadne"] = {
                "name": "Ariadne",
                "import_count": len(ariadne_imports),
                "style": "schema-first",
            }
            examples["ariadne"] = [(rel_path, imp.line) for rel_path, imp in ariadne_imports[:5]]

        # graphql-core (low-level)
        graphql_core_imports = index.find_imports_matching("graphql", limit=20)
        # Filter to avoid false positives from strawberry.graphql etc.
        graphql_core_imports = [
            (rel_path, imp) for rel_path, imp in graphql_core_imports
            if imp.module.startswith("graphql") and "strawberry" not in imp.module
        ]
        if graphql_core_imports and not libraries:
            libraries["graphql_core"] = {
                "name": "graphql-core",
                "import_count": len(graphql_core_imports),
                "style": "low-level",
            }
            examples["graphql_core"] = [(rel_path, imp.line) for rel_path, imp in graphql_core_imports[:5]]

        if not libraries:
            return result

        library_names = [l["name"] for l in libraries.values()]
        primary = max(libraries, key=lambda k: libraries[k]["import_count"])

        style = libraries[primary].get("style", "")
        title = f"GraphQL: {libraries[primary]['name']}"
        description = f"Uses {libraries[primary]['name']} for GraphQL API."
        if style:
            description += f" ({style})"

        if len(libraries) > 1:
            others = [l for l in library_names if l != libraries[primary]["name"]]
            description += f" Also uses: {', '.join(others)}."

        # Modern type-hint based library gets higher confidence
        if primary == "strawberry":
            confidence = 0.95
        elif primary == "graphene":
            confidence = 0.9
        else:
            confidence = 0.85

        evidence = []
        for file_path, line in examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, file_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.graphql",
            category="api",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "libraries": list(libraries.keys()),
                "primary_library": primary,
                "library_details": libraries,
            },
        ))

        return result
