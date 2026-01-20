"""Rust web framework conventions detector."""

from __future__ import annotations

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import RustDetector
from .index import make_evidence


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

        return result
