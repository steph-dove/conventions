"""Dependency update automation detector."""

from __future__ import annotations

from ...fs import read_file_safe
from ..base import BaseDetector, DetectorContext, DetectorResult
from ..registry import DetectorRegistry


@DetectorRegistry.register
class DependencyUpdatesDetector(BaseDetector):
    """Detect dependency update automation configuration."""

    name = "generic_dependency_updates"
    description = "Detects Dependabot, Renovate, and other dependency update tools"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect dependency update automation."""
        result = DetectorResult()

        tools: dict[str, dict] = {}

        # Dependabot
        dependabot_paths = [
            ctx.repo_root / ".github" / "dependabot.yml",
            ctx.repo_root / ".github" / "dependabot.yaml",
        ]
        for path in dependabot_paths:
            if path.is_file():
                content = read_file_safe(path)
                ecosystems = []
                if content:
                    if "npm" in content:
                        ecosystems.append("npm")
                    if "pip" in content:
                        ecosystems.append("pip")
                    if "gomod" in content:
                        ecosystems.append("gomod")
                    if "cargo" in content:
                        ecosystems.append("cargo")
                    if "docker" in content:
                        ecosystems.append("docker")
                    if "github-actions" in content:
                        ecosystems.append("github-actions")

                tools["dependabot"] = {
                    "name": "Dependabot",
                    "ecosystems": ecosystems,
                }
                break

        # Renovate
        renovate_paths = [
            ctx.repo_root / "renovate.json",
            ctx.repo_root / "renovate.json5",
            ctx.repo_root / ".renovaterc",
            ctx.repo_root / ".renovaterc.json",
            ctx.repo_root / ".github" / "renovate.json",
        ]
        for path in renovate_paths:
            if path.is_file():
                content = read_file_safe(path)
                extends = []
                if content:
                    if "config:base" in content:
                        extends.append("base")
                    if "config:recommended" in content:
                        extends.append("recommended")
                    if "schedule" in content:
                        extends.append("custom schedule")
                    if "automerge" in content:
                        extends.append("automerge")

                tools["renovate"] = {
                    "name": "Renovate",
                    "extends": extends,
                }
                break

        # Snyk
        snyk_file = ctx.repo_root / ".snyk"
        if snyk_file.is_file():
            tools["snyk"] = {
                "name": "Snyk",
            }

        if not tools:
            return result

        tool_names = [t["name"] for t in tools.values()]
        title = f"Dependency updates: {', '.join(tool_names)}"

        descriptions = []
        for tool_id, tool_info in tools.items():
            if tool_id == "dependabot" and tool_info.get("ecosystems"):
                descriptions.append(f"Dependabot for {', '.join(tool_info['ecosystems'])}")
            elif tool_id == "renovate" and tool_info.get("extends"):
                descriptions.append(f"Renovate ({', '.join(tool_info['extends'])})")
            else:
                descriptions.append(tool_info["name"])

        description = f"Automated dependency updates via {'; '.join(descriptions)}."
        confidence = min(0.95, 0.7 + len(tools) * 0.1)

        # Determine primary tool (prefer renovate > dependabot > others)
        primary_tool = None
        for preferred in ["renovate", "dependabot", "snyk"]:
            if preferred in tools:
                primary_tool = preferred
                break

        result.rules.append(self.make_rule(
            rule_id="generic.conventions.dependency_updates",
            category="dependencies",
            title=title,
            description=description,
            confidence=confidence,
            language="generic",
            evidence=[],
            stats={
                "tools": list(tools.keys()),
                "tool_details": tools,
                "primary_tool": primary_tool,
            },
        ))

        return result
