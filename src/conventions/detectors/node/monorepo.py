"""Node.js monorepo conventions detector."""

from __future__ import annotations

import json
from pathlib import Path

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import NodeDetector


@DetectorRegistry.register
class NodeMonorepoDetector(NodeDetector):
    """Detect Node.js monorepo conventions."""

    name = "node_monorepo"
    description = "Detects monorepo tools (Turborepo, Lerna, Nx, workspaces)"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect monorepo conventions."""
        result = DetectorResult()

        tools: dict[str, dict] = {}

        # Check for Turborepo
        if (ctx.repo_root / "turbo.json").exists():
            tools["turborepo"] = {
                "name": "Turborepo",
                "config_file": "turbo.json",
            }

        # Check for Lerna
        if (ctx.repo_root / "lerna.json").exists():
            tools["lerna"] = {
                "name": "Lerna",
                "config_file": "lerna.json",
            }

        # Check for Nx
        if (ctx.repo_root / "nx.json").exists():
            tools["nx"] = {
                "name": "Nx",
                "config_file": "nx.json",
            }
        elif (ctx.repo_root / "workspace.json").exists():
            tools["nx"] = {
                "name": "Nx",
                "config_file": "workspace.json",
            }

        # Check for Rush
        if (ctx.repo_root / "rush.json").exists():
            tools["rush"] = {
                "name": "Rush",
                "config_file": "rush.json",
            }

        # Check package.json for workspaces
        pkg_json_path = ctx.repo_root / "package.json"
        workspace_patterns = []

        if pkg_json_path.exists():
            try:
                pkg_data = json.loads(pkg_json_path.read_text())

                # npm/yarn workspaces
                workspaces = pkg_data.get("workspaces")
                if workspaces:
                    if isinstance(workspaces, list):
                        workspace_patterns = workspaces
                    elif isinstance(workspaces, dict):
                        workspace_patterns = workspaces.get("packages", [])

                    if not tools:
                        tools["npm_workspaces"] = {
                            "name": "npm/Yarn workspaces",
                            "patterns": workspace_patterns,
                        }
            except (json.JSONDecodeError, OSError):
                pass

        # Check for pnpm workspaces
        pnpm_workspace = ctx.repo_root / "pnpm-workspace.yaml"
        if pnpm_workspace.exists():
            tools["pnpm_workspaces"] = {
                "name": "pnpm workspaces",
                "config_file": "pnpm-workspace.yaml",
            }

        if not tools:
            return result

        # Scan for workspace packages using workspace patterns + well-known dirs
        packages: list[dict] = []
        seen_paths: set[Path] = set()

        # Resolve workspace globs from package.json
        search_dirs: list[Path] = []
        for pattern in workspace_patterns:
            if pattern.endswith("/*"):
                # Glob pattern like "src/*", "packages/*"
                parent = ctx.repo_root / pattern[:-2]
                if parent.is_dir():
                    search_dirs.append(parent)
            else:
                # Exact directory like "server-ts", "cypress"
                exact = ctx.repo_root / pattern
                if exact.is_dir() and (exact / "package.json").is_file():
                    if exact not in seen_paths:
                        seen_paths.add(exact)
                        try:
                            pkg_data = json.loads((exact / "package.json").read_text())
                            packages.append({
                                "name": pkg_data.get("name", exact.name),
                                "path": str(exact.relative_to(ctx.repo_root)),
                                "private": pkg_data.get("private", False),
                            })
                        except (json.JSONDecodeError, OSError):
                            packages.append({
                                "name": exact.name,
                                "path": str(exact.relative_to(ctx.repo_root)),
                            })

        # Also check well-known monorepo dirs as fallback
        for dirname in ["packages", "apps"]:
            d = ctx.repo_root / dirname
            if d.is_dir() and d not in search_dirs:
                search_dirs.append(d)

        for search_dir in search_dirs:
            for item in sorted(search_dir.iterdir()):
                pkg_json = item / "package.json"
                if item.is_dir() and pkg_json.exists() and item not in seen_paths:
                    seen_paths.add(item)
                    try:
                        pkg_data = json.loads(pkg_json.read_text())
                        packages.append({
                            "name": pkg_data.get("name", item.name),
                            "path": str(item.relative_to(ctx.repo_root)),
                            "private": pkg_data.get("private", False),
                        })
                    except (json.JSONDecodeError, OSError):
                        packages.append({
                            "name": item.name,
                            "path": str(item.relative_to(ctx.repo_root)),
                        })

        package_count = len(packages)

        [t["name"] for t in tools.values()]
        primary = list(tools.keys())[0]

        title = f"Monorepo: {tools[primary]['name']}"
        description = f"Uses {tools[primary]['name']} for monorepo management."

        if package_count > 0:
            description += f" {package_count} package(s) detected."

        if len(tools) > 1:
            others = [t["name"] for k, t in tools.items() if k != primary]
            description += f" Also uses: {', '.join(others)}."

        confidence = 0.95

        result.rules.append(self.make_rule(
            rule_id="node.conventions.monorepo",
            category="architecture",
            title=title,
            description=description,
            confidence=confidence,
            language="javascript",
            evidence=[],
            stats={
                "tools": list(tools.keys()),
                "primary_tool": primary,
                "package_count": package_count,
                "packages": packages,
                "workspace_patterns": workspace_patterns,
                "tool_details": tools,
            },
        ))

        return result
