"""Node.js API conventions detector."""

from __future__ import annotations

import re

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import NodeDetector
from .index import NodeIndex, make_evidence


@DetectorRegistry.register
class NodeAPIDetector(NodeDetector):
    """Detect Node.js API conventions."""

    name = "node_api"
    description = "Detects Node.js API patterns and organization"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Node.js API conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect middleware patterns
        self._detect_middleware_patterns(ctx, index, result)

        # Detect route organization
        self._detect_route_organization(ctx, index, result)

        # Detect response patterns
        self._detect_response_patterns(ctx, index, result)

        # Detect handler pattern
        self._detect_handler_pattern(ctx, index, result)

        # Detect route factory pattern
        self._detect_route_factory_pattern(ctx, index, result)

        # Detect response utility pattern (Reply.ok(), etc.)
        self._detect_response_utility_pattern(ctx, index, result)

        # Detect API routes
        self._detect_api_routes(ctx, index, result)

        return result

    def _detect_middleware_patterns(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect middleware usage patterns."""
        # app.use patterns
        app_use_pattern = r'(?:app|router)\.use\s*\('
        use_count = index.count_pattern(app_use_pattern, exclude_tests=True)

        # Middleware function signature: (req, res, next)
        middleware_pattern = r'(?:function|\(|=>)\s*\(\s*req\s*,\s*res\s*,\s*next\s*\)'
        middleware_count = index.count_pattern(middleware_pattern, exclude_tests=True)

        total = use_count + middleware_count
        if total < 3:
            return

        matches = index.search_pattern(middleware_pattern, limit=20)

        title = "Express middleware pattern"
        description = (
            f"Uses middleware pattern extensively. "
            f".use() calls: {use_count}, middleware functions: {middleware_count}."
        )
        confidence = min(0.9, 0.6 + total * 0.02)

        evidence = []
        for rel_path, line, _ in matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.middleware_patterns",
            category="api",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "use_calls": use_count,
                "middleware_functions": middleware_count,
            },
        ))

    def _detect_route_organization(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect route file organization."""
        # Count route files
        route_files = index.get_files_by_role("api")

        if len(route_files) < 3:
            return

        # Check for Router usage
        router_pattern = r'(?:express\.)?Router\s*\(\s*\)'
        router_count = index.count_pattern(router_pattern, exclude_tests=True)

        # HTTP method handlers
        method_pattern = r'(?:router|app)\.(?:get|post|put|patch|delete)\s*\('
        method_count = index.count_pattern(method_pattern, exclude_tests=True)

        if method_count < 5:
            return

        title = "Organized route files"
        description = (
            f"Routes organized across {len(route_files)} files. "
            f"Router instances: {router_count}, route handlers: {method_count}."
        )
        confidence = min(0.9, 0.6 + len(route_files) * 0.05)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.route_organization",
            category="api",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=[],
            stats={
                "route_file_count": len(route_files),
                "router_instances": router_count,
                "route_handlers": method_count,
            },
        ))

    def _detect_response_patterns(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect API response patterns."""
        # res.json() usage
        res_json_pattern = r'res\.json\s*\('
        json_count = index.count_pattern(res_json_pattern, exclude_tests=True)

        # res.status().json() pattern
        status_json_pattern = r'res\.status\s*\(\s*\d+\s*\)\.json\s*\('
        status_json_count = index.count_pattern(status_json_pattern, exclude_tests=True)

        # res.send() usage
        res_send_pattern = r'res\.send\s*\('
        send_count = index.count_pattern(res_send_pattern, exclude_tests=True)

        total = json_count + send_count
        if total < 5:
            return

        json_ratio = json_count / total if total else 0

        if json_ratio >= 0.8:
            title = "JSON API responses"
            description = (
                f"Consistently uses res.json() for responses. "
                f"json(): {json_count}, send(): {send_count}."
            )
            confidence = 0.9
        elif json_ratio >= 0.5:
            title = "Mixed response methods"
            description = (
                f"Uses both res.json() and res.send(). "
                f"json(): {json_count}, send(): {send_count}."
            )
            confidence = 0.75
        else:
            title = "res.send() responses"
            description = (
                f"Primarily uses res.send() for responses. "
                f"send(): {send_count}, json(): {json_count}."
            )
            confidence = 0.7

        result.rules.append(self.make_rule(
            rule_id="node.conventions.response_patterns",
            category="api",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=[],
            stats={
                "res_json_count": json_count,
                "res_status_json_count": status_json_count,
                "res_send_count": send_count,
                "json_ratio": round(json_ratio, 3),
            },
        ))

    def _detect_handler_pattern(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect handler pattern (async functions with typed responses)."""
        from pathlib import Path

        # Check for handlers/ directory
        handler_dirs = set()
        handler_files = []
        for rel_path, f in index.files.items():
            path_parts = Path(rel_path).parts
            for part in path_parts:
                if part.lower() == "handlers":
                    handler_dirs.add(part)
                    handler_files.append(f)

        # Look for typed handler return types (SendsReply, ApiResponse, etc.)
        handler_return_pattern = r'(?:async\s+)?function\s+\w+[^)]*\)\s*:\s*(?:Promise<)?(?:SendsReply|ApiResponse|Response|HandlerResult)'
        handler_matches = index.search_pattern(handler_return_pattern, limit=30, exclude_tests=True)

        # Also check for arrow function handlers
        arrow_handler_pattern = r'=\s*async\s*\([^)]*\)\s*:\s*(?:Promise<)?(?:SendsReply|ApiResponse|Response|HandlerResult)'
        arrow_count = index.count_pattern(arrow_handler_pattern, exclude_tests=True)

        total = len(handler_matches) + arrow_count + len(handler_files)
        if total < 3:
            return

        title = "Handler pattern"
        parts = []
        if handler_dirs:
            parts.append("handlers/ directory")
        if handler_matches or arrow_count:
            parts.append(f"{len(handler_matches) + arrow_count} typed handlers")

        description = f"Uses handler pattern for request processing. {', '.join(parts)}."
        confidence = min(0.9, 0.6 + total * 0.04)

        evidence = []
        for rel_path, line, _ in handler_matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.handler_pattern",
            category="api",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "handler_directories": list(handler_dirs),
                "typed_handler_count": len(handler_matches) + arrow_count,
                "handler_files": len(handler_files),
            },
        ))

    def _detect_route_factory_pattern(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect route factory pattern (make(config) factories that return Express app)."""
        # Look for factory function pattern: function make(config, ...) or export function make
        factory_pattern = r'(?:export\s+)?(?:async\s+)?function\s+make\s*\(\s*(?:config|options|settings)'
        factory_matches = index.search_pattern(factory_pattern, limit=20, exclude_tests=True)

        # Also check for arrow function factories
        arrow_factory_pattern = r'(?:export\s+)?const\s+make\s*=\s*(?:async\s*)?\([^)]*(?:config|options)'
        arrow_count = index.count_pattern(arrow_factory_pattern, exclude_tests=True)

        # Check for createApp/createRouter patterns as well
        create_pattern = r'(?:export\s+)?(?:async\s+)?function\s+(?:create(?:App|Router|Server)|make(?:App|Router|Server))\s*\('
        create_count = index.count_pattern(create_pattern, exclude_tests=True)

        total = len(factory_matches) + arrow_count + create_count
        if total < 2:
            return

        title = "Route factory pattern"
        description = (
            f"Routes use factory functions that receive config and return Express app. "
            f"Found {total} factory functions."
        )
        confidence = min(0.9, 0.6 + total * 0.1)

        evidence = []
        for rel_path, line, _ in factory_matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=4)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.route_factory",
            category="api",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "make_function_count": len(factory_matches) + arrow_count,
                "create_app_count": create_count,
            },
        ))

    def _detect_response_utility_pattern(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Detect centralized response utility (Reply.ok(), Reply.notFound(), etc.)."""
        # Look for Reply.method() or Response.method() patterns
        reply_pattern = r'(?:Reply|Response|ApiResponse)\.(?:ok|success|error|notFound|badRequest|created|noContent|validationError|unauthorized|forbidden|sendError)\s*\('
        reply_matches = index.search_pattern(reply_pattern, limit=50, exclude_tests=True)

        if len(reply_matches) < 3:
            return

        # Count different response methods used
        method_counts: dict[str, int] = {}
        for _, _, match_text in reply_matches:
            import re
            method_match = re.search(r'\.(\w+)\s*\(', match_text)
            if method_match:
                method = method_match.group(1)
                method_counts[method] = method_counts.get(method, 0) + 1

        title = "Centralized response utility"
        methods_used = list(method_counts.keys())[:5]
        description = (
            f"Uses centralized response utility for consistent API responses. "
            f"Methods: {', '.join(methods_used)}. Total usages: {len(reply_matches)}."
        )
        confidence = min(0.9, 0.7 + len(reply_matches) * 0.01)

        evidence = []
        for rel_path, line, _ in reply_matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=2)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.response_utility",
            category="api",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "total_usages": len(reply_matches),
                "method_counts": method_counts,
            },
        ))

    def _detect_api_routes(
        self,
        ctx: DetectorContext,
        index: NodeIndex,
        result: DetectorResult,
    ) -> None:
        """Extract API route definitions."""
        route_pattern = re.compile(
            r"""(?:router|app)\.(get|post|put|patch|delete)\(\s*['"]([^'"]+)""",
            re.IGNORECASE,
        )

        routes: list[dict[str, str | int]] = []
        methods: dict[str, int] = {}

        for rel_path, file_idx in index.files.items():
            if file_idx.role == "test":
                continue

            content = "\n".join(file_idx.lines)
            for m in route_pattern.finditer(content):
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
            rule_id="node.conventions.api_routes",
            category="api",
            title="API routes",
            description=description,
            confidence=0.90,
            language="node",
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
