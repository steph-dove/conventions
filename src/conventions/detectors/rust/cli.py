"""Rust CLI framework conventions detector."""

from __future__ import annotations

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import RustDetector
from .index import make_evidence


@DetectorRegistry.register
class RustCLIDetector(RustDetector):
    """Detect Rust CLI framework conventions."""

    name = "rust_cli"
    description = "Detects CLI frameworks (clap, structopt, argh)"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect CLI framework conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        frameworks: dict[str, dict] = {}
        examples: list[tuple[str, int]] = []

        # Check for clap
        clap_uses = index.find_uses_matching("clap", limit=30)
        if clap_uses:
            frameworks["clap"] = {
                "name": "clap",
                "count": len(clap_uses),
            }
            examples.extend([(r, ln) for r, _, ln in clap_uses[:3]])

            # Check for derive macro usage
            derive_parser = index.search_pattern(r"#\[derive\([^)]*Parser", limit=10)
            if derive_parser:
                frameworks["clap"]["derive"] = True

        # Check for structopt (deprecated in favor of clap derive)
        structopt_uses = index.find_uses_matching("structopt", limit=30)
        if structopt_uses:
            frameworks["structopt"] = {
                "name": "structopt",
                "count": len(structopt_uses),
                "deprecated": True,
            }

        # Check for argh
        argh_uses = index.find_uses_matching("argh", limit=30)
        if argh_uses:
            frameworks["argh"] = {
                "name": "argh",
                "count": len(argh_uses),
            }

        # Check for pico-args
        pico_uses = index.find_uses_matching("pico_args", limit=30)
        if pico_uses:
            frameworks["pico_args"] = {
                "name": "pico-args",
                "count": len(pico_uses),
            }

        # Check for bpaf
        bpaf_uses = index.find_uses_matching("bpaf", limit=30)
        if bpaf_uses:
            frameworks["bpaf"] = {
                "name": "bpaf",
                "count": len(bpaf_uses),
            }

        # Check for CLI-related crates
        features = []

        # Check for indicatif (progress bars)
        indicatif_uses = index.find_uses_matching("indicatif", limit=10)
        if indicatif_uses:
            features.append("progress bars")

        # Check for dialoguer (prompts)
        dialoguer_uses = index.find_uses_matching("dialoguer", limit=10)
        if dialoguer_uses:
            features.append("interactive prompts")

        # Check for console (styling)
        console_uses = index.find_uses_matching("console", limit=10)
        if console_uses:
            features.append("console styling")

        # Check for colored
        colored_uses = index.find_uses_matching("colored", limit=10)
        if colored_uses:
            features.append("colored output")

        # Check for termcolor
        termcolor_uses = index.find_uses_matching("termcolor", limit=10)
        if termcolor_uses:
            features.append("terminal colors")

        # Check for comfy-table
        table_uses = index.find_uses_matching("comfy_table", limit=10)
        if not table_uses:
            table_uses = index.find_uses_matching("cli_table", limit=10)
        if table_uses:
            features.append("table output")

        if not frameworks:
            return result

        # Determine primary
        priority = ["clap", "structopt", "argh", "bpaf", "pico_args"]
        primary = None
        for fw in priority:
            if fw in frameworks:
                primary = fw
                break
        if primary is None:
            primary = list(frameworks.keys())[0]

        fw_info = frameworks[primary]
        title = f"CLI framework: {fw_info['name']}"
        description = f"Uses {fw_info['name']} for CLI argument parsing."

        if fw_info.get("derive"):
            description += " Uses derive macros."

        if fw_info.get("deprecated"):
            description += " (Consider migrating to clap.)"

        if features:
            description += f" Features: {', '.join(features[:3])}."

        confidence = 0.95

        evidence = []
        for rel_path, line in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="rust.conventions.cli_framework",
            category="cli",
            title=title,
            description=description,
            confidence=confidence,
            language="rust",
            evidence=evidence,
            stats={
                "frameworks": list(frameworks.keys()),
                "primary_framework": primary,
                "features": features,
                "framework_details": frameworks,
            },
        ))

        return result
