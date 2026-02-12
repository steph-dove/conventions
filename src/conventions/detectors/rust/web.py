"""Rust web framework conventions detector."""

from __future__ import annotations

import re

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import RustDetector
from .index import RustIndex, make_evidence


@DetectorRegistry.register
class RustWebDetector(RustDetector):
    """Detect Rust web framework conventions."""

    name = "rust_web"
    description = "Detects web frameworks (Actix, Axum, Rocket, Warp)"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect web framework conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        frameworks: dict[str, dict] = {}
        examples: list[tuple[str, int]] = []

        # Check for Axum
        axum_uses = index.find_uses_matching("axum", limit=50)
        if axum_uses:
            frameworks["axum"] = {
                "name": "Axum",
                "count": len(axum_uses),
            }
            examples.extend([(r, ln) for r, _, ln in axum_uses[:3]])

        # Check for Actix-web
        actix_uses = index.find_uses_matching("actix_web", limit=50)
        if actix_uses:
            frameworks["actix"] = {
                "name": "Actix-web",
                "count": len(actix_uses),
            }
            examples.extend([(r, ln) for r, _, ln in actix_uses[:3]])

        # Check for Rocket
        rocket_uses = index.find_uses_matching("rocket", limit=50)
        if rocket_uses:
            frameworks["rocket"] = {
                "name": "Rocket",
                "count": len(rocket_uses),
            }
            examples.extend([(r, ln) for r, _, ln in rocket_uses[:3]])

        # Check for Warp
        warp_uses = index.find_uses_matching("warp", limit=50)
        if warp_uses:
            frameworks["warp"] = {
                "name": "Warp",
                "count": len(warp_uses),
            }

        # Check for Poem
        poem_uses = index.find_uses_matching("poem", limit=50)
        if poem_uses:
            frameworks["poem"] = {
                "name": "Poem",
                "count": len(poem_uses),
            }

        # Check for Tide
        tide_uses = index.find_uses_matching("tide", limit=50)
        if tide_uses:
            frameworks["tide"] = {
                "name": "Tide",
                "count": len(tide_uses),
            }

        # Check for common web patterns
        patterns = []

        # Check for tower middleware
        tower_uses = index.find_uses_matching("tower", limit=20)
        if tower_uses:
            patterns.append("Tower middleware")

        # Check for tonic (gRPC)
        tonic_uses = index.find_uses_matching("tonic", limit=20)
        if tonic_uses:
            frameworks["tonic"] = {
                "name": "Tonic (gRPC)",
                "count": len(tonic_uses),
            }
            patterns.append("gRPC")

        # Check for reqwest (HTTP client)
        reqwest_uses = index.find_uses_matching("reqwest", limit=20)
        if reqwest_uses:
            patterns.append("reqwest client")

        # Check for hyper
        hyper_uses = index.find_uses_matching("hyper", limit=20)
        if hyper_uses:
            patterns.append("Hyper")

        if not frameworks:
            return result

        # Determine primary framework
        priority = ["axum", "actix", "rocket", "warp", "poem", "tide", "tonic"]
        primary = None
        for fw in priority:
            if fw in frameworks:
                primary = fw
                break
        if primary is None:
            primary = list(frameworks.keys())[0]

        fw_info = frameworks[primary]
        title = f"Web framework: {fw_info['name']}"
        description = f"Uses {fw_info['name']} web framework."

        if len(frameworks) > 1:
            others = [f["name"] for k, f in frameworks.items() if k != primary]
            description += f" Also: {', '.join(others)}."

        if patterns:
            description += f" With: {', '.join(patterns[:3])}."

        confidence = 0.95

        evidence = []
        for rel_path, line in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="rust.conventions.web_framework",
            category="web",
            title=title,
            description=description,
            confidence=confidence,
            language="rust",
            evidence=evidence,
            stats={
                "frameworks": list(frameworks.keys()),
                "primary_framework": primary,
                "patterns": patterns,
                "framework_details": frameworks,
            },
        ))

        # Detect API routes
        self._detect_api_routes(ctx, index, result)

        return result

    def _detect_api_routes(
        self,
        ctx: DetectorContext,
        index: RustIndex,
        result: DetectorResult,
    ) -> None:
        """Extract API route definitions."""
        # Actix/Rocket attribute macros: #[get("/path")]
        attr_pattern = re.compile(
            r"""#\[(get|post|put|patch|delete)\(\s*"([^"]+)""",
        )
        # Axum .route("/path", get|post|...(...))
        axum_route_pattern = re.compile(
            r"""\.route\(\s*"([^"]+)"\s*,\s*(get|post|put|patch|delete)\b""",
        )
        # Axum chained: .route("/path", get(h).post(h2))
        axum_chained_pattern = re.compile(
            r"""\.route\(\s*"([^"]+)"[^)]*\)""",
        )
        axum_method_in_chain = re.compile(r"""\b(get|post|put|patch|delete)\(""")

        routes: list[dict[str, str | int]] = []
        methods: dict[str, int] = {}

        for rel_path, file_idx in index.files.items():
            if file_idx.role in ("test", "example", "bench"):
                continue

            content = "\n".join(file_idx.lines)

            # Attribute macro routes (Actix-web, Rocket)
            for m in attr_pattern.finditer(content):
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

            # Axum .route() calls
            for m in axum_chained_pattern.finditer(content):
                path = m.group(1)
                line = content[: m.start()].count("\n") + 1
                route_text = m.group(0)

                found_methods = axum_method_in_chain.findall(route_text)
                if found_methods:
                    for method_str in found_methods:
                        method = method_str.upper()
                        methods[method] = methods.get(method, 0) + 1
                        routes.append({
                            "method": method,
                            "path": path,
                            "file": rel_path,
                            "line": line,
                        })
                else:
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
            rule_id="rust.conventions.api_routes",
            category="api",
            title="API routes",
            description=description,
            confidence=0.90,
            language="rust",
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
