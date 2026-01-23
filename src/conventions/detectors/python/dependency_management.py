"""Python dependency management conventions detector."""

from __future__ import annotations

from pathlib import Path

from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry
from ...fs import read_file_safe


@DetectorRegistry.register
class PythonDependencyManagementDetector(PythonDetector):
    """Detect Python dependency management conventions."""

    name = "python_dependency_management"
    description = "Detects Python dependency management tools (poetry, pip-tools, uv)"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Python dependency management conventions."""
        result = DetectorResult()

        tools: dict[str, dict] = {}

        # Poetry
        pyproject = ctx.repo_root / "pyproject.toml"
        poetry_lock = ctx.repo_root / "poetry.lock"
        if pyproject.is_file():
            content = read_file_safe(pyproject)
            if content and "[tool.poetry]" in content:
                has_lock = poetry_lock.is_file()
                tools["poetry"] = {
                    "name": "Poetry",
                    "config_file": "pyproject.toml",
                    "has_lock": has_lock,
                }

        # pip-tools (requirements.in -> requirements.txt)
        requirements_in = ctx.repo_root / "requirements.in"
        requirements_txt = ctx.repo_root / "requirements.txt"
        if requirements_in.is_file():
            tools["pip_tools"] = {
                "name": "pip-tools",
                "has_compiled": requirements_txt.is_file(),
            }

        # uv
        uv_lock = ctx.repo_root / "uv.lock"
        if uv_lock.is_file():
            tools["uv"] = {
                "name": "uv",
                "has_lock": True,
            }

        # PDM
        pdm_lock = ctx.repo_root / "pdm.lock"
        if pdm_lock.is_file():
            tools["pdm"] = {
                "name": "PDM",
                "has_lock": True,
            }

        # Pipenv
        pipfile = ctx.repo_root / "Pipfile"
        pipfile_lock = ctx.repo_root / "Pipfile.lock"
        if pipfile.is_file():
            tools["pipenv"] = {
                "name": "Pipenv",
                "has_lock": pipfile_lock.is_file(),
            }

        # Hatch
        if pyproject.is_file():
            content = read_file_safe(pyproject)
            if content and "[tool.hatch]" in content:
                tools["hatch"] = {
                    "name": "Hatch",
                    "config_file": "pyproject.toml",
                }

        # Basic requirements.txt (no tool)
        if not tools and requirements_txt.is_file():
            content = read_file_safe(requirements_txt)
            pinned = 0
            unpinned = 0
            if content:
                for line in content.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith("-"):
                        continue
                    if "==" in line:
                        pinned += 1
                    else:
                        unpinned += 1

            tools["pip"] = {
                "name": "pip (requirements.txt)",
                "pinned_deps": pinned,
                "unpinned_deps": unpinned,
            }

        if not tools:
            return result

        tool_names = [t["name"] for t in tools.values()]
        primary = list(tools.keys())[0]

        title = f"Dependency management: {', '.join(tool_names)}"

        descriptions = []
        for tool_id, tool_info in tools.items():
            if tool_info.get("has_lock"):
                descriptions.append(f"{tool_info['name']} with lock file")
            elif tool_info.get("has_compiled"):
                descriptions.append(f"{tool_info['name']} (compiled)")
            else:
                descriptions.append(tool_info["name"])

        description = f"Uses {', '.join(descriptions)} for dependencies."

        # Modern tools get higher confidence
        if primary in ("poetry", "uv", "pdm"):
            confidence = 0.95
        elif primary in ("pip_tools", "hatch"):
            confidence = 0.85
        else:
            confidence = 0.7

        result.rules.append(self.make_rule(
            rule_id="python.conventions.dependency_management",
            category="dependencies",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=[],
            stats={
                "tools": list(tools.keys()),
                "primary_tool": primary,
                "tool_details": tools,
            },
        ))

        return result
