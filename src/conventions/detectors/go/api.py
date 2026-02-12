"""Go API conventions detector."""

from __future__ import annotations

import re
from collections import Counter

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import GoDetector
from .index import GoIndex, make_evidence


@DetectorRegistry.register
class GoAPIDetector(GoDetector):
    """Detect Go API conventions."""

    name = "go_api"
    description = "Detects Go HTTP API patterns and frameworks"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Go API conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect HTTP framework
        self._detect_http_framework(ctx, index, result)

        # Detect middleware patterns
        self._detect_middleware_patterns(ctx, index, result)

        # Detect response patterns
        self._detect_response_patterns(ctx, index, result)

        # Detect API routes
        self._detect_api_routes(ctx, index, result)

        return result

    def _detect_http_framework(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect HTTP framework usage."""
        frameworks = {
            "gin": "github.com/gin-gonic/gin",
            "echo": "github.com/labstack/echo",
            "chi": "github.com/go-chi/chi",
            "fiber": "github.com/gofiber/fiber",
            "gorilla": "github.com/gorilla/mux",
            "httprouter": "github.com/julienschmidt/httprouter",
            "stdlib": "net/http",
        }

        framework_counts: Counter[str] = Counter()
        examples: dict[str, list[tuple[str, int]]] = {}

        for name, pkg in frameworks.items():
            imports = index.find_imports_matching(pkg, limit=30)
            if imports:
                framework_counts[name] = len(imports)
                examples[name] = [(r, ln) for r, _, ln in imports[:5]]

        if not framework_counts:
            return

        # Prioritize non-stdlib frameworks
        non_stdlib = {k: v for k, v in framework_counts.items() if k != "stdlib"}
        if non_stdlib:
            primary = max(non_stdlib, key=non_stdlib.get)  # type: ignore
            primary_count = non_stdlib[primary]
        else:
            primary = "stdlib"
            primary_count = framework_counts["stdlib"]

        framework_names = {
            "gin": "Gin",
            "echo": "Echo",
            "chi": "Chi",
            "fiber": "Fiber",
            "gorilla": "Gorilla Mux",
            "httprouter": "httprouter",
            "stdlib": "net/http (stdlib)",
        }

        title = f"HTTP framework: {framework_names.get(primary, primary)}"
        description = (
            f"Uses {framework_names.get(primary, primary)} for HTTP routing. "
            f"Found in {primary_count} files."
        )
        confidence = min(0.95, 0.7 + primary_count * 0.02)

        evidence = []
        for rel_path, line in examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.http_framework",
            category="api",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "framework_counts": dict(framework_counts),
                "primary_framework": primary,
            },
        ))

    def _detect_middleware_patterns(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect middleware patterns."""
        # Common middleware patterns
        # func(next http.Handler) http.Handler
        handler_middleware = r'func\s*\([^)]*\)\s*http\.Handler'
        handler_count = index.count_pattern(handler_middleware, exclude_tests=True)

        # Gin middleware: func(c *gin.Context)
        gin_middleware = r'func\s*\(\s*c\s*\*gin\.Context\s*\)'
        gin_count = index.count_pattern(gin_middleware, exclude_tests=True)

        # Echo middleware: func(next echo.HandlerFunc) echo.HandlerFunc
        echo_middleware = r'func\s*\(\s*next\s+echo\.HandlerFunc\s*\)'
        echo_count = index.count_pattern(echo_middleware, exclude_tests=True)

        # Chi/stdlib Use pattern
        use_pattern = r'\.Use\s*\('
        use_count = index.count_pattern(use_pattern, exclude_tests=True)

        total = handler_count + gin_count + echo_count
        if total < 2 and use_count < 3:
            return

        matches = index.search_pattern(handler_middleware, limit=10)
        if gin_count:
            matches.extend(index.search_pattern(gin_middleware, limit=10))

        title = "HTTP middleware pattern"
        description = (
            f"Uses middleware pattern for HTTP handlers. "
            f"Found {total} middleware functions, {use_count} .Use() calls."
        )
        confidence = min(0.9, 0.6 + total * 0.04)

        evidence = []
        for rel_path, line, _ in matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=4)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.http_middleware",
            category="api",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "handler_middleware_count": handler_count,
                "gin_middleware_count": gin_count,
                "echo_middleware_count": echo_count,
                "use_calls": use_count,
            },
        ))

    def _detect_response_patterns(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Detect JSON response patterns."""
        # json.Marshal and json.NewEncoder
        json_marshal = r'json\.(?:Marshal|NewEncoder)'
        marshal_count = index.count_pattern(json_marshal, exclude_tests=True)

        # Gin JSON response: c.JSON(
        gin_json = r'c\.JSON\s*\('
        gin_json_count = index.count_pattern(gin_json, exclude_tests=True)

        # Echo JSON response: c.JSON(
        echo_json = r'return\s+c\.JSON\s*\('
        echo_json_count = index.count_pattern(echo_json, exclude_tests=True)

        total = marshal_count + gin_json_count + echo_json_count
        if total < 3:
            return

        if gin_json_count > marshal_count:
            title = "Gin JSON responses"
            description = f"Uses Gin's c.JSON() for API responses. Found {gin_json_count} usages."
        elif echo_json_count > marshal_count:
            title = "Echo JSON responses"
            description = f"Uses Echo's c.JSON() for API responses. Found {echo_json_count} usages."
        else:
            title = "JSON API responses"
            description = f"Uses json.Marshal/Encoder for API responses. Found {marshal_count} usages."

        confidence = min(0.85, 0.6 + total * 0.02)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.response_patterns",
            category="api",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=[],
            stats={
                "json_marshal_count": marshal_count,
                "gin_json_count": gin_json_count,
                "echo_json_count": echo_json_count,
            },
        ))

    def _detect_api_routes(
        self,
        ctx: DetectorContext,
        index: GoIndex,
        result: DetectorResult,
    ) -> None:
        """Extract API route definitions."""
        # Gin/Echo/Chi: r.GET("/path", handler) or r.Get("/path", handler)
        method_route_pattern = re.compile(
            r"""\.(GET|POST|PUT|PATCH|DELETE|Get|Post|Put|Patch|Delete)\(\s*"([^"]+)""",
        )
        # stdlib / gorilla: HandleFunc("/path", handler) or Handle("/path", handler)
        handlefunc_pattern = re.compile(
            r"""(?:HandleFunc|Handle)\(\s*"([^"]+)""",
        )

        routes: list[dict[str, str | int]] = []
        methods: dict[str, int] = {}

        for rel_path, file_idx in index.files.items():
            if file_idx.role == "test":
                continue

            content = "\n".join(file_idx.lines)

            for m in method_route_pattern.finditer(content):
                method = m.group(1).upper()
                path = m.group(2)
                line = content[: m.start()].count("\n") + 1

                methods[method] = methods.get(method, 0) + 1
                routes.append({
                    "method": method,
                    "path": path,
                    "file": rel_path,
                    "line": line,
                })
                if len(routes) >= 100:
                    break

            for m in handlefunc_pattern.finditer(content):
                path = m.group(1)
                line = content[: m.start()].count("\n") + 1

                methods["ANY"] = methods.get("ANY", 0) + 1
                routes.append({
                    "method": "ANY",
                    "path": path,
                    "file": rel_path,
                    "line": line,
                })
                if len(routes) >= 100:
                    break

            if len(routes) >= 100:
                break

        if not routes:
            return

        path_prefixes = _extract_path_prefixes([str(r["path"]) for r in routes])

        description = (
            f"{len(routes)} API routes detected. "
            f"Methods: {', '.join(f'{k}: {v}' for k, v in sorted(methods.items()))}."
        )

        result.rules.append(self.make_rule(
            rule_id="go.conventions.api_routes",
            category="api",
            title="API routes",
            description=description,
            confidence=0.90,
            language="go",
            evidence=[],
            stats={
                "routes": routes,
                "total_routes": len(routes),
                "methods": methods,
                "path_prefixes": path_prefixes,
            },
        ))


def _extract_path_prefixes(paths: list[str]) -> list[str]:
    """Extract common path prefixes from a list of paths."""
    prefix_counts: dict[str, int] = {}
    for path in paths:
        parts = path.strip("/").split("/")
        if len(parts) >= 2:
            prefix = "/" + "/".join(parts[:2])
            prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
        elif len(parts) == 1 and parts[0]:
            prefix = "/" + parts[0]
            prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1

    return sorted(
        [p for p, c in prefix_counts.items() if c > 1],
        key=lambda p: -prefix_counts[p],
    )[:10]
