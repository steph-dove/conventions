"""Python CLI patterns detector."""

from __future__ import annotations

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from .index import make_evidence


@DetectorRegistry.register
class PythonCLIPatternDetector(PythonDetector):
    """Detect Python CLI framework patterns."""

    name = "python_cli_patterns"
    description = "Detects Python CLI frameworks (click, typer, argparse)"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Python CLI framework patterns."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        frameworks: dict[str, dict] = {}
        examples: dict[str, list[tuple[str, int]]] = {}

        # Typer (modern, type-hinted)
        typer_imports = index.find_imports_matching("typer", limit=20)
        if typer_imports:
            frameworks["typer"] = {
                "name": "Typer",
                "import_count": len(typer_imports),
            }
            examples["typer"] = [(rel_path, imp.line) for rel_path, imp in typer_imports[:5]]

        # Click
        click_imports = index.find_imports_matching("click", limit=20)
        if click_imports:
            frameworks["click"] = {
                "name": "Click",
                "import_count": len(click_imports),
            }
            examples["click"] = [(rel_path, imp.line) for rel_path, imp in click_imports[:5]]

        # argparse (stdlib)
        argparse_imports = index.find_imports_matching("argparse", limit=20)
        if argparse_imports:
            frameworks["argparse"] = {
                "name": "argparse",
                "import_count": len(argparse_imports),
            }
            examples["argparse"] = [(rel_path, imp.line) for rel_path, imp in argparse_imports[:5]]

        # Fire (Google)
        fire_imports = index.find_imports_matching("fire", limit=20)
        if fire_imports:
            frameworks["fire"] = {
                "name": "Python Fire",
                "import_count": len(fire_imports),
            }
            examples["fire"] = [(rel_path, imp.line) for rel_path, imp in fire_imports[:5]]

        # docopt
        docopt_imports = index.find_imports_matching("docopt", limit=20)
        if docopt_imports:
            frameworks["docopt"] = {
                "name": "docopt",
                "import_count": len(docopt_imports),
            }
            examples["docopt"] = [(rel_path, imp.line) for rel_path, imp in docopt_imports[:5]]

        if not frameworks:
            return result

        framework_names = [f["name"] for f in frameworks.values()]
        primary = max(frameworks, key=lambda k: frameworks[k]["import_count"])

        title = f"CLI framework: {frameworks[primary]['name']}"
        description = f"Uses {frameworks[primary]['name']} for CLI."
        if len(frameworks) > 1:
            others = [f for f in framework_names if f != frameworks[primary]["name"]]
            description += f" Also uses: {', '.join(others)}."

        # Modern frameworks get higher confidence
        if primary in ("typer", "click"):
            confidence = 0.9
        else:
            confidence = 0.8

        evidence = []
        for file_path, line in examples.get(primary, [])[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, file_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="python.conventions.cli_framework",
            category="cli",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=evidence,
            stats={
                "frameworks": list(frameworks.keys()),
                "primary_framework": primary,
                "framework_details": frameworks,
            },
        ))

        return result
