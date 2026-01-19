"""Node.js package manager conventions detector."""

from __future__ import annotations

import json
from pathlib import Path

from ..base import DetectorContext, DetectorResult
from .base import NodeDetector
from ..registry import DetectorRegistry


@DetectorRegistry.register
class NodePackageManagerDetector(NodeDetector):
    """Detect Node.js package manager conventions."""

    name = "node_package_manager"
    description = "Detects npm, yarn, pnpm, or bun usage"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect package manager conventions."""
        result = DetectorResult()

        managers: dict[str, dict] = {}

        # Check for lockfiles
        if (ctx.repo_root / "package-lock.json").exists():
            managers["npm"] = {
                "name": "npm",
                "lockfile": "package-lock.json",
            }

        if (ctx.repo_root / "yarn.lock").exists():
            managers["yarn"] = {
                "name": "Yarn",
                "lockfile": "yarn.lock",
            }
            # Check for Yarn version
            if (ctx.repo_root / ".yarnrc.yml").exists():
                managers["yarn"]["version"] = "berry (2+)"
            elif (ctx.repo_root / ".yarnrc").exists():
                managers["yarn"]["version"] = "classic (1.x)"

        if (ctx.repo_root / "pnpm-lock.yaml").exists():
            managers["pnpm"] = {
                "name": "pnpm",
                "lockfile": "pnpm-lock.yaml",
            }

        if (ctx.repo_root / "bun.lockb").exists():
            managers["bun"] = {
                "name": "Bun",
                "lockfile": "bun.lockb",
            }

        # Check package.json for packageManager field
        pkg_json_path = ctx.repo_root / "package.json"
        if pkg_json_path.exists():
            try:
                pkg_data = json.loads(pkg_json_path.read_text())
                if "packageManager" in pkg_data:
                    pm_spec = pkg_data["packageManager"]
                    if pm_spec.startswith("npm"):
                        if "npm" not in managers:
                            managers["npm"] = {"name": "npm"}
                        managers["npm"]["corepack"] = True
                    elif pm_spec.startswith("yarn"):
                        if "yarn" not in managers:
                            managers["yarn"] = {"name": "Yarn"}
                        managers["yarn"]["corepack"] = True
                    elif pm_spec.startswith("pnpm"):
                        if "pnpm" not in managers:
                            managers["pnpm"] = {"name": "pnpm"}
                        managers["pnpm"]["corepack"] = True
            except (json.JSONDecodeError, OSError):
                pass

        # Check for engine restrictions
        if pkg_json_path.exists():
            try:
                pkg_data = json.loads(pkg_json_path.read_text())
                engines = pkg_data.get("engines", {})
                for key in managers:
                    if key in engines:
                        managers[key]["engine_constraint"] = engines[key]
            except (json.JSONDecodeError, OSError):
                pass

        if not managers:
            # Default to npm if package.json exists
            if pkg_json_path.exists():
                managers["npm"] = {"name": "npm", "inferred": True}
            else:
                return result

        # Determine primary manager
        # Prefer explicit lockfiles over inferred
        if len(managers) == 1:
            primary = list(managers.keys())[0]
        else:
            # If multiple, prefer the one that's not inferred
            for key in ["pnpm", "yarn", "bun", "npm"]:
                if key in managers and not managers[key].get("inferred"):
                    primary = key
                    break
            else:
                primary = list(managers.keys())[0]

        pm_info = managers[primary]
        title = f"Package manager: {pm_info['name']}"
        description = f"Uses {pm_info['name']} for dependency management."

        if pm_info.get("version"):
            description += f" Version: {pm_info['version']}."

        if pm_info.get("corepack"):
            description += " Uses Corepack for version management."

        if len(managers) > 1:
            others = [m["name"] for k, m in managers.items() if k != primary]
            description += f" Also detected: {', '.join(others)}."

        confidence = 0.95
        if pm_info.get("inferred"):
            confidence = 0.6

        result.rules.append(self.make_rule(
            rule_id="node.conventions.package_manager",
            category="tooling",
            title=title,
            description=description,
            confidence=confidence,
            language="javascript",
            evidence=[],
            stats={
                "managers": list(managers.keys()),
                "primary_manager": primary,
                "manager_details": managers,
            },
        ))

        return result
