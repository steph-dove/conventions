"""Go CLI framework conventions detector."""

from __future__ import annotations

from ..base import DetectorContext, DetectorResult
from .base import GoDetector
from .index import GoIndex, make_evidence
from ..registry import DetectorRegistry


@DetectorRegistry.register
class GoCLIDetector(GoDetector):
    """Detect Go CLI framework conventions."""

    name = "go_cli"
    description = "Detects Go CLI frameworks (Cobra, urfave/cli, Kong)"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Go CLI framework conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        frameworks: dict[str, dict] = {}
        examples: dict[str, list[tuple[str, int]]] = {}

        # Cobra (most popular)
        cobra_imports = index.find_imports_matching("github.com/spf13/cobra", limit=30)
        if cobra_imports:
            frameworks["cobra"] = {
                "name": "Cobra",
                "import_count": len(cobra_imports),
            }
            examples["cobra"] = [(r, l) for r, _, l in cobra_imports[:5]]

        # urfave/cli
        urfave_imports = index.find_imports_matching("github.com/urfave/cli", limit=30)
        if urfave_imports:
            frameworks["urfave"] = {
                "name": "urfave/cli",
                "import_count": len(urfave_imports),
            }
            examples["urfave"] = [(r, l) for r, _, l in urfave_imports[:5]]

        # Kong
        kong_imports = index.find_imports_matching("github.com/alecthomas/kong", limit=30)
        if kong_imports:
            frameworks["kong"] = {
                "name": "Kong",
                "import_count": len(kong_imports),
            }
            examples["kong"] = [(r, l) for r, _, l in kong_imports[:5]]

        # flag (stdlib)
        flag_imports = index.find_imports_matching("flag", limit=20)
        flag_imports = [i for i in flag_imports if i[1] == "flag"]
        if flag_imports and not frameworks:
            frameworks["flag"] = {
                "name": "flag (stdlib)",
                "import_count": len(flag_imports),
            }
            examples["flag"] = [(r, l) for r, _, l in flag_imports[:5]]

        if not frameworks:
            return result

        framework_names = [f["name"] for f in frameworks.values()]
        primary = max(frameworks, key=lambda k: frameworks[k]["import_count"])

        title = f"CLI framework: {frameworks[primary]['name']}"
        description = f"Uses {frameworks[primary]['name']} for CLI."

        if len(frameworks) > 1:
            others = [f for f in framework_names if f != frameworks[primary]["name"]]
            description += f" Also uses: {', '.join(others)}."

        # Cobra is the standard, gets higher confidence
        if primary == "cobra":
            confidence = 0.95
        elif primary in ("urfave", "kong"):
            confidence = 0.9
        else:
            confidence = 0.8

        evidence = []
        for rel_path, line in examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.cli_framework",
            category="cli",
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
