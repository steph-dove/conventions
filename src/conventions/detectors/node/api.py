"""Node.js API conventions detector."""

from __future__ import annotations

from collections import Counter

from ..base import DetectorContext, DetectorResult
from .base import NodeDetector
from .index import NodeIndex, make_evidence
from ..registry import DetectorRegistry


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
