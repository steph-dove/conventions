"""Node.js build tools conventions detector."""

from __future__ import annotations

import json

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import NodeDetector


@DetectorRegistry.register
class NodeBuildToolsDetector(NodeDetector):
    """Detect Node.js build tools conventions."""

    name = "node_build_tools"
    description = "Detects build tools (Vite, webpack, esbuild, Rollup, Parcel, SWC)"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect build tool conventions."""
        result = DetectorResult()
        self.get_index(ctx)

        tools: dict[str, dict] = {}

        # Check for Vite
        if (ctx.repo_root / "vite.config.js").exists() or \
           (ctx.repo_root / "vite.config.ts").exists() or \
           (ctx.repo_root / "vite.config.mjs").exists():
            tools["vite"] = {"name": "Vite", "config": True}

        # Check for webpack
        webpack_configs = [
            "webpack.config.js",
            "webpack.config.ts",
            "webpack.config.mjs",
            "webpack.common.js",
            "webpack.prod.js",
            "webpack.dev.js",
        ]
        for config in webpack_configs:
            if (ctx.repo_root / config).exists():
                tools["webpack"] = {"name": "webpack", "config": config}
                break

        # Check for esbuild
        esbuild_configs = [
            "esbuild.config.js",
            "esbuild.config.mjs",
        ]
        for config in esbuild_configs:
            if (ctx.repo_root / config).exists():
                tools["esbuild"] = {"name": "esbuild", "config": config}
                break

        # Check for Rollup
        rollup_configs = [
            "rollup.config.js",
            "rollup.config.ts",
            "rollup.config.mjs",
        ]
        for config in rollup_configs:
            if (ctx.repo_root / config).exists():
                tools["rollup"] = {"name": "Rollup", "config": config}
                break

        # Check for Parcel
        if (ctx.repo_root / ".parcelrc").exists():
            tools["parcel"] = {"name": "Parcel", "config": ".parcelrc"}

        # Check for SWC
        if (ctx.repo_root / ".swcrc").exists():
            tools["swc"] = {"name": "SWC", "config": ".swcrc"}

        # Check for tsup (esbuild-based bundler for TypeScript)
        if (ctx.repo_root / "tsup.config.ts").exists() or \
           (ctx.repo_root / "tsup.config.js").exists():
            tools["tsup"] = {"name": "tsup", "config": True}

        # Check for unbuild (Nuxt's bundler)
        if (ctx.repo_root / "build.config.ts").exists():
            tools["unbuild"] = {"name": "unbuild", "config": "build.config.ts"}

        # Check package.json for build tools in dependencies/devDependencies
        pkg_json_path = ctx.repo_root / "package.json"
        if pkg_json_path.exists():
            try:
                pkg_data = json.loads(pkg_json_path.read_text())
                all_deps = {
                    **pkg_data.get("dependencies", {}),
                    **pkg_data.get("devDependencies", {}),
                }

                if "vite" in all_deps and "vite" not in tools:
                    tools["vite"] = {"name": "Vite", "in_deps": True}

                if "webpack" in all_deps and "webpack" not in tools:
                    tools["webpack"] = {"name": "webpack", "in_deps": True}

                if "esbuild" in all_deps and "esbuild" not in tools:
                    tools["esbuild"] = {"name": "esbuild", "in_deps": True}

                if "rollup" in all_deps and "rollup" not in tools:
                    tools["rollup"] = {"name": "Rollup", "in_deps": True}

                if "parcel" in all_deps and "parcel" not in tools:
                    tools["parcel"] = {"name": "Parcel", "in_deps": True}

                if "@swc/core" in all_deps and "swc" not in tools:
                    tools["swc"] = {"name": "SWC", "in_deps": True}

                if "tsup" in all_deps and "tsup" not in tools:
                    tools["tsup"] = {"name": "tsup", "in_deps": True}

            except (json.JSONDecodeError, OSError):
                pass

        if not tools:
            return result

        # Determine primary (by typical preference order)
        priority_order = ["vite", "webpack", "rollup", "esbuild", "parcel", "tsup", "swc", "unbuild"]
        primary = None
        for tool in priority_order:
            if tool in tools:
                primary = tool
                break
        if primary is None:
            primary = list(tools.keys())[0]

        [t["name"] for t in tools.values()]
        title = f"Build tool: {tools[primary]['name']}"
        description = f"Uses {tools[primary]['name']} for building/bundling."

        if len(tools) > 1:
            others = [t["name"] for k, t in tools.items() if k != primary]
            description += f" Also uses: {', '.join(others)}."

        # Higher confidence if config exists
        if tools[primary].get("config"):
            confidence = 0.95
        else:
            confidence = 0.85

        result.rules.append(self.make_rule(
            rule_id="node.conventions.build_tools",
            category="tooling",
            title=title,
            description=description,
            confidence=confidence,
            language="javascript",
            evidence=[],
            stats={
                "tools": list(tools.keys()),
                "primary_tool": primary,
                "tool_details": tools,
            },
        ))

        return result
