"""Go dependency injection conventions detector."""

from __future__ import annotations

from ..base import DetectorContext, DetectorResult
from .base import GoDetector
from .index import GoIndex, make_evidence
from ..registry import DetectorRegistry


@DetectorRegistry.register
class GoDIDetector(GoDetector):
    """Detect Go dependency injection conventions."""

    name = "go_di"
    description = "Detects Go DI frameworks (Wire, Fx, dig)"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Go DI conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        frameworks: dict[str, dict] = {}
        examples: dict[str, list[tuple[str, int]]] = {}

        # Google Wire
        wire_imports = index.find_imports_matching("github.com/google/wire", limit=30)
        if wire_imports:
            frameworks["wire"] = {
                "name": "Wire",
                "import_count": len(wire_imports),
                "style": "compile-time",
            }
            examples["wire"] = [(r, l) for r, _, l in wire_imports[:5]]

        # Uber Fx
        fx_imports = index.find_imports_matching("go.uber.org/fx", limit=30)
        if fx_imports:
            frameworks["fx"] = {
                "name": "Uber Fx",
                "import_count": len(fx_imports),
                "style": "runtime",
            }
            examples["fx"] = [(r, l) for r, _, l in fx_imports[:5]]

        # Uber dig
        dig_imports = index.find_imports_matching("go.uber.org/dig", limit=30)
        if dig_imports:
            frameworks["dig"] = {
                "name": "dig",
                "import_count": len(dig_imports),
                "style": "runtime",
            }
            examples["dig"] = [(r, l) for r, _, l in dig_imports[:5]]

        # samber/do
        do_imports = index.find_imports_matching("github.com/samber/do", limit=30)
        if do_imports:
            frameworks["do"] = {
                "name": "samber/do",
                "import_count": len(do_imports),
                "style": "runtime",
            }
            examples["do"] = [(r, l) for r, _, l in do_imports[:5]]

        if not frameworks:
            return result

        framework_names = [f["name"] for f in frameworks.values()]
        primary = max(frameworks, key=lambda k: frameworks[k]["import_count"])

        style = frameworks[primary].get("style", "")
        title = f"DI framework: {frameworks[primary]['name']}"
        description = f"Uses {frameworks[primary]['name']} for dependency injection."
        if style:
            description += f" ({style})"

        if len(frameworks) > 1:
            others = [f for f in framework_names if f != frameworks[primary]["name"]]
            description += f" Also uses: {', '.join(others)}."

        # Wire is compile-time safe, gets higher confidence
        if primary == "wire":
            confidence = 0.95
        else:
            confidence = 0.9

        evidence = []
        for rel_path, line in examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.di_framework",
            category="patterns",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "frameworks": list(frameworks.keys()),
                "primary_framework": primary,
                "framework_details": frameworks,
            },
        ))

        return result
