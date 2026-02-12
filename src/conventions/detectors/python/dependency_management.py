"""Python dependency management conventions detector."""

from __future__ import annotations

import re

from ...fs import read_file_safe
from ..base import DetectorContext, DetectorResult, PythonDetector
from ..registry import DetectorRegistry


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

        # Detect lock file separately
        self._detect_lock_file(ctx, tools, result)

        # Detect dependency health
        self._detect_dependency_health(ctx, result)

        # Detect src-layout / import path
        self._detect_src_layout(ctx, result)

        return result

    def _detect_lock_file(
        self,
        ctx: DetectorContext,
        tools: dict[str, dict],
        result: DetectorResult,
    ) -> None:
        """Detect lock file presence and type."""
        lock_files: dict[str, dict] = {}

        # uv.lock (modern, fast)
        uv_lock = ctx.repo_root / "uv.lock"
        if uv_lock.is_file():
            lock_files["uv"] = {
                "name": "uv.lock",
                "tool": "uv",
            }

        # poetry.lock
        poetry_lock = ctx.repo_root / "poetry.lock"
        if poetry_lock.is_file():
            lock_files["poetry"] = {
                "name": "poetry.lock",
                "tool": "poetry",
            }

        # pdm.lock
        pdm_lock = ctx.repo_root / "pdm.lock"
        if pdm_lock.is_file():
            lock_files["pdm"] = {
                "name": "pdm.lock",
                "tool": "pdm",
            }

        # Pipfile.lock
        pipfile_lock = ctx.repo_root / "Pipfile.lock"
        if pipfile_lock.is_file():
            lock_files["pipenv"] = {
                "name": "Pipfile.lock",
                "tool": "pipenv",
            }

        # requirements.txt with hashes (pip-compile style)
        requirements_txt = ctx.repo_root / "requirements.txt"
        if requirements_txt.is_file() and not lock_files:
            content = read_file_safe(requirements_txt)
            if content:
                # Check if it has hashes (pip-compile output)
                has_hashes = "--hash=sha256:" in content
                # Check if versions are pinned
                lines = [ln for ln in content.splitlines() if ln.strip() and not ln.startswith("#") and not ln.startswith("-")]
                pinned = sum(1 for ln in lines if "==" in ln)
                total = len(lines)

                if has_hashes:
                    lock_files["pip_hashes"] = {
                        "name": "requirements.txt (hashed)",
                        "tool": "pip-tools",
                        "pinned_ratio": pinned / total if total else 0,
                    }
                elif total > 0 and pinned == total:
                    lock_files["pip_pinned"] = {
                        "name": "requirements.txt (pinned)",
                        "tool": "pip",
                        "pinned_ratio": 1.0,
                    }
                elif total > 0 and pinned / total >= 0.8:
                    lock_files["pip_mostly_pinned"] = {
                        "name": "requirements.txt (mostly pinned)",
                        "tool": "pip",
                        "pinned_ratio": pinned / total,
                    }

        # If no lock file found, check if there's dependency usage
        has_deps = bool(tools) or (ctx.repo_root / "requirements.txt").is_file()
        if not lock_files and not has_deps:
            return  # No dependencies to lock

        if lock_files:
            primary = list(lock_files.keys())[0]
            lock_info = lock_files[primary]

            title = f"Lock file: {lock_info['name']}"
            description = f"Dependencies locked with {lock_info['name']}."

            if primary in ("uv", "poetry"):
                quality = "modern"
                confidence = 0.95
            elif primary in ("pdm", "pipenv", "pip_hashes"):
                quality = "good"
                confidence = 0.9
            elif primary == "pip_pinned":
                quality = "basic"
                confidence = 0.8
            else:
                quality = "partial"
                confidence = 0.7
        else:
            # No lock file but has dependencies
            title = "No lock file"
            description = "Dependencies found but no lock file for reproducibility."
            quality = "none"
            confidence = 0.85
            primary = "none"

        result.rules.append(self.make_rule(
            rule_id="python.conventions.lock_file",
            category="dependencies",
            title=title,
            description=description,
            confidence=confidence,
            language="python",
            evidence=[],
            stats={
                "lock_files": {k: v["name"] for k, v in lock_files.items()},
                "primary_lock": primary,
                "quality": quality if lock_files else "none",
                "has_lock": bool(lock_files),
            },
        ))

    def _detect_dependency_health(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Analyze dependency pinning strategy."""
        exact_count = 0  # ==
        compatible_count = 0  # ~=
        minimum_count = 0  # >=
        unpinned_count = 0
        total = 0

        # Check requirements.txt
        req_txt = ctx.repo_root / "requirements.txt"
        if req_txt.is_file():
            content = read_file_safe(req_txt)
            if content:
                for line in content.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith("-"):
                        continue
                    total += 1
                    if "==" in line:
                        exact_count += 1
                    elif "~=" in line:
                        compatible_count += 1
                    elif ">=" in line:
                        minimum_count += 1
                    else:
                        unpinned_count += 1

        # Check pyproject.toml [project.dependencies]
        pyproject = ctx.repo_root / "pyproject.toml"
        if pyproject.is_file():
            content = read_file_safe(pyproject)
            if content:
                # Simple regex to find dependencies list
                dep_match = re.search(
                    r'\[project\]\s*(?:.*?\n)*?dependencies\s*=\s*\[(.*?)\]',
                    content,
                    re.DOTALL,
                )
                if dep_match:
                    for line in dep_match.group(1).splitlines():
                        line = line.strip().strip(',').strip('"').strip("'")
                        if not line or line.startswith("#"):
                            continue
                        total += 1
                        if "==" in line:
                            exact_count += 1
                        elif "~=" in line:
                            compatible_count += 1
                        elif ">=" in line:
                            minimum_count += 1
                        else:
                            unpinned_count += 1

        if total == 0:
            return

        # Determine pinning strategy
        counts = {
            "exact": exact_count,
            "compatible": compatible_count,
            "minimum": minimum_count,
            "unpinned": unpinned_count,
        }
        pinning_strategy = max(counts, key=counts.get)  # type: ignore[arg-type]

        has_lock_file = any(
            (ctx.repo_root / lf).is_file()
            for lf in ("poetry.lock", "uv.lock", "pdm.lock", "Pipfile.lock")
        )

        parts = [f"{total} deps"]
        parts.append(f"pinning: {pinning_strategy} ({counts[pinning_strategy]}/{total})")
        if has_lock_file:
            parts.append("lock file present")

        description = f"Dependency health: {'; '.join(parts)}."

        result.rules.append(self.make_rule(
            rule_id="python.conventions.dependency_health",
            category="dependencies",
            title="Dependency health",
            description=description,
            confidence=0.85,
            language="python",
            evidence=[],
            stats={
                "total_deps": total,
                "exact_count": exact_count,
                "compatible_count": compatible_count,
                "minimum_count": minimum_count,
                "unpinned_count": unpinned_count,
                "pinning_strategy": pinning_strategy,
                "has_lock_file": has_lock_file,
            },
        ))

    def _detect_src_layout(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Detect src-layout vs flat-layout and import path."""
        src_dir = ctx.repo_root / "src"
        layout = "flat"
        package_name = None

        if src_dir.is_dir():
            # Check if src/ contains a Python package
            for item in src_dir.iterdir():
                if item.is_dir() and (item / "__init__.py").is_file():
                    layout = "src"
                    package_name = item.name
                    break

        # Also check pyproject.toml for explicit configuration
        pyproject = ctx.repo_root / "pyproject.toml"
        if pyproject.is_file():
            content = read_file_safe(pyproject)
            if content:
                # setuptools src layout
                if 'where = ["src"]' in content or "where = ['src']" in content:
                    layout = "src"
                # poetry packages
                if 'from = "src"' in content or "from = 'src'" in content:
                    layout = "src"
                # Try to find package name from pyproject
                if not package_name:
                    name_match = re.search(r'^name\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
                    if name_match:
                        package_name = name_match.group(1).replace("-", "_")

        if not package_name:
            # Try to find any top-level package
            for item in ctx.repo_root.iterdir():
                if item.is_dir() and (item / "__init__.py").is_file():
                    if item.name not in ("tests", "test", "docs", "scripts", "bin"):
                        package_name = item.name
                        break

        if not package_name:
            return

        desc = f"Python {layout}-layout. Import: `{package_name}`."

        result.rules.append(self.make_rule(
            rule_id="python.conventions.import_aliases",
            category="language",
            title=f"Python import path ({layout}-layout)",
            description=desc,
            confidence=0.85,
            language="python",
            evidence=[],
            stats={
                "layout": layout,
                "package_name": package_name,
            },
        ))
