"""Node.js code generation and scaffolding conventions detector."""

from __future__ import annotations

import json

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import NodeDetector
from .index import make_evidence


@DetectorRegistry.register
class NodeCodeGenDetector(NodeDetector):
    """Detect Node.js code generation and scaffolding conventions."""

    name = "node_codegen"
    description = "Detects code generation tools and marker comment patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect code generation conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        # Detect scaffolding tools
        self._detect_scaffolding_tools(ctx, index, result)

        # Detect marker comment patterns
        self._detect_marker_comments(ctx, index, result)

        return result

    def _detect_scaffolding_tools(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect scaffolding tools (Plop, Hygen, etc.)."""
        tools: dict[str, dict] = {}

        pkg_json_path = ctx.repo_root / "package.json"
        all_deps = {}
        if pkg_json_path.exists():
            try:
                pkg_data = json.loads(pkg_json_path.read_text())
                all_deps = {
                    **pkg_data.get("dependencies", {}),
                    **pkg_data.get("devDependencies", {}),
                }
            except (json.JSONDecodeError, OSError):
                pass

        # Plop
        if "plop" in all_deps:
            tools["plop"] = {"name": "Plop"}
            # Check for plopfile
            for plopfile in ["plopfile.js", "plopfile.ts", "plopfile.mjs"]:
                if (ctx.repo_root / plopfile).exists():
                    tools["plop"]["config"] = plopfile
                    break

        # Hygen
        if "hygen" in all_deps:
            tools["hygen"] = {"name": "Hygen"}
            # Check for _templates directory
            if (ctx.repo_root / "_templates").is_dir():
                tools["hygen"]["templates_dir"] = "_templates"

        # Yeoman
        if "yo" in all_deps or "yeoman-generator" in all_deps:
            tools["yeoman"] = {"name": "Yeoman"}

        # Nx generators
        if "@nx/devkit" in all_deps or "@nrwl/devkit" in all_deps:
            tools["nx_generators"] = {"name": "Nx Generators"}

        # Angular schematics
        if "@angular-devkit/schematics" in all_deps:
            tools["schematics"] = {"name": "Angular Schematics"}

        # Check for templates/ or plop-templates/ directory
        templates_dirs = []
        for template_dir in ["templates", "plop-templates", "generators", "_templates"]:
            if (ctx.repo_root / template_dir).is_dir():
                templates_dirs.append(template_dir)

        if not tools and not templates_dirs:
            return

        if tools:
            primary = list(tools.keys())[0]
            tool_info = tools[primary]
            title = f"Code generation: {tool_info['name']}"
            description = f"Uses {tool_info['name']} for code scaffolding."
            if tool_info.get("config"):
                description += f" Config: {tool_info['config']}."
        else:
            title = "Code templates"
            description = f"Has template directories: {', '.join(templates_dirs)}."

        if templates_dirs:
            description += f" Template dirs: {', '.join(templates_dirs)}."

        confidence = 0.9

        result.rules.append(self.make_rule(
            rule_id="node.conventions.code_generation",
            category="tooling",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=[],
            stats={
                "tools": list(tools.keys()),
                "tool_details": tools,
                "template_directories": templates_dirs,
            },
        ))

    def _detect_marker_comments(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
    ) -> None:
        """Detect marker comment patterns for code generation."""
        # Common marker patterns:
        # /* IMPORT_SERVICE */ or /* ADD_IMPORT_HERE */
        # // @plop-import or // @hygen-import
        # <!-- inject:service --> or <!-- endinject -->

        marker_patterns = [
            # Plop-style markers
            (r'/\*\s*(?:IMPORT|ADD|INSERT|INJECT)_\w+\s*\*/', "injection markers"),
            # Inline markers with @
            (r'//\s*@(?:plop|hygen|inject|codegen)-\w+', "codegen markers"),
            # HTML/JSX injection markers
            (r'<!--\s*inject:\w+\s*-->', "HTML injection markers"),
            # Generic TODO-style markers for generation
            (r'//\s*TODO:\s*(?:GENERATE|INSERT|ADD)\s+\w+', "TODO generation markers"),
        ]

        all_matches: list[tuple[str, int, str]] = []
        marker_types: set[str] = set()

        for pattern, marker_type in marker_patterns:
            matches = index.search_pattern(pattern, limit=20, exclude_tests=True)
            if matches:
                all_matches.extend(matches)
                marker_types.add(marker_type)

        if len(all_matches) < 2:
            return

        title = "Code generation markers"
        description = (
            f"Uses marker comments for code generation injection points. "
            f"Found {len(all_matches)} markers. Types: {', '.join(marker_types)}."
        )
        confidence = min(0.85, 0.6 + len(all_matches) * 0.05)

        evidence = []
        for rel_path, line, _ in all_matches[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=2)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.codegen_markers",
            category="tooling",
            title=title,
            description=description,
            confidence=confidence,
            language="node",
            evidence=evidence,
            stats={
                "marker_count": len(all_matches),
                "marker_types": list(marker_types),
            },
        ))
