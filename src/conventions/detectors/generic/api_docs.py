"""API documentation detector."""

from __future__ import annotations

from pathlib import Path

from ..base import BaseDetector, DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from ...fs import read_file_safe


@DetectorRegistry.register
class APIDocumentationDetector(BaseDetector):
    """Detect API documentation patterns."""

    name = "generic_api_docs"
    description = "Detects OpenAPI/Swagger and other API documentation"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect API documentation patterns."""
        result = DetectorResult()

        docs_found: dict[str, dict] = {}

        # OpenAPI/Swagger files
        openapi_patterns = [
            "openapi.yaml", "openapi.yml", "openapi.json",
            "swagger.yaml", "swagger.yml", "swagger.json",
            "api.yaml", "api.yml", "api.json",
        ]

        # Check root and common directories
        search_dirs = [
            ctx.repo_root,
            ctx.repo_root / "docs",
            ctx.repo_root / "api",
            ctx.repo_root / "spec",
            ctx.repo_root / "specs",
        ]

        for search_dir in search_dirs:
            if not search_dir.is_dir():
                continue

            for pattern in openapi_patterns:
                spec_file = search_dir / pattern
                if spec_file.is_file():
                    content = read_file_safe(spec_file)
                    version = None
                    if content:
                        if "openapi:" in content or '"openapi":' in content:
                            # Try to extract version
                            import re
                            match = re.search(r'openapi["\']?\s*:\s*["\']?(\d+\.\d+)', content)
                            if match:
                                version = match.group(1)
                            docs_found["openapi"] = {
                                "name": "OpenAPI",
                                "file": str(spec_file.relative_to(ctx.repo_root)),
                                "version": version or "3.x",
                            }
                        elif "swagger:" in content or '"swagger":' in content:
                            docs_found["swagger"] = {
                                "name": "Swagger",
                                "file": str(spec_file.relative_to(ctx.repo_root)),
                                "version": "2.0",
                            }
                    break
            if docs_found:
                break

        # AsyncAPI for event-driven APIs
        asyncapi_patterns = ["asyncapi.yaml", "asyncapi.yml", "asyncapi.json"]
        for search_dir in search_dirs:
            if not search_dir.is_dir():
                continue
            for pattern in asyncapi_patterns:
                spec_file = search_dir / pattern
                if spec_file.is_file():
                    docs_found["asyncapi"] = {
                        "name": "AsyncAPI",
                        "file": str(spec_file.relative_to(ctx.repo_root)),
                    }
                    break

        # GraphQL schema
        graphql_patterns = ["schema.graphql", "schema.gql"]
        for search_dir in search_dirs:
            if not search_dir.is_dir():
                continue
            for pattern in graphql_patterns:
                spec_file = search_dir / pattern
                if spec_file.is_file():
                    docs_found["graphql"] = {
                        "name": "GraphQL Schema",
                        "file": str(spec_file.relative_to(ctx.repo_root)),
                    }
                    break

        # Postman collection
        postman_files = list(ctx.repo_root.glob("**/postman*.json")) + \
                       list(ctx.repo_root.glob("**/*.postman_collection.json"))
        if postman_files:
            docs_found["postman"] = {
                "name": "Postman Collection",
                "file": str(postman_files[0].relative_to(ctx.repo_root)),
                "count": len(postman_files),
            }

        if not docs_found:
            return result

        doc_names = [d["name"] for d in docs_found.values()]
        title = f"API documentation: {', '.join(doc_names)}"

        descriptions = []
        for doc_id, doc_info in docs_found.items():
            desc = doc_info["name"]
            if doc_info.get("version"):
                desc += f" {doc_info['version']}"
            descriptions.append(desc)

        description = f"API documented with {', '.join(descriptions)}."
        confidence = min(0.95, 0.7 + len(docs_found) * 0.1)

        result.rules.append(self.make_rule(
            rule_id="generic.conventions.api_documentation",
            category="documentation",
            title=title,
            description=description,
            confidence=confidence,
            language="generic",
            evidence=[],
            stats={
                "doc_types": list(docs_found.keys()),
                "doc_details": docs_found,
            },
        ))

        return result
