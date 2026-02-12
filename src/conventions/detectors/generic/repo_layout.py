"""Generic repository layout conventions detector."""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..base import BaseDetector, DetectorContext, DetectorResult
from ..registry import DetectorRegistry

# Directories to skip during recursive scanning
_SKIP_DIRS = {
    "node_modules", ".git", "dist", "build", ".next", ".nuxt", ".cache",
    "coverage", "__pycache__", ".tox", ".mypy_cache", ".pytest_cache",
    ".venv", "venv", "env", ".env", ".eggs", "target", ".turbo",
    ".parcel-cache", ".webpack", ".rollup", "out", ".output",
}


@DetectorRegistry.register
class GenericRepoLayoutDetector(BaseDetector):
    """Detect generic repository layout conventions."""

    name = "generic_repo_layout"
    description = "Detects common repository layout patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect common repository layout patterns."""
        result = DetectorResult()

        # Known top-level directory purposes
        common_dirs = {
            "src": "source code",
            "lib": "library code",
            "tests": "tests",
            "test": "tests",
            "docs": "documentation",
            "doc": "documentation",
            "scripts": "scripts",
            "bin": "binaries/scripts",
            "config": "configuration",
            "configs": "configuration",
            "examples": "examples",
            "tools": "tooling",
            ".github": "GitHub configuration",
            ".circleci": "CircleCI configuration",
            ".gitlab": "GitLab configuration",
        }

        # Get workspace descriptions for annotation
        ws_descriptions = self._get_workspace_descriptions(ctx)

        # Build directory tree by scanning repo root children recursively
        found_dirs = []
        tree: dict[str, dict] = {}
        try:
            children = sorted(ctx.repo_root.iterdir())
        except OSError:
            children = []

        for child in children:
            if not child.is_dir():
                continue
            name = child.name
            if name in _SKIP_DIRS:
                continue
            # Only include known common dirs or workspace dirs
            if name not in common_dirs and name not in ws_descriptions:
                continue

            found_dirs.append(name)
            purpose = ws_descriptions.get(name) or common_dirs.get(name, "")
            subtree = self._scan_tree(child, ctx.repo_root, ws_descriptions, max_depth=3, current_depth=1)
            tree[name] = {"purpose": purpose, "children": subtree}

        if found_dirs:
            dir_list = [f"{d} ({common_dirs.get(d, 'workspace')})" for d in found_dirs[:5]]
            description = f"Repository has standard directories: {', '.join(dir_list)}"
            if len(found_dirs) > 5:
                description += f" and {len(found_dirs) - 5} more"

            stats: dict = {
                "found_directories": found_dirs,
                "directory_tree": tree,
            }

            proj_desc = self._extract_project_description(ctx)
            if proj_desc:
                stats["project_description"] = proj_desc

            result.rules.append(self.make_rule(
                rule_id="generic.conventions.repo_layout",
                category="structure",
                title="Standard repository layout",
                description=description,
                confidence=min(0.9, 0.5 + len(found_dirs) * 0.05),
                language="generic",
                evidence=[],
                stats=stats,
            ))

        # Check for common config files
        config_files = {
            "README.md": "documentation",
            "README.rst": "documentation",
            "LICENSE": "license",
            "LICENSE.md": "license",
            "LICENSE.txt": "license",
            "LICENSE.rst": "license",
            "CHANGES.rst": "changelog",
            "CHANGES.md": "changelog",
            "HISTORY.md": "changelog",
            "HISTORY.rst": "changelog",
            "CONTRIBUTING.md": "contributing guidelines",
            "CHANGELOG.md": "changelog",
            "CODE_OF_CONDUCT.md": "code of conduct",
            ".gitignore": "git configuration",
            ".editorconfig": "editor configuration",
            "Makefile": "build automation",
            "docker-compose.yml": "Docker Compose",
            "docker-compose.yaml": "Docker Compose",
            "Dockerfile": "Docker",
            ".pre-commit-config.yaml": "pre-commit hooks",
        }

        found_files = []
        for file_name, purpose in config_files.items():
            file_path = ctx.repo_root / file_name
            if file_path.is_file():
                found_files.append((file_name, purpose))

        if len(found_files) >= 3:
            file_list = [f[0] for f in found_files[:5]]
            description = f"Repository has standard files: {', '.join(file_list)}"
            if len(found_files) > 5:
                description += f" and {len(found_files) - 5} more"

            result.rules.append(self.make_rule(
                rule_id="generic.conventions.standard_files",
                category="structure",
                title="Standard repository files",
                description=description,
                confidence=min(0.85, 0.4 + len(found_files) * 0.05),
                language="generic",
                evidence=[],
                stats={
                    "found_files": [f[0] for f in found_files],
                },
            ))

        return result

    @classmethod
    def _scan_tree(
        cls,
        directory: Path,
        repo_root: Path,
        ws_descriptions: dict[str, str],
        max_depth: int = 3,
        current_depth: int = 0,
    ) -> dict:
        """Recursively scan directory tree, returning nested dict.

        Returns: {child_name: {"purpose": str, "children": {nested...}}}
        """
        if current_depth >= max_depth:
            return {}

        result: dict = {}
        try:
            children = sorted(directory.iterdir())
        except OSError:
            return {}

        for child in children:
            if not child.is_dir():
                continue
            name = child.name
            if name in _SKIP_DIRS or (name.startswith(".") and current_depth > 0):
                continue

            rel = str(child.relative_to(repo_root))
            purpose = ws_descriptions.get(rel, "")
            subtree = cls._scan_tree(child, repo_root, ws_descriptions, max_depth, current_depth + 1)
            result[name] = {"purpose": purpose, "children": subtree}

        return result

    @staticmethod
    def _extract_project_description(ctx: DetectorContext) -> str:
        """Extract a project description from manifest files."""
        # Try package.json
        pkg_json = ctx.repo_root / "package.json"
        if pkg_json.is_file():
            try:
                data = json.loads(pkg_json.read_text())
                desc = data.get("description", "").strip('"')
                if desc and len(desc) > 5:
                    return desc.strip()
            except (json.JSONDecodeError, OSError):
                pass

        # Try pyproject.toml (regex — no toml parser dependency)
        pyproject = ctx.repo_root / "pyproject.toml"
        if pyproject.is_file():
            try:
                content = pyproject.read_text()
                m = re.search(r'(?:^|\n)description\s*=\s*"([^"]+)"', content)
                if m and len(m.group(1)) > 5:
                    return m.group(1).strip()
            except OSError:
                pass

        # Try Cargo.toml
        cargo = ctx.repo_root / "Cargo.toml"
        if cargo.is_file():
            try:
                content = cargo.read_text()
                m = re.search(r'(?:^|\n)description\s*=\s*"([^"]+)"', content)
                if m and len(m.group(1)) > 5:
                    return m.group(1).strip()
            except OSError:
                pass

        return ""

    @staticmethod
    def _get_workspace_descriptions(ctx: DetectorContext) -> dict[str, str]:
        """Build a map of directory relative paths to descriptions from workspace configs."""
        descriptions: dict[str, str] = {}
        pkg_json = ctx.repo_root / "package.json"
        if pkg_json.is_file():
            try:
                data = json.loads(pkg_json.read_text())
                workspaces = data.get("workspaces", [])
                if isinstance(workspaces, dict):
                    workspaces = workspaces.get("packages", [])
                for pattern in workspaces:
                    if pattern.endswith("/*"):
                        # Glob pattern — resolve to actual child directories
                        parent = ctx.repo_root / pattern[:-2]
                        if parent.is_dir():
                            try:
                                for child in sorted(parent.iterdir()):
                                    if child.is_dir() and not child.name.startswith("."):
                                        rel = str(child.relative_to(ctx.repo_root))
                                        desc = _read_pkg_description(child)
                                        descriptions[rel] = desc
                                        # Also register the parent as a workspace root
                                        parent_rel = pattern[:-2]
                                        if parent_rel not in descriptions:
                                            descriptions[parent_rel] = ""
                            except OSError:
                                pass
                    else:
                        ws_dir = ctx.repo_root / pattern
                        if ws_dir.is_dir():
                            desc = _read_pkg_description(ws_dir)
                            descriptions[pattern] = desc
            except (json.JSONDecodeError, OSError):
                pass
        return descriptions


def _read_pkg_description(directory: Path) -> str:
    """Read description from a package.json in the given directory."""
    pkg = directory / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(pkg.read_text())
            return (data.get("description", "") or "").strip('"')
        except (json.JSONDecodeError, OSError):
            pass
    return ""
